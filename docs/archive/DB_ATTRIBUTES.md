# Database Attributes — User Input vs AI Populated vs System Generated

**Purpose:** For every field in the SafeVoice database, explicitly classify its source. This doc answers the tutor's question: *"Can you tell me, for each attribute, whether it's user input or AI populated, and why?"*

Source of truth: `backend/app/database.py`. Schema design: `schema.dbml`.

## Legend

| Marker | Meaning |
|--------|---------|
| 🧑 **USER_INPUT** | The human typed / uploaded / chose this. Required for consent and legal validity. |
| 🤖 **AI_POPULATED** | The AI classifier produced this. Can change if the classifier is re-run. Must be reproducible. |
| ⚙️ **SYSTEM_GENERATED** | The system computed this deterministically (UUIDs, timestamps, hashes). Never changes once set. |
| 🔗 **FOREIGN_KEY** | Reference to another record. Structure, not content. |

## `users` table

| Field | Source | Notes |
|-------|--------|-------|
| `id` | ⚙️ SYSTEM | UUID generated on insert |
| `email` | 🧑 USER | Primary identifier for magic-link auth |
| `display_name` | 🧑 USER | Optional, shown in UI |
| `language` | 🧑 USER | `"de"` or `"en"` — user's preferred UI language |
| `created_at` | ⚙️ SYSTEM | UTC insert timestamp |
| `updated_at` | ⚙️ SYSTEM | Auto-updates on modification |
| `deleted_at` | ⚙️ SYSTEM | Set when user triggers GDPR soft-delete. `NULL` for active users. |

**Privacy note:** `deleted_at` is the only field that can move a user from "visible" to "pending hard delete". After 7 days, hard-delete runs and the row is removed entirely.

## `cases` table

| Field | Source | Notes |
|-------|--------|-------|
| `id` | ⚙️ SYSTEM | UUID |
| `user_id` | 🔗 FK | References `users.id`. Nullable for anonymous cases. |
| `title` | 🤖 AI | Suggested by classifier from first evidence item; user can edit → becomes 🧑 USER |
| `summary` | 🤖 AI | Classifier-generated short description (English) |
| `summary_de` | 🤖 AI | German translation produced by the same LLM call |
| `status` | ⚙️ SYSTEM → 🧑 USER | Defaults to `"open"`; user transitions to `in_progress`, `closed` |
| `overall_severity` | 🤖 AI | Computed from aggregate of evidence-item severities (`pattern_detector.compute_overall_severity`) |
| `created_at` | ⚙️ SYSTEM | UTC |
| `updated_at` | ⚙️ SYSTEM | Auto-updates |

## `evidence_items` table

| Field | Source | Notes |
|-------|--------|-------|
| `id` | ⚙️ SYSTEM | UUID |
| `case_id` | 🔗 FK | References `cases.id` |
| `content_type` | 🧑 USER | `"text"`, `"url"`, or `"screenshot"` — determined by how user submitted |
| `raw_content` | 🧑 USER | Original text, URL, or base64-encoded image the user provided |
| `extracted_text` | 🤖 AI | OCR (`services/ocr.py`) for screenshots, scraped text (`services/scraper.py`) for URLs. NULL for direct text input. |
| `content_hash` | ⚙️ SYSTEM | SHA-256 of `raw_content` — evidence-integrity anchor |
| `hash_chain_previous` | ⚙️ SYSTEM | SHA-256 of the previous evidence item in this case — forms tamper-evident chain |
| `platform` | 🤖 AI | Detected from URL domain (`scraper.detect_platform`) or from classification context |
| `source_url` | 🧑 USER | Original URL if user submitted a link |
| `archived_url` | ⚙️ SYSTEM | Archive.org snapshot URL — created at ingest time, independent of AI |
| `timestamp_utc` | ⚙️ SYSTEM | UTC capture timestamp |
| `metadata_json` | ⚙️ SYSTEM | Additional structured data (author, scraped comments count, etc.) |

**Evidence-integrity guarantee:** `content_hash` + `hash_chain_previous` form a cryptographic chain. Tampering with any past evidence item invalidates every subsequent hash. Used in court-export (`services/court_export.py`).

## `classifications` table

Every field here is AI-produced by the 3-tier classifier (see `AI_FLOW.md`).

| Field | Source | Notes |
|-------|--------|-------|
| `id` | ⚙️ SYSTEM | UUID |
| `evidence_item_id` | 🔗 FK | 1:1 with evidence_items |
| `severity` | 🤖 AI | `none` / `low` / `medium` / `high` / `critical` |
| `confidence` | 🤖 AI | 0.0-1.0 — classifier's self-reported confidence |
| `classifier_tier` | ⚙️ SYSTEM | `1`=LLM, `2`=transformer, `3`=regex. Records which tier produced this. Critical for audit. |
| `summary` | 🤖 AI | EN narrative of the classification |
| `summary_de` | 🤖 AI | DE narrative |
| `potential_consequences` | 🤖 AI | EN — legal consequences for the perpetrator |
| `potential_consequences_de` | 🤖 AI | DE |
| `recommended_actions` | 🤖 AI | EN — what the victim should do |
| `recommended_actions_de` | 🤖 AI | DE |
| `classified_at` | ⚙️ SYSTEM | When this classification ran |

**Reproducibility rule:** if `classifier_tier=3` (regex) classifications are always deterministic — same input produces same output. Tier 1/2 are non-deterministic by default (we use `temperature=0` to minimize variance, but model updates can shift output). This is why `classifier_tier` is stored.

## `categories` table (reference data)

All 🧑 USER / authored — seeded from `database.py::seed_categories_and_laws()`. Not user-generated at runtime; populated at deploy time.

| Field | Source | Notes |
|-------|--------|-------|
| `id` | 🧑 AUTHOR | String slug like `"harassment"` |
| `name`, `name_de` | 🧑 AUTHOR | Display labels |
| `description`, `description_de` | 🧑 AUTHOR | Long-form explanation |

## `laws` table (reference data)

Same as `categories` — authored reference data, seeded at deploy time.

| Field | Source | Notes |
|-------|--------|-------|
| `id` | 🧑 AUTHOR | Slug like `"stgb-185"` |
| `code` | 🧑 AUTHOR | `"stgb"` / `"netzdg"` |
| `section` | 🧑 AUTHOR | `"185"` / `"126a"` |
| `name`, `name_de` | 🧑 AUTHOR | Display labels |
| `full_text`, `full_text_de` | 🧑 AUTHOR | Actual statute text |
| `max_penalty` | 🧑 AUTHOR | E.g. `"Up to 5 years"` |
| `jurisdiction` | 🧑 AUTHOR | Default `"DE"` — ready for multi-jurisdiction |

## Junction tables

`classification_categories` and `classification_laws` — pure relational structure, no content. Both columns are FK + PK.

## Summary Counts

| Source | Count |
|--------|-------|
| 🧑 USER_INPUT fields | 10 |
| 🤖 AI_POPULATED fields | 14 |
| ⚙️ SYSTEM_GENERATED fields | 12 |
| 🔗 FOREIGN_KEY fields | 3 |
| 🧑 AUTHORED (reference data) | ~18 |

## Why This Classification Matters

1. **Legal reliability:** For court evidence, judges need to know which fields humans entered (subjective, contestable) vs which the system measured (objective, verifiable). Hashes and timestamps are defensible because they're 🔗 SYSTEM_GENERATED.
2. **GDPR compliance:** "Right to rectification" (Art. 16 DSGVO) applies mainly to 🧑 USER_INPUT fields. 🤖 AI_POPULATED fields require re-classification rather than direct edit.
3. **Reproducibility:** Only 🤖 AI fields may change between classifier versions. This is why we store `classifier_tier` — to know which classifier produced any given result.
4. **Cost audits:** 🤖 AI_POPULATED fields cost money (OpenAI tokens). Knowing exactly which fields are AI-produced lets us estimate per-case cost.

## Open Questions for Tutor

These are real design tensions, not gaps:

1. Should `overall_severity` be stored (current) or always recomputed from evidence items? Trade-off: storage consistency vs performance.
2. Should `title` default to first 60 chars of first evidence, or always require AI generation? Current: AI. Costs ~200 tokens per case.
3. If a classification changes between runs (tier 1 vs tier 3), do we overwrite or version? Current: overwrite. Should consider keeping history for audit.
