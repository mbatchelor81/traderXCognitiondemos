"""Trade processing service layer."""
import logging
import time
from datetime import datetime
from typing import Dict, List

import httpx
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.config import (
    TENANT_ALLOWED_SIDES, TENANT_AUTO_SETTLE,
    MIN_TRADE_QUANTITY, MAX_TRADE_QUANTITY,
    ACCOUNT_SERVICE_URL, REFERENCE_DATA_SERVICE_URL,
)
from app.models import Trade, Position

logger = logging.getLogger(__name__)

_sio = None


def set_socketio_server(sio):
    global _sio
    _sio = sio
    logger.info("Socket.io server reference set in trading service")


async def validate_account_exists(account_id: int) -> bool:
    """Validate account exists via Account Service HTTP call."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{ACCOUNT_SERVICE_URL}/account/{account_id}", timeout=5.0)
            return resp.status_code == 200
    except httpx.RequestError as e:
        logger.warning("Account service unavailable: %s", str(e))
        return False


async def validate_security_exists(security: str) -> bool:
    """Validate security exists via Reference Data Service HTTP call."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{REFERENCE_DATA_SERVICE_URL}/stocks/{security}", timeout=5.0)
            return resp.status_code == 200
    except httpx.RequestError as e:
        logger.warning("Reference data service unavailable: %s", str(e))
        return False


def update_position(db: Session, account_id: int, security: str,
                    quantity_delta: int, tenant_id: str) -> Position:
    position = db.query(Position).filter(
        Position.account_id == account_id,
        Position.security == security,
        Position.tenant_id == tenant_id,
    ).first()
    if position is None:
        position = Position(
            account_id=account_id, security=security,
            tenant_id=tenant_id, quantity=0, updated=datetime.utcnow(),
        )
        db.add(position)
    position.quantity = position.quantity + quantity_delta
    position.updated = datetime.utcnow()
    db.flush()
    return position


async def process_trade(db: Session, account_id: int, security: str,
                        side: str, quantity: int, tenant_id: str) -> Dict:
    start_time = time.time()
    logger.info("Processing trade: account=%d security=%s side=%s qty=%d tenant=%s",
                account_id, security, side, quantity, tenant_id)

    if side not in TENANT_ALLOWED_SIDES:
        return {"success": False, "error": f"Invalid trade side: {side}", "trade": None, "position": None}

    if not (MIN_TRADE_QUANTITY <= quantity <= MAX_TRADE_QUANTITY):
        return {"success": False, "error": f"Invalid quantity: {quantity}", "trade": None, "position": None}

    if not await validate_account_exists(account_id):
        return {"success": False, "error": f"Account {account_id} not found", "trade": None, "position": None}

    if not await validate_security_exists(security):
        return {"success": False, "error": f"Security {security} not found", "trade": None, "position": None}

    trade = Trade(
        tenant_id=tenant_id, account_id=account_id, security=security,
        side=side, quantity=quantity, state="New",
        created=datetime.utcnow(), updated=datetime.utcnow(),
    )
    db.add(trade)
    db.flush()

    trade.state = "Processing"
    trade.updated = datetime.utcnow()
    db.flush()

    quantity_delta = quantity if side == "Buy" else -quantity
    position = update_position(db, account_id, security, quantity_delta, tenant_id)

    if TENANT_AUTO_SETTLE:
        trade.state = "Settled"
        trade.updated = datetime.utcnow()

    db.commit()
    db.refresh(trade)
    db.refresh(position)

    sio = _sio
    if sio is not None:
        try:
            trade_room = f"/accounts/{trade.account_id}/trades"
            pos_room = f"/accounts/{position.account_id}/positions"
            await sio.emit("publish", {"topic": trade_room, "payload": trade.to_dict()}, room=trade_room)
            await sio.emit("publish", {"topic": pos_room, "payload": position.to_dict()}, room=pos_room)
        except Exception as e:
            logger.error("Error publishing Socket.io events: %s", str(e))

    elapsed_ms = (time.time() - start_time) * 1000
    logger.info("Trade processed: id=%d state=%s elapsed=%.2fms", trade.id, trade.state, elapsed_ms)

    return {"success": True, "error": None, "trade": trade.to_dict(), "position": position.to_dict()}


def get_trades_for_account(db: Session, account_id: int, tenant_id: str) -> List[Trade]:
    return db.query(Trade).filter(
        Trade.account_id == account_id, Trade.tenant_id == tenant_id,
    ).order_by(desc(Trade.created)).all()


def get_all_trades(db: Session, tenant_id: str) -> List[Trade]:
    return db.query(Trade).filter(Trade.tenant_id == tenant_id).order_by(desc(Trade.created)).all()
