"""
Trade processing for the trading-service.

Ported from the monolith's `trade_processor` god service, reduced to the trading
domain: validation rules, the trade state machine, trade queries and Socket.io
publishing. Everything outside the domain — account existence and users,
security reference data, positions — is fetched over HTTP from the owning
service.
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.clients import account_client, position_client, reference_data_client
from app.config import (
    ALLOWED_SIDES,
    AUTO_SETTLE,
    MAX_ACCOUNTS,
    MAX_TRADE_QUANTITY,
    MIN_TRADE_QUANTITY,
)
from app.logging_config import get_logger
from app.models.trade import Trade
from app.utils.helpers import (
    log_trade_event,
    now_utc,
    validate_trade_quantity,
    validate_trade_side,
)

logger = get_logger(__name__)

# Module-level Socket.io server reference — set by main.py at startup
_sio = None


def set_socketio_server(sio) -> None:
    """Set the Socket.io server instance. Called once at app startup."""
    global _sio
    _sio = sio
    logger.info("socketio_server_registered")


def get_socketio_server():
    """Get the Socket.io server instance."""
    return _sio


# =============================================================================
# Trade Validation — cross-domain checks go over HTTP
# =============================================================================

async def validate_trade_request(
    account_id: int, security: str, side: str, quantity: int, tenant_id: str
) -> Tuple[bool, str]:
    """
    Comprehensive trade validation combining all checks.
    Returns (is_valid, error_message). Raises PeerServiceError when a peer
    service needed for validation cannot be reached.
    """
    logger.info(
        "trade_validation_started",
        extra={
            "account_id": account_id,
            "security": security,
            "side": side,
            "quantity": quantity,
            "tenant_id": tenant_id,
        },
    )

    if not validate_trade_side(side):
        return False, f"Invalid trade side: {side}. Must be 'Buy' or 'Sell'."

    if not validate_trade_quantity(quantity):
        return False, (
            f"Invalid trade quantity: {quantity}. "
            f"Must be between {MIN_TRADE_QUANTITY} and {MAX_TRADE_QUANTITY}."
        )

    if not await account_client.account_exists(account_id):
        return False, f"Account {account_id} not found for tenant {tenant_id}."

    if not await account_client.account_has_users(account_id):
        return False, f"Account {account_id} has no users assigned."

    if not await reference_data_client.security_exists(security):
        return False, f"Security {security} not found in reference data."

    if side not in ALLOWED_SIDES:
        return False, (
            f"Trade side '{side}' not allowed for tenant {tenant_id}. "
            f"Allowed: {ALLOWED_SIDES}"
        )

    # Selling more than the current position is allowed but logged — the
    # monolith deliberately behaves this way.
    if side == "Sell":
        current_position = await position_client.get_position_quantity(
            account_id, security
        )
        if current_position < quantity:
            logger.warning(
                "sell_exceeds_position",
                extra={
                    "account_id": account_id,
                    "security": security,
                    "quantity": quantity,
                    "current_position": current_position,
                    "tenant_id": tenant_id,
                },
            )

    logger.info("trade_validation_passed", extra={"account_id": account_id})
    return True, ""


# =============================================================================
# Trade State Machine
# =============================================================================

VALID_STATE_TRANSITIONS = {
    "New": ["Processing", "Cancelled"],
    "Processing": ["Settled", "Cancelled"],
    "Settled": [],
    "Cancelled": [],
}


def can_transition(current_state: str, new_state: str) -> bool:
    """Check if a state transition is valid."""
    return new_state in VALID_STATE_TRANSITIONS.get(current_state, [])


def transition_trade_state(db: Session, trade: Trade, new_state: str) -> bool:
    """Transition a trade to a new state. Returns True when it was applied."""
    old_state = trade.state

    if not can_transition(old_state, new_state):
        logger.error(
            "invalid_state_transition",
            extra={
                "trade_id": trade.id,
                "from_state": old_state,
                "to_state": new_state,
            },
        )
        return False

    trade.state = new_state
    trade.updated = now_utc()
    db.flush()

    log_trade_event(
        trade.id,
        trade.account_id,
        f"STATE_CHANGE:{old_state}->{new_state}",
        trade.tenant_id,
    )
    logger.info(
        "trade_state_changed",
        extra={
            "trade_id": trade.id,
            "from_state": old_state,
            "to_state": new_state,
            "tenant_id": trade.tenant_id,
        },
    )
    return True


# =============================================================================
# Socket.io Publishing
# =============================================================================

async def publish_trade_update(trade: Trade) -> None:
    """Publish a trade update via Socket.io."""
    sio = get_socketio_server()
    if sio is None:
        logger.warning("socketio_unavailable", extra={"publish": "trade"})
        return

    room = f"/accounts/{trade.account_id}/trades"
    try:
        await sio.emit("publish", {"topic": room, "payload": trade.to_dict()}, room=room)
        logger.info(
            "trade_update_published",
            extra={"room": room, "trade_id": trade.id, "state": trade.state},
        )
    except Exception as exc:  # noqa: BLE001 — publishing must never fail a trade
        logger.error("trade_publish_failed", extra={"reason": str(exc)})


async def publish_position_update(account_id: int, position: Optional[dict]) -> None:
    """Publish a position update via Socket.io."""
    sio = get_socketio_server()
    if sio is None:
        logger.warning("socketio_unavailable", extra={"publish": "position"})
        return
    if not position:
        return

    room = f"/accounts/{account_id}/positions"
    try:
        await sio.emit("publish", {"topic": room, "payload": position}, room=room)
        logger.info(
            "position_update_published",
            extra={
                "room": room,
                "security": position.get("security"),
                "quantity": position.get("quantity"),
            },
        )
    except Exception as exc:  # noqa: BLE001 — publishing must never fail a trade
        logger.error("position_publish_failed", extra={"reason": str(exc)})


async def publish_trade_and_position(
    trade: Trade, account_id: int, position: Optional[dict]
) -> None:
    """Publish both trade and position updates."""
    await publish_trade_update(trade)
    await publish_position_update(account_id, position)


# =============================================================================
# Core Trade Processing
# =============================================================================

async def process_trade(
    db: Session, account_id: int, security: str, side: str, quantity: int,
    tenant_id: str,
) -> Dict:
    """
    Process a trade order end to end:
    1. Validate the request (account and security checks over HTTP)
    2. Create the trade record (state: New)
    3. Transition to Processing
    4. Apply the position delta via position-service
    5. Transition to Settled when auto-settle is enabled
    6. Publish Socket.io events

    Raises PeerServiceError when a peer service is unreachable; the caller turns
    that into a 502 so a trade is never silently accepted.
    """
    start_time = time.time()
    logger.info(
        "trade_processing_started",
        extra={
            "account_id": account_id,
            "security": security,
            "side": side,
            "quantity": quantity,
            "tenant_id": tenant_id,
        },
    )

    is_valid, error_msg = await validate_trade_request(
        account_id, security, side, quantity, tenant_id
    )
    if not is_valid:
        logger.error(
            "trade_validation_failed",
            extra={"account_id": account_id, "error": error_msg},
        )
        return {"success": False, "error": error_msg, "trade": None, "position": None}

    trade = Trade(
        tenant_id=tenant_id,
        account_id=account_id,
        security=security,
        side=side,
        quantity=quantity,
        state="New",
        created=now_utc(),
        updated=now_utc(),
    )
    db.add(trade)
    db.flush()  # Get the trade ID

    log_trade_event(
        trade.id, account_id, "CREATED", tenant_id,
        f"security={security} side={side} qty={quantity}",
    )

    if not transition_trade_state(db, trade, "Processing"):
        db.rollback()
        return {
            "success": False,
            "error": "Failed to process trade",
            "trade": None,
            "position": None,
        }

    quantity_delta = quantity if side == "Buy" else -quantity
    try:
        position = await position_client.apply_position_delta(
            account_id, security, quantity_delta
        )
    except Exception:
        db.rollback()
        raise

    if AUTO_SETTLE:
        transition_trade_state(db, trade, "Settled")
    else:
        logger.info(
            "trade_left_in_processing",
            extra={"trade_id": trade.id, "reason": "auto_settle_disabled"},
        )

    db.commit()
    db.refresh(trade)

    await publish_trade_and_position(trade, account_id, position)

    elapsed_ms = (time.time() - start_time) * 1000
    log_trade_event(
        trade.id, account_id, "COMPLETED", tenant_id,
        f"elapsed_ms={elapsed_ms:.2f} final_state={trade.state}",
    )
    logger.info(
        "trade_processing_complete",
        extra={
            "trade_id": trade.id,
            "state": trade.state,
            "duration_ms": round(elapsed_ms, 2),
            "tenant_id": tenant_id,
        },
    )

    return {
        "success": True,
        "error": None,
        "trade": trade.to_dict(),
        "position": position,
    }


# =============================================================================
# Trade Queries
# =============================================================================

def get_trade_by_id(db: Session, trade_id: int, tenant_id: str) -> Optional[Trade]:
    """Get a single trade by ID."""
    return db.query(Trade).filter(
        Trade.id == trade_id,
        Trade.tenant_id == tenant_id,
    ).first()


def get_trades_for_account(db: Session, account_id: int, tenant_id: str) -> List[Trade]:
    """Get all trades for an account, newest first."""
    return db.query(Trade).filter(
        Trade.account_id == account_id,
        Trade.tenant_id == tenant_id,
    ).order_by(desc(Trade.created)).all()


def get_all_trades(db: Session, tenant_id: str) -> List[Trade]:
    """Get all trades for the tenant, newest first."""
    return db.query(Trade).filter(
        Trade.tenant_id == tenant_id,
    ).order_by(desc(Trade.created)).all()


def count_trades_for_account(db: Session, account_id: int, tenant_id: str) -> int:
    """Count trades for an account."""
    return db.query(func.count(Trade.id)).filter(
        Trade.account_id == account_id,
        Trade.tenant_id == tenant_id,
    ).scalar() or 0


def get_trades_by_state(db: Session, state: str, tenant_id: str) -> List[Trade]:
    """Get all trades in a specific state."""
    return db.query(Trade).filter(
        Trade.state == state,
        Trade.tenant_id == tenant_id,
    ).order_by(desc(Trade.created)).all()


def get_trades_by_security(db: Session, security: str, tenant_id: str) -> List[Trade]:
    """Get all trades for a specific security."""
    return db.query(Trade).filter(
        Trade.security == security,
        Trade.tenant_id == tenant_id,
    ).order_by(desc(Trade.created)).all()


def get_trade_history(
    db: Session, account_id: int, security: str, tenant_id: str
) -> List[Dict]:
    """Get the complete trade history for an account/security pair."""
    trades = db.query(Trade).filter(
        Trade.account_id == account_id,
        Trade.security == security,
        Trade.tenant_id == tenant_id,
    ).order_by(Trade.created).all()
    return [t.to_dict() for t in trades]


# =============================================================================
# Batch Processing Utilities
# =============================================================================

def settle_pending_trades(db: Session, tenant_id: str) -> int:
    """Settle every trade still in Processing state. Returns the count settled."""
    pending = db.query(Trade).filter(
        Trade.tenant_id == tenant_id,
        Trade.state == "Processing",
    ).all()

    settled_count = 0
    for trade in pending:
        if transition_trade_state(db, trade, "Settled"):
            settled_count += 1
            log_trade_event(trade.id, trade.account_id, "BATCH_SETTLED", tenant_id)

    if settled_count > 0:
        db.commit()

    logger.info(
        "batch_settle_complete",
        extra={"settled_count": settled_count, "tenant_id": tenant_id},
    )
    return settled_count


def cancel_stale_trades(db: Session, tenant_id: str, max_age_hours: int = 24) -> int:
    """Cancel trades stuck in New/Processing for too long. Returns the count."""
    cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)

    stale = db.query(Trade).filter(
        Trade.tenant_id == tenant_id,
        Trade.state.in_(["New", "Processing"]),
        Trade.created < cutoff,
    ).all()

    cancelled_count = 0
    for trade in stale:
        if transition_trade_state(db, trade, "Cancelled"):
            cancelled_count += 1
            log_trade_event(
                trade.id, trade.account_id, "STALE_CANCELLED", tenant_id,
                f"created={trade.created.isoformat()}",
            )

    if cancelled_count > 0:
        db.commit()

    logger.info(
        "stale_cancel_complete",
        extra={"cancelled_count": cancelled_count, "tenant_id": tenant_id},
    )
    return cancelled_count


# =============================================================================
# Tenant Business Rules (resolved from config for the startup tenant only)
# =============================================================================

def get_tenant_trade_restrictions() -> Dict:
    """Trade restrictions in force for this deployment's tenant."""
    return {
        "allowedSides": ALLOWED_SIDES,
        "autoSettle": AUTO_SETTLE,
        "maxQuantity": MAX_TRADE_QUANTITY,
        "minQuantity": MIN_TRADE_QUANTITY,
        "maxAccounts": MAX_ACCOUNTS,
    }
