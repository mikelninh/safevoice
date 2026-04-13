# Case CRUD — Endpoint Design

**Router:** `backend/app/routers/cases.py`
**Prefix:** `/cases`

Cases are the primary user-facing entity. A **case** groups related **evidence items** (harassment messages, screenshots, URLs) with their **classifications** and **pattern flags**.

## Mental Model

```
Case (1) ──< has many >── Evidence Item (n) ──< 1:1 >── Classification
   │
   └── title, summary, status, overall_severity
```

- One user can have many cases
- One case has many evidence items
- Each evidence item has exactly zero or one classification (classifications are idempotent re-runs)

## Endpoints

### `GET /cases/` — List all cases

Returns `CaseListOut` (lightweight — no nested evidence for performance).

**Why separate `CaseListOut` from `CaseOut`:**
- List view shows 10-50 cases — loading all evidence per case would be N+1 catastrophe
- List shows only summary fields: title, status, severity, dates, evidence count
- Drill-down to detail via `GET /cases/{id}`

**Order:** `updated_at DESC` (most recently active first).

**Response:**
```json
[
  {
    "id": "uuid",
    "title": "Instagram harassment campaign",
    "status": "open",
    "overall_severity": "high",
    "created_at": "2026-04-10T...",
    "updated_at": "2026-04-12T...",
    "evidence_count": 7
  }
]
```

### `GET /cases/{case_id}` — Case detail

Returns `CaseOut` with all nested evidence items and their classifications. Uses SQLAlchemy `joinedload` for a single query (no N+1).

**404** if case doesn't exist.

### `POST /cases/` — Create empty case

**Request:**
```json
{
  "title": "Optional — defaults to 'New Case'",
  "victim_context": "Optional free-text context from the victim"
}
```

Creates a new case row with defaults. `overall_severity="none"`, `status="open"`, no evidence yet. User adds evidence via subsequent calls.

### `PUT /cases/{case_id}` — Update case metadata

```json
{"title": "Renamed case", "status": "closed"}
```

Only non-null fields are updated. Partial update pattern (PATCH semantics with PUT endpoint — common shortcut).

**Allowed status transitions:**
- `open` → `in_progress`
- `in_progress` → `closed`
- Any → `open` (reopening)

(Validation currently permissive — production should reject invalid transitions.)

### `DELETE /cases/{case_id}` — Delete case

Cascades to all evidence items and their classifications (SQLAlchemy `cascade` on relationship).

**Hard delete**, not soft. A case being deleted means evidence is gone. This is by design — if a victim wants to delete a case, they want the evidence GONE, not marked deleted.

### `POST /cases/{case_id}/evidence` — Add evidence (the hot path)

This is where most of the AI work happens. Endpoint lives in `cases.py` because evidence always belongs to a case.

**Request:**
```json
{
  "content_type": "text",
  "text": "You should kill yourself, nobody wants you here.",
  "source_url": "https://instagram.com/p/abc123",
  "author_username": "toxic_user",
  "platform": "instagram"
}
```

**What happens (in order):**
1. Verify case exists (404 if not)
2. Determine active classifier tier (LLM → transformer → regex)
3. Classify the text (`services/classifier.classify`)
4. Fetch the previous evidence item's hash (`get_last_hash`) — for the cryptographic chain
5. Archive the URL (if any) via archive.org (`archive_url_sync`)
6. Persist evidence + classification atomically (`add_evidence_with_classification`)
7. Return full evidence record with classification

**Why atomic persistence:** if the DB write fails mid-way, we don't want half an evidence item with no classification. The helper wraps both inserts in one transaction.

**Archive.org call is synchronous** — we block the request for ~1-2 seconds. Trade-off: simpler code, no job queue needed. If archive.org is down, we continue without the backup (graceful degradation).

## CRUD Coverage

| Operation | Endpoint | Method | Returns |
|-----------|----------|--------|---------|
| Create | `POST /cases/` | POST | CaseOut |
| Read (list) | `GET /cases/` | GET | `list[CaseListOut]` |
| Read (detail) | `GET /cases/{id}` | GET | CaseOut |
| Update | `PUT /cases/{id}` | PUT | CaseOut |
| Delete | `DELETE /cases/{id}` | DELETE | `{"message": "..."}` |
| Add evidence | `POST /cases/{id}/evidence` | POST | EvidenceOut |

## Schemas

Defined in `backend/app/schemas.py`:

| Schema | Used for | Key difference from SQLAlchemy model |
|--------|----------|--------------------------------------|
| `CaseCreate` | POST body | only `title`, `victim_context` — everything else is system-set |
| `CaseUpdate` | PUT body | optional fields; nulls mean "don't change" |
| `CaseListOut` | List response | no nested evidence |
| `CaseOut` | Detail response | full evidence + classifications |
| `EvidenceCreate` | POST body | what the user submits |
| `EvidenceOut` | Response | full record with hash, archive URL, classification |
| `ClassificationOut` | Nested in EvidenceOut | with nested categories + laws |

**Why separate Pydantic schemas from SQLAlchemy models:**
- SQLAlchemy models represent storage (column types, relationships)
- Pydantic schemas represent API contracts (request validation, response shape)
- Coupling them tightly leaks DB concerns to the API surface
- Allows renaming DB columns without breaking API clients

**`model_config = {"from_attributes": True}`:** tells Pydantic to read values from SQLAlchemy object attributes (not dict keys). Replaces the old `orm_mode = True`.

## Ownership & Multi-tenancy (Sprint 1)

**Current state:** cases have optional `user_id` FK but endpoints don't enforce ownership. Anyone with the case_id can read/write it.

**This is an MVP gap, not a design choice.** Sprint 1 hardening:
- `/cases/` lists only *current user's* cases
- `GET/PUT/DELETE /cases/{id}` verifies `case.user_id == current_user.id`
- Organization ownership: `case.org_id` for NGO multi-tenancy
- Row-level security via Supabase RLS when we migrate auth

## Error Handling

| HTTP | When |
|------|------|
| 400 | Invalid request body (missing `text` in EvidenceCreate) |
| 404 | `case_id` doesn't exist |
| 422 | URL scraping fails (content unreachable) |

## Hash Chain Invariants

Every evidence item links to the previous one via `hash_chain_previous`. This creates a tamper-evident chain per case:

```
Evidence 1: content_hash = H1, hash_chain_previous = NULL
Evidence 2: content_hash = H2, hash_chain_previous = H1
Evidence 3: content_hash = H3, hash_chain_previous = H2
```

Modifying evidence 1's content changes H1, breaking the link to evidence 2. Visible in exported court documents.

**`get_last_hash(db, case_id)`** returns the most recent evidence's `content_hash` in this case. Used when adding new evidence to preserve the chain.

## Open Questions for Tutor

1. **Delete cascades to evidence.** If a user deletes a case, should archived evidence (archive.org snapshots) also be purged? Trade-off: DSGVO right-to-erasure vs preserving cryptographic history for already-exported court packets.
2. **Case merging:** what if a user creates two cases about the same attacker, then realises they should be one? No endpoint for this today. Workaround: delete + recreate.
3. **`victim_context`** is in `CaseCreate` but currently unused downstream. Should it be stored? Fed to the classifier as context? Data-minimization argues against.
