# Live Walkthrough Guide: Building Reusable Devin Artifacts for TraderX

Functional scope for a live session. What to build, why it's reusable, and how to show it across Windsurf, CLI, and Devin Cloud.

---

## Part 1: Skills to Build Live

### Why Skills First

Skills are the atomic unit. Everything else (playbooks, sub-agents, knowledge) references skills or is consumed by them. Build skills live because the audience immediately sees the input (a markdown file) and output (scaffolded code). The reusability proof is built into the repo: the same skill applies to N targets.

---

### Skill A: `add-new-service` (Build This One Live — ~10 min)

**What it does:** Scaffolds a complete domain service module inside the monolith — model, service layer, routes, main.py registration, tests.

**Why this one:** `TARGET_ARCHITECTURE_CONSTRAINTS.md` §7 defines 5 planned service extractions. This skill applies identically to all 5. Building it once and showing it work for 2 different services is the clearest "1 → N" proof.

**File to create:** `.devin/skills/add-new-service/SKILL.md`

```markdown
---
name: add-new-service
description: Scaffold a new domain service in the TraderX monolith (model, service, routes, tests)
argument-hint: "[service-name]"
---

Create a new domain service for `$ARGUMENTS` in the TraderX monolith.

## Pattern

Follow the 6-step extraction pattern. Every service in this codebase follows the same structure:

### 1. Model (`traderx-monolith/app/models/{name}.py`)
- Import `Base` from `app.database` and `from app.config import *`
- Include `tenant_id = Column(String(50), nullable=False, default=DEFAULT_TENANT)`
- Include `to_dict()` with **camelCase** keys
- Register in `app/models/__init__.py`
- Reference: `app/models/account.py`

### 2. Service (`traderx-monolith/app/services/{name}_service.py`)
- Every function takes `db: Session` and `tenant_id: str` as first args
- All queries filter by `tenant_id`
- Use `log_audit_event()` from `app.utils.helpers` for mutations
- Register in `app/services/__init__.py`
- Reference: `app/services/account_service.py`

### 3. Routes (`traderx-monolith/app/routes/{name}.py`)
- Pydantic request models with camelCase fields at top of file
- Use `get_tenant_from_request(request)` for tenant extraction
- Use `Depends(get_db)` for session injection
- Call service layer — no inline SQLAlchemy
- Reference: `app/routes/accounts.py`

### 4. Register in `app/main.py`
```python
app.include_router({name}.router, tags=["{Name}"])
```

### 5. Tests (`traderx-monolith/tests/test_{name}.py`)
- Use `client` fixture from `conftest.py` (in-memory SQLite, auto table create/drop)
- Happy path + 404 + validation errors
- Reference: `tests/test_trade_submit.py`

### 6. Verify
```bash
cd traderx-monolith && python -m pytest tests/ -v
```
```

**How to show reusability live:**

1. Build the skill file from scratch (or type it live — it's ~40 lines of markdown)
2. Invoke it in the CLI: `/add-new-service notification` → watch it scaffold 5 files
3. Run tests → green
4. Then invoke it again: `/add-new-service audit` → same structure, different domain
5. Say: "That's 2 down, 3 to go. Same skill, same output contract, every time."

**Reusability proof (show on screen):**

```
TARGET_ARCHITECTURE_CONSTRAINTS.md §7 defines 5 services:
  ┌─────────────────────┐
  │ add-new-service      │ ← 1 skill
  └──────────┬──────────┘
             │
  ┌──────────┼──────────┬──────────┬──────────┬──────────┐
  ▼          ▼          ▼          ▼          ▼          ▼
Account   Trading    Position   RefData    People    + any future service
  ✓          ✓          ✓          ✓          ✓
```

---

### Skill B: `add-api-endpoint` (Show Briefly — ~3 min)

**What it does:** Adds a single REST endpoint to an existing route module.

**Why show it:** It's the most *frequent* task (every feature adds endpoints). And it's a natural "I already have the service — now I need a new endpoint on it" follow-on from Skill A.

**File to create:** `.devin/skills/add-api-endpoint/SKILL.md`

```markdown
---
name: add-api-endpoint
description: Add a REST endpoint to an existing TraderX route module
argument-hint: "[method] [path] [route-module]"
---

Add a new $ARGUMENTS endpoint to the TraderX monolith.

## Steps

1. **Service function** → `app/services/{module}_service.py`
   - `db: Session`, `tenant_id: str` as first args
   - Filter by `tenant_id`, use `log_audit_event()` for mutations

2. **Pydantic model** → top of `app/routes/{module}.py`
   - camelCase fields, co-located (not in separate schemas file)

3. **Route handler** → `app/routes/{module}.py`
   - `get_tenant_from_request(request)` + `Depends(get_db)`
   - Call service layer, return `.to_dict()`, raise `HTTPException` on errors

4. **Test** → `tests/test_{module}.py`
   - Happy path + error cases using `client` fixture

5. **Verify** → `cd traderx-monolith && python -m pytest tests/ -v`
```

**How to show reusability:** "Every route module in the repo follows this pattern. `accounts.py` has 4 endpoints. `trades.py` has 3. You'll add dozens more. This skill ensures they all look the same."

---

### Skill C: `review-service-extraction` (Show as Read-Only Skill — ~3 min)

**What it does:** Read-only audit of a service module against `TARGET_ARCHITECTURE_CONSTRAINTS.md`.

**Why show it:** Demonstrates that skills aren't just for code gen — they can enforce standards. This is the quality gate before a PR merges.

**File to create:** `.devin/skills/review-service-extraction/SKILL.md`

```markdown
---
name: review-service-extraction
description: Audit a service module against TARGET_ARCHITECTURE_CONSTRAINTS.md
argument-hint: "[service-name]"
subagent: true
allowed-tools:
  - read
  - grep
  - glob
---

Audit the `$ARGUMENTS` service in the TraderX monolith for compliance with TARGET_ARCHITECTURE_CONSTRAINTS.md.

Check each item and report PASS/FAIL:

1. **Tenant isolation (§1):** Every query filters by `tenant_id`. No global state references.
2. **Service boundaries (§7):** No cross-domain imports from other `*_service.py` modules.
3. **No cross-service DB access (§8):** No imports of models from other domains.
4. **Observability (§10):** Uses `logging.getLogger(__name__)`, has `log_audit_event()` calls.
5. **API contract:** Pydantic models defined, camelCase fields, `to_dict()` used in responses.
6. **Tests exist:** `tests/test_{service}.py` exists with happy path + error cases.

Report as a table: | Check | Status | Evidence (file:line) |
```

**How to show reusability:** "This runs on every PR. It doesn't write code — it reads code and reports compliance. Same checklist, every service, forever."

---

### How to Convey Reusability (The Narrative)

Don't just say "it's reusable." **Prove it in the session** with this structure:

```
Step 1: Show the SPEC
  └─ TARGET_ARCHITECTURE_CONSTRAINTS.md §7 (5 services listed)

Step 2: Build the SKILL live
  └─ add-new-service/SKILL.md (encodes the pattern once)

Step 3: Invoke it TWICE for different targets
  └─ /add-new-service notification → 5 files created, tests pass
  └─ /add-new-service audit → same 5 files, same structure, tests pass

Step 4: Show the MATH
  └─ "5 services × 1 skill = 5 identical extractions.
      At 50 clients × 5 services = 250 extractions from 1 skill."
```

The key insight for the audience: **the skill IS the spec, in executable form.** They already write specs. Now the spec runs.

---

## Part 2: Knowledge Notes and Playbooks

### Knowledge Notes to Create

Knowledge notes are the **tribal knowledge that skills can't encode** — context that changes how you interpret a skill's output, or gotchas that prevent a 30-minute debugging session.

#### Knowledge Note 1: Multi-Tenant Middleware Pattern

**Create in:** Devin Knowledge UI (org-scoped or repo-scoped)

**Title:** TraderX Multi-Tenant Isolation via Middleware

**Trigger:** When modifying any route, service, or model in `traderx-monolith/`

**Content:**
```
Every request flows through TenantMiddleware (app/middleware.py) which reads
X-Tenant-ID from the header and falls back to CURRENT_TENANT from app/config.py.

Critical rules:
- Every DB query MUST include .filter(Model.tenant_id == tenant_id)
- The tenant_id comes from get_tenant_from_request(request) in route handlers
- In service functions, tenant_id is always the second parameter after db
- Tests must set X-Tenant-ID header: client.get("/...", headers={"X-Tenant-ID": "acme_corp"})
- Omitting the tenant filter leaks data across tenants — this is a security bug

Tenant-specific business rules are in app/config.py lines 76-92:
  TENANT_MAX_ACCOUNTS, TENANT_ALLOWED_SIDES, TENANT_AUTO_SETTLE
```

**Why show this live:** It's the single most common mistake an agent (or engineer) makes in this codebase. And it directly connects to the client story: "At 50 clients, every client's data must be isolated. This knowledge note makes sure the agent enforces that."

---

#### Knowledge Note 2: The God Service Problem

**Title:** trade_processor.py is Intentionally a God Service

**Trigger:** When modifying `traderx-monolith/app/services/trade_processor.py` or creating a new service that needs trade data

**Content:**
```
trade_processor.py (1046 lines) intentionally violates single-responsibility.
It handles: trade validation, processing, position calculation, settlement,
Socket.io publishing, AND cross-domain queries (account validation, position updates).

This is a documented architectural smell (see LEGACY_ARCHITECTURE.md).

Rules for agents:
- Do NOT import from trade_processor in new service modules
- Do NOT add new functions to trade_processor — create a new service module instead
- If you need trade data in another service, accept it as a function parameter
- Safe imports: app.models.* (model classes only, no business logic)
- Unsafe imports: app.services.trade_processor (creates circular dependency)

The circular dependency: trade_processor imports Account/AccountUser models,
account_service needs trade count functions → resolved via lazy import.
Adding more cross-service imports deepens this cycle.
```

**Why show this live:** Every team has a god service. This knowledge note shows how to document it so agents don't make it worse. Reusable pattern: "Find your god service, document its boundaries, tell the agent what NOT to do."

---

#### Knowledge Note 3: Test Fixture Architecture

**Title:** TraderX Test Fixtures — In-Memory SQLite with Auto Table Management

**Trigger:** When writing or modifying tests in `traderx-monolith/tests/`

**Content:**
```
conftest.py sets up:
- In-memory SQLite with StaticPool (no file, no persistence between tests)
- autouse=True fixture creates ALL tables before each test, drops after
- get_db dependency is overridden globally (line 38) — no config needed per test
- Use the `client` fixture for TestClient access

Key patterns:
- Create prerequisite data in the test itself (e.g., create account before submitting trade)
- Set tenant via headers: client.get("/...", headers={"X-Tenant-ID": "acme_corp"})
- Default tenant is "default_tenant" if no header is set
- Tests are independent — no shared state between test functions
```

---

### Playbooks to Create

#### Playbook 1: End-to-End Service Extraction

**Create in:** Devin Playbook UI

**Goal:** Extract a complete domain service from the TraderX monolith — from discovery through tested, reviewable code.

**Why show this live:** It chains everything together — skills, knowledge, sub-agents. The audience sees the full orchestration.

**Structure:**

```
Playbook: Extract Domain Service
Inputs: service_name, model_columns, endpoints

Step 1 — Discover (Ask Devin)
  "List all existing services in traderx-monolith/app/services/ and compare
   against TARGET_ARCHITECTURE_CONSTRAINTS.md §7. Which are implemented vs. missing?"

Step 2 — Scaffold (Full Session, references /add-new-service skill)
  "Use the add-new-service skill to create the {service_name} service.
   Model columns: {model_columns}. Endpoints: {endpoints}.
   Run python -m pytest tests/ -v and confirm all tests pass."

Step 3 — Review (Sub-agent, references /review-service-extraction skill)
  "Use the review-service-extraction skill to audit the {service_name} service
   against TARGET_ARCHITECTURE_CONSTRAINTS.md. Report any compliance gaps."

Step 4 — Create PR
  "Create a PR with title 'feat: add {service_name} service module'.
   Reference TARGET_ARCHITECTURE_CONSTRAINTS.md §7 in the description."
```

**Reusability proof:** "This playbook runs identically for all 5 services. Change the inputs, get the same quality output. At 50 clients, each client gets the same extraction playbook parameterized with their domain."

---

#### Playbook 2: Onboard New Tenant

**Goal:** Add a new tenant to the TraderX system — config, seed data, validation.

**Structure:**

```
Playbook: Onboard New Tenant
Inputs: tenant_id, max_accounts, allowed_sides, auto_settle

Step 1 — Add tenant config
  "Add {tenant_id} to KNOWN_TENANTS in app/config.py.
   Set TENANT_MAX_ACCOUNTS['{tenant_id}'] = {max_accounts},
   TENANT_ALLOWED_SIDES['{tenant_id}'] = {allowed_sides},
   TENANT_AUTO_SETTLE['{tenant_id}'] = {auto_settle}."

Step 2 — Validate isolation
  "Run the test suite with X-Tenant-ID={tenant_id} and verify:
   - Can create accounts under the new tenant
   - Cannot see accounts from other tenants
   - Business rules (max_accounts, allowed_sides) are enforced"

Step 3 — Create PR
  "Create a PR with title 'feat: onboard tenant {tenant_id}'."
```

**Why show this live:** This is the "client onboarding" use case. The audience immediately maps `tenant_id` to their own `client_id`. "When you onboard client #51, it's this playbook with their config values."

---

## Part 3: Custom Sub-Agents to Build via CLI

Sub-agents are defined as `AGENT.md` files in `.devin/agents/{name}/AGENT.md`. They're specialized workers with scoped tools and permissions.

Reference: https://cli.devin.ai/docs/subagents

---

### Sub-Agent 1: `architecture-auditor` (Read-Only — Build Live)

**What it does:** Audits any service module against `TARGET_ARCHITECTURE_CONSTRAINTS.md`. Read-only — cannot modify code.

**File:** `.devin/agents/architecture-auditor/AGENT.md`

```markdown
---
name: architecture-auditor
description: Audits TraderX service modules against TARGET_ARCHITECTURE_CONSTRAINTS.md
model: sonnet
allowed-tools:
  - read
  - grep
  - glob
permissions:
  deny:
    - write
    - edit
    - exec
---

You are an architecture auditor for the TraderX monolith. Your job is to read
service modules and report compliance against TARGET_ARCHITECTURE_CONSTRAINTS.md.

For every service module you audit, check:

1. **Tenant isolation** — every DB query filters by tenant_id
2. **No cross-service imports** — does not import from other *_service.py files
3. **Model convention** — has to_dict() with camelCase keys, tenant_id column
4. **Service convention** — functions accept (db: Session, tenant_id: str)
5. **Route convention** — uses get_tenant_from_request(), Depends(get_db), Pydantic models
6. **Test coverage** — corresponding test file exists in tests/

Output a compliance table:
| Check | Status | Evidence (file:line) | Remediation |

Be exhaustive. Cite specific file paths and line numbers.
```

**Why this one:** It's a *guard rail*, not a code generator. The audience sees that sub-agents aren't just for writing code — they enforce standards. And because it's read-only (denied write/edit/exec), it's safe to run in background on every PR.

**Live demo:**
```
> Use the architecture-auditor subagent to audit the account service
```
→ Returns a compliance table showing `app/services/account_service.py` passes all checks except observability (no structured logging yet).

---

### Sub-Agent 2: `test-generator` (Write-Capable — Build Live)

**What it does:** Generates comprehensive integration tests for any service module.

**File:** `.devin/agents/test-generator/AGENT.md`

```markdown
---
name: test-generator
description: Generates integration tests for TraderX service endpoints
allowed-tools:
  - read
  - grep
  - glob
  - exec
  - write
  - edit
permissions:
  allow:
    - Exec(cd traderx-monolith && python -m pytest*)
    - Write(traderx-monolith/tests/*)
    - Edit(traderx-monolith/tests/*)
  deny:
    - Write(traderx-monolith/app/*)
    - Edit(traderx-monolith/app/*)
---

You are a test generation subagent for the TraderX monolith. You write integration
tests and NOTHING ELSE. You cannot modify application code — only test files.

When generating tests, follow these patterns from conftest.py:
- Use the `client` fixture (TestClient with in-memory SQLite)
- Tables are auto-created/dropped per test (autouse fixture)
- Create prerequisite data in each test (e.g., create account before trading)

Required test cases for every service:
1. CRUD happy path (create → read → list → verify data)
2. 404 on missing resource (GET with invalid ID)
3. 422 on bad input (POST with missing required fields)
4. Multi-tenant isolation (create in tenant A, query in tenant B → empty)
5. Tenant-specific business rules (e.g., max accounts from app/config.py)

After writing tests, run: cd traderx-monolith && python -m pytest tests/ -v
Report pass/fail results.
```

**Why this one:** Scoped permissions are the key teaching moment. This sub-agent can write to `tests/` but is *denied* from modifying `app/`. Show the audience: "It can create any test file, run pytest, but literally cannot touch production code. That's the safety contract."

**Live demo:**
```
> Use the test-generator subagent to write tests for the account service
```
→ Creates `tests/test_accounts_comprehensive.py` with 5+ test cases, runs pytest, reports results. Point out: it couldn't modify `app/accounts.py` even if it wanted to.

---

### Sub-Agent 3: `service-scaffolder` (Orchestrator Skill + Sub-Agent — The Showcase)

This one ties everything together. It's a **skill that orchestrates sub-agents** — the full pattern the audience should take to their clients.

**File:** `.devin/skills/extract-service/SKILL.md`

```markdown
---
name: extract-service
description: Full service extraction — scaffolds code, audits compliance, generates tests
argument-hint: "[service-name]"
---

Extract a complete domain service for `$ARGUMENTS` from the TraderX monolith:

1. First, use /add-new-service to scaffold the model, service, routes, and registration
2. Then, use the architecture-auditor subagent to verify the new service is compliant
3. Then, use the test-generator subagent to create comprehensive integration tests
4. Finally, run the full test suite: `cd traderx-monolith && python -m pytest tests/ -v`

Report:
- Files created
- Compliance audit results
- Test results (pass/fail count)
```

**Why this is the showcase:** It chains a skill (`/add-new-service`) with two custom sub-agents (`architecture-auditor`, `test-generator`) into an orchestrated workflow. One command → scaffolded code + compliance audit + tests. This is the "1 foundation → N implementations" in action.

**Live demo:**
```
> /extract-service notification
```
→ Scaffolds the notification service, audits it, generates tests, runs them. All from one command.

**Reusability diagram (show on screen):**

```
/extract-service {name}
       │
       ├──→ /add-new-service {name}        ← Skill (code gen)
       │         └─ Creates 5 files
       │
       ├──→ architecture-auditor           ← Sub-agent (read-only audit)
       │         └─ Compliance table
       │
       └──→ test-generator                 ← Sub-agent (scoped write)
                 └─ 5+ test cases, pytest results

Same pipeline for:
  notification, audit, alert, billing, reporting, ...
  × 50 clients = 250+ service extractions, zero drift
```

---

## Summary: What to Build and in What Order

| # | Artifact | Type | Surface | Build Time | Key Teaching Moment |
|---|---|---|---|---|---|
| 1 | `add-new-service` | Skill | CLI + Windsurf | 10 min | "Invoke twice → same output. The spec is executable." |
| 2 | `add-api-endpoint` | Skill | CLI | 3 min | "Higher frequency task. Same pattern, smaller scope." |
| 3 | Multi-tenant knowledge note | Knowledge | Devin UI | 3 min | "The gotcha every agent needs. Prevents data leaks." |
| 4 | God service knowledge note | Knowledge | Devin UI | 2 min | "Tell the agent what NOT to do. Guard rails, not just rails." |
| 5 | `architecture-auditor` | Sub-agent | CLI | 5 min | "Read-only. Denied write/edit/exec. Safe to run on every PR." |
| 6 | `test-generator` | Sub-agent | CLI | 5 min | "Scoped permissions. Can write tests, cannot touch app code." |
| 7 | `review-service-extraction` | Skill (subagent) | CLI | 3 min | "Skills can run AS sub-agents. `subagent: true` in frontmatter." |
| 8 | `extract-service` | Orchestrator skill | CLI | 5 min | "Chains skill + 2 sub-agents. One command, full pipeline." |
| 9 | Extract service playbook | Playbook | Devin Cloud UI | 5 min | "Same orchestration, but for long-running autonomous work." |
| 10 | Onboard tenant playbook | Playbook | Devin Cloud UI | 3 min | "Client onboarding. tenant_id = client_id. Parameterized." |

**Total live build time: ~44 min** (leaves room for discussion and audience questions)

---

## The Narrative Arc

```
"You already write specs. Here's what changes:"

BEFORE                              AFTER
┌──────────────────┐                ┌──────────────────┐
│ Write spec doc   │                │ Write spec doc   │
│       ↓          │                │       ↓          │
│ Engineer reads   │                │ Spec becomes     │
│ spec, writes     │                │ SKILL.md         │
│ code manually    │                │       ↓          │
│       ↓          │                │ Invoke skill →   │
│ Review, test,    │                │ code scaffolded  │
│ fix, repeat      │                │       ↓          │
│       ↓          │                │ Sub-agent audits │
│ Ship for 1       │                │ compliance       │
│ client           │                │       ↓          │
│       ↓          │                │ Sub-agent writes │
│ Copy-paste for   │                │ tests            │
│ client #2        │                │       ↓          │
│ ...              │                │ Playbook runs    │
│ Drift at         │                │ for N clients    │
│ client #50       │                │ Zero drift       │
└──────────────────┘                └──────────────────┘
```
