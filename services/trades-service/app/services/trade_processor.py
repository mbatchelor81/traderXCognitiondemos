"""Trade Processor for Trades Service.

Handles trade validation, processing, position calculation, and Socket.io publishing.
Account validation is done via HTTP call to the Users Service (no direct DB access).
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import httpx
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.config import (
    TENANT_ID,
    TENANT_ALLOWED_SIDES,
    TENANT_AUTO_SETTLE,
    MIN_TRADE_QUANTITY,
    MAX_TRADE_QUANTITY,
    USERS_SERVICE_URL,
)
from app.models.trade import Trade
from app.models.position import Position
from app.utils.helpers import (
    find_stock_by_ticker,
    log_audit_event,
    now_utc,
    validate_trade_side,
    validate_trade_quantity,
)

logger = logging.getLogger(__name__)

# Module-level Socket.io server reference
_sio = None


def set_socketio_server(sio):
    """Set the Socket.io server instance. Called once at app startup."""
    global _sio
    _sio = sio
    logger.info("Socket.io server reference set in trade_processor")


def get_socketio_server():
    """Get the Socket.io server instance."""
    return _sio


# =============================================================================
# Account Validation via HTTP (cross-service call to Users Service)
# =============================================================================

async def validate_account_exists(account_id: int, tenant_id: str) -> bool:
    """Validate that an account exists by calling the Users Service over HTTP."""
    logger.debug("Validating account %d via Users Service", account_id)
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{USERS_SERVICE_URL}/account/{account_id}",
                headers={"X-Tenant-ID": tenant_id},
                timeout=5.0,
            )
        if response.status_code == 200:
            logger.info("Account %d validated via Users Service", account_id)
            return True
        logger.warning("Account %d not found in Users Service (status %d)",
                       account_id, response.status_code)
        return False
    except httpx.RequestError as e:
        logger.error("Error calling Users Service for account validation: %s", str(e))
        return False


def validate_security_exists(security: str) -> bool:
    """Validate that a security/ticker exists in reference data."""
    stock = find_stock_by_ticker(security)
    if stock is None:
        logger.warning("Security %s not found in reference data", security)
        return False
    return True


async def validate_trade_request(db: Session, account_id: int, security: str,
                                 side: str, quantity: int,
                                 tenant_id: str) -> Tuple[bool, str]:
    """Comprehensive trade validation combining all checks."""
    if not validate_trade_side(side):
        return False, f"Invalid trade side: {side}. Must be 'Buy' or 'Sell'."

    if not validate_trade_quantity(quantity, MIN_TRADE_QUANTITY, MAX_TRADE_QUANTITY):
        return False, (f"Invalid trade quantity: {quantity}. "
                       f"Must be between {MIN_TRADE_QUANTITY} and {MAX_TRADE_QUANTITY}.")

    if not await validate_account_exists(account_id, tenant_id):
        return False, f"Account {account_id} not found for tenant {tenant_id}."

    if not validate_security_exists(security):
        return False, f"Security {security} not found in reference data."

    if side not in TENANT_ALLOWED_SIDES:
        return False, (f"Trade side '{side}' not allowed for tenant {tenant_id}. "
                       f"Allowed: {TENANT_ALLOWED_SIDES}")

    return True, ""


# =============================================================================
# Position Management
# =============================================================================

def get_current_position_quantity(db: Session, account_id: int, security: str,
                                 tenant_id: str) -> int:
    """Get the current position quantity for an account/security pair."""
    position = db.query(Position).filter(
        Position.account_id == account_id,
        Position.security == security,
        Position.tenant_id == tenant_id,
    ).first()
    return position.quantity if position else 0


def update_position(db: Session, account_id: int, security: str,
                    quantity_delta: int, tenant_id: str) -> Position:
    """Update or create a position for an account/security pair."""
    position = db.query(Position).filter(
        Position.account_id == account_id,
        Position.security == security,
        Position.tenant_id == tenant_id,
    ).first()

    if position is None:
        position = Position(
            account_id=account_id,
            security=security,
            tenant_id=tenant_id,
            quantity=0,
            updated=now_utc(),
        )
        db.add(position)

    old_quantity = position.quantity
    position.quantity = position.quantity + quantity_delta
    position.updated = now_utc()
    db.flush()

    logger.info("Position updated: account=%d security=%s old_qty=%d new_qty=%d",
                account_id, security, old_quantity, position.quantity)
    return position


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
    """Transition a trade to a new state."""
    old_state = trade.state
    if not can_transition(old_state, new_state):
        logger.error("Invalid state transition: %s -> %s for trade %d",
                     old_state, new_state, trade.id)
        return False

    trade.state = new_state
    trade.updated = now_utc()
    db.flush()
    logger.info("Trade %d state: %s -> %s", trade.id, old_state, new_state)
    return True


# =============================================================================
# Socket.io Publishing
# =============================================================================

async def publish_trade_update(trade: Trade):
    """Publish a trade update via Socket.io."""
    sio = get_socketio_server()
    if sio is None:
        return

    room = f"/accounts/{trade.account_id}/trades"
    try:
        await sio.emit("publish", {"topic": room, "payload": trade.to_dict()}, room=room)
    except Exception as e:
        logger.error("Error publishing trade update: %s", str(e))


async def publish_position_update(position: Position):
    """Publish a position update via Socket.io."""
    sio = get_socketio_server()
    if sio is None:
        return

    room = f"/accounts/{position.account_id}/positions"
    try:
        await sio.emit("publish", {"topic": room, "payload": position.to_dict()}, room=room)
    except Exception as e:
        logger.error("Error publishing position update: %s", str(e))


# =============================================================================
# Core Trade Processing
# =============================================================================

async def process_trade(db: Session, account_id: int, security: str,
                        side: str, quantity: int,
                        tenant_id: str) -> Dict:
    """Process a trade order end-to-end."""
    start_time = time.time()

    # Validate
    is_valid, error_msg = await validate_trade_request(
        db, account_id, security, side, quantity, tenant_id
    )
    if not is_valid:
        return {"success": False, "error": error_msg, "trade": None, "position": None}

    # Create trade record
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
    db.flush()

    # Transition to Processing
    if not transition_trade_state(db, trade, "Processing"):
        return {"success": False, "error": "Failed to process trade",
                "trade": trade.to_dict(), "position": None}

    # Update position
    quantity_delta = quantity if side == "Buy" else -quantity
    position = update_position(db, account_id, security, quantity_delta, tenant_id)

    # Auto-settle if configured
    if TENANT_AUTO_SETTLE:
        transition_trade_state(db, trade, "Settled")

    db.commit()
    db.refresh(trade)
    db.refresh(position)

    # Publish Socket.io events
    try:
        await publish_trade_update(trade)
        await publish_position_update(position)
    except Exception as e:
        logger.error("Error publishing Socket.io events: %s", str(e))

    elapsed_ms = (time.time() - start_time) * 1000
    logger.info("Trade processing complete: trade_id=%d state=%s elapsed=%.2fms",
                trade.id, trade.state, elapsed_ms)

    return {
        "success": True,
        "error": None,
        "trade": trade.to_dict(),
        "position": position.to_dict(),
    }


# =============================================================================
# Trade Queries
# =============================================================================

def get_trades_for_account(db: Session, account_id: int,
                           tenant_id: str) -> List[Trade]:
    """Get all trades for an account."""
    return db.query(Trade).filter(
        Trade.account_id == account_id,
        Trade.tenant_id == tenant_id,
    ).order_by(desc(Trade.created)).all()


def get_all_trades(db: Session, tenant_id: str) -> List[Trade]:
    """Get all trades for a tenant."""
    return db.query(Trade).filter(
        Trade.tenant_id == tenant_id,
    ).order_by(desc(Trade.created)).all()


def count_trades_for_account(db: Session, account_id: int,
                             tenant_id: str) -> int:
    """Count trades for an account."""
    return db.query(func.count(Trade.id)).filter(
        Trade.account_id == account_id,
        Trade.tenant_id == tenant_id,
    ).scalar() or 0
