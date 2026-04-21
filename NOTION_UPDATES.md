# Notion Updates — SafeVoice · 21 April 2026

All copy-paste blocks for your Masterschool Notion page. Work top to bottom.
Every `===` section is a single copy-paste target.


═══════════════════════════════════════════════════════════════════════════
1 · PROJECT IDEA DEFINITION  —  replace the whole section
═══════════════════════════════════════════════════════════════════════════

SafeVoice is a digital justice platform that helps victims of online harassment document evidence, get instant legal classification under German criminal law, and export a court-ready report — in 30 seconds.

The stack is a React PWA frontend (bilingual DE/EN with a live Impressum + Datenschutz page) and a FastAPI + SQLAlchemy backend on Railway. Classification runs on OpenAI gpt-4o-mini using Pydantic Structured Outputs — a single LLM call that returns a schema-enforced verdict (severity, categories, applicable paragraphs). If the model refuses or the response fails schema validation, the API returns a clean 503 — no silent fallback.

Today the classifier maps content to 11 German paragraphs (§§ 130, 185, 186, 187, 201a, 238, 241, 126a, 263, 269 StGB + NetzDG § 3). UI and output are available in German and English. The architecture is multi-jurisdictional by design — adding Austria, Switzerland, UK and France is a configuration change, not a rewrite. Turkish and Arabic UI coverage is on the roadmap.

The report layer generates NetzDG platform reports, Strafanzeige drafts, BaFin scam reports, and a full court evidence package (ZIP with PDFs, SHA-256 hash chain, UTC chain of custody). An institutional Partner API exposes the same core to police, NGOs, and law firms. Roadmap integrations: HateAid counselling handoff and Onlinewache across all 16 German states.

Live pages: safevoice-production-0847.up.railway.app (backend + OpenAPI docs) · /impressum · /datenschutz · /analyze · /cases.

Target users — victims of digital harassment first; NGOs (HateAid, Weisser Ring), police cybercrime units, law firms, and policy researchers second.


═══════════════════════════════════════════════════════════════════════════
2 · GITHUB REPO SECTION  —  replace the "[TODO: Deploy…]" line
═══════════════════════════════════════════════════════════════════════════

https://github.com/mikelninh/safevoice

Live on Railway: https://safevoice-production-0847.up.railway.app
Interactive API docs: https://safevoice-production-0847.up.railway.app/docs


═══════════════════════════════════════════════════════════════════════════
3 · DATABASE SCHEMA SECTION  —  replace both old dbdiagram links
═══════════════════════════════════════════════════════════════════════════

DBML source: https://github.com/mikelninh/safevoice/blob/main/schema.dbml

Paste into https://dbdiagram.io to visualise — 8 tables, every column labelled USER INPUT / AI POPULATED / system generated. Core flow: users → cases → evidence_items → classifications, with categories and laws as seeded reference data joined via two M:N junction tables.


═══════════════════════════════════════════════════════════════════════════
4 · "1. users" TABLE DESCRIPTION  —  replace the whole section
═══════════════════════════════════════════════════════════════════════════

1. users

SafeVoice has TWO usage flows — which is why the users table is "optional by design".

Quick flow (default, ~90% of users):
   No email needed. The /analyze page accepts content anonymously, creates a case
   with user_id = NULL (the column is nullable=True in the schema), and stores
   progress in localStorage. This is what the UI copy "Kein Konto nötig. Deine
   Daten bleiben auf deinem Gerät" describes.

Power flow (optional, for anyone who wants it):
   User requests a magic link (POST /auth/login) → receives a 15-minute
   single-use token → session created. Now cases can be claimed across devices,
   exported for GDPR Art. 20, deleted for GDPR Art. 17, and linked to an NGO
   case-worker via the Partner API.

Fields:
   - email             user input, unique, only captured in the power flow
   - display_name      user input, optional
   - language          user input, default 'de' — determines PDF report language
                       (UI language is auto-detected from browser + togglable)
   - created_at, updated_at, deleted_at   system generated (soft-delete for GDPR)

Why no password? Magic-link auth with single-use tokens is safer for victims
under stress: no password to forget, no password DB to leak, tokens are
phishing-resistant because they expire in 15 minutes and only work once.


═══════════════════════════════════════════════════════════════════════════
5 · CLARIFY THE 8 TABLES  —  add note after "classification_laws" section
═══════════════════════════════════════════════════════════════════════════

Note: The database has 8 tables total. Reference data lives in two seeded tables — categories (15 entries) and laws (11 entries). classification_categories and classification_laws are the M:N junction tables that connect a single classification to many categories and many laws. Complete list: users, cases, evidence_items, classifications, categories, laws, classification_categories, classification_laws.


═══════════════════════════════════════════════════════════════════════════
6 · ENDPOINTS SECTION  —  replace the "8 Endpoints" block entirely
═══════════════════════════════════════════════════════════════════════════

30+ endpoints across 12 routers. Core trio: auth · cases · analyze.

Auth (backend/app/routers/auth.py — 8 endpoints)
  POST   /auth/login              request magic link
  POST   /auth/verify             exchange token for session
  GET    /auth/me                 read current user
  PUT    /auth/me                 update display_name, language
  POST   /auth/logout             end session
  DELETE /auth/me                 soft delete (GDPR Art. 17)
  DELETE /auth/me/emergency       hard delete (Safe-Exit pattern)
  GET    /auth/me/export          Art. 20 data export (JSON)

Cases (routers/cases.py — 6 endpoints)
  GET    /cases/                  list
  GET    /cases/{id}              detail + evidence + classifications
  POST   /cases/                  explicit create (rarely used)
  PUT    /cases/{id}              update
  DELETE /cases/{id}              delete (cascade)
  POST   /cases/{id}/evidence     attach evidence to existing case

Analyze (routers/analyze.py — 4 endpoints)
  POST   /analyze/text            classify a string (no DB write)
  POST   /analyze/ingest          evidence + classify + case in one tx
  POST   /analyze/url             scrape URL → classify
  POST   /analyze/case            case-level RAG across N evidence items

Reports, Hash chain, Partner API, Policy exports, Dashboard, Bulk import
— additional routers for downstream use (see /docs at runtime).

Full interactive OpenAPI docs at https://safevoice-production-0847.up.railway.app/docs


═══════════════════════════════════════════════════════════════════════════
7 · "4 TECHNIQUES" TECHNIQUE #3  —  replace the whole JSON-schema block
═══════════════════════════════════════════════════════════════════════════

3. System prompt + Pydantic Structured Outputs (best — what we use)

Same system prompt as in technique #2, but instead of asking for JSON in free text, we pass a Pydantic schema to OpenAI's Structured Outputs API. The schema enforces enum-constrained categories and laws — the model cannot return anything outside the allowed values, because OpenAI refuses schema-invalid responses server-side.

from pydantic import BaseModel, Field, ConfigDict
from enum import Enum

class LLMSeverity(str, Enum):
    low = "low"; medium = "medium"; high = "high"; critical = "critical"

class LLMCategory(str, Enum):
    harassment = "harassment"
    threat = "threat"
    death_threat = "death_threat"
    # ... 15 total, exhaustive

class LLMClassification(BaseModel):
    model_config = ConfigDict(extra="forbid")
    severity: LLMSeverity
    categories: list[LLMCategory] = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)
    summary: str
    summary_de: str
    applicable_laws: list[LLMLaw]

completion = client.chat.completions.parse(
    model="gpt-4o-mini",
    temperature=0,
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Klassifiziere diesen Inhalt:\n\n{text}"},
    ],
    response_format=LLMClassification,
)

parsed = completion.choices[0].message.parsed

This is what we use. Every response is a validated Pydantic instance or None. No json.loads, no code-fence stripping, no regex cleanup. If the model tries to invent a category, the API refuses it before our code sees anything. Refusals are explicit (msg.refusal), not hidden exceptions.


═══════════════════════════════════════════════════════════════════════════
8 · "4 TECHNIQUES" NARRATIVE  —  global find-and-replace
═══════════════════════════════════════════════════════════════════════════

In techniques #1, #2, and #4: replace every occurrence of "Claude" with "OpenAI gpt-4o-mini" — the examples stay the same, just the model name changes. Our stack is OpenAI across both classifier and legal_ai since 20 April 2026.


═══════════════════════════════════════════════════════════════════════════
9 · PROJECT SLIDES LINK  —  replace the mvp.html path
═══════════════════════════════════════════════════════════════════════════

Old link: file:///Users/mikel/safevoice/presentation/mvp.html

New link: https://github.com/mikelninh/safevoice/blob/main/DEMO_SLIDES.html

Description: 11-slide tutor deck. Each action-item slide follows one structure — Task, code/endpoint inventory, design decision, and a one-sentence solution.

Also available in the repo:
  - DEMO_CODE_WALKTHROUGH.html — standalone code walkthrough (see: https://github.com/mikelninh/safevoice/blob/main/DEMO_CODE_WALKTHROUGH.html)
  - STUDY_GUIDE.html — step-by-step implementation guide (see: https://github.com/mikelninh/safevoice/blob/main/STUDY_GUIDE.html)
  - QUIZ.html — 20 MC-question self-check (see: https://github.com/mikelninh/safevoice/blob/main/QUIZ.html)


═══════════════════════════════════════════════════════════════════════════
10 · COMPARISON TABLE  —  paste into the linked Notion sub-page
═══════════════════════════════════════════════════════════════════════════

| #  | Technique                                  | Model        | Accuracy                     | Tokens/call | Cost/call  | Notes                            |
|----|--------------------------------------------|--------------|------------------------------|-------------|------------|----------------------------------|
| 1  | Zero-shot                                  | gpt-4o-mini  | Bad — unstructured text      | ~150        | €0.00003   | Unparseable, no severity, no laws |
| 2  | System prompt + categories                 | gpt-4o-mini  | Better — correct labels      | ~380        | €0.00008   | Still freeform, fragile parsing   |
| 3  | System prompt + Pydantic Structured Outputs (WHAT WE USE) | gpt-4o-mini | Best — schema-enforced | ~420 | €0.00015 | Validated typed instance, refusals explicit |
| 4  | Few-shot with examples                     | gpt-4o-mini  | Same as #3                   | ~900        | €0.00035   | Extra tokens not worth it        |


═══════════════════════════════════════════════════════════════════════════
11 · PROGRESS TIMELINE CHECKMARKS  —  mark these DONE (x)
═══════════════════════════════════════════════════════════════════════════

WEEK 2-3 (16-23.03) — Backend & Database setup
  [x] Initial Backend infrastructure setup         (FastAPI running on Railway)
  [x] Initial DB setup                             (SQLAlchemy + SQLite dev / Postgres prod)
  [x] Create endpoints for CRUD operations         (auth, cases, analyze + 9 more routers)

WEEK 4 (30.03) — First GenAI request
  [x] Study OpenAI docs
  [x] GA101.4 - Prompt Engineering                 (if learning module completed)
  [x] Create text generation endpoint              (POST /analyze/text → OpenAI gpt-4o-mini)
  [x] Iteratively experiment with system + user prompts  (classifier_llm_v2.py, 4 iterations documented in Comparison Table)
  [x] Define and use response format / Structured Outputs  (Pydantic + .parse() → classifications table)
  [x] Update DB schema                             (single-tier LLM schema, categories + laws seeded)

WEEK 5-8 (06-27.04) — GenAI iterations
  [x] GA102.1 - Ethics of Generative AI            (if learning module completed)
  [x] Experiment with temperature, max_completion_tokens  (temperature=0, max_tokens=1024 — "legal must be deterministic")
  [x] Try different prompting techniques           (zero-shot → system prompt → JSON schema → Pydantic Structured Outputs)
  [x] Iteratively for all text-generation requests (both classifier_llm_v2.py AND services/legal_ai.py migrated)
  [ ] [opt] Create 2nd/3rd client (gemini, groq)   — optional, skip
  [x] Create comparison table                      (see Notion Comparison Table sub-page, updated 21 April)

WEEK 9-10 (04-11.05) — RAG & Extras
  [x] Study RAG                                    (implemented in services/legal_ai.py — classic retrieve → augment → generate)
  [ ] Setup VectorDB + embeddings + similarity search  — DESIGN CHOICE: no VectorDB. We retrieve from the relational DB (case_id → N evidence_items). The RAG pattern is preserved; the infrastructure is deliberate. Vector retrieval adds no value for a structured case where the relevant set is bounded and already indexed by case_id.
  [x] [opt] Frontend                               (React PWA live, bilingual DE/EN, Impressum + Datenschutz, deployed to Vercel)
  [x] [opt] Deployment                             (Railway for backend, Vercel for frontend)

WEEK 11-12 (18-25.05) — Finalizing (still ahead)
  [ ] Clean up repo              — already mostly clean; README polished 20 April
  [ ] Create/refine README       — done 20 April (single-tier LLM framing, full endpoint inventory)
  [ ] 3-5 slide deck             — DONE: DEMO_SLIDES.html (11 slides, task/solution structure)
  [ ] 3-5 min video              — still to record
  [ ] Final presentation         — 29.05.2026


═══════════════════════════════════════════════════════════════════════════
END
═══════════════════════════════════════════════════════════════════════════

Reihenfolge wenn du kurz Zeit hast:
  1. Section 1 (Project Idea Definition)           2 min — biggest impact
  2. Section 6 (Endpoints)                         2 min — Zisis will scan this
  3. Section 7 (Technique #3)                      3 min — removes stale Claude
  4. Section 11 (Progress checkmarks)              5 min — visibly huge progress

Rest kann später. Gute Arbeit, Mikel.
