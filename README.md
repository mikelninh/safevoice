# SafeVoice

**Document digital harassment. Understand your legal rights. File reports. In 30 seconds.**

Built for Germany, expanding across Europe. DSGVO-compliant. Bilingual (DE/EN). Free for victims. Always.

> *"Every 3 minutes, someone in Germany is harassed online. 90% goes unreported — not because victims don't care, but because the system fails them. SafeVoice fixes this."*

---

## Status

| Phase | Progress | Tests |
|-------|----------|-------|
| Phase 1 — Foundation | 11/11 | 42 |
| Phase 2 — Trust & Reach | 10/10 | 88 |
| Phase 3 — Institutional | 8/8 | 179 |
| Phase 4 — Scale (DE, AT, CH, UK, FR) | 7/7 | 366 |
| Phase 5 — Policy Impact | 5/5 | 412 |
| **Production hardening** | **Security + Docker + legal pages** | **452** |

**ALL PHASES COMPLETE. 452 backend tests. 41 features. 33 laws across 5 countries. Production-hardened.**

---

## What SafeVoice does

### For victims

1. **Paste a URL** (Instagram, X/Twitter), **upload a screenshot** (WhatsApp), or **type text directly**
2. **Get instant legal classification** — 3-tier AI identifies the offense, maps to criminal law (DE/AT/CH/UK/FR), assesses severity
3. **Generate court-ready reports** — NetzDG platform report, police complaint (Strafanzeige), BaFin scam report, court evidence ZIP
4. **Preserve evidence** — SHA-256 hashing, UTC timestamps, archive.org backup, cryptographic chain of custody
5. **Get human support** — HateAid hotline (one tap), Onlinewache for all 16 Bundeslaender, BaFin for scams
6. **Stay safe** — Quick exit button, no account required, emergency delete (instant, no trace)

### For institutions (police, NGOs, law firms)

7. **Partner API** — submit and retrieve cases via API key authentication
8. **Case assignment** — route to jurisdiction and unit (cybercrime, fraud, etc.)
9. **Anonymized dashboard** — aggregate patterns for BKA, researchers, policy makers
10. **SLA tracking** — NetzDG 24h/7d removal deadline monitoring with compliance stats
11. **Serial offender database** — cross-case pattern matching (pseudonymized)
12. **Policy data exports** — DSA transparency reports, Europol SIENA packages, research datasets

---

## Quick start

### Option 1: Docker (recommended)

```bash
docker compose up
```

App runs at http://localhost:8000 (backend + frontend served together).

### Option 2: Development (two terminals)

**Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

### Optional: Enable Claude API classifier (most accurate)

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

Without this, the system uses transformer model (tier 2) or regex (tier 3) automatically.

### Run tests

```bash
cd backend
source venv/bin/activate
TESTING=1 python3 -m pytest tests/ -v
```

---

## Architecture

```
safevoice/
├── backend/
│   └── app/
│       ├── main.py                       # FastAPI + CORS + rate limiting + security headers
│       ├── models/
│       │   ├── evidence.py               # Case, EvidenceItem, Classification, GermanLaw
│       │   ├── partner.py                # Organization, OrgMember, CaseAssignment
│       │   ├── sla.py                    # SLARecord, SLAStatus, SLADashboard
│       │   └── user.py                   # User, MagicLink, Session
│       ├── data/
│       │   ├── mock_data.py              # 4 realistic cases + German law definitions
│       │   ├── laws_austria.py           # 6 Austrian criminal laws
│       │   ├── laws_switzerland.py       # 6 Swiss criminal laws
│       │   ├── laws_uk.py                # 7 UK laws (Online Safety Act, etc.)
│       │   └── laws_france.py            # 6 French laws (Loi Avia, Code penal)
│       ├── services/
│       │   ├── classifier.py             # 3-tier: Claude API -> transformer -> regex
│       │   ├── classifier_llm.py         # Tier 1: Claude API (Sonnet)
│       │   ├── classifier_transformer.py # Tier 2: HuggingFace toxic-comment-model
│       │   ├── scraper.py                # Instagram + X/Twitter + generic URL scraper
│       │   ├── ocr.py                    # Screenshot OCR (Tesseract, WhatsApp detection)
│       │   ├── evidence.py               # SHA-256 hashing, UTC timestamps, archive.org
│       │   ├── chain.py                  # Cryptographic evidence hash chain
│       │   ├── auth.py                   # Magic link auth, sessions, emergency delete
│       │   ├── legal_ai.py               # AI legal analysis (Claude API + fallback)
│       │   ├── offender_db.py            # Serial offender database (pseudonymized)
│       │   ├── law_mapper.py             # Multi-country law mapping (DE/AT/CH/UK/FR)
│       │   ├── pattern_detector.py       # Coordination, escalation, repeat detection
│       │   ├── report_generator.py       # NetzDG, police, general text reports
│       │   ├── pdf_generator.py          # Court-ready A4 PDF generation (ReportLab)
│       │   ├── court_export.py           # ZIP evidence package for courts
│       │   ├── bafin_report.py           # BaFin scam report generator
│       │   ├── platform_submit.py        # NetzDG submission for Instagram/X/TikTok
│       │   ├── sla_tracker.py            # NetzDG 24h/7d deadline tracking
│       │   ├── partner_store.py          # Organization + member management
│       │   └── policy_export.py          # DSA reports, research data, Europol SIENA
│       └── routers/
│           ├── analyze.py                # /analyze/text, /analyze/ingest, /analyze/url
│           ├── cases.py                  # /cases/, /cases/{id}
│           ├── reports.py                # /reports/{id}, /pdf, /court-package, /bafin
│           ├── upload.py                 # /upload/screenshot (OCR + classify)
│           ├── chain.py                  # /chain/build, /chain/verify
│           ├── auth.py                   # /auth/login, /auth/verify, /auth/me
│           ├── partners.py               # /partners/* (API key auth)
│           ├── dashboard.py              # /dashboard/stats, /categories, /platforms
│           ├── sla.py                    # /sla/report, /sla/dashboard
│           ├── legal.py                  # /legal/{id}, /offenders/*, /submit/*
│           └── policy.py                 # /policy/* (DSA, research, Europol)
│
├── frontend/
│   └── src/
│       ├── App.tsx                       # Router + nav + footer + SafeExit
│       ├── types/index.ts                # TypeScript interfaces
│       ├── i18n/index.ts                 # DE/EN translations (190+ strings)
│       ├── services/
│       │   ├── api.ts                    # All backend API calls
│       │   └── storage.ts                # localStorage CRUD for cases
│       ├── components/
│       │   ├── SafeExit.tsx              # Quick exit button (always visible)
│       │   ├── AcknowledgementBanner.tsx  # Trauma-informed welcome
│       │   ├── AnalysisProgress.tsx      # Animated multi-step progress
│       │   ├── StatsBar.tsx              # "You are not alone" trust stats
│       │   ├── HateAidReferral.tsx       # Warm handoff to HateAid counseling
│       │   ├── OnlinewachePanel.tsx      # 16 Bundeslaender police report links
│       │   ├── SeverityBadge.tsx         # Color-coded severity indicator
│       │   ├── CategoryTag.tsx           # Offense category labels
│       │   ├── LawCard.tsx               # Law card with explanation
│       │   ├── EvidenceCard.tsx          # Evidence item with legal details
│       │   ├── PatternFlagCard.tsx       # Pattern detection results
│       │   └── ReportModal.tsx           # Report export + PDF download
│       └── pages/
│           ├── Home.tsx                  # Landing page
│           ├── Analyze.tsx               # URL scrape + text + screenshot upload
│           ├── Cases.tsx                 # Case list (local + API)
│           ├── CaseDetail.tsx            # Full case + HateAid + Onlinewache
│           ├── Login.tsx                 # Magic link auth
│           ├── Dashboard.tsx             # Institutional stats
│           ├── Impressum.tsx             # Legal notice (§ 5 TMG)
│           └── Datenschutz.tsx           # Privacy policy (DSGVO)
│
├── Dockerfile                            # Multi-stage: Node build + Python serve
├── docker-compose.yml                    # App + PostgreSQL with health checks
├── ROADMAP.md                            # 5-phase product roadmap + monetisation
├── DESIGN.md                             # 13-section architecture + design decisions
├── DEMO.md                               # Demo script (4 scenarios)
├── PRESENTATION.md                       # Full 7-part investor/partner presentation
└── README.md                             # This file
```

---

## API endpoints (40+)

### Analysis
```
POST /analyze/text       — Classify raw text
POST /analyze/ingest     — Classify + create evidence item
POST /analyze/url        — Scrape URL (Instagram/X) + classify + comments
POST /upload/screenshot  — OCR screenshot + classify (WhatsApp detection)
```

### Cases & reports
```
GET  /cases/                    — List cases
GET  /cases/{id}                — Case details
GET  /reports/{id}              — Text report (general/netzdg/police)
GET  /reports/{id}/pdf          — PDF report
GET  /reports/{id}/court-package — ZIP evidence package (PDFs + manifest + hashes)
GET  /reports/{id}/bafin        — BaFin scam report
```

### Evidence chain
```
POST /chain/build        — Build cryptographic hash chain for case
POST /chain/verify       — Verify chain integrity
GET  /chain/{case_id}    — Get/build chain
```

### Authentication (magic link, no passwords)
```
POST   /auth/login         — Request magic link
POST   /auth/verify        — Verify → session token
GET    /auth/me            — Current user
PUT    /auth/me            — Update profile
POST   /auth/logout        — End session
DELETE /auth/me            — Soft delete (7-day recovery)
DELETE /auth/me/emergency  — EMERGENCY: instant hard delete, no recovery
```

### Partner API (X-API-Key header)
```
POST /partners/organizations     — Register organization
POST /partners/cases/submit      — Submit case
POST /partners/cases/assign      — Assign to org
GET  /partners/cases             — List assigned cases
PUT  /partners/assignments/{id}  — Update status
```

### Dashboard & SLA
```
GET  /dashboard/stats       — Anonymized aggregate statistics
GET  /dashboard/categories  — Category breakdown by severity
GET  /dashboard/platforms   — Platform statistics
POST /sla/report            — File NetzDG report (starts deadline)
GET  /sla/{case_id}         — SLA records for case
GET  /sla/dashboard         — Compliance dashboard
```

### Legal AI & serial offenders
```
GET  /legal/{case_id}              — AI legal analysis (deep reasoning)
GET  /offenders/check/{username}   — Check repeat offender status
GET  /offenders/serial             — List serial offenders (anonymized)
GET  /offenders/stats              — Database statistics
GET  /submit/{case_id}/{platform}  — Pre-filled NetzDG submission
```

### Policy & research
```
GET  /policy/evidence-standard     — Evidence format JSON schema (Bundestag)
GET  /policy/dsa-report            — EU DSA Art. 16 transparency report
GET  /policy/research-dataset      — Anonymized dataset (zero PII)
GET  /policy/research-dictionary   — Data dictionary for researchers
GET  /policy/dgeg-submission       — Digitale-Gewalt-Gesetz consultation data
GET  /policy/europol-siena         — Europol SIENA cross-border package
```

### System
```
GET  /health               — Health + classifier tier
```

Full interactive docs: http://localhost:8000/docs

---

## Classifier

Three tiers with automatic fallback — SafeVoice never returns "analysis unavailable":

| Tier | Engine | Accuracy | Requires |
|------|--------|----------|----------|
| 1 | Claude API (Sonnet) | Highest — context, sarcasm, legal nuance | `ANTHROPIC_API_KEY` |
| 2 | Transformer (toxic-comment-model) | Good — multilingual toxicity | `torch` + `transformers` |
| 3 | Regex rules | Baseline — keyword patterns | Nothing |

**Languages classified:** German, English, Turkish, Arabic

---

## Legal coverage — 33 laws across 5 countries

| Country | Laws | Coverage |
|---------|------|----------|
| Germany | 8 (StGB + NetzDG) | Full: insult, defamation, threats, fraud, cybercrime |
| Austria | 6 (StGB AT) | Full: stalking, cybermobbing, threats, coercion |
| Switzerland | 6 (StGB CH) | Full: defamation, threats, telecom abuse |
| United Kingdom | 7 (OSA, CMA, etc.) | Full: harassment, fraud, computer misuse |
| France | 6 (CP + Loi Avia) | Full: cyberbullying, death threats, fraud |

---

## Production features

| Feature | Implementation |
|---------|---------------|
| Rate limiting | 120 req/min per IP (configurable via `RATE_LIMIT_RPM`) |
| Security headers | X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy |
| CORS | Configurable origins via `CORS_ORIGINS` env var |
| Docker | Multi-stage build, docker-compose with PostgreSQL |
| Legal pages | Impressum (§ 5 TMG), Datenschutz (DSGVO Art. 13/14) |
| Auth | Magic link (no passwords), 30-day sessions, emergency delete |
| Evidence integrity | SHA-256 + hash chain + archive.org + UTC timestamps |
| Anonymization | Research API strips all PII, offender DB uses pseudonymized hashes |

---

## Test coverage

| Suite | Tests | Covers |
|-------|-------|--------|
| Classifier (DE/EN/TR/AR) | 33 | All categories, 4 languages |
| Scraper (IG/X/generic) | 27 | HTML parsing, platform detection |
| Evidence integrity | 10 | Hashing, timestamps, verification |
| PDF generation | 9 | All report types, DE+EN |
| BaFin reports | 9 | Scam detection, wallet extraction |
| Evidence chain | 26 | Hash chain, tamper detection |
| SLA tracking | 19 | Deadlines, expiry, dashboard |
| Screenshot upload | 22 | OCR, WhatsApp detection |
| Authentication | 20 | Magic link, sessions, deletion |
| Partner API + dashboard | 24 | Org management, case assignment |
| Legal AI + offenders | 20 | Analysis, serial detection, platform submit |
| International laws | 28 | Austrian + Swiss law mapping |
| UK + French laws | 123 | All law field validation |
| Policy APIs | 42 | DSA, research, Europol |
| Edge cases + security | 44 | XSS, injection, empty input, unicode |
| **Total** | **452** | **(4 skipped: tesseract optional)** |

---

## Documentation

| File | What it covers |
|------|---------------|
| [ROADMAP.md](ROADMAP.md) | 5-phase product roadmap, monetisation strategy, revenue targets |
| [DESIGN.md](DESIGN.md) | 13-section deep dive: victim-first design, classifier rationale, evidence integrity, encryption, deletion model, tech stack |
| [DEMO.md](DEMO.md) | 4 demo scenarios with exact text to paste, curl examples |
| [PRESENTATION.md](PRESENTATION.md) | 7-part presentation: crisis, solution, design philosophy, technical deep dive, business model, competitive landscape, go-to-market |

---

## Legal note

SafeVoice documents evidence and provides legal context as general information.
It does not constitute legal advice. For individual legal advice, contact
[HateAid](https://hateaid.org) (free counseling for victims of digital violence)
or a qualified attorney.

---

## License

Copyright 2024-2026. All rights reserved.
