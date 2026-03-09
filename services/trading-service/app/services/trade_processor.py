"""Trade processing service — validates, creates, and settles trades.

Cross-service calls:
- Account Service: validate account exists
- Reference Data Service: validate security exists
- Position Service: update positions after trade settles
"""

import logging
import time
from datetime import datetime
from typing import Dict

import httpx
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.config import (
    TENANT_ID, TENANT_ALLOWED_SIDES, TENANT_AUTO_SETTLE,
    MIN_TRADE_QUANTITY, MAX_TRADE_QUANTITY,
    ACCOUNT_SERVICE_URL, REFERENCE_DATA_SERVICE_URL, POSITION_SERVICE_URL,
)
from app.models.trade import Trade

logger = logging.getLogger(__name__)

# Module-level Socket.io server reference
_sio = None


def set_socketio_server(sio):
    global _sio
    _sio = sio


def _validate_account(account_id: int) -> bool:
    """Validate account exists via Account Service HTTP call."""
    try:
        resp = httpx.get(
            f"{ACCOUNT_SERVICE_URL}/account/{account_id}",
            timeout=5.0,
        )
        return resp.status_code == 200
    except httpx.RequestError as e:
        logger.warning("Account service unavailable: %s", str(e))
        return True  # Allow if service is unavailable


def _validate_security(security: str) -> bool:
    """Validate security exists via Reference Data Service HTTP call."""
    try:
        resp = httpx.get(
            f"{REFERENCE_DATA_SERVICE_URL}/stocks/{security}",
            timeout=5.0,
        )
        return resp.status_code == 200
    except httpx.RequestError as e:
        logger.warning("Reference data service unavailable: %s", str(e))
        return True  # Allow if service is unavailable


def _update_position(account_id: int, security: str, side: str, quantity: int,
                     tenant_id: str) -> dict:
    """Update position via Position Service HTTP call."""
    try:
        resp = httpx.post(
            f"{POSITION_SERVICE_URL}/positions/update",
            json={
                "accountId": account_id,
                "security": security,
                "side": side,
                "quantity": quantity,
                "tenant_id": tenant_id,
            },
            timeout=5.0,
        )
        if resp.status_code == 200:
            return resp.json()
        logger.warning("Position service returned %d", resp.status_code)
    except httpx.RequestError as e:
        logger.warning("Position service unavailable: %s", str(e))
    return {}


def _now_utc() -> datetime:
    return datetime.utcnow()


async def process_trade(db: Session, account_id: int, security: str,
                        side: str, quantity: int, tenant_id: str) -> Dict:
    """Process a trade order end-to-end."""
    start_time = time.time()

    # Validate side
    if side not in TENANT_ALLOWED_SIDES:
        return {"success": False, "error": f"Invalid trade side: {side}",
                "trade": None, "position": None}

    # Validate quantity
    if not (MIN_TRADE_QUANTITY <= quantity <= MAX_TRADE_QUANTITY):
        return {"success": False, "error": f"Invalid quantity: {quantity}",
                "trade": None, "position": None}

    # Validate account via HTTP
    if not _validate_account(account_id):
        return {"success": False, "error": f"Account {account_id} not found",
                "trade": None, "position": None}

    # Validate security via HTTP
    if not _validate_security(security):
        return {"success": False, "error": f"Security {security} not found",
                "trade": None, "position": None}

    # Create trade
    trade = Trade(
        tenant_id=tenant_id, account_id=account_id, security=security,
        side=side, quantity=quantity, state="New",
        created=_now_utc(), updated=_now_utc(),
    )
    db.add(trade)
    db.flush()

    # Transition to Processing
    trade.state = "Processing"
    trade.updated = _now_utc()
    db.flush()

    # Auto-settle
    if TENANT_AUTO_SETTLE:
        trade.state = "Settled"
        trade.updated = _now_utc()
        db.flush()

    db.commit()
    db.refresh(trade)

    # Update position via Position Service (after trade committed)
    position_data = _update_position(account_id, security, side, quantity, tenant_id)

    # Publish Socket.io events
    if _sio is not None:
        try:
            trade_room = f"/accounts/{trade.account_id}/trades"
            await _sio.emit("publish", {"topic": trade_room, "payload": trade.to_dict()},
                            room=trade_room)
            if position_data:
                pos_room = f"/accounts/{account_id}/positions"
                await _sio.emit("publish", {"topic": pos_room, "payload": position_data},
                                room=pos_room)
        except Exception as e:
            logger.error("Socket.io publish error: %s", str(e))

    elapsed_ms = (time.time() - start_time) * 1000
    logger.info("Trade processed: id=%d state=%s elapsed=%.2fms",
                trade.id, trade.state, elapsed_ms,
                extra={"tenant_id": tenant_id, "service": "trading-service"})

    return {"success": True, "error": None, "trade": trade.to_dict(),
            "position": position_data}


def get_trades_for_account(db: Session, account_id: int, tenant_id: str):
    return db.query(Trade).filter(
        Trade.account_id == account_id, Trade.tenant_id == tenant_id,
    ).order_by(desc(Trade.created)).all()


def get_all_trades(db: Session, tenant_id: str):
    return db.query(Trade).filter(
        Trade.tenant_id == tenant_id,
    ).order_by(desc(Trade.created)).all()
