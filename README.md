# SafeVoice

**Document digital harassment. Understand your legal rights. File reports.**

Built for Germany. DSGVO-compliant. Bilingual (DE/EN). Free for victims.

---

## Status

| Phase | Progress | Tests |
|-------|----------|-------|
| Phase 1 — Foundation | 11/11 | 42 |
| Phase 2 — Trust & Reach | 9/10 | 88 |
| Phase 3 — Institutional | 8/8 | 179 |
| Phase 4 — Scale (DACH + UK) | 0/8 | — |
| Phase 5 — Policy Impact | 0/5 | — |

**179 backend tests passing. 4 commits on main.**

One item deferred: 2.1 User accounts (needs database infrastructure).

---

## What SafeVoice does

A victim of digital harassment can:

1. **Paste a URL** (Instagram, X/Twitter) or **upload a screenshot** (WhatsApp) or **type text directly**
2. **Get instant classification** — AI identifies the offense type, maps to German criminal law, assesses severity
3. **Generate court-ready reports** — NetzDG platform report, police complaint (Strafanzeige), BaFin scam report
4. **Download a court evidence package** — ZIP with PDFs, evidence files, SHA-256 hash verification, chain of evidence
5. **Get referred to human support** — HateAid hotline, Onlinewache (all 16 Bundeslaender)

For institutions (police, NGOs, law firms):

6. **Partner API** — submit and retrieve cases via authenticated API
7. **Case assignment** — route to jurisdiction and unit (cybercrime, fraud, etc.)
8. **Anonymized dashboard** — aggregate patterns for BKA/research
9. **SLA tracking** — NetzDG 24h/7d removal deadline monitoring

---

## Quick start

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend: http://localhost:8000
API docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:5173

### Optional: Enable Claude API classifier (most accurate)

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

Without this, the system uses transformer model (tier 2) or regex (tier 3) automatically.

### Run tests

```bash
cd backend
source venv/bin/activate
python3 -m pytest tests/ -v
```

---

## Architecture

```
safevoice/
├── backend/
│   └── app/
│       ├── main.py                    # FastAPI app, CORS, router registration
│       ├── models/
│       │   ├── evidence.py            # Case, EvidenceItem, Classification, GermanLaw
│       │   ├── partner.py             # Organization, OrgMember, CaseAssignment
│       │   └── sla.py                 # SLARecord, SLAStatus, SLADashboard
│       ├── data/
│       │   └── mock_data.py           # 4 realistic cases + German law definitions
│       ├── services/
│       │   ├── classifier.py          # 3-tier classifier (Claude API → transformer → regex)
│       │   ├── classifier_llm.py      # Tier 1: Claude API classifier
│       │   ├── classifier_transformer.py # Tier 2: HuggingFace transformer
│       │   ├── scraper.py             # Instagram + X/Twitter + generic URL scraper
│       │   ├── ocr.py                 # Screenshot OCR (Tesseract, WhatsApp detection)
│       │   ├── evidence.py            # SHA-256 hashing, UTC timestamps, archive.org
│       │   ├── chain.py               # Cryptographic evidence hash chain
│       │   ├── pattern_detector.py    # Coordination, escalation, repeat detection
│       │   ├── report_generator.py    # NetzDG, police, general text reports
│       │   ├── pdf_generator.py       # Court-ready A4 PDF generation
│       │   ├── court_export.py        # ZIP evidence package for courts
│       │   ├── bafin_report.py        # BaFin scam report generator
│       │   ├── sla_tracker.py         # NetzDG deadline tracking
│       │   └── partner_store.py       # Organization + member management
│       └── routers/
│           ├── analyze.py             # /analyze/text, /analyze/ingest, /analyze/url
│           ├── cases.py               # /cases/, /cases/{id}
│           ├── reports.py             # /reports/{id}, /reports/{id}/pdf, /reports/{id}/court-package
│           ├── upload.py              # /upload/screenshot
│           ├── chain.py               # /chain/build, /chain/verify, /chain/{case_id}
│           ├── partners.py            # /partners/* (API key auth)
│           ├── dashboard.py           # /dashboard/stats, /dashboard/categories
│           └── sla.py                 # /sla/report, /sla/{case_id}, /sla/dashboard
│
├── frontend/
│   └── src/
│       ├── App.tsx                    # Router + nav + SafeExit + AcknowledgementBanner
│       ├── types/index.ts             # TypeScript interfaces
│       ├── i18n/index.ts              # DE/EN translations (190+ strings)
│       ├── services/
│       │   ├── api.ts                 # Backend API calls (analyze, scrape, upload, PDF)
│       │   └── storage.ts             # localStorage CRUD for cases
│       ├── components/
│       │   ├── SafeExit.tsx           # Quick exit button (always visible)
│       │   ├── AcknowledgementBanner.tsx # Trauma-informed welcome
│       │   ├── AnalysisProgress.tsx   # Animated multi-step progress
│       │   ├── StatsBar.tsx           # "You are not alone" trust stats
│       │   ├── HateAidReferral.tsx    # Warm handoff to HateAid counseling
│       │   ├── OnlinewachePanel.tsx   # 16 Bundeslaender police report links
│       │   ├── SeverityBadge.tsx      # Color-coded severity indicator
│       │   ├── CategoryTag.tsx        # Offense category labels
│       │   ├── LawCard.tsx            # German law with explanation
│       │   ├── EvidenceCard.tsx       # Evidence item with legal details
│       │   ├── PatternFlagCard.tsx    # Pattern detection results
│       │   └── ReportModal.tsx        # Report export modal + PDF download
│       └── pages/
│           ├── Home.tsx               # Landing page with hero + coverage grid
│           ├── Analyze.tsx            # URL scrape + text input + screenshot upload
│           ├── Cases.tsx              # Case list (local + API)
│           └── CaseDetail.tsx         # Full case + HateAid + Onlinewache + export
│
├── ROADMAP.md                         # 5-phase product roadmap + monetisation
├── DESIGN.md                          # Architecture + design decisions
└── README.md                          # This file
```

---

## API endpoints

### Analysis
```
POST /analyze/text       — Classify raw text
POST /analyze/ingest     — Classify text + create evidence item
POST /analyze/url        — Scrape URL (Instagram/X) + classify
POST /upload/screenshot  — OCR screenshot + classify (WhatsApp support)
```

### Cases & reports
```
GET  /cases/             — List mock cases
GET  /cases/{id}         — Get case details
GET  /reports/{id}       — Generate text report (general/netzdg/police)
GET  /reports/{id}/pdf   — Download PDF report
GET  /reports/{id}/court-package — Download ZIP evidence package
GET  /reports/{id}/bafin — Generate BaFin scam report
```

### Evidence chain
```
POST /chain/build        — Build hash chain for a case
POST /chain/verify       — Verify chain integrity
GET  /chain/{case_id}    — Get/build chain
```

### Partner API (X-API-Key auth)
```
POST /partners/organizations     — Register organization
POST /partners/cases/submit      — Submit case via API
POST /partners/cases/assign      — Assign case to org
GET  /partners/cases             — List assigned cases
PUT  /partners/assignments/{id}  — Update assignment status
```

### Dashboard & SLA
```
GET  /dashboard/stats            — Anonymized aggregate statistics
GET  /dashboard/categories       — Category breakdown
GET  /dashboard/platforms        — Platform statistics
POST /sla/report                 — File NetzDG report (starts deadline)
GET  /sla/{case_id}              — SLA records for case
GET  /sla/dashboard              — SLA compliance dashboard
```

### System
```
GET  /health             — Health check + classifier tier status
```

Full interactive docs: http://localhost:8000/docs

---

## Classifier tiers

| Tier | Engine | Accuracy | Requires |
|------|--------|----------|----------|
| 1 | Claude API (Sonnet) | Highest — context-aware, German law expertise | `ANTHROPIC_API_KEY` env var |
| 2 | Transformer (toxic-comment-model) | Good — multilingual toxicity scoring | `torch` + `transformers` installed |
| 3 | Regex rules | Baseline — keyword patterns in DE/EN/TR/AR | Nothing (always available) |

Automatic fallback: if tier 1 fails, tries tier 2, then tier 3.

---

## Languages supported

| Language | Classifier | UI | Reports |
|----------|-----------|-----|---------|
| German | Full | Full | Full |
| English | Full | Full | Full |
| Turkish | Harassment/threats/misogyny | — | — |
| Arabic | Harassment/threats/misogyny | — | — |

---

## German laws covered

| Paragraph | Offense | Max penalty |
|-----------|---------|-------------|
| § 185 StGB | Beleidigung (Insult) | 1 year |
| § 186 StGB | Uble Nachrede (Defamation) | 1 year |
| § 241 StGB | Bedrohung (Threat) | 2 years |
| § 126a StGB | Strafbare Bedrohung (Criminal threat) | 3 years |
| § 263 StGB | Betrug (Fraud) | 5 years |
| § 263a StGB | Computerbetrug (Computer fraud) | 5 years |
| § 269 StGB | Falschung beweiserheblicher Daten | 5 years |
| NetzDG § 3 | Platform removal obligation | Up to 50M fine |

---

## Legal note

SafeVoice documents evidence and provides legal context as general information.
It does not constitute legal advice. For individual legal advice, contact
[HateAid](https://hateaid.org) (free counseling) or a qualified attorney.

---

## License

Copyright 2024-2026. All rights reserved.
