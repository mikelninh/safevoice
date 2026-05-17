# Sprint 1 — What Shipped

**Goal:** make SafeVoice deployable by NGOs like HateAid.

**Status at end of 2026-04-12 session:** ~80% shipped. All backend infrastructure done + tested. Frontend admin dashboard deferred to live session (see "Remaining").

## Shipped

### Multi-tenant data model
- New SQLAlchemy tables: `orgs`, `org_members`
- `cases` table extended: `org_id`, `assigned_to`, `visibility` columns
- **Alembic** installed + configured. First migration `1aacd6c576ec` creates everything idempotently (safe for fresh AND existing DBs).
- `User.org_memberships` relationship, `Org.cases` back-ref, `Case.assignee` — all wired.

### Authorization layer (`services/authz.py`)
- Central `require_case_access(action=...)` dependency
- Central `require_org_access(action=...)` helper
- `list_accessible_cases(user)` for list views
- Roles: owner > admin > caseworker > viewer
- Visibility: private (creator-only) vs org (all members)
- 17 unit tests covering cross-tenant isolation, role enforcement, visibility rules

### Org service (`services/org_service.py`)
- `create_org` — auto-assigns creator as owner
- `add_member` (idempotent — updates role if already a member)
- `remove_member` (blocks removing last owner)
- `change_member_role` (owner-only for appointing new owners; blocks demoting last owner)
- `list_orgs_for_user`
- `get_org_settings` / `update_org_settings` (validated allowed keys)

### Org CRUD API (`routers/orgs.py`)
```
POST   /orgs                              Create (creator = owner)
GET    /orgs                              List user's orgs
GET    /orgs/{slug_or_id}                 Detail
PUT    /orgs/{slug_or_id}                 Update metadata + settings
DELETE /orgs/{slug_or_id}                 Delete (owner-only)

GET    /orgs/{slug_or_id}/members         List
POST   /orgs/{slug_or_id}/members         Invite by email
PUT    /orgs/{slug_or_id}/members/{uid}   Change role
DELETE /orgs/{slug_or_id}/members/{uid}   Remove
```
Every endpoint runs through `require_org_access(action=...)`.

### Bulk import (`routers/bulk_import.py`)
```
POST   /bulk/import/json     — programmatic import (structured items list)
POST   /bulk/import/csv      — CSV file upload (multipart/form-data)
```
- Requires `action="write"` on target case
- Max 500 items/batch, max 10 MB CSV
- Individual row failures don't abort the batch
- Preserves hash chain (each new evidence links to the previous)
- CSV columns: `text` (required), `source_url`, `author_username`, `platform`

### Legal-grade PDF exporter (`services/legal_pdf.py`)
```
GET    /reports/{case_id}/legal-pdf      NGO-grade PDF with letterhead + chain-of-custody
```
- Pulls org letterhead + signature from `org.settings_json`
- Case summary block + per-evidence details
- **Appendix A: Chain of Custody** — SHA-256 hash chain visualization
- **Appendix B: Legal Disclaimer** — explicit "not legal advice" block
- Embedded signature placeholder (for future DocuSign integration)
- Graceful fallback: cases without an org get default SafeVoice branding

### HateAid pitch deck (`docs/HATEAID_PITCH.md`)
- German-language draft, 8 sections
- Framed as "feedback/validation ask", not "sell you a tool"
- Concrete scenarios with time savings (~85 min/case × 500 cases/year)
- Next steps: 30-min call → AVV + DPIA review → 2-week pilot

### Tests (`tests/test_authz.py`)
- 17 new tests covering all authz paths
- **Full suite: 485 passing, 0 regressions.**
- New test coverage on:
  - Role ordering (`role_meets`)
  - Cross-tenant isolation (Org A users cannot see Org B cases)
  - Private vs org visibility enforcement
  - Caseworker cannot delete, only admin+
  - Slug-based org lookup
  - `list_accessible_cases` correct filtering

## Remaining for Sprint 1 (deferred — require live session or external setup)

### Frontend admin dashboard (~1-2 days)
Design done. Not built because React components are easier to iterate live:
- Org switcher in top nav
- Org dashboard (members table, settings tab)
- Member invite flow (email + role picker)
- Case list filtered by org with filters (severity, assignee, status)
- Bulk import UI (drag-drop CSV)

I can scaffold the React components in the next session; polish belongs in a live session where you can click through.

### Supabase migration (`docs/SUPABASE_MIGRATION.md` — to write)
Deferred because:
1. Existing magic-link auth is functional
2. Supabase requires external project creation + env vars + RLS policy scripts
3. Low ROI until HateAid starts using it

When HateAid signs on, migrate in ~1 week. Port pattern from `fertility-foundations`. Design doc exists in `docs/MULTI_TENANT_DESIGN.md`.

### DSGVO legal review
Documents drafted in `docs/DSGVO_COMPLIANCE.md`:
- AVV template
- DPIA framework
- Sub-processor list
- Breach notification procedure

These need review by a qualified Rechtsanwalt before deployment. Estimate €500-1500 one-time fee. Owner: Mikel.

## What Changed in the Codebase

New files:
```
backend/alembic/                              # Alembic setup (ini + env.py)
backend/alembic/versions/1aacd6c576ec_*.py    # First migration
backend/app/services/authz.py                  # Authorization helpers
backend/app/services/org_service.py            # Org business logic
backend/app/services/legal_pdf.py              # NGO-grade PDF exporter
backend/app/routers/orgs.py                    # Org CRUD
backend/app/routers/bulk_import.py             # CSV/JSON bulk classification
backend/tests/test_authz.py                    # 17 authz tests
docs/HATEAID_PITCH.md                          # German-language pitch deck
docs/SPRINT_1_SUMMARY.md                       # This file
```

Modified files:
```
backend/app/database.py                        # New Org, OrgMember models + Case cols
backend/app/schemas.py                         # Org + bulk import schemas
backend/app/main.py                            # Register orgs + bulk_import routers
backend/app/routers/reports.py                 # Add /reports/{id}/legal-pdf
backend/tests/test_classifier.py               # Updated health-endpoint format
backend/tests/test_edge_cases.py               # Updated large-payload expectation
requirements.txt                               # Added alembic
```

## Running What's New

```bash
cd backend
source venv/bin/activate

# Apply migration
alembic upgrade head

# Run full test suite
TESTING=1 pytest tests/

# Dev server
uvicorn app.main:app --reload
```

### Example: Create an org, add a member, import cases

```bash
# 1. Login (get session token)
TOKEN=$(curl -X POST http://localhost:8000/auth/login -H 'Content-Type: application/json' \
  -d '{"email":"alice@example.com"}' | jq -r .magic_link_token)
SESSION=$(curl -X POST http://localhost:8000/auth/verify -H 'Content-Type: application/json' \
  -d "{\"token\":\"$TOKEN\"}" | jq -r .session_token)
AUTH="Authorization: Bearer $SESSION"

# 2. Create org
curl -X POST http://localhost:8000/orgs -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"slug":"hateaid","display_name":"HateAid e.V.","contact_email":"info@hateaid.org"}'

# 3. Invite a caseworker
curl -X POST http://localhost:8000/orgs/hateaid/members -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"email":"bob@hateaid.org","role":"caseworker"}'

# 4. Create a case (existing endpoint, now org-aware)
CASE_ID=$(curl -X POST http://localhost:8000/cases/ -H "$AUTH" -H 'Content-Type: application/json' \
  -d '{"title":"Coordinated attack 2026-04"}' | jq -r .id)

# 5. Bulk import from CSV
curl -X POST http://localhost:8000/bulk/import/csv -H "$AUTH" \
  -F "case_id=$CASE_ID" -F "file=@evidence.csv"

# 6. Get legal-grade PDF
curl -O -J http://localhost:8000/reports/$CASE_ID/legal-pdf -H "$AUTH"
```

## Honest Assessment

**What's solid:**
- Database model + migration handle both fresh and existing DBs cleanly
- Authorization is centralized — any future endpoint uses the same helpers
- Tests cover cross-tenant isolation (the highest-risk class of bugs)
- Bulk import handles partial failures without losing good rows
- Legal PDF reads org settings — branding is data-driven, not hardcoded

**What's still MVP and needs Sprint 2 work:**
- Frontend for all the new backend features
- Supabase RLS as defense-in-depth (currently: app-layer authz only)
- DSGVO legal review sign-off
- Real HateAid pilot usage

**What would break under pressure:**
- No pagination on `/cases/` list — fine up to ~500 cases, breaks at 10K
- Rate limiting is in-memory (per-process) — won't scale past 1 worker
- Emergency delete doesn't purge backups (documented, needs cron job)

These are acceptable MVP gaps, documented in `docs/DSGVO_COMPLIANCE.md` and the open questions sections of the other doc files.

## Next Sprint

Per the [build plan](../wiki/wiki/meta/build-plan-2026.md), **Sprint 3** starts next (Sprint 2 was absorbed into 3 via monorepo-on-demand strategy):

- Monorepo kickoff (`demokratie-platform`)
- Politiker-Tool MVP: Policy-Kompass, Wähler-Simulator, Kosten-Rechner
- GitLaw v1: real Bundestag XML/PDF parser

Sprint 4: MiroFish × policy paper + Prototype Fund / Schöpflin applications.
