# SafeVoice

**Live:** [safevoice-vert.vercel.app](https://safevoice-vert.vercel.app)

> **🧪 Status: Closed Beta · NGO-Partner-Pilot · Mai 2026**
> Live deployt, anonym im Browser nutzbar, im Test mit Tutor + Team und ersten NGO-Partnern.
> Klassifikator gegen **35 reale Test-Cases** validiert. **12 deutsche Paragraphen** (11 StGB + NetzDG) durch das Schema garantiert.
> **Noch kein Produktivbetrieb für Massenanwendung** — Datenschutzerklärung & Impressum
> sind Vorab-Versionen, nicht anwaltlich geprüft. Postanschrift gemäß § 5 TMG wird
> vor Live-Gang ergänzt. Wir suchen Trägerschaft (z. B. HateAid).
> Feedback und Pull Requests sehr willkommen.

**Document digital harassment. Classify under German law. Generate court-ready Strafanzeige in 30 seconds.**

---

## Agents (Mai 2026)

SafeVoice ships an autonomous **Court-Prep Agent** as of May 2026. It is the first of [8 agents](docs/AGENT_MASTERPLAN.md) planned across the SafeVoice / GitLaw / PMM ecosystem and runs on a native agent-loop (no LangChain — see [AGENT_MASTERPLAN.md](docs/AGENT_MASTERPLAN.md#decision-native-kein-langchain) for the reasoning).

| | |
|---|---|
| **Court-Prep Agent** | `POST /agent/court-prep/{case_id}` — produces Strafanzeige PDF + NetzDG `.eml` per platform + Staatsanwaltschaft routing + § 77 StGB Strafantrags-Frist-Check + auto re-archived evidence URLs + § 200a StPO Anonymisierungs-Antrag when needed. 8 tools, ~30 seconds, replaces ~3 hours of manual work. |
| **Agent runtime** | `backend/app/services/agent_loop.py` · `court_prep_agent.py` · `court_prep_tools.py` |
| **Safety guards (built in from day 1)** | `max_iterations=10` · `max_cost_usd=0.50` · idempotency key `(run_id, tool, sha256(input))` · tool-call audit table (`agent_runs` + `tool_calls`) · human-in-loop checkpoint before every external send |
| **Eval set** | `evals/agent_court_prep.json` — runs on every prompt change |
| **Cross-project plan** | [`docs/AGENT_MASTERPLAN.md`](docs/AGENT_MASTERPLAN.md) — 8 agents across SafeVoice, GitLaw Citizen, GitLaw Pro, PMM. #1 in production, #2-3 next. |

The same `agent_loop` contract is being ported to TypeScript for the GitLaw repo so both projects share one Agent-Runtime pattern.

---

Anonymous-first (no account needed). UI in **DE + EN**; the OpenAI `gpt-4o-mini` classifier handles Turkish and Arabic input text out of the box — UI translations for TR/AR are on the roadmap. DSGVO-by-design: no personal data leaves your browser unless you explicitly submit it.

---

## The Problem

Every 3 minutes someone in Germany is harassed online. 90% goes unreported because:
- Victims don't know which laws apply
- Evidence disappears (posts get deleted)
- Filing a Strafanzeige takes hours of paperwork

## The Solution

```
PASTE → CLASSIFY → DOCUMENT → STRAFANZEIGE
 10s       3s       instant     1 click
```

Paste a hateful message, link, or screenshot → AI classifies it under German criminal law → evidence is preserved with SHA-256 hash chain → court-ready PDF Strafanzeige with executive summary, evidence exhibits, and AI legal assessment ready for the police.

---

## How It Works

### 1. Get content in (3 paths)
- **Paste text** — copy a hateful comment from anywhere, paste it. Most common path.
- **Paste a URL** — public news/blog URLs work directly. Instagram/X/TikTok/Facebook block server-side scraping by design — for those, screenshot is the reliable path and is also DSGVO-cleaner since SafeVoice never touches the platform.
- **Upload a screenshot** — OCR is Vision-only via **OpenAI Vision (gpt-4o-mini)**. One codepath in dev and prod, no system-package dependency. Vision returns structured JSON: extracted text + sender_handle + platform_hint, so the @username and platform auto-fill from the screenshot.

### 2. AI classifies it
Single-tier LLM classifier — OpenAI `gpt-4o-mini` with Pydantic Structured Outputs. Detects **16 offense categories** including death_threat, volksverhetzung, doxxing, intimate_images, sexual_harassment, stalking. Returns severity, applicable German paragraphs, bilingual summary (DE + EN), and a `requires_immediate_action` flag.

Schema enforcement is server-side. Categories and laws are exhaustive Python enums, so the model cannot invent a category or a paragraph. If the model refuses on safety grounds or the response fails schema validation, the API returns a clean `503` — **no silent fallback by design**, because a weak classification (e.g. regex misreading a death threat) would be worse than no classification.

Few-shot prompt strategy with explicit doxxing example, idiom false-positive (*"Das bringt mich um"* → low) and obfuscation case (*"Stirbt endlich, du H\*re"* → critical).

Every `/analyze/*` response carries an `LLMMetadata` block — model, prompt/completion/total tokens, estimated USD cost, request_id, and the prompt version that produced it. Same telemetry is persisted to an `llm_usage` audit table per request via a central `llm_gateway` module, so per-user / per-feature cost dashboards read from one source of truth. Prompt revisions are versioned (`PROMPT_VERSION = "v2"`) and stored on every classification row, so historical classifications stay attributable when the prompt changes.

### 3. Case-level legal AI (second layer)
Once a case has multiple pieces of evidence, a second AI pass produces a **Juristische Gesamteinschätzung**: free-text assessment, escalation risk + reason, strongest charges with strength scores (`strong` / `medium` / `weak`), and prioritised next steps with deadlines. Auto-refreshes when evidence or victim_context changes. Embedded in the Strafanzeige PDF so the police get one document.

### 4. Evidence is preserved
- SHA-256 content hash (sha256:…) per evidence
- UTC timestamp with timezone
- archive.org backup link when scraping
- **Browser-side hash verifier** — anyone (police, court, lawyer) can paste the original text into SafeVoice and confirm it produces the same hash. Web Crypto API, no network.

### 5. Strafanzeige PDF (the deliverable for police)
A4, court-ready, ~8 KB:
- **Executive summary card** at the top — complainant, severity badge, case-id, incident counts (with critical count highlighted), statutes — readable in 3 seconds
- **Förmliche Strafanzeige body** with the victim's personal data substituted in (no [PLACEHOLDER] markers if a name is provided)
- **Beweismittel as numbered exhibits** — each with severity-colored dot, italic quote with thin left rule, classification line, statutes, mono SHA-256 footer
- **KI-gestützte Bewertung** as the last section — typographically distinct (tracked-out caps label + italic disclaimer) so police instantly see this is the AI's voice, not the victim's
- Page footer with case-id and page numbers, 30 mm left margin for 2-hole punching
- Tiny `✂` fold mark for envelope folding

Plus alternate templates: NetzDG-Meldung (24 h / 7 d platform deadline), allgemeiner Bericht.

### 6. Submit (Onlinewache or email)
3-step Onlinewache flow built into the case page: select Bundesland → copy the prepared text → open the form and paste. Or download the `.eml` for Apple Mail / Outlook / Thunderbird with attachments pre-attached. PLZ-driven recipient pre-selection.

---

## Quick Start (local dev)

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload          # :8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev                             # :5173
```

- Frontend: http://localhost:5173
- API docs: http://localhost:8000/docs

### Required env
```
OPENAI_API_KEY=sk-…   # required — without it /analyze returns 503
DATABASE_URL=…        # optional, defaults to sqlite:///./safevoice.db
```

---

## Production deployment

**Single platform: Vercel** (Frankfurt, Fluid Compute).

| Layer | Where |
|-------|-------|
| Frontend (Vite SPA) | Vercel static |
| Backend (FastAPI) | Vercel Python Function via `api/proxy.py` |
| Database | Neon Postgres (Vercel Marketplace integration) |
| OCR | OpenAI Vision (`gpt-4o-mini`) — single codepath |
| Classifier + Legal AI | OpenAI `gpt-4o-mini` |

`vercel.json` rewrites `/api/(.*)` → `/api/proxy?_p=$1`; the ASGI shim in `api/proxy.py` re-applies the original path before delegating to the FastAPI app whose routers are mounted at both `/` and `/api/`.

Env vars on Vercel: `OPENAI_API_KEY`, `DATABASE_URL` (auto via Neon), `CORS_ORIGINS`, `VITE_OPERATOR_NAME`, `VITE_OPERATOR_EMAIL`, `VITE_OPERATOR_CITY` (Impressum, § 5 TMG).

---

## API Endpoints

```
# Analyze  (backend/app/routers/analyze.py)
POST   /analyze/ingest                 — text → classify (no DB write)
POST   /analyze/url                    — scrape URL → classify (returns 422 + helpful hint for IG/X/TikTok)
POST   /analyze/case                   — case-level RAG analysis
POST   /analyze/chat                   — case-aware follow-up Q&A

# Cases  (backend/app/routers/cases.py)
GET    /cases/                          — list
GET    /cases/{id}                      — detail + evidence
POST   /cases/                          — create
PUT    /cases/{id}                      — update title + victim_context
DELETE /cases/{id}                      — cascade delete
POST   /cases/{id}/evidence             — append evidence (auto-syncs from frontend)

# Reports  (backend/app/routers/reports.py)
GET    /reports/{id}?report_type=…      — preview text
GET    /reports/{id}/pdf?…              — A4 PDF (Strafanzeige | NetzDG | general)
                                          — accepts ?victim_name=…&victim_address=…&victim_phone=…&victim_email=…
GET    /reports/{id}/legal-pdf          — standalone legal-analysis PDF
GET    /reports/{id}/court-package      — ZIP bundle
POST   /reports/{id}/eml                — RFC 5322 .eml export with attachments

# Legal AI  (backend/app/routers/legal.py)
GET    /legal/{case_id}                 — case-level analysis (auto-cached server-side)

# Upload  (backend/app/routers/upload.py)
POST   /upload/screenshot               — OCR via OpenAI Vision (gpt-4o-mini)

# Auth (optional, NGO/lawyer flow)  (backend/app/routers/auth.py)
POST   /auth/login                      — magic link
POST   /auth/verify
GET    /auth/me · PUT · DELETE
GET    /auth/me/export                  — Art. 20 data export

# Health
GET    /health · /api/health
```

Full interactive OpenAPI docs: `http://localhost:8000/docs` (or `/api/docs` on Vercel preview).

---

## German Laws Covered

| Paragraph | Offense | Max Penalty |
|-----------|---------|-------------|
| § 130 StGB | Volksverhetzung (Incitement to hatred) | 5 years |
| § 185 StGB | Beleidigung (Insult) | 1 year |
| § 186 StGB | Üble Nachrede (Defamation) | 1 year |
| § 187 StGB | Verleumdung (Slander) | 5 years |
| § 201a StGB | Intimate image violation / Deepfakes | 2 years |
| § 238 StGB | Nachstellung (Stalking) | 3 years (5 with aggravating factors) |
| § 241 StGB | Bedrohung (Threat) | 2 years |
| § 126a StGB | Gefährdende Verbreitung personenbezogener Daten · Strafbare Bedrohung | 3 years |
| § 263 StGB | Betrug (Fraud) | 5 years |
| § 263a StGB | Computerbetrug (Computer fraud) | 5 years |
| § 269 StGB | Fälschung beweiserheblicher Daten | 5 years |
| NetzDG § 3 | Platform removal obligation | €50M fine |

> 12 entries total — exhaustive list, enforced server-side via Pydantic enum (model literally cannot return anything else).

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + TypeScript + Vite + Tailwind 4 |
| Backend | Python 3.12 + FastAPI |
| Hosting | Vercel (frontend static + Python Fluid Compute) · Frankfurt |
| Database | Neon Postgres (Vercel Marketplace) |
| AI Classifier | OpenAI `gpt-4o-mini` (Pydantic structured outputs) |
| OCR | OpenAI Vision (`gpt-4o-mini`) |
| Evidence | SHA-256 hash chain + browser-side Web-Crypto verifier |
| Reports | ReportLab (A4 PDF) + Python `email` (RFC 5322 .eml) |
| Auth (optional) | Magic-link, DB-backed sessions |

---

## Project Structure

```
safevoice/
├── api/proxy.py                       — Vercel Python Function entry point (ASGI shim)
├── backend/app/
│   ├── main.py                        — FastAPI app + middleware
│   ├── database.py                    — SQLAlchemy models + seed
│   ├── models/                        — Pydantic domain (Case, Evidence, …)
│   ├── services/
│   │   ├── classifier.py              — orchestrator (single-tier LLM)
│   │   ├── classifier_llm_v2.py       — gpt-4o-mini + Pydantic .parse()
│   │   ├── llm_gateway.py             — central LLM gateway (tokens + cost + request_id)
│   │   ├── legal_ai.py                — case-level second-layer analysis
│   │   ├── ocr.py                     — OpenAI Vision OCR (gpt-4o-mini)
│   │   ├── scraper.py                 — public web scraper
│   │   ├── evidence.py                — SHA-256 hashing
│   │   ├── pdf_generator.py           — A4 Strafanzeige PDF (exec summary + exhibits + AI block)
│   │   ├── report_generator.py        — Strafanzeige / NetzDG / general body builders
│   │   └── legal_pdf.py               — standalone NGO-grade legal PDF
│   └── routers/                       — FastAPI routes (analyze, cases, reports, legal, upload, …)
├── frontend/src/
│   ├── pages/                         — Home, Analyze, Cases, CaseDetail, Login, Impressum, Datenschutz
│   ├── components/
│   │   ├── ReportModal.tsx            — Vorschau + Senden tabs, shared victim form
│   │   ├── SendReport.tsx             — recipient picker, .eml builder
│   │   ├── CaseEditor.tsx             — add evidence + edit context (tabbed)
│   │   ├── EvidenceCard.tsx           — inline @author edit + hash verifier
│   │   ├── HashVerifier.tsx           — browser-side SHA-256 verifier
│   │   ├── OnlinewachePanel.tsx       — 3-step copy/open/paste flow
│   │   └── …                          — SeverityBadge, LawCard, AcknowledgementBanner, SafeExit
│   └── i18n/                          — DE/EN translations
├── requirements.txt                   — pinned for Vercel build
├── runtime.txt                        — python-3.12
├── vercel.json                        — function config + rewrites
├── schema.dbml                        — DB schema for dbdiagram.io
└── Dockerfile                         — production deployment (alternative to Vercel)
```

---

## Docs

Everything beyond the quick start lives in `docs/`.

- [`docs/DEPLOY.md`](docs/DEPLOY.md) — deploy guide, env vars
- [`docs/DESIGN.md`](docs/DESIGN.md) — design system + product principles
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — what's next
- [`docs/AI_FLOW.md`](docs/AI_FLOW.md), [`docs/CASE_CRUD.md`](docs/CASE_CRUD.md), [`docs/USER_CRUD.md`](docs/USER_CRUD.md), [`docs/CLASSIFICATION_API.md`](docs/CLASSIFICATION_API.md) — per-topic deep dives

Meeting + presentation artefacts in `docs/meeting/` (tutor deck, code walkthrough, study guide, quiz).

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
