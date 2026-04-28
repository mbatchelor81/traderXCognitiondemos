# COE Enablement Session: Skill-Driven Development with Devin

**Duration:** 60 minutes
**Audience:** 3–5 senior engineers standing up a Devin Center of Excellence
**Prerequisite:** Team already practices spec-driven development
**Demo Repo:** `mbatchelor81/traderXCognitiondemos` (TraderX trading platform)

---

## Agenda

### Opening (0:00–0:05)

**Goal:** Align on the session outcome — a committed foundation layer that scales to 50+ implementations.

- The TraderX monolith has **5 planned service extractions** defined in [`TARGET_ARCHITECTURE_CONSTRAINTS.md` §7](../TARGET_ARCHITECTURE_CONSTRAINTS.md). Each follows an identical pattern: model → service → routes → register → tests.
- Today we encode that pattern **once** as a skill, chain it into a playbook, and show how it runs identically across Windsurf, Chisel, and Devin Cloud.
- By session end: **1 committed skill + 1 knowledge note + 1 playbook** in the repo. Post-session target: 5 skills committed and tested within 2 weeks.

---

### Architecture Overview (0:05–0:15)

**Goal:** Map the three-tool model to the team's existing workflow.

#### The Three Surfaces

```
┌─────────────────────────────────────────────────────────────┐
│                    Foundation Layer                          │
│   .agents/skills/   +   Knowledge Notes   +   Playbooks     │
│                                                             │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│   │  SKILL.md    │  │  Note: multi │  │  Playbook:       │  │
│   │  add-new-    │  │  tenant arch │  │  extract-service │  │
│   │  service     │  │  gotchas     │  │  end-to-end      │  │
│   └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘  │
│          │                 │                    │            │
└──────────┼─────────────────┼────────────────────┼────────────┘
           │                 │                    │
     ┌─────┴─────┐    ┌─────┴─────┐     ┌────────┴────────┐
     │ Windsurf  │    │  Chisel   │     │  Devin Cloud    │
     │ 2.0 (IDE) │    │  (CLI)    │     │  (Autonomous)   │
     │           │    │           │     │                 │
     │ Developer │    │ CI/batch  │     │ Long-running    │
     │ writes    │    │ scripts   │     │ multi-step      │
     │ spec →    │    │ across N  │     │ sessions with   │
     │ code in   │    │ targets   │     │ sub-agents      │
     │ editor    │    │           │     │                 │
     └───────────┘    └───────────┘     └─────────────────┘
```

#### How It Maps to TraderX

| Team Workflow Step | Without Foundation | With Foundation |
|---|---|---|
| "Add a new service module" | Read `account_service.py`, copy-paste, adapt manually | Invoke `add-new-service` skill — scaffolds model, service, routes, tests |
| "Add observability to 5 services" | Repeat same logging/health changes 5× | Chisel batch script runs `add-observability` skill across all 5 |
| "Extract a complete microservice" | Multi-day manual effort | Playbook chains skills + sub-agents, runs in Devin Cloud |

#### Key Concept: Specs Become Skills

The team already writes specs. Show how [`TARGET_ARCHITECTURE_CONSTRAINTS.md`](../TARGET_ARCHITECTURE_CONSTRAINTS.md) maps directly:

```
Spec §7 (Service Boundaries)  →  Skill: add-new-service
Spec §10 (Observability)      →  Skill: add-observability-to-service
Spec §5 (CI/CD)               →  Skill: add-integration-test
Spec §3 (Containerization)    →  Playbook: extract-service (chains all three)
```

---

### Live Demo: Skill-Driven Development (0:15–0:30)

**Goal:** Show the full loop — spec → skill → code — using the `add-new-service` skill against TraderX.

#### Setup (presenter does this before the session)

```bash
cd traderx-monolith && pip install -r requirements.txt
python -m pytest tests/ -v        # Confirm green baseline
```

#### Demo Script — Progressive Prompt Sequence

The demo follows the **Ask → Ask → Execute** pattern: two lightweight discovery prompts, then a full session that produces code.

**Step 1: Show the spec.** Open [`TARGET_ARCHITECTURE_CONSTRAINTS.md` §7](../TARGET_ARCHITECTURE_CONSTRAINTS.md). Point to the 5 planned services — Account, Trading, Position, Reference Data, People. Note: Account, Trading, and People already have route modules in the monolith. The task is to create a **Notification Service** following the extraction pattern.

**Step 2: Show the existing skill.** Open [`.windsurf/skills/add-new-service/SKILL.md`](../.windsurf/skills/add-new-service/SKILL.md). Walk through:
- The 6-step pattern (model → service → routes → register → tests → verify)
- Templates at `.windsurf/skills/add-new-service/templates/`
- Examples at `.windsurf/skills/add-new-service/examples/`

Point out: this same skill also exists in [`.agents/skills/add-new-service/SKILL.md`](../.agents/skills/add-new-service/SKILL.md) for Devin Cloud.

**Step 3: Ask Devin — Discover (Prompt 1).** In Devin, send an Ask Devin prompt:

> Scan `traderx-monolith/app/` and list all existing route modules, service modules, and models. Which domains from `TARGET_ARCHITECTURE_CONSTRAINTS.md` §7 are already implemented vs. missing?

Show the audience: Devin audits the codebase and returns a table of implemented vs. planned services with file paths. This is discovery — no code changes, just context surfacing.

**Step 4: Ask Devin — Scope (Prompt 2).** Follow up with a second Ask Devin prompt:

> For a new `notification` service, generate a file-by-file extraction plan. List every file to create or modify, with the expected content structure for each.

Show the audience: Devin produces a numbered plan referencing real paths (`app/models/notification.py`, `app/services/notification_service.py`, etc.). Still no code changes — this is scoping.

**Step 5: Full Session — Execute (Prompt 3).** Now kick off a full Devin session:

> Use the `add-new-service` skill to create a `notification` service. The Notification model should have columns: `id` (Integer PK), `tenant_id` (String), `account_id` (ForeignKey to accounts), `message` (String), `read` (Boolean), `created` (DateTime). Service functions: `create_notification`, `get_notifications_for_account`, `mark_as_read`. Endpoints: `GET /notifications/{account_id}`, `POST /notifications/`, `PUT /notifications/{id}/read`.

Show Devin scaffolding the full service:
- `app/models/notification.py` — with `tenant_id`, `to_dict()`, `Base` import
- `app/services/notification_service.py` — with `db: Session`, `tenant_id: str` params, `log_audit_event()` calls
- `app/routes/notifications.py` — Pydantic models, `get_tenant_from_request()`, `Depends(get_db)`
- Registration in `app/main.py` — `app.include_router(notifications.router, tags=["Notifications"])`
- `tests/test_notifications.py` — using `client` fixture from `conftest.py`

**Step 6: Show the same skill in Windsurf.** Paste the same Prompt 3 into Windsurf. Show it follows the same skill, produces the same structure. The foundation layer is the shared substrate across all surfaces.

**Key takeaway:** Ask → Ask → Execute. Discovery and scoping are cheap (Ask Devin). Execution is where the skill drives consistency. The same skill works identically in Windsurf, Chisel, and Devin Cloud.

---

### Hands-On: Build Your First Playbook (0:30–0:45)

**Goal:** Participants pair up. Each pair picks a different repeatable task and authors a skill + knowledge note + playbook.

#### Task Assignments

| Pair | Repeatable Task | Skill to Author | Key Files to Reference |
|---|---|---|---|
| Pair A | Add a Dockerfile to a service | `containerize-service` | `TARGET_ARCHITECTURE_CONSTRAINTS.md` §3 |
| Pair B | Add CI pipeline for a new service | `add-service-ci` | `.github/workflows/ci.yml`, `TARGET_ARCHITECTURE_CONSTRAINTS.md` §5 |
| Pair C | Add tenant-specific config | `add-tenant-config` | `app/config.py` (lines 76–92), `app/middleware.py` |

#### Instructions for Each Pair

1. **Write the skill** (10 min): Create `.agents/skills/{task-name}/SKILL.md` following the structure in the [sample skill file](../.agents/skills/add-new-service/SKILL.md). Every step must reference real file paths and commands from this repo.

2. **Write a knowledge note** (3 min): Capture one non-obvious thing you learned while writing the skill. Format:
   ```markdown
   # {Title}
   ## Trigger
   {When this knowledge should surface}
   ## Content
   {The actual knowledge}
   ```

3. **Write a playbook** (7 min): Chain your skill with at least one sub-agent delegation. The spec you already know *becomes* the playbook — same structure, now executable.

#### Coach's Checklist

- [ ] Each skill has concrete file paths (not `<placeholder>`)
- [ ] Each skill ends with a verification step (`python -m pytest tests/ -v`)
- [ ] Each knowledge note has a trigger condition
- [ ] Each playbook has at least one sub-agent step with an exact prompt
- [ ] Each playbook has measurable success criteria

---

### Scaling Strategy (0:45–0:55)

**Goal:** Show how the foundation layer multiplies across implementations.

#### The Multiplication Model

```
                    Foundation Layer (committed once)
                    ┌─────────────────────────────┐
                    │ 5 Skills                     │
                    │ 3 Knowledge Notes            │
                    │ 2 Playbooks                  │
                    │ 1 Chisel Batch Script        │
                    └──────────────┬──────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
              ▼                    ▼                    ▼
     ┌────────────────┐  ┌────────────────┐  ┌────────────────┐
     │ Tenant:        │  │ Tenant:        │  │ Tenant:        │
     │ acme_corp      │  │ globex_inc     │  │ initech        │
     │                │  │                │  │                │
     │ 5 services     │  │ 5 services     │  │ 5 services     │
     │ extracted      │  │ extracted      │  │ extracted      │
     │ Same skills    │  │ Same skills    │  │ Same skills    │
     │ Same playbooks │  │ Same playbooks │  │ Same playbooks │
     │ Tenant-scoped  │  │ Tenant-scoped  │  │ Tenant-scoped  │
     │ config only    │  │ config only    │  │ config only    │
     └────────────────┘  └────────────────┘  └────────────────┘

     At 50 tenants: 5 skills × 50 tenants = 250 service deployments
                    from 1 foundation layer
```

#### (a) Sub-Agent Orchestration via Chisel

Show [`coe-enablement/chisel-batch.sh`](chisel-batch.sh):
- Loops over all 5 planned services from `TARGET_ARCHITECTURE_CONSTRAINTS.md` §7
- Invokes the `add-observability-to-service` skill for each
- Validates all tests pass at the end
- This is 1 script that replaces 5 manual sessions

#### (b) Repo-Scoped vs. Org-Scoped Knowledge

| Scope | Where | What Goes Here | TraderX Example |
|---|---|---|---|
| **Repo-scoped** | `.agents/skills/` in this repo | Patterns specific to TraderX: multi-tenant middleware, SQLAlchemy model conventions, trade state machine | `add-new-service` skill |
| **Org-scoped** | Devin Knowledge Notes (org-level) | Cross-repo standards: Python coding conventions, testing pyramid, PR review checklist | "Python Coding Best Practices" note |

#### (c) Playbook Parameterization

The `extract-service` playbook accepts `{service_name}`, `{domain}`, `{responsibilities}` as inputs. Same playbook, different parameters:

```
extract-service(service=account, domain=Accounts, resp="Account CRUD, validation")
extract-service(service=trading, domain=Trading, resp="Trade submission, state machine")
extract-service(service=position, domain=Positions, resp="Position tracking, queries")
```

Each invocation produces identical structure, tenant-parameterized config.

#### (d) CI Integration

Trigger Devin sessions from GitHub Actions:

```yaml
# .github/workflows/devin-extract-service.yml
on:
  workflow_dispatch:
    inputs:
      service_name:
        description: 'Service to extract'
        required: true
jobs:
  extract:
    runs-on: ubuntu-latest
    steps:
      - uses: cognition-ai/devin-action@v1
        with:
          prompt: |
            Use the extract-service playbook to extract the
            ${{ inputs.service_name }} service from the TraderX monolith.
```

---

### Wrap-Up & Next Steps (0:55–1:00)

#### Ownership Matrix

| Skill | Owner | Status |
|---|---|---|
| `add-new-service` | (already committed) | ✓ Done |
| `add-api-endpoint` | (already committed) | ✓ Done |
| `add-integration-test` | (already committed) | ✓ Done |
| `add-observability-to-service` | (already committed) | ✓ Done |
| `containerize-service` | {Pair A} | Due in 1 week |
| `add-service-ci` | {Pair B} | Due in 1 week |
| `add-tenant-config` | {Pair C} | Due in 1 week |
| `extract-service` (playbook) | {Lead engineer} | Due in 2 weeks |

#### Milestone: 2-Week Sprint

- [ ] 5 new skills committed, tested, and reviewed
- [ ] 3 knowledge notes capturing tribal knowledge
- [ ] 1 playbook used in a real delivery sprint
- [ ] Chisel batch script validated against all 5 target services
- [ ] First Devin Cloud session triggered from GitHub Actions

#### Resources

- [Foundation Layer Checklist](foundation-checklist.md) — track progress post-session
- [Sample Playbook](playbook.md) — `extract-service` reference playbook
- [Chisel Batch Script](chisel-batch.sh) — batch observability instrumentation
- [Devin Docs: Skills](https://docs.devin.ai) — skill file authoring reference
- [`TARGET_ARCHITECTURE_CONSTRAINTS.md`](../TARGET_ARCHITECTURE_CONSTRAINTS.md) — the spec driving all of this
- [`LEGACY_ARCHITECTURE.md`](../LEGACY_ARCHITECTURE.md) — current state architecture
