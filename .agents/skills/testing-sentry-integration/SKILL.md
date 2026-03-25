# Testing Sentry Integration for TraderX

## Overview
The TraderX backend (FastAPI) has Sentry SDK integration for runtime error monitoring. Sentry is conditionally initialized based on the `SENTRY_DSN` environment variable.

## Devin Secrets Needed
- `SENTRY_DSN` — The DSN string from the Sentry project (repo-scoped to `mbatchelor81/traderXCognitiondemos`)
- `SENTRY_ORG_AUTH_TOKEN` — Sentry Organization Auth Token for API access (repo-scoped)

## How It Works
- `traderx-monolith/app/main.py` initializes `sentry_sdk.init()` only if `SENTRY_DSN` env var is set
- The `/sentry-debug` endpoint deliberately triggers a `ZeroDivisionError` for demo/testing
- When Sentry is active, the SDK's FastAPI/Starlette integrations intercept errors and send them to Sentry

## Testing Steps

### Test 1: Verify Sentry Captures Errors (DSN set)
1. Start backend: `SENTRY_DSN=$SENTRY_DSN python run.py` from `traderx-monolith/`
2. Wait for startup, then `curl http://localhost:8000/health` → should return `{"status":"UP"}`
3. `curl http://localhost:8000/sentry-debug` → should return HTTP 500
4. Check server logs for `sentry_sdk/integrations/fastapi.py` in the stack trace — this proves Sentry intercepted the error
5. Server should still be running after the error (not crashed)

### Test 2: Verify App Works Without Sentry (DSN unset)
1. Start backend WITHOUT `SENTRY_DSN`: `unset SENTRY_DSN && python run.py`
2. `curl http://localhost:8000/health` → should return `{"status":"UP"}`
3. `curl http://localhost:8000/sentry-debug` → still returns HTTP 500 (error still happens, just not sent to Sentry)
4. Server logs should NOT contain `sentry_sdk` references in the stack trace

### Test 3: Verify Error Arrived in Sentry (via API)
1. Query Sentry org: `curl -H "Authorization: Bearer $SENTRY_ORG_AUTH_TOKEN" "https://us.sentry.io/api/0/organizations/"`
   - Note the org slug (e.g., `mason-demo`)
2. Query issues: `curl -H "Authorization: Bearer $SENTRY_ORG_AUTH_TOKEN" "https://us.sentry.io/api/0/projects/{org-slug}/{project-slug}/issues/?query=ZeroDivisionError"`
   - Project slug might be `traderx-demo` or similar
3. Verify the response contains an issue with:
   - `title`: `ZeroDivisionError: division by zero`
   - `culprit`: `/sentry-debug`
   - `metadata.filename`: `app/main.py`
   - `metadata.function`: `trigger_error`

## Tips
- The Sentry org slug and project slug may change if the account is recreated. Use the organizations API to discover them dynamically.
- The Sentry ingest endpoint is region-specific (e.g., `us.sentry.io`). Use the `regionUrl` from the org API response.
- If the SENTRY_ORG_AUTH_TOKEN returns permission errors, verify its scopes include `org:read`, `project:read`, and `event:read`.
- The `/sentry-debug` endpoint is intentionally left unprotected for demo purposes. In a real deployment, consider adding auth or removing it.
