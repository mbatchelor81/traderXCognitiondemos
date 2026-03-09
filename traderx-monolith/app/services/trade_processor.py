"""
Trade Processor - backward compatibility shim.

The former god service has been decomposed into:
- trading_service.py (trade validation, processing, state machine)
- position_service.py (position CRUD, recalculation)

This module re-exports key symbols so that existing imports continue to work
during the transition period.
"""

# Re-export from trading_service
from app.services.trading_service import (  # noqa: F401
    set_socketio_server,
    get_socketio_server,
    validate_trade_request,
    process_trade,
    get_trade_by_id,
    get_trades_for_account,
    get_all_trades,
    count_trades_for_account,
    get_trades_by_state,
    settle_pending_trades,
    cancel_stale_trades,
    publish_trade_update,
    publish_position_update,
    publish_trade_and_position,
)

# Re-export from position_service
from app.services.position_service import (  # noqa: F401
    get_current_position_quantity,
    update_position,
    get_positions_for_account,
    get_all_positions,
    recalculate_positions,
)
