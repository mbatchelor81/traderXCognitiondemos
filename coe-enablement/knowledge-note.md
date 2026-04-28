# Circular Dependency: trade_processor ↔ account_service

## Trigger
When modifying `traderx-monolith/app/services/trade_processor.py` or `traderx-monolith/app/services/account_service.py`, or when creating a new service module that needs to call functions from either.

## Content

`trade_processor.py` and `account_service.py` have a **circular import dependency** — this is an intentional architectural smell documented in both files' docstrings.

**The cycle:**
```
trade_processor.py
  └─ imports Account, AccountUser from app.models.account
  └─ directly queries accounts table (validate_account_exists, validate_account_has_users)

account_service.py
  └─ needs count_trades_for_account() from trade_processor (cross-domain helper)
  └─ resolved via lazy import at runtime, not at module top-level
```

**Why it matters for agents and new engineers:**

1. **Do not add new imports between these two modules.** If your new service needs trade data AND account data, accept them as function parameters rather than importing from both modules. This prevents deepening the cycle.

2. **The god service pattern:** `trade_processor.py` is 1046 lines and combines trade validation, processing, position calculation, Socket.io publishing, and cross-domain queries. This is by design for the monolith demo — it represents the legacy code that the service extraction (TARGET_ARCHITECTURE_CONSTRAINTS.md §7) is meant to decompose.

3. **Safe pattern for new services:** If your new service module needs to reference data from another domain:
   - **Preferred:** Accept the data as a parameter to your function (`def my_func(db, account: Account, tenant_id)`)
   - **Acceptable:** Import only from `app.models.*` (model classes are safe — no business logic)
   - **Avoid:** Importing from another service's `*_service.py` module

4. **Test implications:** The `conftest.py` test fixtures create all tables via `Base.metadata.create_all()`, which means all models are loaded. If you accidentally introduce a new circular import, it will fail at import time in tests with `ImportError` — not at runtime.

**Related files:**
- `traderx-monolith/app/services/trade_processor.py` (lines 1–21 — docstring explaining the smell)
- `traderx-monolith/app/services/account_service.py` (lines 1–8 — docstring explaining the cycle)
- `traderx-monolith/app/services/__init__.py` — import registration
- `LEGACY_ARCHITECTURE.md` — documents the god service pattern
