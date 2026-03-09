"""
Trade processor for trades-service.
Handles trade validation, processing, position updates, and Socket.IO publishing.
Account validation is done via HTTP call to users-service.
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
    TENANT_AUTO_SETTLE,
    TENANT_ALLOWED_SIDES,
    MAX_TRADE_QUANTITY,
    MIN_TRADE_QUANTITY,
    USERS_SERVICE_URL,
)
from app.models.trade import Trade
from app.models.position import Position
from app.services.reference_data import find_stock_by_ticker

logger = logging.getLogger(__name__)

# Module-level Socket.io server reference
_sio = None


def set_socketio_server(sio):
    """Set the Socket.io server instance."""
    global _sio
    _sio = sio
    logger.info("Socket.io server reference set in trade_processor")


def get_socketio_server():
    """Get the Socket.io server instance."""
    return _sio


def _now_utc() -> datetime:
    """Return current UTC datetime."""
    return datetime.utcnow()


# =============================================================================
# Trade Validation
# =============================================================================

async def validate_account_exists(account_id: int, tenant_id: str) -> bool:
    """Validate account exists via async HTTP call to users-service."""
    try:
        url = f"{USERS_SERVICE_URL}/account/{account_id}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers={"X-Tenant-ID": tenant_id}, timeout=5.0)
        if resp.status_code == 200:
            logger.info("Account %d validated via users-service", account_id)
            return True
        logger.warning("Account %d not found in users-service (status %d)",
                       account_id, resp.status_code)
        return False
    except httpx.RequestError as e:
        logger.error("Failed to reach users-service for account validation: %s", e)
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
    """Comprehensive trade validation."""
    if side not in ("Buy", "Sell"):
        return False, f"Invalid trade side: {side}. Must be 'Buy' or 'Sell'."

    if not (MIN_TRADE_QUANTITY <= quantity <= MAX_TRADE_QUANTITY):
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
            updated=_now_utc(),
        )
        db.add(position)

    position.quantity = position.quantity + quantity_delta
    position.updated = _now_utc()
    db.flush()
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


def transition_trade_state(db: Session, trade: Trade, new_state: str) -> bool:
    """Transition a trade to a new state."""
    allowed = VALID_STATE_TRANSITIONS.get(trade.state, [])
    if new_state not in allowed:
        logger.error("Invalid state transition: %s -> %s for trade %d",
                     trade.state, new_state, trade.id)
        return False

    trade.state = new_state
    trade.updated = _now_utc()
    db.flush()
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
                        side: str, quantity: int, tenant_id: str) -> Dict:
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
        created=_now_utc(),
        updated=_now_utc(),
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
    logger.info("Trade processed: id=%d state=%s elapsed=%.2fms",
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
