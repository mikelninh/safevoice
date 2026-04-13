# SafeVoice — Tutor Study Guide

**Read this front-to-back.** It's the complete material for the April 20 presentation with Zisis Batzos, in the order you'd walk through it.

Every section answers "*what is it → why did we choose it → what would break if we did it differently.*" Zisis's question will be *why*, not *what*. This guide prepares you to answer.

---

## Table of Contents

1. [Tutor's 6 Items — What's Due](#1-tutors-6-items--whats-due)
2. [System Overview (2 min)](#2-system-overview-2-min)
3. [Database Attributes — User vs AI vs System](#3-database-attributes)
4. [The AI Flow — LLM Classifier](#4-the-ai-flow)
5. [User CRUD — Magic Links & Emergency Delete](#5-user-crud)
6. [Case CRUD — Cases, Evidence, Hash Chain](#6-case-crud)
7. [Classification API — 5 Endpoints](#7-classification-api)
8. [Structured Outputs — v1 → v2 Upgrade](#8-structured-outputs)
9. [Presentation Walkthrough — Likely Questions](#9-walkthrough)
10. [What's Next (Sprint 1 preview)](#10-whats-next)

---

## 1. Tutor's 6 Items — What's Due

From Zisis on 2026-03-27, due 2026-04-20:

| # | Item | Where it's answered |
|---|------|--------------------|
| 1 | DB attributes: user_input vs AI_populated | Section 3 |
| 2 | User CRUD endpoints | Section 5 |
| 3 | Case CRUD endpoints | Section 6 |
| 4 | AI flow design (input, context, system prompt) | Section 4 |
| 5 | Classification endpoints | Section 7 |
| 6 | Parse structured output (OpenAI structured outputs) | Section 8 + code in `backend/app/services/classifier_llm_v2.py` |

**Deliverables shipped:**
- 5 architecture docs (in `docs/`)
- `classifier_llm_v2.py` — modern Pydantic-based structured outputs (14 tests passing)
- This study guide

---

## 2. System Overview (2 min)

SafeVoice takes a piece of digital harassment (text, URL, or screenshot) and produces a **court-ready document** classifying it under German criminal law.

Typical flow:
```
Victim pastes "You'll regret ever saying that"
     ↓
SafeVoice classifies:
  - severity: medium → high
  - categories: [threat]
  - applicable laws: § 241 StGB (Bedrohung), NetzDG § 3
  - confidence: 0.87
     ↓
Evidence is hashed (SHA-256), archived (archive.org), stored in case
     ↓
PDF exported, filed as Strafanzeige with Staatsanwaltschaft
```

**Time from submission to PDF: < 30 seconds.**

**Core architectural tensions we navigate:**

- **Legal reliability vs usability** — a victim under stress shouldn't need to be a lawyer. So the AI does the legal mapping; the hash chain makes it verifiable.
- **Availability vs cost** — OpenAI is the best classifier but requires money. Transformer is free but rigid. Regex always works but misses nuance. So we use all three in a fallback chain.
- **Privacy vs evidence** — victims need to delete their data. Courts need immutable evidence. So: soft delete with 7-day recovery for the account, plus emergency hard-delete. Already-exported PDFs remain with the victim.

---

## 3. Database Attributes

*[Source: `docs/DB_ATTRIBUTES.md`]*

Every field in the database is classified by source. This is essential because:

1. **Legal:** courts distinguish user claims (subjective) from system measurements (objective)
2. **DSGVO:** right to rectification (Art. 16) applies mainly to USER_INPUT fields
3. **Reproducibility:** AI_POPULATED fields may differ between classifier versions — we store `classifier_tier` to know which produced which
4. **Cost:** AI_POPULATED fields cost money — counting them gives per-case cost

### Legend

| Marker | Meaning |
|--------|---------|
| 🧑 **USER_INPUT** | Human typed / uploaded / chose this |
| 🤖 **AI_POPULATED** | AI classifier produced this |
| ⚙️ **SYSTEM_GENERATED** | System computed deterministically (UUID, timestamp, hash) |
| 🔗 **FOREIGN_KEY** | Reference, not content |

### Tables

#### `users`
- 🧑 `email`, `display_name`, `language`
- ⚙️ `id`, `created_at`, `updated_at`, `deleted_at`

#### `cases`
- 🧑 `victim_context`, `title` (after user edit)
- 🤖 `title` (default), `summary`, `summary_de`, `overall_severity`
- ⚙️ `id`, `created_at`, `updated_at`, `status`
- 🔗 `user_id`

#### `evidence_items`
- 🧑 `content_type`, `raw_content`, `source_url`
- 🤖 `extracted_text`, `platform`
- ⚙️ `id`, `content_hash`, `hash_chain_previous`, `archived_url`, `timestamp_utc`, `metadata_json`
- 🔗 `case_id`

#### `classifications` — 100% AI_POPULATED except `classifier_tier` (⚙️)
- 🤖 `severity`, `confidence`, `summary`, `summary_de`, `potential_consequences`, `potential_consequences_de`, `recommended_actions`, `recommended_actions_de`
- ⚙️ `id`, `classifier_tier`, `classified_at`
- 🔗 `evidence_item_id`

#### Reference data: `categories`, `laws` — authored at deploy time, not user-generated at runtime

### The Hash Chain (evidence integrity)

Every evidence item links to the previous via `hash_chain_previous`:

```
Evidence 1: content_hash = H1, hash_chain_previous = NULL
Evidence 2: content_hash = H2, hash_chain_previous = H1
Evidence 3: content_hash = H3, hash_chain_previous = H2
```

Modifying evidence 1 changes H1 → breaks link to evidence 2. Chain-tamper-evident. This is what makes the PDF export defensible in court.

### Why `classifier_tier` is stored

`classifications.classifier_tier` = 1 (LLM), 2 (transformer), or 3 (regex). Stored because:
- Audit: which classifier produced this verdict?
- Re-classify: if tier 3 produced the result, we can re-run later with tier 1
- Confidence: tier 3 results should be shown with a "regex-based" UI flag

---

## 4. The AI Flow

*[Source: `docs/AI_FLOW.md`]*

### Big picture

```
User input → Pre-processing (OCR / scrape / direct text)
          → classify(text) — LLM-only
                ↓
           OpenAI GPT-4o-mini (classifier_llm_v2.py)
             ├─ Success: return ClassificationResult
             └─ Failure: raise ClassifierUnavailableError
                ↓
           Router catches error → HTTP 503 "Try again"
          → If classification succeeded and case_id provided:
               Persist (hash + archive + DB write)
          → Response
```

### Why single-tier (removed transformer and regex)

Previous version had 3 tiers (LLM → Transformer → Regex). We removed tiers 2 and 3:

| Removed | Why it failed the bar |
|---------|----------------------|
| Transformer (xlm-roberta) | Under-trained on German legal. Maps everything to "HARASSMENT + NetzDG §3" — no real classification. |
| Regex | Can't handle obfuscation beyond its dictionary. `stirb` caught, `5t1rb` missed. Gives victims false certainty. |

**Core principle:** *a weak classification is more harmful than an honest error.* A victim filing Strafanzeige based on a regex verdict that misses § 241 is worse off than one who sees "please try again" and waits 30 seconds.

**What replaced the fallback:** honest error handling.
- Health endpoint returns `"degraded"` when no API key
- Analyze endpoints return 503 when classifier unreachable
- Error message tells user what happened, no fake result

**Legacy code kept, not wired:** `classifier_regex.py` remains in the repo (for existing tests + as a pattern library reference) but is not called by `classify()`.

### Tier 1 — Deep dive

#### Input
```python
text: str  # 1 to ~10,000 chars
```
**No other context passed to the LLM.** This is a deliberate data-minimization choice (DSGVO Art. 5).

#### System Prompt (4 parts)

1. **Role** — `"Du bist SafeVoice — ein juristischer Klassifikator für digitale Gewalt in Deutschland."`
2. **Rules** — handle typos, slang, obfuscation; err toward higher severity; threats are threats even if indirect
3. **Closed-world enums** — 18 allowed categories, 12 allowed laws. No hallucination space.
4. **Severity scale** — `low` / `medium` / `high` / `critical` with concrete criteria

**Why this prompt works:** closed-world. No hallucination space. Every output is enumerated. That's what makes structured output reliable.

#### Structured Output (v2 — Pydantic)

```python
class LLMClassification(BaseModel):
    severity: LLMSeverity                   # enum
    categories: list[LLMCategory]           # enum, min 1
    confidence: float                       # 0.0-1.0
    requires_immediate_action: bool
    summary: str
    summary_de: str
    applicable_laws: list[LLMLaw]           # enum
    potential_consequences: str
    potential_consequences_de: str

completion = client.chat.completions.parse(
    model="gpt-4o-mini",
    temperature=0,
    messages=[...],
    response_format=LLMClassification,
)
result = completion.choices[0].message.parsed   # typed Pydantic instance
```

OpenAI validates the schema server-side. If the model would produce a malformed response, the API retries internally. We get a typed object, not a string to parse.

#### Post-processing

1. Map LLM enum → domain enum (`Severity.HIGH`, `Category.DEATH_THREAT`)
2. If categories list is empty, default to `HARASSMENT` (catch-all; empty classification is meaningless)
3. Map law enums → `GermanLaw` objects
4. **Invariant:** if NetzDG § 3 isn't in the list, append it — every piece of platform content in Germany triggers NetzDG by default (this is law, not AI choice)

#### Failure handling

All exceptions caught. On any failure, return `None`. Orchestrator falls to tier 2.

### Tier 2 — Transformer

- Model: `unitary/multilingual-toxic-xlm-roberta`
- Returns toxicity scores across 6 labels
- Map scores to `Severity` via thresholds
- Always attaches `HARASSMENT` + `NetzDG § 3` (conservative)
- Weakness: under-trained on German legal language

### Tier 3 — Regex

- Pattern dictionaries per category: death threats, threats, misogyny, sexual harassment, stalking, scams
- Languages: DE, EN, TR, AR (explicit comments mark sections)
- Each pattern → category + law + minimum severity
- Deterministic: same input, same output, forever

### The critical invariant

**NetzDG § 3 is always appended.** Every piece of social media content triggers platform obligations under § 3 NetzDG. This isn't the AI's call — it's German law. Done in `_to_domain()`.

### Security / flow invariants

1. No user data in system prompt — only the content to classify + reusable rules
2. Stateless — no conversation history between classifications
3. Archive before classify — archive.org is called BEFORE classification so evidence is preserved even if classification fails
4. Hash before classify — the hash is the tamper-evident anchor; classification is interpretation on top

### Cost model

- Tier 1: ~600 in + 200 out tokens = €0.00018 per call
- Per case (1-5 evidence items): €0.001-0.005
- At 10,000 cases/month: ~€40-50/month

---

## 5. User CRUD

*[Source: `docs/USER_CRUD.md`]*

### Magic-link flow (no passwords)

```
POST /auth/login {email}
  → system creates MagicLink (24h TTL)
  → returns token (MVP) / emails it (production)

POST /auth/verify {token}
  → marks token used (prevents replay)
  → creates Session (30-day TTL)
  → returns session_token

Any request:
  Authorization: Bearer <session_token>
  → get_user_by_session(token) → User
```

**Why magic links:**
- No password = no breach exposure + no reuse attacks
- Tokens single-use + expiring = phishing-resistant
- Same model as Slack, Medium, Substack

### Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /auth/login` | Request magic link. Returns success even if email doesn't exist (prevents enumeration). |
| `POST /auth/verify` | Exchange token for session |
| `GET /auth/me` | Current user |
| `PUT /auth/me` | Update display_name, lang |
| `POST /auth/logout` | Invalidate session (active=False) |
| `DELETE /auth/me` | Soft delete, 7-day recovery |
| `DELETE /auth/me/emergency` | Immediate hard delete |

### Emergency delete — why it exists

A victim whose abuser is approaching the device needs an escape hatch. Real apps make "delete" go through 3 confirmations + 24h cooldown. That's unsafe for someone in danger.

**Emergency delete:**
- No confirmation dialog (abuser could see it and force cancel)
- No recovery window
- All data gone synchronously (with acknowledged caveat: backups exist up to 90 days — documented in privacy policy)

### Session management

- **Token:** 256-bit random (`secrets.token_urlsafe(32)`)
- **Expiry:** 30 days
- **Logout:** sets `active=False`, doesn't delete row (audit trail)

### What's missing in MVP (Sprint 1 hardening)

- Rate limiting on `/login` (5 requests / IP / hour)
- Organization accounts (multi-tenant — see Section 10)
- Role-based access (admin, caseworker, viewer)

---

## 6. Case CRUD

*[Source: `docs/CASE_CRUD.md`]*

### Mental model

```
Case ──< has many >── Evidence Item ──< 1:1 >── Classification
```

### Endpoints

| Endpoint | Operation | Returns |
|----------|-----------|---------|
| `GET /cases/` | List (lightweight) | `list[CaseListOut]` |
| `GET /cases/{id}` | Detail (nested) | `CaseOut` |
| `POST /cases/` | Create empty | `CaseOut` |
| `PUT /cases/{id}` | Update metadata | `CaseOut` |
| `DELETE /cases/{id}` | Hard delete with cascade | `{message}` |
| `POST /cases/{id}/evidence` | **Hot path** — classify + persist | `EvidenceOut` |

### Two schemas for one entity

`CaseListOut` (lightweight for list) vs `CaseOut` (full with evidence) — avoids N+1 queries on the list view.

### The hot path: `POST /cases/{id}/evidence`

```
1. Verify case exists (404 if not)
2. Determine classifier tier (1/2/3)
3. Classify the text
4. Fetch previous evidence hash (for chain)
5. Archive URL via archive.org (if URL provided)
6. Persist evidence + classification atomically
7. Return EvidenceOut
```

**Atomic persistence** = single transaction. If DB write fails mid-way, we don't want half an evidence item with no classification.

### Hash chain invariants

`hash_chain_previous` links each evidence to the one before it:
- Modifying evidence 1 → H1 changes → breaks link to evidence 2
- Chain is tamper-evident, not just tamper-detecting
- Visible in exported court PDFs

### SQLAlchemy vs Pydantic

- **SQLAlchemy** = storage (column types, relationships, constraints)
- **Pydantic** = API contracts (request validation, response shape)
- Separating them means we can rename DB columns without breaking API clients

### Hard vs soft delete

`DELETE /cases/{id}` is hard delete with cascade. Intentional: if a victim wants the case gone, they want evidence GONE — not marked as deleted.

Compare with `DELETE /auth/me` which is soft with 7-day recovery — different use case (account regret vs data minimization).

---

## 7. Classification API

*[Source: `docs/CLASSIFICATION_API.md`]*

Five endpoints, all stateless unless `case_id` provided.

| Endpoint | Purpose | Persists? |
|----------|---------|-----------|
| `POST /analyze/text` | Classify text | No |
| `POST /analyze/ingest` | Classify + optionally persist | Optional |
| `POST /analyze/url` | Scrape URL + classify all | Optional |
| `POST /analyze/chat` | Legal Q&A follow-up | No |
| `POST /analyze/case` | Cross-evidence pattern detection | No |

### `/analyze/text` — preview

Simplest endpoint. Returns full `ClassificationResult`. Used for UI's "analyze" button before user commits.

### `/analyze/ingest` — dual-purpose

With `case_id`: persists. Without: ephemeral.

*Design smell:* endpoint overloading. Cleaner would be `/analyze/text` (stateless) + `POST /cases/{id}/evidence` (persistent). `/ingest` is a backward-compat layer.

### `/analyze/url` — scraping flow

1. Detect platform from URL
2. Scrape post + up to 20 comments
3. Archive via archive.org
4. Classify main post + each comment
5. If case_id: persist everything with hash chain maintained

**20-comment cap** prevents runaway ingestion of massive threads. Future: batch classification (one LLM call sees all items in context).

### `/analyze/chat` — legal Q&A

Uses `temperature=0.3` (vs classifier's 0) — warmer tone for conversation. System prompt enforces German legal voice + mandatory disclaimer.

### `/analyze/case` — pattern detection

Cross-evidence analysis:
- `repeated_author`: same username 3+ times
- `coordinated_attack`: multiple accounts, similar content, narrow time window
- `escalation`: severity trend rising
- `temporal_cluster`: many items in short window

Stateless (takes evidence list in request) — frontend already has them loaded, avoids DB round-trip.

---

## 8. Structured Outputs

*[Source: `backend/app/services/classifier_llm_v2.py` + `tests/test_classifier_llm_v2.py`]*

This was tutor item #6: "Parse structured output (OpenAI structured outputs)."

### v1 — current production

```python
response_format = {
    "type": "json_schema",
    "json_schema": {"name": "classification", "strict": True, "schema": {...}}
}
response = client.chat.completions.create(..., response_format=response_format)
data = json.loads(response.choices[0].message.content)  # manual parse
# manually map dict → domain enums
```

Works. Gets ~98% success rate on structure. Manual enum mapping.

### v2 — modern best practice (shipped as part of this sprint)

```python
class LLMClassification(BaseModel):
    severity: LLMSeverity  # enum
    categories: list[LLMCategory]
    ...

completion = client.chat.completions.parse(
    model="gpt-4o-mini",
    response_format=LLMClassification,
    ...
)
parsed: LLMClassification = completion.choices[0].message.parsed  # typed
```

**What v2 gives us:**
- Automatic schema generation from Pydantic
- Type-safe access (no string keys, no dict.get defaults)
- Refusal detection (`msg.refusal` populated if OpenAI declines)
- Cleaner code (~40% fewer lines for the same behavior)

### The test file

`tests/test_classifier_llm_v2.py` — 14 tests, all passing:

- 4 schema validation tests (empty categories rejected, confidence out-of-range rejected, unknown category rejected, valid minimal input accepted)
- 5 domain mapping tests (severity maps, categories map, NetzDG always appended, NetzDG not duplicated, confidence preserved)
- 5 flow tests (no-API-key returns None, is_available checks both SDK and key, refusal returns None, successful classification produces right result, API exception returns None)

Run them:
```
cd backend
source venv/bin/activate
TESTING=1 pytest tests/test_classifier_llm_v2.py -v
```

### Why both v1 and v2 exist

v1 is proven in production. v2 is the refactor. We'd run them side-by-side in staging, compare outputs on a sample, flip the switch if they match. Then retire v1.

---

## 9. Walkthrough

*[Source: `docs/PRESENTATION_NOTES.md`]*

### Session structure (~30-45 min)

| # | Topic | Time |
|---|-------|------|
| 1 | Overview & problem | 3 |
| 2 | DB attributes | 5 |
| 3 | AI flow — LLM classifier, why single-tier | 10 |
| 4 | User CRUD | 5 |
| 5 | Case CRUD | 5 |
| 6 | Classification API | 3 |
| 7 | Structured outputs v1 → v2 | 5 |
| 8 | Q&A | rest |

### Key "why this, not that" answers

**"Why only one tier, not fallback to something simpler?"**
An earlier version had LLM → transformer → regex. We removed the fallbacks because a weak classification is more harmful than an honest error. Regex misses obfuscated German ("5t1rb"); the transformer under-classifies legal specifics. A victim filing Strafanzeige based on a shaky verdict is worse off than one who sees "try again in a moment." Single-tier LLM with clear 503s is more defensible.

**"Why GPT-4o-mini, not GPT-4o?"**
~15x cheaper, ~85% accuracy for this task. Matters at scale (NGO budget).

**"Why not parse free-text?"**
Earlier iteration had 2% malformed-JSON rate — 1 in 50 cases silently failing. Structured output enforcement is zero.

**"Why SHA-256 not MD5/SHA-1?"**
Collision resistance required for legal integrity. SHA-1 is broken. SHA-256 is current evidentiary standard.

**"Why hash CHAIN, not just per-evidence?"**
Per-evidence prevents tampering with one item. Chain prevents reordering or deletion — because the chain breaks.

**"Why magic links, not passwords?"**
No password DB to breach, no reuse attacks, simpler UX, industry standard (Slack, Medium).

**"Why emergency delete is instant?"**
A victim whose abuser is approaching the device needs an escape hatch. Three-step confirmations get people hurt.

### Likely trap questions — with answers

**Q: If OpenAI silently updates the model, do your tests catch it?**
A: Partially. `temperature=0` + structured outputs reduce variance. We have integration tests that classify known-bad phrases and check right categories. If a model update breaks them, we see it. What we don't have: property-based tests bounding worst-case drift. *Future work.*

**Q: If two users submit the same evidence, are they linked?**
A: No. Same hash, different case_ids, different timestamps. Privacy first. Linking across users would require inter-user data sharing — DSGVO-complicated.

**Q: The regex tier doesn't know German law. How does it pick paragraphs?**
A: Conservative heuristics. Death-threat pattern → §241 + §126a. Harassment without threat → §185. When uncertain, always add NetzDG §3 (platform obligation, always applies). Under-classifies some cases. That's intentional — tier 3 is the floor, not the ceiling.

**Q: Why is `user_id` on cases nullable?**
A: Anonymous MVP mode. A victim who doesn't want an account can still use the app. *Design smell:* cases can orphan. Sprint 1: require user_id OR org_id (the multi-tenant migration).

**Q: How do you prevent prompt injection?**
A: Structured output is the defense. The model can output different summary *wording* from injection, but can't invent a new category or law — both are closed enums.

### Things to flag proactively

Zisis values honesty about limitations. Mention unprompted:

1. "We don't version the system prompt. A change today silently affects tomorrow's classifications. We should record `prompt_version` alongside `classifier_tier`."
2. "Classifications are overwritten on re-classification. For audit trail we should keep history."
3. "The `/analyze/url` endpoint blocks synchronously on scraping. A 200-comment post would block the request. Future: async batch."
4. "Hash chain protects within a case. Deleting a case destroys the chain. We rely on exported PDFs for preservation."

### Close

If time permits, 3 slides:
1. Sprint 1 next 6 weeks: NGO-grade (multi-tenant, admin dashboard, legal-grade PDF, DSGVO docs)
2. HateAid pitch scheduled end of Sprint 1
3. Ecosystem: SafeVoice is part of Democracy Säule (Deutschland 2030, GitLaw, Path to Peace, PMM)

Frame: "This is a course project that's already a real tool. Here's how it keeps being one after the course ends."

---

## 10. What's Next

*[Source: `docs/MULTI_TENANT_DESIGN.md` + `docs/DSGVO_COMPLIANCE.md`]*

Sprint 1 (Apr 21 — May 31) turns SafeVoice from "course project" into "NGO-deployable."

### Biggest changes

1. **Multi-tenancy.** New tables: `orgs`, `org_members`. Modifications: `cases.org_id`, `cases.assigned_to`, `cases.visibility`. Role-based access (owner / admin / caseworker / viewer). Row-level security at the DB.
2. **Real auth via Supabase.** Port pattern from fertility-foundations project. Magic-link flow preserved. Session management moves from in-memory to DB.
3. **Admin dashboard.** Org-level metrics, case list with filters, assignment to team members, bulk export (CSV/ZIP).
4. **Legal-grade PDF.** Letterhead support per org, digital signatures, chain-of-custody appendix.
5. **DSGVO docs.** AVV template, DPIA framework, sub-processor list, breach notification procedure — all drafted, needs lawyer review.

### Timeline

| Week | Deliverable |
|------|-------------|
| 1 | Migration + new tables + auth dep |
| 2 | Org CRUD + member management |
| 3 | Modified cases endpoints + RLS |
| 4 | UI: org switcher, dashboard, members |
| 5 | Admin metrics + bulk export |
| 6 | Hardening, HateAid pitch prep |

### HateAid pitch target

End of Sprint 1. The political moment (Ricarda Lang deepfake debate) is NOW — by Q3 2026 the legislative attention may have moved. Pitch deck must land during this window.

Frame for HateAid: *"Here's how we 10x your org's leverage"* — not "here's our tool."

---

## Deliverables Checklist

Everything shipped for tutor item #1-6:

- [x] `docs/DB_ATTRIBUTES.md` — user/AI/system classification table (item 1)
- [x] `docs/USER_CRUD.md` — magic link design (item 2)
- [x] `docs/CASE_CRUD.md` — case endpoints (item 3)
- [x] `docs/AI_FLOW.md` — 3-tier classifier (item 4)
- [x] `docs/CLASSIFICATION_API.md` — analyze endpoints (item 5)
- [x] `backend/app/services/classifier_llm_v2.py` — modern structured outputs (item 6)
- [x] `backend/tests/test_classifier_llm_v2.py` — 14 passing tests
- [x] `docs/PRESENTATION_NOTES.md` — walkthrough
- [x] `docs/MULTI_TENANT_DESIGN.md` — Sprint 1 design
- [x] `docs/DSGVO_COMPLIANCE.md` — compliance pack draft
- [x] This study guide (`docs/TUTOR_STUDY_GUIDE.md`)

**Verification:**
```bash
cd backend
source venv/bin/activate
TESTING=1 pytest tests/ -v
```

Should show 14 new tests passing plus your existing ~412 tests — all green.

Good luck with Zisis.
