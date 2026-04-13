# Classification API — Endpoint Design

**Router:** `backend/app/routers/analyze.py`
**Prefix:** `/analyze`

These endpoints handle **classification without persistence**. They're the "preview" or "quick check" surface — useful for the UI to show a severity estimate before the user commits to creating a case.

Persisted classification happens through `/cases/{id}/evidence` (see `CASE_CRUD.md`).

## The 5 Endpoints

| Endpoint | Purpose | Persists? |
|----------|---------|-----------|
| `POST /analyze/text` | Classify raw text | No |
| `POST /analyze/ingest` | Classify + optionally persist to case | Optional |
| `POST /analyze/url` | Scrape URL + classify | Optional |
| `POST /analyze/chat` | Follow-up legal Q&A | No |
| `POST /analyze/case` | Detect cross-evidence patterns | No |

## `POST /analyze/text` — Stateless Classification

The simplest endpoint. Text in, classification out.

**Request:**
```json
{"text": "You're a worthless piece of shit. I hope you die."}
```

**Response:** full `ClassificationResult`:
```json
{
  "severity": "high",
  "categories": ["harassment", "threat", "death_threat"],
  "confidence": 0.92,
  "requires_immediate_action": true,
  "summary": "Explicit death threat with severe harassment...",
  "summary_de": "Ausdrückliche Todesdrohung mit schwerer Belästigung...",
  "applicable_laws": [
    {"paragraph": "§ 241 StGB", "title": "Threat", ...},
    {"paragraph": "§ 126a StGB", ...},
    {"paragraph": "NetzDG § 3", ...}
  ],
  "potential_consequences": "...",
  "potential_consequences_de": "..."
}
```

**Use case:** UI's "analyze" button — user pastes text, sees classification, then decides whether to save it to a case.

## `POST /analyze/ingest` — Classify + Optionally Persist

This one's dual-purpose: if `case_id` is provided, the evidence is saved to the case; otherwise, returns an ephemeral result.

**Request:**
```json
{
  "text": "...",
  "author_username": "toxic_user",
  "url": "https://instagram.com/p/abc",
  "case_id": "optional-uuid-or-empty"
}
```

**Response (with case_id):**
```json
{
  "evidence_id": "uuid",
  "case_id": "uuid",
  "classification": {...},
  "content_hash": "sha256...",
  "persisted": true,
  "message": "Evidence classified and saved to case."
}
```

**Response (no case_id):** returns the evidence object inline with `persisted: false`.

**Why dual behavior:** lets the frontend have a single endpoint for "analyze and maybe save". Avoids duplicating request logic.

**Design smell:** endpoint overloading. A cleaner design would be two endpoints: `/analyze/text` (stateless) + `POST /cases/{id}/evidence` (persistent). The `/ingest` endpoint is a transitional layer maintained for backward compatibility with early frontend code.

## `POST /analyze/url` — Scrape + Classify

Accepts a social-media URL, scrapes the post and comments, classifies each one.

**Request:**
```json
{"url": "https://instagram.com/p/xyz", "case_id": "optional"}
```

**Behavior:**
1. Detect platform from URL (`scraper.detect_platform`)
2. Scrape main post + up to 20 comments
3. Archive URL via archive.org
4. Classify main post
5. Classify each comment
6. If `case_id`: persist everything atomically, maintaining hash chain
7. Return everything

**Response (with case_id):**
```json
{
  "evidence_id": "main-post-uuid",
  "comment_evidence_ids": ["uuid1", "uuid2", ...],
  "case_id": "uuid",
  "classification": {...},
  "platform": "instagram",
  "persisted": true,
  "message": "Content from instagram classified and saved (8 items)."
}
```

**Design choices:**
- **Cap at 20 comments** — prevents runaway ingestion of 10k-comment posts
- **Graceful scraper failures** return 422 with message
- **Empty-comment filtering** — skip comments with no text (image-only)

**Known weakness:** each comment is classified with its own LLM call. A single Instagram post with 20 comments costs 21 classification calls. Future: batch classification (one LLM call analyzes all 21 items in context).

## `POST /analyze/chat` — Legal Follow-up

Not classification — this is a conversational Q&A about an existing classification.

**Request:**
```json
{
  "question": "Can I file a criminal complaint for this?",
  "context": "Original message: 'You'll regret this'. Classification: high severity, § 241 Threat..."
}
```

**Response:**
```json
{
  "answer": "Yes, this qualifies as § 241 Threat. To file a Strafanzeige you can..."
}
```

**Design choices:**
- Uses `gpt-4o-mini` with `temperature=0.3` — slightly more creative than classification (which uses 0)
- System prompt enforces German legal voice + mandatory disclaimer at the end
- No persistence — chat history is not stored

**Why temperature=0.3, not 0:** legal advice feels robotic at 0. 0.3 allows natural-sounding but still grounded responses.

## `POST /analyze/case` — Cross-Evidence Pattern Detection

Stateless pattern analysis across a batch of evidence items.

**Request:**
```json
{
  "evidence_items": [
    {"id": "...", "author_username": "x", "content_text": "...", "classification": {...}},
    {"id": "...", "author_username": "x", "content_text": "...", "classification": {...}}
  ]
}
```

**Response:**
```json
{
  "pattern_flags": [
    {"type": "repeated_author", "description": "...", "severity": "medium", "evidence_count": 5},
    {"type": "escalation", "description": "...", "severity": "high", "evidence_count": 3}
  ],
  "overall_severity": "high",
  "evidence_count": 5
}
```

Delegates to `pattern_detector.detect_patterns` and `pattern_detector.compute_overall_severity`.

**Patterns detected:**
- `repeated_author` — same username appears 3+ times
- `coordinated_attack` — multiple distinct accounts, similar content, narrow time window
- `escalation` — severity trend increasing across evidence
- `temporal_cluster` — many items in a short window

**Why stateless:** the frontend already has all evidence loaded for the current case; passing it in avoids another DB round-trip.

## Request Schemas Summary

Defined in `backend/app/schemas.py`:

| Schema | Fields |
|--------|--------|
| `AnalyzeTextRequest` | `text: str` |
| `IngestRequest` | `text, author_username, url, case_id?` |
| `AnalyzeUrlRequest` | `url, case_id?` |
| `ChatRequest` | `question, context` |
| `AnalyzeCaseRequest` | `evidence_items: list[EvidenceItem]` |

## Error Codes

| HTTP | When |
|------|------|
| 400 | Missing required field (`text`, `url`) |
| 404 | `case_id` provided but doesn't exist |
| 422 | URL scraping failed (content private / unreachable) |
| 500 | Classifier + fallback + regex all failed (shouldn't happen — regex always succeeds) |

## Rate Limiting

- Default: 120 requests per minute per IP (configurable via `RATE_LIMIT_RPM`)
- Disabled when `TESTING` env var is set (for pytest)
- Classification endpoints are the highest-cost to protect (each = 1 LLM call)

## Open Questions for Tutor

1. **`/analyze/text`** returns a full `ClassificationResult` but doesn't persist — should we hash the text anyway so re-submitting the same text could return cached results? Cost optimization potential.
2. **`/analyze/chat`** uses classification as context but can hallucinate legal specifics. Should we add a retrieval step (pull actual StGB statute text into context)? Would reduce hallucination risk.
3. **`/analyze/url` scrapes up to 20 comments.** Should this be configurable? Higher cap = more evidence captured but higher cost + slower.
