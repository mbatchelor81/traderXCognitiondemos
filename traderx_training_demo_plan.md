# TraderX Demo Plan: Devin Product Training (Feb-March 2026)

**Repository:** [mbatchelor81/traderXCognitiondemos](https://github.com/mbatchelor81/traderXCognitiondemos)
**Purpose:** End-to-end demo script covering every training section using the TraderX legacy monolith trading application
**Audience:** Experienced Devin users

---

## Repository Quick Reference

TraderX is a legacy Python/FastAPI monolith with a React frontend, featuring intentional technical debt for training purposes:

| Component | Tech | Port | Purpose |
|-----------|------|------|---------|
| `traderx-monolith` | Python/FastAPI + SQLAlchemy + Socket.IO | 8000 | All backend logic (accounts, trades, positions, reference data, people) |
| `web-front-end/react` | React/TypeScript + Material-UI + AgGrid | 3000 | Trading UI with real-time updates |

**Key architectural smells (intentional):**
- `trade_processor.py` — 1,047-line god service handling trade validation, processing, position management, Socket.IO publishing, reporting, and audit
- `config.py` — global mutable state imported everywhere via `from app.config import *`
- Circular dependency between `trade_processor.py` and `account_service.py`
- Inconsistent service layer usage (some routes use services, others use inline SQLAlchemy queries)
- No authentication, no CI/CD, no containerization, single SQLite database shared by all tenants

**Run locally:**
```bash
# Backend
cd traderx-monolith && pip install -r requirements.txt && python run.py

# Frontend (separate terminal)
cd web-front-end/react && npm install && npm start
```

---

## Section 1: Devin 2.2 & Performance (10 min)

### What to Show
- Fast startup time (sessions produce output almost immediately)
- Unified UI flow: start session -> view PR -> jump back to session
- Slack / Linear integration for kicking off sessions

### Demo 1.1 -- Fast Startup & Unified UI Flow

**Session Type:** Standard Devin session from the web app

**Prompt:**
```
In the TraderX repo (mbatchelor81/traderXCognitiondemos), the trades route 
handler in traderx-monolith/app/routes/trades.py returns a generic 
HTTPException with status 400 for all trade validation failures. Add a 
dedicated handler so that when a trade references a non-existent account, 
it returns HTTP 404 Not Found with a clear error message, and when the 
trade quantity is invalid, it returns HTTP 422 Unprocessable Entity. 
Create a PR with this change.
```

**What to point out to attendees:**
1. **Speed:** Note how quickly Devin begins producing output after you hit Enter -- contrast with the old experience of waiting
2. **Unified UI:** Once Devin creates the PR, click the PR link directly within the session to review it without leaving Devin
3. **Session link on PR:** Show how the PR description links back to the Devin session that created it -- click it to jump back

**Progressive prompting (follow-up in the same session):**
```
Also add a handler for when the security/ticker is not found in reference 
data — return HTTP 404 with the ticker symbol in the error message.
```

> **Talking point:** "Notice how the follow-up is handled in the same session context -- Devin already knows the file, the patterns, and the PR branch."

---

### Demo 1.2 -- Slack Integration

**Session Type:** Start from Slack (requires Slack integration configured)

**Slack message:**
```
@Devin In mbatchelor81/traderXCognitiondemos, the trade_processor.py god 
service has validate_account_exists() and validate_account_has_users() 
functions that directly query the accounts and account_users tables 
(cross-domain queries). Refactor these two functions into account_service.py 
where they belong, and update trade_processor.py to call the account_service 
functions instead. Create a PR.
```

**What to point out:**
1. Devin picks up the task directly from Slack
2. Thread-based updates show progress in real time
3. The PR link appears in the Slack thread when ready

---

## Section 2: Full Desktop Testing (10 min)

### What to Show
- Devin launching the app, interacting with the UI via mouse/keyboard
- Annotated screen recording of the QA session
- Multi-step user flow verification

### Prerequisites
- Enable Desktop mode: **Settings > Customization > Enable Desktop mode**
- Ensure Python 3.11+ and Node 18+ are available on the Devin VM

---

### Demo 2.1 -- Frontend Feature + Desktop QA

**Session Type:** Standard session with Desktop mode enabled

**Step 1 prompt -- Implement the feature:**
```
In the TraderX repo (mbatchelor81/traderXCognitiondemos), the React trade 
creation dialog (web-front-end/react/src/ActionButtons/CreateTradeButton.tsx) 
currently lets users submit a trade with quantity 0 or negative values. 
Add client-side validation to the trade creation form:

1. Quantity must be a positive integer greater than 0
2. Show an inline error message below the quantity field when invalid
3. Disable the "Submit" button until the form is valid (valid security 
   selected AND valid quantity AND valid side selected)

Use Material-UI components consistent with the existing component patterns. 
Create a PR with this change.
```

**Step 2 prompt -- Trigger Desktop QA (after PR is created):**
```
Please QA this change. Start the TraderX application:
1. cd traderx-monolith && pip install -r requirements.txt && python run.py
2. In a separate terminal: cd web-front-end/react && npm install && npm start

Then open the React UI at http://localhost:3000. Test the following:

1. Select a tenant from the dropdown in the header
2. Select an account from the account dropdown
3. Click the trade creation button to open the dialog
4. Try to submit with quantity = 0 — verify the error message appears and 
   Submit button is disabled
5. Enter a negative quantity — verify validation blocks submission
6. Enter a valid quantity (e.g. 100), select a security and side (Buy/Sell) 
   — verify Submit button becomes enabled
7. Submit the trade and verify it appears in the Trade Blotter

Record your testing session.
```

**What to point out:**
1. Devin starts the Python backend and React frontend as two separate processes
2. Devin opens a browser, navigates to the React UI, and interacts with real UI elements
3. The screen recording is sped up during idle time and annotated at key test moments
4. The recording is shared with you for review -- no manual QA needed

---

### Demo 2.2 -- Visual Regression Check (simpler, faster)

**Prompt:**
```
In the TraderX React frontend (web-front-end/react/src/App.tsx), add a 
light/dark mode toggle button to the AppBar header next to the tenant 
selector. When toggled, the app should switch between the existing dark 
theme and a new light theme. Store the preference in localStorage so it 
persists across page refreshes.

After creating the PR, QA it by:
1. Starting the backend: cd traderx-monolith && python run.py
2. Starting the frontend: cd web-front-end/react && npm start
3. Opening the React UI at http://localhost:3000
4. Verifying the toggle appears in the header
5. Clicking the toggle and verifying the theme switches
6. Refreshing the page and verifying the preference persists

Record the QA session.
```

**What to point out:**
- Desktop testing is not limited to form validation -- it works for any visual change
- Devin verifies persistence by refreshing the browser, just like a human tester would

---

## Section 3: Skills & Scheduled Sessions (10 min)

### What to Show
- How to define a Skill in the repo that Devin follows automatically
- How to set up a recurring scheduled session

---

### Demo 3.1 -- Creating a Skill

**Session Type:** Standard Devin session

**Step 1 prompt -- Create the Skill file:**
```
In mbatchelor81/traderXCognitiondemos, create a Devin Skill file at 
.devin/skills/add-fastapi-endpoint.md that encodes our team's conventions 
for adding a new REST endpoint to the TraderX Python monolith.

The skill should instruct Devin to:
1. Add the endpoint function to the appropriate route file in 
   traderx-monolith/app/routes/ (or create a new route file if needed)
2. Include a docstring describing the endpoint's purpose
3. Use Pydantic BaseModel for request/response validation
4. Use the Depends(get_db) pattern for database session injection
5. Use get_tenant_from_request(request) for tenant extraction
6. Add Python logging at INFO level for the endpoint entry
7. Add proper error handling with HTTPException and appropriate status codes
8. If business logic is needed, add it to the service layer (not inline in the route)
9. Run pytest in the traderx-monolith directory to verify nothing is broken

Create a PR with this skill file.
```

**What to point out:**
1. Skills travel with the repo -- any Devin session on this repo will discover and follow them
2. This enforces team conventions: Pydantic models, dependency injection, tenant middleware, error handling
3. New team members (and Devin) automatically follow established patterns

**Step 2 prompt -- Invoke the Skill:**
```
Using the add-fastapi-endpoint skill, add a GET /account/{account_id}/summary 
endpoint to the accounts route that returns a combined view of the account 
details, its positions, and trade count. This gives consumers a single 
aggregation endpoint instead of needing to call multiple routes.
```

**What to point out:**
- Devin discovers the skill and follows the checklist (Pydantic models, logging, error handling, pytest verification)
- The output is consistent with team conventions every time

---

### Demo 3.2 -- Scheduled Sessions

**Session Type:** Create from Settings > Schedules (or from the input box via Advanced mode)

**Schedule 1 -- Weekly Dependency Audit:**

| Field | Value |
|-------|-------|
| Name | `Weekly TraderX Dependency Audit` |
| Repository | `mbatchelor81/traderXCognitiondemos` |
| Frequency | Weekly, Mondays at 9:00 AM UTC |
| Prompt | See below |

**Prompt for the schedule:**
```
Run the dependency audit workflow for TraderX:

1. For the Python backend (traderx-monolith/):
   - Run: pip install pip-audit && pip-audit -r requirements.txt
   - Check for known vulnerabilities in all Python packages

2. For the React frontend (web-front-end/react/):
   - Run: npm audit
   - Check for known vulnerabilities in all npm packages

Compile a summary report with:
- Total vulnerabilities found per component (backend vs frontend)
- Any CRITICAL or HIGH severity issues
- Recommended upgrades for the top 3 most severe findings

If any CRITICAL vulnerabilities are found, create a PR that bumps the 
affected dependency to a patched version.
```

**What to point out:**
1. This runs every Monday automatically -- no human needs to remember
2. Devin creates PRs for critical findings, just reports for lower severity
3. The schedule can be triggered on-demand with the "Run now" button

---

**Schedule 2 -- Daily npm outdated check (simpler):**

| Field | Value |
|-------|-------|
| Name | `Daily npm outdated check` |
| Repository | `mbatchelor81/traderXCognitiondemos` |
| Frequency | Daily at 7:00 AM UTC |
| Prompt | See below |

**Prompt for the schedule:**
```
For the TraderX React frontend (web-front-end/react/):

1. Run npm outdated and capture the output
2. If any dependencies are more than 2 major versions behind, flag them

Post a summary of outdated dependencies. Only create a PR if there are 
security-related updates available (check npm audit).
```

---

**Schedule 3 -- One-Time Schedule (demo the one-time feature):**

**From the input box, use Advanced mode > "Create schedule" tab:**

| Field | Value |
|-------|-------|
| Name | `Python requirements pinning` |
| Repository | `mbatchelor81/traderXCognitiondemos` |
| Run at | Tomorrow, 2:00 PM UTC (one-time) |
| Prompt | See below |

```
In TraderX, the Python backend (traderx-monolith/requirements.txt) has 
unpinned dependencies (e.g., "fastapi" instead of "fastapi==0.115.0"). 

1. Install the current dependencies: pip install -r requirements.txt
2. Capture the resolved versions: pip freeze
3. Update requirements.txt to pin all dependencies to their current 
   resolved versions
4. Verify the backend still starts: python run.py (check it responds 
   to GET /health)
5. Verify tests pass: python -m pytest tests/ -v

Create a PR with the pinned requirements.
```

---

## Section 4: Devin Review (10 min)

### What to Show
- PR review workflow end-to-end in Devin Review
- Batch comments
- Code changes from chat
- Applying commits from the review UI

### Setup
You need an existing PR to review. Use one of the PRs created in the earlier demos, or create one now:

**Prompt to generate a reviewable PR:**
```
In mbatchelor81/traderXCognitiondemos, the trade_processor.py god service 
(traderx-monolith/app/services/trade_processor.py) has several issues in 
the process_trade() function (around line 365):

1. It uses string concatenation for some log messages instead of consistent 
   SLF4J-style parameterized messages (logger.info("msg %s", var))
2. Trade state transitions (New -> Processing -> Settled) happen instantly 
   with no simulated delay or actual async processing
3. There's no error handling around the database commit on line 448
4. Position quantity calculation (line 430) is done inline instead of in a 
   dedicated helper method

Refactor the process_trade() function to:
- Use parameterized logging consistently throughout
- Extract position delta calculation into a private _calculate_quantity_delta() 
  helper function
- Add try-except around db.commit() with proper error logging and trade state 
  set to Cancelled on failure
- Add inline comments explaining the state machine transitions

Create a PR with these changes.
```

---

### Demo 4.1 -- Full Review Workflow

Once the PR exists, open it in **Devin Review** (click the PR from the sessions list or navigate directly).

**Walk through these features live:**

1. **Read the diff** -- Show the side-by-side diff view with syntax highlighting

2. **Batch comments** -- Click on 3 different lines to leave comments:
   - Line where `_calculate_quantity_delta()` is defined: _"Consider using an enum for trade sides instead of string comparison"_
   - Line with try-except: _"Should we also rollback the session explicitly before setting state to Cancelled?"_
   - Line with parameterized logging fix: _"Nice improvement -- parameterized logging avoids string formatting when the log level is disabled"_
   
   Check **"Start a review"** on each to batch them. Then submit all at once.

3. **Code change from chat** -- In the Devin Review chat panel, type:
   ```
   The _calculate_quantity_delta method should also handle an unexpected 
   side value (not Buy or Sell) by raising a ValueError. Can you add that 
   validation?
   ```
   
   **What to point out:**
   - Devin proposes the code change inline in the chat
   - You can review it, then click **"Apply as commit"** to push it to the PR branch
   - No need to leave Devin Review, open an IDE, or start a new session

4. **GitHub commit status** -- Switch to the GitHub PR page and show the Devin Review status check on the latest commit, with a link back to the full analysis

---

### Demo 4.2 -- Draft PR Workflow (quick)

**Prompt:**
```
In mbatchelor81/traderXCognitiondemos, add a GET /metrics endpoint to the 
FastAPI app (traderx-monolith/app/main.py) that returns basic runtime 
metrics from config._runtime_state: total_trades_processed, 
last_trade_timestamp, active_sessions, and startup_time. 
Create this as a DRAFT PR since we want to review before merging.
```

**In Devin Review:**
- Open the draft PR
- Show the **"Ready for review"** button in Devin Review
- Optionally leave a comment, then click Ready for review -- no need to go to GitHub

---

## Section 5: AskDevin & Fast Mode (5 min)

### What to Show
- Ask mode for codebase exploration
- Plan mode for scoping before execution
- Fast mode for time-sensitive tasks

---

### Demo 5.1 -- Ask Mode (Codebase Exploration)

**Open AskDevin and select Ask mode.**

**Question 1 -- Architecture understanding:**
```
In the TraderX repo (mbatchelor81/traderXCognitiondemos), trace the 
complete lifecycle of a trade from when a user clicks "Submit" in the 
React UI to when the position is updated in the database. Walk through 
every file involved, the HTTP and WebSocket communication, and the key 
function entry points.
```

**Expected output:** A detailed trace through:
- `CreateTradeButton.tsx` -> `fetchWithTenant()` (HTTP POST to `/trade/`)
- -> `trades.py:submit_trade()` route handler
- -> `trade_processor.process_trade()` (validates, creates trade, transitions states)
- -> `trade_processor.update_position()` (updates position in SQLite)
- -> `trade_processor.publish_trade_and_position()` (Socket.IO emit to rooms)
- -> `Datatable.tsx` Socket.IO listener receives `publish` event and updates AgGrid

**What to point out:** AskDevin provides code references with file paths and line numbers -- you can click through to the actual code.

---

**Question 2 -- Security audit:**
```
What authentication and authorization mechanisms does TraderX use? 
Are there any endpoints that should be protected but aren't?
```

**Expected output:** AskDevin should identify that TraderX has CORS set to `"*"`, no authentication middleware, the `X-Tenant-ID` header is trusted without validation, and any client can access any tenant's data by changing the header -- documented as intentional in `LEGACY_ARCHITECTURE.md`.

---

### Demo 5.2 -- Plan Mode (Scope Before You Build)

**Open AskDevin and select Plan mode.**

**Prompt:**
```
I want to add JWT authentication to the TraderX FastAPI backend so that 
only authenticated users can create accounts or submit trades. The people 
service data (traderx-monolith/data/people.json) should be the user 
directory for validating credentials. 

Plan the implementation: which files need to change, what new files are 
needed, and what's the right order of implementation?
```

**Expected output:** A structured implementation plan covering:
- New auth utility module in `traderx-monolith/app/utils/auth.py` (JWT creation/validation)
- New `/auth/login` endpoint in a new route file `traderx-monolith/app/routes/auth.py`
- FastAPI dependency for JWT validation (to be used in protected routes)
- Updates to `accounts.py` and `trades.py` routes to require authentication
- Updates to `fetchWithTenant.ts` to include JWT token in requests
- Order: auth utility first, then login endpoint, then protected routes, then frontend

**Follow-up -- Launch a session from the plan:**
```
Execute this plan. Start with the auth utility module and login endpoint.
```

**What to point out:**
- Plan mode scoped the work with full codebase context
- The session launched from the plan already has all the context baked in
- This is the recommended workflow: **Ask/Plan first -> then execute**

---

### Demo 5.3 -- Fast Mode

**Open a new session and select Fast mode from the agent picker.**

**Prompt:**
```
In mbatchelor81/traderXCognitiondemos, the backend tests 
(traderx-monolith/tests/) only have test_account_crud.py and 
test_trade_submit.py. Add a new test_positions.py file that tests the 
position endpoints: GET /positions/ and GET /positions/{account_id}. 
Cover at least: listing positions for a tenant, listing positions for 
a specific account, and handling a request for a non-existent account 
(should return empty list). Use the existing conftest.py fixtures. 
Create a PR.
```

**What to point out:**
- Note the ~2x faster response time compared to standard mode
- This is a well-scoped task (add tests to one module) -- perfect for Fast mode
- Remind attendees: Fast mode costs 4x ACU, so use it for time-sensitive or simple tasks

---

## Section 6: API, Security & Platform (10 min)

### What to Show
- v3 API for programmatic session creation
- Secure mode for compliance
- UX improvements (PWA, status indicators, merge conflict detection)

---

### Demo 6.1 -- v3 API: Programmatic Session

**Run this from a terminal or script to show programmatic Devin usage:**

```bash
curl -X POST "https://api.devin.ai/v3/sessions" \
  -H "Authorization: Bearer $DEVIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "In mbatchelor81/traderXCognitiondemos, add a GET /stocks/count endpoint to the reference_data route (traderx-monolith/app/routes/reference_data.py) that returns the total number of available S&P 500 securities as {\"count\": N}. Create a PR.",
    "repository": "mbatchelor81/traderXCognitiondemos"
  }'
```

**What to point out:**
1. The session is created programmatically -- this enables CI/CD integrations, chatbots, custom tooling
2. Session attribution shows it was created via API (not webapp or Slack)
3. You can poll `GET /v3/sessions/{id}/messages` to monitor progress

---

**Demo 6.1b -- Retrieve session messages via API:**

```bash
curl "https://api.devin.ai/v3/sessions/{SESSION_ID}/messages" \
  -H "Authorization: Bearer $DEVIN_API_KEY"
```

**What to point out:**
- New `GET /messages` endpoint gives full programmatic access to session history
- Enables building dashboards, audit logs, or feeding results into other systems

---

### Demo 6.2 -- Secure Mode

**Navigate to Settings > Customization > Security settings**

**What to show:**
1. Toggle Secure Mode on
2. Explain: when enabled, Devin loses native internet deployment capabilities
3. Show that Devin can still work on code, create PRs, and run local builds -- it just can't deploy to public endpoints
4. This is important for teams with strict compliance requirements (FedRAMP, SOC2, etc.)

**Optional demo prompt (with Secure Mode on):**
```
In mbatchelor81/traderXCognitiondemos, review the TraderX monolith codebase 
for security best practices:
1. Check if any secrets or credentials are hardcoded in source files
2. Verify that SQL queries use parameterized queries (not string formatting)
3. Review CORS configuration in main.py — is allow_origins=["*"] appropriate?
4. Check if the X-Tenant-ID header is validated against known tenants
5. Review the deploy.sh script for any security concerns

Create a PR with any improvements you find.
```

**What to point out:** Devin works normally for code changes even in Secure Mode -- the restriction is only on internet-facing deployments.

---

### Demo 6.3 -- UX Improvements (Quick Walkthrough)

These don't require prompts -- just show the UI:

1. **PWA Install:** Click the install icon in the Chrome/Edge address bar. Show that Devin opens as a standalone app. Links to Devin sessions now open directly in the app.

2. **Browser tab status:** Open multiple Devin sessions in different tabs. Point out the favicon dots:
   - Green = Devin is working
   - Orange = Devin is waiting for you
   - This lets you monitor sessions without switching tabs

3. **Sessions list redesign:** Navigate to the sessions list. Show:
   - Inline PR previews (you can see the PR status without clicking in)
   - Message snippets showing the latest update
   - Sort by creation date

4. **Merge conflict detection:** If any of the earlier demo PRs have conflicts (or create one intentionally), show that Devin automatically notifies you in the session.

5. **Settings search:** Go to Settings, click the search bar, type "desktop" -- show it jumps to the Desktop mode setting immediately.

---

## Appendix: Session Summary

| # | Section | Session Type | Prompt Summary | Key Feature Shown |
|---|---------|-------------|----------------|-------------------|
| 1.1 | Devin 2.2 | Web session | Add specific HTTP error handlers to trades route | Fast startup, unified UI |
| 1.2 | Devin 2.2 | Slack | Refactor cross-domain queries out of trade_processor | Slack integration |
| 2.1 | Desktop Testing | Web + Desktop | Add trade form validation + QA | Desktop QA with recording |
| 2.2 | Desktop Testing | Web + Desktop | Add light/dark mode toggle + QA | Visual regression check |
| 3.1 | Skills | Web session | Create + invoke a FastAPI endpoint skill | Skills in repo |
| 3.2 | Schedules | Settings | Dependency audit, npm outdated, requirements pinning | Recurring + one-time schedules |
| 4.1 | Devin Review | Review UI | Refactor trade_processor.process_trade() | Batch comments, code from chat |
| 4.2 | Devin Review | Web session | Add /metrics endpoint (draft PR) | Draft PR workflow |
| 5.1 | AskDevin | Ask mode | Trace trade lifecycle through Python monolith | Codebase exploration |
| 5.2 | AskDevin | Plan mode | Plan JWT auth implementation for FastAPI | Plan -> execute workflow |
| 5.3 | Fast Mode | Fast session | Add position endpoint tests (pytest) | Speed comparison |
| 6.1 | API | Terminal/curl | Create session via v3 API | Programmatic access |
| 6.2 | Secure Mode | Settings | Python monolith security review | Compliance controls |
| 6.3 | UX | UI walkthrough | N/A | PWA, status dots, search |

---

## Tips for Presenters

1. **Pre-install dependencies** before the training session. Run `pip install -r traderx-monolith/requirements.txt` and `cd web-front-end/react && npm install` ahead of time so the app starts quickly during demos.

2. **Have a PR ready** for the Devin Review section (Section 4). Either create one the day before or use Demo 4.1's prompt to generate one live -- just be aware it adds time.

3. **Use Fast mode** for any live demo where you want quick results (Section 5.3 is a good candidate to run live).

4. **For AskDevin demos**, the questions work best if attendees haven't seen the TraderX codebase before -- the "aha moment" is Devin tracing through the monolith's tangled dependencies (god service, circular imports, cross-domain queries) and explaining the data flow.

5. **Keep the sessions list open** in a separate tab so attendees can see the green/orange status indicators in real time (Section 6.3).

6. **For the API demo**, have the curl commands ready in a terminal. You can also show the Swagger docs at the API reference URL for context.

7. **Progressive prompting pattern:** In Sections 1.1, 2.1, and 3.1, the demos are structured as "initial prompt -> follow-up prompt." This shows Devin's session continuity -- it remembers context from the first task. Call this out explicitly.

8. **TraderX architectural smells:** The repo has intentional anti-patterns documented in `LEGACY_ARCHITECTURE.md`. Several demos (1.2, 4.1, 5.1) leverage these smells for realistic refactoring tasks. Mention that the technical debt is by design -- it makes the demos feel like real-world legacy code.
