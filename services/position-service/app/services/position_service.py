"""
Position business logic.

Ported from the position functions of traderx-monolith/app/services/trade_processor.py
(`get_current_position_quantity`, `update_position`, `get_positions_for_account`,
`get_all_positions`, `recalculate_positions`). Semantics are unchanged except that
recalculation works from trades supplied by the caller — position-service does not
own a trades table and never queries one.
"""

from typing import Dict, Iterable, List, Mapping

from sqlalchemy.orm import Session

from app.logging_config import get_logger
from app.models.position import Position
from app.utils.helpers import log_audit_event, log_position_event, now_utc

logger = get_logger(__name__)


def get_all_positions(db: Session, tenant_id: str) -> List[Position]:
    """Get all positions for a tenant."""
    return db.query(Position).filter(
        Position.tenant_id == tenant_id,
    ).all()


def get_positions_for_account(db: Session, account_id: int,
                              tenant_id: str) -> List[Position]:
    """Get all positions for an account."""
    return db.query(Position).filter(
        Position.account_id == account_id,
        Position.tenant_id == tenant_id,
    ).all()


def get_position(db: Session, account_id: int, security: str,
                 tenant_id: str) -> Position | None:
    """Get a single position for an account/security pair, if it exists."""
    return db.query(Position).filter(
        Position.account_id == account_id,
        Position.security == security,
        Position.tenant_id == tenant_id,
    ).first()


def get_current_position_quantity(db: Session, account_id: int, security: str,
                                  tenant_id: str) -> int:
    """Get the current position quantity for an account/security pair."""
    position = get_position(db, account_id, security, tenant_id)
    if position is None:
        return 0
    return position.quantity


def update_position(db: Session, account_id: int, security: str,
                    quantity_delta: int, tenant_id: str) -> Position:
    """
    Apply a quantity delta to a position, creating the position when absent.
    Upserts on (account_id, security, tenant_id).
    """
    position = get_position(db, account_id, security, tenant_id)

    if position is None:
        logger.info("position_created", extra={
            "account_id": account_id,
            "security": security,
            "tenant_id": tenant_id,
        })
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

    log_position_event(
        account_id, security, "UPDATE", tenant_id,
        f"old_qty={old_quantity} new_qty={position.quantity} delta={quantity_delta}"
    )

    logger.info("position_updated", extra={
        "account_id": account_id,
        "security": security,
        "tenant_id": tenant_id,
        "old_quantity": old_quantity,
        "new_quantity": position.quantity,
        "quantity_delta": quantity_delta,
    })

    return position


def apply_position_delta(db: Session, account_id: int, security: str,
                         quantity_delta: int, tenant_id: str) -> Position:
    """Apply a delta and commit — the write path used by trading-service."""
    position = update_position(db, account_id, security, quantity_delta, tenant_id)
    db.commit()
    db.refresh(position)
    return position


def recalculate_positions(db: Session, account_id: int,
                          trades: Iterable[Mapping], tenant_id: str) -> List[Position]:
    """
    Recalculate an account's positions from the trades supplied by the caller.

    Each trade is a mapping with `security`, `side` and `quantity`. A Buy adds,
    anything else subtracts — the monolith's rule. Positions touched by the
    supplied trades are overwritten with the recomputed net quantity; positions
    for securities absent from the trade list are left untouched, matching
    traderx-monolith's `recalculate_positions`.
    """
    position_map: Dict[str, int] = {}
    for trade in trades:
        security = trade["security"]
        quantity = trade["quantity"]
        delta = quantity if trade["side"] == "Buy" else -quantity
        position_map[security] = position_map.get(security, 0) + delta

    updated_positions: List[Position] = []
    for security, quantity in position_map.items():
        position = get_position(db, account_id, security, tenant_id)

        if position is None:
            position = Position(
                account_id=account_id,
                security=security,
                tenant_id=tenant_id,
                quantity=quantity,
                updated=now_utc(),
            )
            db.add(position)
        else:
            position.quantity = quantity
            position.updated = now_utc()

        updated_positions.append(position)

    db.commit()
    for position in updated_positions:
        db.refresh(position)

    log_audit_event("POSITION_RECALC", tenant_id,
                    f"account_id={account_id} securities={len(position_map)}")

    logger.info("positions_recalculated", extra={
        "account_id": account_id,
        "tenant_id": tenant_id,
        "securities": len(updated_positions),
    })

    return updated_positions
