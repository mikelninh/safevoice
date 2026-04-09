# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is SafeVoice

SafeVoice is a bilingual (DE/EN) web app that helps victims document digital harassment, classify it under German criminal law, and generate court-ready reports. Flow: paste text / URL / screenshot → AI classifies → evidence preserved with SHA-256 hash → PDF report generated.

## Commands

### Backend
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload          # dev server on :8000
pytest tests/                           # all tests
pytest tests/test_classifier.py         # single test file
pytest tests/test_classifier.py -k "test_name"  # single test
```

### Frontend
```bash
cd frontend
npm install
npm run dev       # dev server on :5173
npm run build     # production build (tsc + vite)
```

### Docker (full stack with Postgres)
```bash
docker-compose up --build    # app on :8000, Postgres on :5432
```

## Architecture

**Backend** — Python/FastAPI (`backend/app/`), no database yet (in-memory models via Pydantic). The FastAPI app is at `app.main:app`.

**3-tier classifier** (`services/classifier.py`): OpenAI GPT-4o-mini → HuggingFace transformer → regex fallback. Each tier returns `ClassificationResult` or `None` to trigger the next tier. The regex tier (`classify_regex`) is always available with zero external deps. Tier availability is checked via `is_available()` in each module.

**Core models** are all in `models/evidence.py`: `Severity`, `Category`, `GermanLaw`, `ClassificationResult`, `EvidenceItem`, `PatternFlag`, `Case`. These are Pydantic models (no ORM yet).

**Routers** — each router maps to an API domain:
- `analyze.py` — `/analyze/text`, `/analyze/ingest`, `/analyze/url`, `/analyze/case`
- `cases.py` — `/cases/` CRUD
- `reports.py` — `/reports/{id}` text and PDF generation
- Other routers: `chain`, `upload`, `sla`, `partners`, `dashboard`, `auth`, `legal`, `policy`

**Frontend** — React 18 + TypeScript + Vite + Tailwind CSS. Single-page app with react-router-dom. Language state (`de`/`en`) is passed as prop; translations in `src/i18n/index.ts`.

**Key frontend pages**: `Home`, `Analyze` (main input flow), `Cases`, `CaseDetail`, `Dashboard`, `Login`, plus legal pages (`Impressum`, `Datenschutz`) required in Germany.

## Environment

- `OPENAI_API_KEY` — enables Tier 1 LLM classifier. Without it, regex fallback is used.
- `CORS_ORIGINS` — comma-separated allowed origins (defaults to localhost:5173,8000)
- `RATE_LIMIT_RPM` — requests per minute (default 120, disabled when `TESTING` env var set)
- `TESTING` — set to any value to disable rate limiting in tests

## Schema

Database schema is in `schema.dbml` (paste into dbdiagram.io to visualize). 8 tables: `users`, `cases`, `evidence_items`, `classifications`, `categories`, `laws`, plus junction tables `classification_categories` and `classification_laws`. No ORM or migrations exist yet — the app uses in-memory Pydantic models.

## Multilingual

Content classification supports German, English, Turkish, and Arabic regex patterns. UI is bilingual DE/EN. All classification results produce both `summary` + `summary_de` and `potential_consequences` + `potential_consequences_de`.

## German Law Context

The app maps content to specific StGB paragraphs (§185 Insult, §186 Defamation, §241 Threat, §126a Criminal threat, §263/263a Fraud, §269 Data falsification) and NetzDG §3. Law reference data is in `data/mock_data.py`. Multi-jurisdiction law data (Austria, Switzerland, UK, France) is in `data/laws_*.py`.
