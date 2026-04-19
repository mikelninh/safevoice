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

**Backend** — Python/FastAPI (`backend/app/`) with a real SQLAlchemy database (SQLite for dev at `safevoice.db`, Postgres-ready for production). Alembic migrations live in `alembic/versions/`. The FastAPI app is at `app.main:app`; categories + German laws are auto-seeded on startup.

**Single-tier classifier** (`services/classifier.py`): OpenAI GPT-4o-mini via `classifier_llm_v2.py` with Pydantic-v2 structured outputs. If the LLM is unavailable (no key, API down), `classify()` raises `ClassifierUnavailableError` and the API returns **503** — **by design**. A previous 3-tier fallback (transformer + regex) was removed on 13 April 2026 because a weak fallback classification gave victims false confidence in a legal outcome. The `classifier_regex.py` and `classifier_transformer.py` modules remain only for backwards-compat imports in tests.

**Core models** live in two places:
- `app/database.py` — SQLAlchemy ORM tables backing all persistence (`User`, `Case`, `EvidenceItem`, `Classification`, `Category`, `Law`, `Org`, `OrgMember` + junction tables).
- `app/models/*.py` — Pydantic models for API contracts and LLM output parsing (`evidence.py`, `user.py`, `partner.py`, `sla.py`). Do not confuse `partner.Organization` (Pydantic) with `database.Org` (ORM) — the first is an API shape, the second is what gets persisted.

**Multi-tenancy** — `orgs` and `org_members` tables (added 12 April 2026) let NGO partners run their own intake flows. See `services/org_service.py` and `routers/orgs.py`.

**Routers** — each router maps to an API domain:
- `analyze.py` — `/analyze/text`, `/analyze/ingest`, `/analyze/url`, `/analyze/case`
- `cases.py` — `/cases/` CRUD
- `reports.py` — `/reports/{id}` text and PDF generation
- Other routers: `chain`, `upload`, `sla`, `partners`, `dashboard`, `auth`, `legal`, `policy`

**Frontend** — React 18 + TypeScript + Vite + Tailwind CSS. Single-page app with react-router-dom. Language state (`de`/`en`) is passed as prop; translations in `src/i18n/index.ts`.

**Key frontend pages**: `Home`, `Analyze` (main input flow), `Cases`, `CaseDetail`, `Dashboard`, `Login`, plus legal pages (`Impressum`, `Datenschutz`) required in Germany.

## Environment

- `OPENAI_API_KEY` — **required** for classification. Without it, `/analyze/*` endpoints return 503 (by design — see classifier rationale above).
- `DATABASE_URL` — SQLAlchemy URL. Dev defaults to `sqlite:///./safevoice.db`. Production uses Postgres.
- `CORS_ORIGINS` — comma-separated allowed origins (defaults to `localhost:5173,localhost:8000`).
- `RATE_LIMIT_RPM` — requests per minute (default 120, disabled when `TESTING` env var is set).
- `TESTING` — set to any value to disable rate limiting in tests.
- `VITE_OPERATOR_NAME`, `VITE_OPERATOR_EMAIL`, `VITE_OPERATOR_ADDRESS`, `VITE_OPERATOR_CITY` — required on the **frontend** build to populate Impressum (§5 TMG). See `DEPLOY.md`.

## Schema

Database schema lives both in `schema.dbml` (paste into dbdiagram.io to visualize) and as real SQLAlchemy models in `models/db.py`. Tables: `users`, `cases`, `evidence_items`, `classifications`, `categories`, `laws` + junction tables `classification_categories`, `classification_laws` + multi-tenancy tables `orgs`, `org_members`. Alembic migration history lives in `alembic/versions/` — apply with `alembic upgrade head` (the Docker entrypoint runs this automatically).

## Multilingual

Content classification supports German, English, Turkish, and Arabic regex patterns. UI is bilingual DE/EN. All classification results produce both `summary` + `summary_de` and `potential_consequences` + `potential_consequences_de`.

## German Law Context

The app maps content to specific StGB paragraphs (§185 Insult, §186 Defamation, §241 Threat, §126a Criminal threat, §263/263a Fraud, §269 Data falsification) and NetzDG §3. Law reference data is in `data/mock_data.py`. Multi-jurisdiction law data (Austria, Switzerland, UK, France) is in `data/laws_*.py`.
