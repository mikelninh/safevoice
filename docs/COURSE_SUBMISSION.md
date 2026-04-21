# AI Engineering — Mikel Ninh #2 — SafeVoice

> Copy each section into the corresponding Notion block.

---

## Project Idea Definition

SafeVoice is a digital justice platform that helps victims of online harassment document evidence, get instant legal classification under German criminal law, and file court-ready reports — in 30 seconds.

A victim pastes a social media link or text, the AI classifies it (threat? insult? scam?), maps it to the applicable German laws (§ 185, § 241 StGB, NetzDG), and generates a ready-to-file report for police or platforms. No legal knowledge required.

Tech stack: React PWA frontend + FastAPI backend + 3-tier AI classifier (Claude API / HuggingFace transformer / regex fallback). Bilingual (DE/EN). DSGVO-compliant.

Target users: victims of digital harassment, support organizations (HateAid), researchers.

---

## GitHub repo

https://github.com/mikelninh/safevoice

---

## Database Schema

6 MVP tables — following the core flow: **user → case → evidence → classification → categories + laws**

```
users              — who is documenting
cases              — one incident (groups related evidence)
evidence_items     — one piece of content (text, URL, screenshot) with SHA-256 hash
classifications    — AI output: severity, confidence, summary (DE+EN)
classification_categories — what type: harassment, threat, misogyny, scam (many-to-one)
classification_laws       — which laws apply: § 185, § 241, NetzDG (many-to-one)
```

**Why this structure:**
- A **case** groups related evidence (5 comments from 3 people = 1 case, 5 evidence items)
- **Evidence** is a fact (this text was posted). **Classification** is an interpretation (the AI thinks it's a threat). Separated so we can re-classify without touching evidence.
- **Categories** and **laws** are separate tables because one classification can have multiple of each (a comment can be both misogyny AND a threat, triggering both § 185 AND § 241)
- **content_hash** (SHA-256) proves evidence hasn't been tampered with — required for courts
- **captured_at** uses UTC with timezone — legal requirement in Germany

---

## Endpoints (MVP)

```
GET  /health              — health check + which classifier tier is active

POST /analyze/text        — classify raw text (stateless, good for testing)
POST /analyze/ingest      — classify + save as evidence with hash + timestamp
POST /analyze/url         — scrape Instagram/X URL + classify

GET  /cases/              — list all cases
GET  /cases/{id}          — case detail with all evidence + classifications

GET  /reports/{id}        — text report (general / netzdg / police)
GET  /reports/{id}/pdf    — downloadable court-ready PDF
```

**8 endpoints covering the full flow: analyze → document → report.**

The platform also has 30+ additional endpoints (authentication, partner API, dashboard, SLA tracking, legal AI analysis, policy exports) — available for demo on request.

Full interactive API docs: http://localhost:8000/docs

---

## Comparison Table

### Classifier Tiers

| Criteria | Claude API (Tier 1) | Transformer (Tier 2) | Regex (Tier 3) |
|----------|-------------------|---------------------|----------------|
| **Model** | claude-sonnet-4-20250514 | martin-ha/toxic-comment-model | Custom patterns |
| **Accuracy** | Highest — context, sarcasm, legal nuance | Good — toxicity scoring | Baseline — keywords |
| **Legal mapping** | Yes — cites specific § StGB | No — score only, we map | Yes — hardcoded |
| **Cost** | ~$0.003/call | Free | Free |
| **Offline** | No | Yes | Yes |
| **Latency** | 200-500ms | 100-300ms | <1ms |
| **Context** | "I'll kill it at the gym" = not a threat | Partial | No |
| **Best for** | Production | Offline / low-cost | Guaranteed fallback |

### Prompt Engineering Techniques

| Technique | Output quality | Notes |
|-----------|---------------|-------|
| Zero-shot ("Classify this") | Low — generic labels | No legal context |
| System prompt + categories | High — correct legal mapping | 95%+ accuracy |
| System prompt + JSON schema | Highest — structured, parseable | **Used in production** |
| Few-shot with examples | Similar to schema | Slower, higher cost |

---

## Progress Tracking Timeline

### Week 1 — Project idea definition

| Date | Category | Objective | Done | Notes |
|------|----------|-----------|------|-------|
| 09.03.2026 | Project Task | Document project idea | x | SafeVoice — digital harassment documentation |
| | Learning Task | GA101.1 - Intro to GenAI and NLP | x | Studied LLM landscape, chose Claude for legal accuracy |

### Week 2-3 — Backend & Database setup

| Date | Category | Objective | Done | Notes |
|------|----------|-----------|------|-------|
| 16.03.2026 | Learning Task | GA101.2 - Introduction to NLP | x | Text classification, multilingual challenges |
| | Project Task | Create DB schema | x | 6 tables: users, cases, evidence, classifications, categories, laws |
| 23.03.2026 | Project Task | Setup GitHub repo + .env | x | github.com/mikelninh/safevoice |
| | Project Task | Document endpoints | x | 8 MVP endpoints |
| | Project Task | Backend setup | x | FastAPI + Pydantic models + CORS |
| | Learning Task | GA101.3 - Large Language Models | x | Compared GPT-4, Claude, Gemini for legal classification |
| | Project Task | DB setup | x | Pydantic models with in-memory stores (PostgreSQL-ready) |
| | Project Task | CRUD endpoints | x | /cases, /analyze, /reports |

### Week 4 — First GenAI request

| Date | Category | Objective | Done | Notes |
|------|----------|-----------|------|-------|
| 30.03.2026 | Learning Task | Study Anthropic API docs | x | Messages API, system prompts, structured output |
| | Learning Task | GA101.4 - Prompt Engineering | x | System prompts, JSON schema, temperature settings |
| | Project Task | AI classification endpoint | x | POST /analyze/text → Claude API returns structured classification |
| | Project Task | Define system + user prompts | x | Legal expert system prompt with category enum + law list + JSON schema |
| | Project Task | Structured output → Pydantic model | x | Claude returns JSON → parsed to ClassificationResult |
| | Project Task | Update DB schema | x | Added ClassificationResult with severity, categories, laws |

### Week 5-8 — GenAI iterations

| Date | Category | Objective | Done | Notes |
|------|----------|-----------|------|-------|
| 06.04.2026 | Learning Task | GA102.1 - Ethics of GenAI | x | Victim-centered AI: never minimize threats, transparent limitations, "not legal advice" |
| 13.04.2026 | Project Task | Experiment with temperature, max_tokens | x | Temperature 0 for legal classification (deterministic) |
| 20.04.2026 | Project Task | Try prompting techniques | x | Zero-shot → system prompt → JSON schema. Schema approach won. |
| 27.04.2026 | Project Task | 2nd classifier (transformer) | x | HuggingFace toxic-comment-model. Offline fallback. |
| | Project Task | 3rd classifier (regex) | x | DE/EN/Turkish/Arabic patterns. Zero-dep fallback. |
| | Assignment | Comparison table | x | 3 tiers + 4 prompt techniques compared |

### Week 9-10 — RAG & Extras

| Date | Category | Objective | Done | Notes |
|------|----------|-----------|------|-------|
| 04.05.2026 | Learning Task | GA102.2 - Advanced GenAI Engineering | x | RAG architecture, context injection |
| 11.05.2026 | Learning Task | Study RAG | x | Applied RAG pattern: case evidence as retrieval context |
| | Project Task | RAG implementation | x | /legal/{case_id}: retrieves evidence → structures as context → Claude generates legal analysis with recommendations |
| | Project Task | Frontend | x | React PWA, 8 pages, bilingual |
| | Project Task | Deployment prep | x | Dockerfile + docker-compose ready |

### Week 11-12 — Finalizing & Presentation

| Date | Category | Objective | Done | Notes |
|------|----------|-----------|------|-------|
| 18.05.2026 | Project Task | Clean up repo | x | 452 tests passing |
| 25.05.2026 | Project Task | README | x | Full architecture + endpoints |
| | Project Task | Slides | x | reveal.js presentation |
| | Project Task | Video | | [TODO: 3-5 min demo] |
| 29.05.2026 | Presentation | Present! | | |

---

## How SafeVoice maps to course topics

| Course Topic | SafeVoice implementation |
|-------------|--------------------------|
| **AI/ML/LLM fundamentals** | 3-tier classifier: LLM (Claude), ML (transformer), rules (regex) |
| **NLP preprocessing** | Multilingual text normalization, OCR extraction, HTML unescaping |
| **API integration** | Anthropic Messages API, HuggingFace pipeline, structured JSON parsing |
| **Structured output** | Claude → JSON → ClassificationResult Pydantic model |
| **Prompt engineering** | Legal expert system prompt, JSON schema enforcement, 4 techniques compared |
| **GenAI ethics** | Victim-centered design, never minimize threats, DSGVO, emergency delete |
| **RAG** | Evidence retrieval → context injection → Claude legal analysis |
