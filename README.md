# SafeVoice

> **🧪 Status: Closed Beta · NGO-Partner-Pilot · April 2026**
> Funktionsfähig und im Test mit ersten NGO-Partnern. **Noch kein Produktivbetrieb** —
> Datenschutzerklärung & Impressum sind Vorab-Versionen, nicht anwaltlich geprüft. Wir
> suchen Trägerschaft (z. B. HateAid) bevor SafeVoice für Massenanwendung empfohlen
> werden kann. Feedback und Pull Requests sehr willkommen.

**Document digital harassment. Classify under German law. Generate court-ready reports. In 30 seconds.**

Bilingual UI (DE/EN). Classifier runs in German and English on OpenAI `gpt-4o-mini` with Pydantic Structured Outputs. DSGVO-by-design. Free for victims. Turkish and Arabic coverage on the roadmap.

---

## The Problem

Every 3 minutes, someone in Germany is harassed online. 90% goes unreported because:
- Victims don't know which laws apply
- Evidence disappears (posts get deleted)
- Reporting is complex and takes hours

## The Solution

Paste text, a URL, or upload a screenshot → AI classifies it under German criminal law → evidence is preserved with SHA-256 hash chain → court-ready PDF report generated.

```
PASTE → CLASSIFY → PRESERVE → REPORT
 10s       3s      instant    1 click
```

---

## Quick Start

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

- Frontend: http://localhost:5173
- API docs: http://localhost:8000/docs

### Enable AI classifier
Add your OpenAI key to `.env`:
```
OPENAI_API_KEY=sk-your-key
```
Without it, the regex classifier (Tier 3) is used automatically.

---

## How It Works

### 1. Victim pastes content
Three ways to get content in:
- **Paste the comment text** — copy a harassing comment directly from Instagram/WhatsApp/X, paste into SafeVoice (best for comments)
- **Paste a post link** — SafeVoice fetches the post caption automatically (works for Instagram posts, reels, X tweets)
- **Upload a screenshot** — OCR extracts the text from WhatsApp/DM screenshots

### 2. AI classifies it
Single-tier LLM classifier — OpenAI `gpt-4o-mini` with **Pydantic Structured
Outputs** via `client.chat.completions.parse()`. Detects **15 offense
categories** and returns: severity, confidence, applicable German paragraphs,
bilingual summary (DE + EN), and recommended actions.

**Prompt strategy: few-shot with victim_context handling.** The system
prompt contains four worked examples (including a false-positive idiom
*"Das bringt mich um"* and an obfuscation case *"Stirbt endlich, du H\*re"*),
plus explicit rules for how `victim_context` — if provided — should change
the classification (e.g. *"Ex-Partner → § 238 StGB (Stalking)"* instead of
just § 241 StGB). This is the same content documented in the Comparison
Table.

Schema enforcement is server-side. Categories and laws are exhaustive Python
enums, so the model cannot invent a category or a paragraph. If the model
refuses on safety grounds or a response fails schema validation, the API
returns a clean `503` — no silent fallback.

Earlier versions had a 3-tier fallback (LLM → transformer → regex). We
removed it because (a) the LLM is dramatically more accurate on real
evidence, (b) the regex tier produced too many false positives to send to
police, and (c) running a transformer added 1.5 GB of dependencies for
marginal gain. A regex-only fallback for organisations that cannot send data
to OpenAI remains on the roadmap.

### 3. Evidence is preserved
- SHA-256 content hash for integrity
- Cryptographic hash chain linking evidence items
- UTC timestamp with timezone (legal requirement)
- archive.org backup

### 4. Reports are generated
- **NetzDG report** — for platform (Instagram must respond in 24h/7d)
- **Strafanzeige** — police complaint template
- **PDF export** — court-ready A4 document

---

## Database Schema

10 tables. Core flow: **user → case → evidence → classification → categories + laws.**
Auth state (`magic_link_tokens`, `session_tokens`) persisted so Railway cold-starts don't log users out.

```
users                     — who is documenting (email + status + last_login)
magic_link_tokens         — single-use login tokens · 15 min TTL · DB-backed
session_tokens            — long-lived session tokens · 30 day TTL · DB-backed
cases                     — one incident (groups related evidence)
evidence_items            — one piece of content with SHA-256 hash chain
classifications           — AI output: severity, confidence, summary (DE+EN)
categories                — 15 offense types (harassment, Volksverhetzung, stalking, deepfakes...)
laws                      — 11 German law references (§130–§269 StGB, NetzDG)
classification_categories — many-to-many junction
classification_laws       — many-to-many junction
```

---

## API Endpoints

The core trio — **auth**, **cases**, **analyze** — is what the tutor
action items map to. A dozen more routers cover reports, the Partner API, policy
exports, the hash chain, and dashboards.

```
# Auth  (backend/app/routers/auth.py)
POST   /auth/login              — request magic link
POST   /auth/verify             — exchange token for session
GET    /auth/me                 — read user
PUT    /auth/me                 — update user
POST   /auth/logout             — end session
DELETE /auth/me                 — soft delete (GDPR Art. 17)
DELETE /auth/me/emergency       — hard delete (purges cases + evidence)
GET    /auth/me/export          — Art. 20 data export (JSON)

# Cases  (backend/app/routers/cases.py)
GET    /cases/                  — list
GET    /cases/{id}              — detail + evidence + classifications
POST   /cases/                  — explicit create (rare — usually implicit)
PUT    /cases/{id}              — update
DELETE /cases/{id}              — delete (cascade)
POST   /cases/{id}/evidence     — attach evidence to existing case

# Analyze  (backend/app/routers/analyze.py)
POST   /analyze/text            — classify a string (no DB write)
POST   /analyze/ingest          — evidence + classify + case in one tx
POST   /analyze/url             — scrape URL → classify
POST   /analyze/case            — case-level RAG analysis across N evidence

# Reports  (backend/app/routers/reports.py)
GET    /reports/{id}            — text report
GET    /reports/{id}/pdf        — PDF
GET    /reports/{id}/bafin      — BaFin scam report
GET    /reports/{id}/court-package  — ZIP bundle
POST   /reports/{id}/eml        — RFC 5322 email export

# Partner API  (backend/app/routers/partners.py)
POST   /partners/organizations  — onboard NGO / law firm
POST   /partners/cases/submit   — institutional case submission
…                               — 9 endpoints total

# Hash chain  (backend/app/routers/chain.py)
POST   /chain/build             — build tamper-proof hash chain for a case
POST   /chain/verify            — verify the chain
GET    /chain/{case_id}         — read the chain

# Health
GET    /health                  — liveness check
```

Full interactive OpenAPI docs: http://localhost:8000/docs

---

## German Laws Covered

| Paragraph | Offense | Max Penalty |
|-----------|---------|-------------|
| § 130 StGB | Volksverhetzung (Incitement to hatred) | 5 years |
| § 185 StGB | Beleidigung (Insult) | 1 year |
| § 186 StGB | Üble Nachrede (Defamation) | 1 year |
| § 187 StGB | Verleumdung (Slander) | 5 years |
| § 201a StGB | Intimate image violation / Deepfakes | 2 years |
| § 238 StGB | Nachstellung (Stalking) | 3-5 years |
| § 241 StGB | Bedrohung (Threat) | 2 years |
| § 126a StGB | Strafbare Bedrohung (Criminal threat) | 3 years |
| § 263 StGB | Betrug (Fraud) | 5 years |
| § 263a StGB | Computerbetrug (Computer fraud) | 5 years |
| § 269 StGB | Fälschung beweiserheblicher Daten | 5 years |
| NetzDG § 3 | Platform removal obligation | €50M fine |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS |
| Backend | Python 3.13 + FastAPI |
| Database | SQLAlchemy (SQLite dev / PostgreSQL prod) |
| AI Classifier | OpenAI GPT-4o-mini (structured outputs) |
| Evidence | SHA-256 hash chain + UTC timestamps |
| Reports | ReportLab (PDF) + Python `email` (RFC 5322 .eml export) |
| Auth | Magic-link (passwordless) |
| Deploy | Docker · Railway (Postgres + FastAPI) |

---

## Project Structure

```
safevoice/
├── backend/app/
│   ├── main.py                   — FastAPI app
│   ├── database.py               — SQLAlchemy models + seed data
│   ├── models/                   — Pydantic domain objects (Case, Evidence, …)
│   ├── services/
│   │   ├── classifier.py         — orchestrator (single-tier LLM)
│   │   ├── classifier_llm_v2.py  — OpenAI gpt-4o-mini + Pydantic .parse()
│   │   ├── legal_ai.py           — case-level RAG: retrieve → augment → generate
│   │   ├── scraper.py            — Instagram + X URL scraper
│   │   ├── evidence.py           — SHA-256 hashing + hash chain
│   │   └── pdf_generator.py      — court-ready PDF reports
│   └── routers/                  — FastAPI routes (auth, cases, analyze, reports, …)
├── frontend/src/
│   ├── pages/                    — Home, Analyze, Cases, CaseDetail
│   ├── components/               — SeverityBadge, LawCard, SafeExit, …
│   └── i18n/                     — DE/EN translations
├── schema.dbml                   — DB schema for dbdiagram.io
├── .env                          — OPENAI_API_KEY (not committed)
└── Dockerfile                    — production deployment
```

---

## Legal Note

SafeVoice provides legal context as general information, not legal advice. For individual advice, contact [HateAid](https://hateaid.org) or a qualified attorney.

## Ökosystem — Digitale Demokratie

Dieses Projekt ist Teil eines Open-Source-Ökosystems für digitale Demokratie:

| Projekt | Frage | Link |
|---------|-------|------|
| **FairEint** | Was sollte Deutschland anders machen? | [GitHub](https://github.com/mikelninh/faireint) · [Live](https://mikelninh.github.io/faireint/) |
| **GitLaw** | Was steht im Gesetz? | [GitHub](https://github.com/mikelninh/gitlaw) · [Live](https://mikelninh.github.io/gitlaw/) |
| **Public Money Mirror** | Wohin fließt das Steuergeld? | [GitHub](https://github.com/mikelninh/Public-Money-Mirror) |
| **SafeVoice** | Wer wird online angegriffen? | [GitHub](https://github.com/mikelninh/safevoice) |

Alle Projekte: [github.com/mikelninh](https://github.com/mikelninh) · Unterstützen: [Ko-fi](https://ko-fi.com/mikel777) · [GitHub Sponsors](https://github.com/sponsors/mikelninh)

