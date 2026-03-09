"""
Trading Service - handles trade validation, processing, and state machine.

Extracted from the former trade_processor.py god service.
This module owns trade lifecycle logic only.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.config import (
    MAX_TRADE_QUANTITY,
    MIN_TRADE_QUANTITY,
    ALLOWED_SIDES,
    AUTO_SETTLE,
)
from app.models.trade import Trade
from app.services.account_service import get_account_by_id
from app.services.position_service import (
    get_current_position_quantity,
    update_position,
)
from app.utils.helpers import (
    find_stock_by_ticker,
    log_trade_event,
    now_utc,
    validate_trade_side,
    validate_trade_quantity,
)

logger = logging.getLogger(__name__)

_sio = None


def set_socketio_server(sio):
    """Set the Socket.io server instance. Called once at app startup."""
    global _sio
    _sio = sio
    logger.info("Socket.io server reference set in trading_service")


def get_socketio_server():
    """Get the Socket.io server instance."""
    return _sio


# =============================================================================
# Trade Validation
# =============================================================================

def validate_account_exists(db: Session, account_id: int) -> bool:
    """Validate that an account exists by calling account_service."""
    account = get_account_by_id(db, account_id)
    if account is None:
        logger.warning("Account %d not found", account_id)
        return False
    logger.info("Account %d validated: %s", account_id, account.display_name)
    return True


def validate_security_exists(security: str) -> bool:
    """Validate that a security/ticker exists in reference data."""
    stock = find_stock_by_ticker(security)
    if stock is None:
        logger.warning("Security %s not found in reference data", security)
        return False
    logger.info("Security %s validated: %s", security, stock["companyName"])
    return True


def validate_trade_request(db: Session, account_id: int, security: str,
                           side: str, quantity: int) -> Tuple[bool, str]:
    """
    Comprehensive trade validation combining all checks.
    Returns (is_valid, error_message).
    """
    logger.info("Validating trade request: account=%d security=%s side=%s qty=%d",
                account_id, security, side, quantity)

    if not validate_trade_side(side):
        return False, f"Invalid trade side: {side}. Must be 'Buy' or 'Sell'."

    if not validate_trade_quantity(quantity):
        return False, (f"Invalid trade quantity: {quantity}. "
                       f"Must be between {MIN_TRADE_QUANTITY} and {MAX_TRADE_QUANTITY}.")

    if not validate_account_exists(db, account_id):
        return False, f"Account {account_id} not found."

    if not validate_security_exists(security):
        return False, f"Security {security} not found in reference data."

    if side not in ALLOWED_SIDES:
        return False, f"Trade side '{side}' not allowed. Allowed: {ALLOWED_SIDES}"

    if side == "Sell":
        current_position = get_current_position_quantity(db, account_id, security)
        if current_position < quantity:
            logger.warning(
                "Sell quantity %d exceeds current position %d for "
                "account %d security %s. Allowing trade but logging warning.",
                quantity, current_position, account_id, security
            )

    logger.info("Trade request validated successfully")
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
    allowed = VALID_STATE_TRANSITIONS.get(current_state, [])
    return new_state in allowed


def transition_trade_state(db: Session, trade: Trade, new_state: str) -> bool:
    """Transition a trade to a new state. Returns True if successful."""
    old_state = trade.state
    if not can_transition(old_state, new_state):
        logger.error("Invalid state transition: %s -> %s for trade %d",
                     old_state, new_state, trade.id)
        return False

    trade.state = new_state
    trade.updated = now_utc()
    db.flush()
    log_trade_event(trade.id, trade.account_id,
                    f"STATE_CHANGE:{old_state}->{new_state}")
    logger.info("Trade %d state: %s -> %s", trade.id, old_state, new_state)
    return True


# =============================================================================
# Socket.io Publishing
# =============================================================================

async def publish_trade_update(trade: Trade):
    """Publish a trade update via Socket.io."""
    sio = get_socketio_server()
    if sio is None:
        logger.warning("Socket.io server not initialized, skipping trade publish")
        return
    room = f"/accounts/{trade.account_id}/trades"
    trade_data = trade.to_dict()
    try:
        await sio.emit("publish", {"topic": room, "payload": trade_data}, room=room)
        logger.info("Published trade update to room %s: trade_id=%d state=%s",
                     room, trade.id, trade.state)
    except Exception as e:
        logger.error("Error publishing trade update: %s", str(e))


async def publish_position_update(position):
    """Publish a position update via Socket.io."""
    sio = get_socketio_server()
    if sio is None:
        logger.warning("Socket.io server not initialized, skipping position publish")
        return
    room = f"/accounts/{position.account_id}/positions"
    position_data = position.to_dict()
    try:
        await sio.emit("publish", {"topic": room, "payload": position_data}, room=room)
        logger.info("Published position update to room %s: security=%s qty=%d",
                     room, position.security, position.quantity)
    except Exception as e:
        logger.error("Error publishing position update: %s", str(e))


async def publish_trade_and_position(trade: Trade, position):
    """Publish both trade and position updates."""
    await publish_trade_update(trade)
    await publish_position_update(position)


# =============================================================================
# Core Trade Processing
# =============================================================================

async def process_trade(db: Session, account_id: int, security: str,
                        side: str, quantity: int) -> Dict:
    """
    Process a trade order end-to-end:
    1. Validate the trade request
    2. Create the trade record (state: New)
    3. Transition to Processing
    4. Calculate and update positions
    5. Transition to Settled (if auto-settle enabled)
    6. Publish Socket.io events
    """
    start_time = time.time()
    logger.info("=" * 60)
    logger.info("PROCESSING TRADE ORDER")
    logger.info("Account: %d | Security: %s | Side: %s | Qty: %d",
                account_id, security, side, quantity)

    # Step 1: Validate
    is_valid, error_msg = validate_trade_request(
        db, account_id, security, side, quantity
    )
    if not is_valid:
        logger.error("Trade validation failed: %s", error_msg)
        return {"success": False, "error": error_msg, "trade": None, "position": None}

    # Step 2: Create trade record
    trade = Trade(
        account_id=account_id, security=security, side=side,
        quantity=quantity, state="New", created=now_utc(), updated=now_utc(),
    )
    db.add(trade)
    db.flush()
    log_trade_event(trade.id, account_id, "CREATED",
                    f"security={security} side={side} qty={quantity}")
    logger.info("Trade created with ID: %d", trade.id)

    # Step 3: Transition to Processing
    if not transition_trade_state(db, trade, "Processing"):
        return {"success": False, "error": "Failed to process trade",
                "trade": trade.to_dict(), "position": None}

    # Step 4: Calculate position delta and update
    quantity_delta = quantity if side == "Buy" else -quantity
    position = update_position(db, account_id, security, quantity_delta)

    # Step 5: Check auto-settle config
    if AUTO_SETTLE:
        if transition_trade_state(db, trade, "Settled"):
            logger.info("Trade %d auto-settled", trade.id)
    else:
        logger.info("Trade %d left in Processing (auto-settle disabled)", trade.id)

    db.commit()
    db.refresh(trade)
    db.refresh(position)

    # Step 6: Publish Socket.io events
    try:
        await publish_trade_and_position(trade, position)
    except Exception as e:
        logger.error("Error publishing Socket.io events: %s", str(e))

    elapsed_ms = (time.time() - start_time) * 1000
    log_trade_event(trade.id, account_id, "COMPLETED",
                    f"elapsed_ms={elapsed_ms:.2f} final_state={trade.state}")
    logger.info("Trade processing complete: trade_id=%d state=%s elapsed=%.2fms",
                trade.id, trade.state, elapsed_ms)

    return {"success": True, "error": None,
            "trade": trade.to_dict(), "position": position.to_dict()}


# =============================================================================
# Trade Queries
# =============================================================================

def get_trade_by_id(db: Session, trade_id: int) -> Optional[Trade]:
    """Get a single trade by ID."""
    return db.query(Trade).filter(Trade.id == trade_id).first()


def get_trades_for_account(db: Session, account_id: int) -> List[Trade]:
    """Get all trades for an account."""
    return db.query(Trade).filter(
        Trade.account_id == account_id,
    ).order_by(desc(Trade.created)).all()


def get_all_trades(db: Session) -> List[Trade]:
    """Get all trades."""
    return db.query(Trade).order_by(desc(Trade.created)).all()


def count_trades_for_account(db: Session, account_id: int) -> int:
    """Count trades for an account."""
    return db.query(func.count(Trade.id)).filter(
        Trade.account_id == account_id,
    ).scalar() or 0


def get_trades_by_state(db: Session, state: str) -> List[Trade]:
    """Get all trades in a specific state."""
    return db.query(Trade).filter(
        Trade.state == state,
    ).order_by(desc(Trade.created)).all()


# =============================================================================
# Batch Processing Utilities
# =============================================================================

def settle_pending_trades(db: Session) -> int:
    """Settle all trades in Processing state. Returns count settled."""
    pending = db.query(Trade).filter(Trade.state == "Processing").all()
    settled_count = 0
    for trade in pending:
        if transition_trade_state(db, trade, "Settled"):
            settled_count += 1
            log_trade_event(trade.id, trade.account_id, "BATCH_SETTLED")
    if settled_count > 0:
        db.commit()
    logger.info("Batch settled %d trades", settled_count)
    return settled_count


def cancel_stale_trades(db: Session, max_age_hours: int = 24) -> int:
    """Cancel trades in New/Processing state for too long."""
    cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
    stale = db.query(Trade).filter(
        Trade.state.in_(["New", "Processing"]),
        Trade.created < cutoff,
    ).all()
    cancelled_count = 0
    for trade in stale:
        if transition_trade_state(db, trade, "Cancelled"):
            cancelled_count += 1
            log_trade_event(trade.id, trade.account_id, "STALE_CANCELLED",
                            f"created={trade.created.isoformat()}")
    if cancelled_count > 0:
        db.commit()
    logger.info("Cancelled %d stale trades", cancelled_count)
    return cancelled_count
