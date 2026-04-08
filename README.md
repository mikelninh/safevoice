# SafeVoice

**Document digital harassment. Classify under German law. Generate court-ready reports. In 30 seconds.**

Bilingual (DE/EN). Multilingual classifier (DE/EN/TR/AR). DSGVO-compliant. Free for victims.

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
3-tier classifier with automatic fallback:

| Tier | Engine | When |
|------|--------|------|
| 1 | OpenAI GPT-4o-mini | `OPENAI_API_KEY` set |
| 2 | HuggingFace transformer | torch installed |
| 3 | Regex patterns (DE/EN/TR/AR) | Always works, zero deps |

Detects 18 offense categories across 4 languages. Returns: severity, categories, applicable German laws, bilingual summary + recommended actions.

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

8 tables following the core flow: **user → case → evidence → classification → categories + laws**

```
users                     — who is documenting
cases                     — one incident (groups related evidence)
evidence_items            — one piece of content with SHA-256 hash chain
classifications           — AI output: severity, confidence, summary (DE+EN)
categories                — 15 offense types (harassment, Volksverhetzung, stalking, deepfakes...)
laws                      — 11 German law references (§130–§269 StGB, NetzDG)
classification_categories — many-to-many junction
classification_laws       — many-to-many junction
```

---

## API Endpoints (MVP)

```
GET  /health              — health check + active classifier tier

POST /analyze/text        — classify raw text
POST /analyze/ingest      — classify + save as evidence with hash
POST /analyze/url         — scrape Instagram/X URL + classify

GET  /cases/              — list cases
GET  /cases/{id}          — case detail with evidence + classifications

GET  /reports/{id}        — text report (general / netzdg / police)
GET  /reports/{id}/pdf    — downloadable PDF report
```

Full interactive docs: http://localhost:8000/docs

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
| AI Tier 1 | OpenAI GPT-4o-mini |
| AI Tier 2 | HuggingFace Transformers |
| AI Tier 3 | Regex patterns (DE/EN/TR/AR) |
| Evidence | SHA-256 hash chain + UTC timestamps |
| Reports | ReportLab (PDF) |
| Deploy | Docker + docker-compose |

---

## Project Structure

```
safevoice/
├── backend/app/
│   ├── main.py              — FastAPI app
│   ├── models/evidence.py   — Case, Evidence, Classification, Law
│   ├── services/
│   │   ├── classifier.py    — 3-tier classifier (OpenAI → transformer → regex)
│   │   ├── classifier_llm.py — Tier 1: OpenAI with prompt engineering
│   │   ├── scraper.py       — Instagram + X URL scraper
│   │   ├── evidence.py      — SHA-256 hashing + timestamps
│   │   └── pdf_generator.py — Court-ready PDF reports
│   └── routers/
│       ├── analyze.py       — /analyze/text, /ingest, /url
│       ├── cases.py         — /cases/
│       └── reports.py       — /reports/{id}, /pdf
├── frontend/src/
│   ├── pages/               — Home, Analyze, Cases, CaseDetail
│   ├── components/          — SeverityBadge, LawCard, SafeExit, etc.
│   └── i18n/                — DE/EN translations
├── .env                     — OPENAI_API_KEY (not committed)
└── Dockerfile               — Production deployment
```

---

## Legal Note

SafeVoice provides legal context as general information, not legal advice. For individual advice, contact [HateAid](https://hateaid.org) or a qualified attorney.
