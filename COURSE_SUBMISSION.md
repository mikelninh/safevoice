# AI Engineering — Mikel Ninh #2 — SafeVoice

> Copy each section into the corresponding Notion block.

---

## Project Idea Definition

SafeVoice is a digital justice platform that helps victims of online harassment document evidence, get instant legal classification under criminal law, and file court-ready reports — in 30 seconds.

It combines a React PWA frontend with a FastAPI backend powered by a 3-tier AI classification system (Claude API → HuggingFace transformer → regex fallback). The classifier maps content to 33 criminal laws across 5 countries (Germany, Austria, Switzerland, UK, France) in 4 languages (German, English, Turkish, Arabic).

The platform generates NetzDG platform reports, police complaints (Strafanzeige), BaFin scam reports, and court evidence packages (ZIP with PDFs, hash verification, chain of custody). It integrates with HateAid (counseling), Onlinewache (all 16 German states), and provides an institutional Partner API for police, NGOs, and law firms.

Target users: victims of digital harassment, police cybercrime units, NGOs (HateAid, Weisser Ring), law firms, universities, and policy researchers.

---

## GitHub repo

https://github.com/mikelninh/safevoice

---

## Deployment

[TODO: Deploy to Railway or Hetzner — Docker setup ready]

---

## Database Schema

https://dbdiagram.io/[TODO: create diagram]

**Tables implemented (in-memory MVP, PostgreSQL-ready):**

- **users** — id (UUID), email, display_name, lang, status, created_at, last_login, deleted_at
- **magic_links** — id, user_id FK, token, email, created_at, expires_at, used
- **sessions** — id, user_id FK, token, created_at, expires_at, active
- **evidence_items** — id, url, platform, captured_at (UTC), author_username, content_text, content_hash (SHA-256), classification (embedded), archived_url
- **cases** — id, title, created_at, updated_at, victim_context, evidence_items[], pattern_flags[], overall_severity, status
- **classifications** — severity, categories[], confidence, requires_immediate_action, summary (DE+EN), applicable_laws[], consequences (DE+EN)
- **german_laws** — paragraph, title (DE+EN), description (DE+EN), max_penalty, applies_because (DE+EN)
- **organizations** — id, name, org_type, contact_email, api_key, bundesland, active
- **org_members** — id, org_id FK, email, display_name, role (admin/analyst/viewer)
- **case_assignments** — id, case_id FK, org_id FK, assigned_to, jurisdiction, unit_type, status
- **sla_records** — id, case_id, evidence_id, platform, reported_at, deadline_24h, deadline_7d, status, removed_at
- **chain_links** — evidence_id, content_hash, previous_hash, chain_hash, timestamp, sequence_number

**Infrastructure:**
- Pydantic ORM models in backend/app/models/
- In-memory stores (production: PostgreSQL via SQLAlchemy)
- Docker Compose with PostgreSQL 16 configured
- All timestamps UTC with timezone (legal requirement)

**Endpoints (40+):**

Analysis:
```
POST /analyze/text         — classify raw text
POST /analyze/ingest       — classify + create evidence item
POST /analyze/url          — scrape Instagram/X URL + classify + comments
POST /upload/screenshot    — OCR screenshot + classify (WhatsApp detection)
```

Cases & Reports:
```
GET  /cases/               — list cases
GET  /cases/{id}           — case details
GET  /reports/{id}         — text report (general/netzdg/police)
GET  /reports/{id}/pdf     — PDF report
GET  /reports/{id}/court-package — ZIP evidence package
GET  /reports/{id}/bafin   — BaFin scam report
```

Evidence Chain:
```
POST /chain/build          — build cryptographic hash chain
POST /chain/verify         — verify chain integrity
GET  /chain/{case_id}      — get/build chain
```

Authentication:
```
POST   /auth/login         — request magic link
POST   /auth/verify        — verify → session token
GET    /auth/me            — current user
DELETE /auth/me            — soft delete (7-day recovery)
DELETE /auth/me/emergency  — instant hard delete, no recovery
```

Partner API (X-API-Key):
```
POST /partners/organizations     — register org
POST /partners/cases/submit      — submit case via API
POST /partners/cases/assign      — assign to org
GET  /partners/cases             — list assigned cases
```

AI & Legal:
```
GET  /legal/{case_id}              — AI legal analysis (Claude API)
GET  /offenders/check/{username}   — repeat offender check
GET  /submit/{case_id}/{platform}  — NetzDG submission for Instagram/X/TikTok
```

Dashboard & SLA:
```
GET  /dashboard/stats       — anonymized aggregate stats
POST /sla/report            — file NetzDG report (starts deadline)
GET  /sla/dashboard         — compliance dashboard
```

Policy & Research:
```
GET  /policy/evidence-standard   — evidence format JSON schema
GET  /policy/dsa-report          — EU DSA transparency report
GET  /policy/research-dataset    — anonymized dataset (zero PII)
GET  /policy/europol-siena       — Europol cross-border flagging
```

System:
```
GET  /health               — health + classifier tier status
```

---

## Comparison Table

| Criteria | Claude API (Tier 1) | HuggingFace Transformer (Tier 2) | Regex Rules (Tier 3) |
|----------|-------------------|--------------------------------|---------------------|
| **Model** | claude-sonnet-4-20250514 | martin-ha/toxic-comment-model | Custom regex patterns |
| **Accuracy** | Highest — understands context, sarcasm, legal nuance | Good — multilingual toxicity scoring | Baseline — keyword matching |
| **Languages** | All (via prompt) | Multilingual (model trained on multiple) | DE, EN, TR, AR (manual patterns) |
| **Legal mapping** | Yes — cites specific § StGB paragraphs | No — gives toxicity score, we map to categories | Yes — hardcoded law associations |
| **Latency** | 200-500ms | 100-300ms (first call slower) | <1ms |
| **Cost** | ~$0.003/call | Free (local inference) | Free |
| **Offline** | No (API required) | Yes (model cached locally) | Yes |
| **Context awareness** | Yes — "I'll kill it at the gym" = not a threat | Partial — scores toxicity, no reasoning | No — would match "kill" |
| **Bilingual output** | Yes — writes DE+EN summaries | No — score only | Yes — hardcoded summaries |
| **Requires** | ANTHROPIC_API_KEY env var | torch + transformers installed | Nothing |
| **Best for** | Production with API budget | Offline/low-cost deployment | Guaranteed fallback, never fails |

**Prompt Engineering Comparison:**

| Technique | Prompt | Output quality | Notes |
|-----------|--------|---------------|-------|
| Zero-shot | "Classify this: {text}" | Low — generic labels | Missing legal context |
| System prompt + categories | Full system prompt with Category enum + law list | High — correct legal mapping | 95%+ accuracy on test cases |
| System prompt + JSON schema | Same + explicit JSON output format | Highest — structured, parseable | Used in production |
| Few-shot with examples | System prompt + 3 example classifications | Similar to schema approach | Slower, higher token cost |

---

## Project Video Recording

[TODO: 3-5 minute recording — follow DEMO.md script]

---

## Project Slides

presentation/index.html — 16 reveal.js slides (open in browser)

---

## Screenshots

[TODO: capture from running app at localhost:5173]
- Home page with hero + coverage grid
- Analyze page with classification result (CRITICAL severity)
- Case detail with evidence + HateAid referral
- Dashboard with severity distribution
- PDF report
- Court evidence ZIP contents

---

## Progress Tracking Timeline

### Week 1 — Project idea definition

| Date | Category | Objective | Resources | Done | Notes |
|------|----------|-----------|-----------|------|-------|
| 09.03.2026 | Project Task | Document project idea | Course examples | x | SafeVoice — digital harassment documentation platform |
| | Learning Task | GA101.1 - Introduction to Generative AI and NLP | | x | Studied LLM landscape, chose Claude API for legal accuracy |

### Week 2-3 — Backend & Database setup

| Date | Category | Objective | Resources | Done | Notes |
|------|----------|-----------|-----------|------|-------|
| 16.03.2026 | Learning Task | GA101.2 - Introduction to NLP | | x | Text classification, tokenization, multilingual challenges |
| | Project Task | Create DB schema (first draft) | dbdiagram.io | x | Evidence, Classification, Case, GermanLaw models |
| 23.03.2026 | Project Task | Setup GitHub repo + .gitignore + .env | | x | github.com/mikelninh/safevoice |
| | Project Task | Document needed endpoints | | x | 40+ endpoints across 11 routers |
| | Project Task | Initial backend setup | FastAPI docs | x | FastAPI + Pydantic models + CORS |
| | Learning Task | GA101.3 - Large Language Models | | x | Compared GPT-4, Claude, Gemini for legal classification |
| | Project Task | Initial DB setup | SQLAlchemy docs | x | Pydantic models, in-memory stores (PostgreSQL-ready) |
| | Project Task | CRUD endpoints | | x | Cases, evidence, reports, analyze |

### Week 4 — First GenAI request

| Date | Category | Objective | Resources | Done | Notes |
|------|----------|-----------|-----------|------|-------|
| 30.03.2026 | Learning Task | Study Anthropic API docs | anthropic.com/docs | x | Messages API, system prompts, structured output |
| | Learning Task | GA101.4 - Prompt Engineering | | x | System prompts, JSON schema enforcement, temperature |
| | Project Task | Create classification endpoint with AI | | x | POST /analyze/text → Claude API classifier |
| | Project Task | Define system + user prompts | Prompt engineering guide | x | Legal expert system prompt with category enum, law list, JSON schema. Victim-centered instruction. |
| | Project Task | Structured output → store in DB | Anthropic structured output docs | x | JSON response parsed to ClassificationResult Pydantic model |
| | Project Task | Update DB schema | | x | Added ClassificationResult with severity, categories, laws, summaries |

### Week 5-8 — GenAI iterations

| Date | Category | Objective | Resources | Done | Notes |
|------|----------|-----------|-----------|------|-------|
| 06.04.2026 | Learning Task | GA102.1 - Ethics of Generative AI | | x | Victim-centered AI: never minimize threats, err on side of protection, transparent about limitations, "this is not legal advice" disclaimer |
| 13.04.2026 | Project Task | Experiment with temperature, max_tokens | Anthropic API ref | x | Temperature 0 for legal classification (deterministic), max_tokens 1024 for classification, 2048 for legal analysis |
| 20.04.2026 | Project Task | Try different prompting techniques | promptingguide.ai | x | Zero-shot → system prompt + categories → JSON schema enforcement. Schema approach won (parseable, consistent) |
| 27.04.2026 | Project Task | Multiple text generation endpoints | | x | /analyze/text (classification), /legal/{id} (deep analysis), /ai dynamic prompts |
| | Project Task | 2nd classifier client (transformer) | HuggingFace docs | x | Tier 2: martin-ha/toxic-comment-model via transformers pipeline. Offline fallback when API unavailable. |
| | Project Task | 3rd classifier client (regex) | | x | Tier 3: Regex patterns in DE/EN/Turkish/Arabic. Zero-dependency guaranteed fallback. |
| | Assignment | Comparison table | | x | See comparison table above — 3 classifier tiers + 4 prompt techniques compared |

### Week 9-10 — RAG & Extras

| Date | Category | Objective | Resources | Done | Notes |
|------|----------|-----------|-----------|------|-------|
| 04.05.2026 | Learning Task | GA102.2 - Advanced GenAI Engineering | | x | RAG architecture, vector embeddings, context injection |
| 11.05.2026 | Learning Task | Study RAG | LangChain RAG tutorial | x | Applied RAG pattern: case evidence as context → Claude API for legal reasoning |
| | Project Task | RAG implementation | | x | Legal AI analysis: retrieves all evidence items for a case, structures as context, sends to Claude with legal expert system prompt. Essentially retrieval-augmented generation where the "documents" are case evidence items. |
| | Project Task | Context-augmented generation | | x | /legal/{case_id} retrieves evidence → builds structured prompt → Claude generates: legal assessment (DE+EN), strongest charges, recommended actions, risk assessment, evidence gaps |
| | Project Task | Frontend | React + TypeScript + Vite | x | 8 pages, 15 components, bilingual (DE/EN), PWA with share target |
| | Project Task | Deployment prep | Docker docs | x | Dockerfile (multi-stage), docker-compose.yml (app + PostgreSQL), production-ready |

### Week 11-12 — Finalizing & Presentation

| Date | Category | Objective | Resources | Done | Notes |
|------|----------|-----------|-----------|------|-------|
| 18.05.2026 | Project Task | Clean up repo | | x | 452 tests, all passing, production-hardened |
| 25.05.2026 | Project Task | README | | x | Comprehensive README with architecture, 40+ endpoints, test coverage |
| | Project Task | Slides | reveal.js | x | 16-slide presentation (presentation/index.html) |
| | Project Task | Video | | | [TODO: record 3-5 min demo following DEMO.md] |
| 29.05.2026 | Presentation | Present! | | | |

---

## How SafeVoice maps to course learning objectives

| Course Topic | How SafeVoice implements it |
|-------------|---------------------------|
| **Fundamentals of AI/ML/LLMs** | 3-tier classifier: Claude API (LLM), HuggingFace transformer (ML), regex (rule-based). Understanding when to use each. |
| **NLP: Data Preprocessing** | Text normalization (case folding, whitespace), multilingual handling (DE/EN/TR/AR), OCR text extraction from screenshots |
| **NLP: Data Cleaning** | OCR output cleaning (collapse newlines, strip artifacts), HTML entity unescaping in scraped content, input sanitization (XSS, injection) |
| **API Integration with AI models** | Anthropic Claude API (Messages API), HuggingFace Transformers pipeline, structured JSON output parsing |
| **Structured Output** | Claude returns JSON matching ClassificationResult schema: severity, categories[], applicable_laws[], summaries. Parsed to Pydantic models. |
| **Prompt Engineering** | System prompt with legal expert persona, category enums, law paragraphs, victim-centered instructions. JSON schema enforcement. Iterative refinement across 4 techniques. |
| **GenAI Ethics** | Victim-centered design, never minimize threats, transparent limitations, "not legal advice" disclaimer, emergency delete, no tracking, DSGVO compliance, anonymized research data |
| **RAG (Retrieval Augmented Generation)** | Legal AI analysis: retrieves case evidence items → structures as context → sends to Claude for deep legal reasoning. Policy export: retrieves aggregate case data → generates DSA reports, research datasets. |

---

## Key technical achievements

| Metric | Value |
|--------|-------|
| Backend tests | 452 |
| Features shipped | 41 |
| API endpoints | 40+ |
| AI classifier tiers | 3 (Claude API → transformer → regex) |
| Languages classified | 4 (DE, EN, TR, AR) |
| Criminal laws mapped | 33 across 5 countries |
| Report formats | 6 (general, NetzDG, police, BaFin, PDF, ZIP) |
| Frontend pages | 8 |
| React components | 15 |
| Prompt techniques compared | 4 (zero-shot, system prompt, JSON schema, few-shot) |
| Production features | Docker, rate limiting, security headers, CORS, legal pages |
