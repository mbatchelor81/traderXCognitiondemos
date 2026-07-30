# ⚠️ DEPRECATED — TraderX Monolith (legacy reference)

**This monolith is deprecated. It is kept as the legacy reference implementation only.**
New work belongs in the extracted single-tenant domain services under
[`../services/`](../services/):

| Service | Port | Owns |
|---|---|---|
| [`account-service`](../services/account-service) | 8001 | Account CRUD, account-user management, validation |
| [`trading-service`](../services/trading-service) | 8002 | Trade submission/validation, trade state machine, Socket.io events |
| [`position-service`](../services/position-service) | 8003 | Position tracking, queries, recalculation |
| [`reference-data-service`](../services/reference-data-service) | 8004 | S&P 500 ticker lookup |
| [`people-service`](../services/people-service) | 8005 | Person directory and validation |

See [`../migration/MIGRATION_PLAN.md`](../migration/MIGRATION_PLAN.md) for the migration and
[`../TARGET_ARCHITECTURE_CONSTRAINTS.md`](../TARGET_ARCHITECTURE_CONSTRAINTS.md) for the target state.

---

## Running the legacy monolith

It has been converted to the single-tenant runtime model, so `TENANT_ID` is required and each
tenant gets its own database (`traderx_<TENANT_ID>.db`). It refuses to start without it.

```bash
cd traderx-monolith
pip install -r requirements.txt
TENANT_ID=acme_corp python run.py     # http://localhost:8000
python -m pytest tests/ -v
```

Requests may omit `X-Tenant-ID`; a request naming a different tenant is rejected with `403`.
