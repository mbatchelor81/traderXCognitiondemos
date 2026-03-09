"""
Position Service - owns position CRUD and recalculation.

Extracted from the former trade_processor.py god service.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.position import Position
from app.models.trade import Trade
from app.utils.helpers import log_audit_event, log_position_event, now_utc

logger = logging.getLogger(__name__)


# =============================================================================
# Position Queries
# =============================================================================

def get_current_position_quantity(db: Session, account_id: int,
                                  security: str) -> int:
    """Get the current position quantity for an account/security pair."""
    position = db.query(Position).filter(
        Position.account_id == account_id,
        Position.security == security,
    ).first()
    if position is None:
        return 0
    return position.quantity


def get_positions_for_account(db: Session, account_id: int) -> List[Position]:
    """Get all positions for an account."""
    return db.query(Position).filter(
        Position.account_id == account_id,
    ).all()


def get_all_positions(db: Session) -> List[Position]:
    """Get all positions."""
    return db.query(Position).all()


# =============================================================================
# Position Updates
# =============================================================================

def update_position(db: Session, account_id: int, security: str,
                    quantity_delta: int) -> Position:
    """
    Update or create a position for an account/security pair.
    If position doesn't exist, creates a new one.
    """
    logger.info("Updating position: account=%d security=%s delta=%d",
                account_id, security, quantity_delta)

    position = db.query(Position).filter(
        Position.account_id == account_id,
        Position.security == security,
    ).first()

    if position is None:
        logger.info("Creating new position for account %d security %s",
                     account_id, security)
        position = Position(
            account_id=account_id,
            security=security,
            quantity=0,
            updated=now_utc(),
        )
        db.add(position)

    old_quantity = position.quantity
    position.quantity = position.quantity + quantity_delta
    position.updated = now_utc()
    db.flush()

    log_position_event(
        account_id, security, "UPDATE",
        f"old_qty={old_quantity} new_qty={position.quantity} delta={quantity_delta}"
    )

    logger.info("Position updated: account=%d security=%s old_qty=%d new_qty=%d",
                account_id, security, old_quantity, position.quantity)
    return position


# =============================================================================
# Position Recalculation
# =============================================================================

def recalculate_positions(db: Session, account_id: int) -> List[Position]:
    """
    Recalculate all positions for an account from settled trades.
    Used for reconciliation / maintenance.
    """
    logger.info("Recalculating positions for account %d", account_id)

    trades = db.query(Trade).filter(
        Trade.account_id == account_id,
        Trade.state == "Settled",
    ).all()

    position_map: Dict[str, int] = {}
    for trade in trades:
        delta = trade.quantity if trade.side == "Buy" else -trade.quantity
        if trade.security in position_map:
            position_map[trade.security] += delta
        else:
            position_map[trade.security] = delta

    updated_positions = []
    for security, quantity in position_map.items():
        position = db.query(Position).filter(
            Position.account_id == account_id,
            Position.security == security,
        ).first()

        if position is None:
            position = Position(
                account_id=account_id,
                security=security,
                quantity=quantity,
                updated=now_utc(),
            )
            db.add(position)
        else:
            position.quantity = quantity
            position.updated = now_utc()

        updated_positions.append(position)

    db.commit()
    log_audit_event("POSITION_RECALC",
                    f"account_id={account_id} securities={len(position_map)}")
    logger.info("Recalculated %d positions for account %d",
                len(updated_positions), account_id)
    return updated_positions


def get_position_concentration(db: Session, account_id: int) -> List[Dict]:
    """
    Get position concentration for an account.
    Shows what percentage of total position each security represents.
    """
    positions = get_positions_for_account(db, account_id)
    total_abs_quantity = sum(abs(p.quantity) for p in positions)
    if total_abs_quantity == 0:
        return []
    return [
        {
            "security": p.security,
            "quantity": p.quantity,
            "percentage": round(abs(p.quantity) / total_abs_quantity * 100, 2),
        }
        for p in positions
    ]
