# SafeVoice

Document digital harassment, understand your legal rights, file reports.

Built for Germany – DSGVO-compliant, bilingual (DE/EN).

---

## Quick start

You need two terminals.

### Terminal 1 – Backend

```bash
cd safevoice/backend
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn pydantic pydantic-settings python-multipart httpx python-dateutil langdetect
uvicorn app.main:app --reload
```

Backend runs at: http://localhost:8000
API docs at: http://localhost:8000/docs

### Terminal 2 – Frontend

```bash
cd safevoice/frontend
npm install
npm run dev
```

Frontend runs at: http://localhost:5173

Open http://localhost:5173 in your browser.

---

## What you can demo right now

### Mock cases (pre-loaded)

Navigate to **Meine Fälle / My Cases** to see 3 realistic cases:

| Case | Severity | What it shows |
|------|----------|---------------|
| Coordinated harassment after vegan post | HIGH | 3 accounts, coordinated timing, pattern detection |
| Death threat following opinion piece | CRITICAL | Escalation pattern, § 241 + § 126a StGB |
| Body shaming and sexual harassment | HIGH | Sexual coercion, immediate action flow |

Each case shows:
- Classified evidence items with legal mapping
- Pattern flags (coordinated attack, escalation, repeat offender)
- Exportable reports: NetzDG, police (Strafanzeige), general

### Live text analysis

Go to **Neuer Fall / New Case**, paste any text and click Analyze.

Try these examples:
```
I know where you live. Watch yourself.
```
```
Frauen wie du sollten die Klappe halten.
```
```
Send me a private message or I'll post things about you everywhere.
```

### Report export

Open any case → click **Bericht exportieren** → switch between:
- NetzDG (platform report, triggers legal obligation)
- Strafanzeige (police report template)
- Allgemeiner Bericht (general documentation)

---

## Project structure

```
safevoice/
├── backend/
│   └── app/
│       ├── main.py                 # FastAPI app + CORS
│       ├── models/evidence.py      # All data models
│       ├── data/mock_data.py       # 3 realistic mock cases
│       ├── services/
│       │   ├── classifier.py       # Rule-based classification engine
│       │   ├── pattern_detector.py # Coordination, escalation, repeat detection
│       │   └── report_generator.py # NetzDG, police, general report formats
│       └── routers/
│           ├── cases.py            # GET /cases/, GET /cases/{id}
│           ├── analyze.py          # POST /analyze/text, POST /analyze/ingest
│           └── reports.py          # GET /reports/{id}?report_type=&lang=
│
└── frontend/
    └── src/
        ├── types/index.ts          # TypeScript types
        ├── i18n/index.ts           # DE/EN translations
        ├── services/api.ts         # Backend API calls
        ├── components/
        │   ├── SeverityBadge.tsx   # Color-coded severity indicator
        │   ├── CategoryTag.tsx     # Harassment category labels
        │   ├── LawCard.tsx         # German law with explanation
        │   ├── EvidenceCard.tsx    # Full evidence item with legal details
        │   ├── PatternFlagCard.tsx # Pattern detection results
        │   └── ReportModal.tsx     # 3-tab report export modal
        └── pages/
            ├── Home.tsx            # Landing page
            ├── Analyze.tsx         # Input + live classification
            ├── Cases.tsx           # Case list
            └── CaseDetail.tsx      # Full case with export
```

---

## API endpoints

```
GET  /health
GET  /cases/
GET  /cases/{id}
POST /analyze/text      { text, author_username, url }
POST /analyze/ingest    { text, author_username, url }
POST /analyze/case      { evidence_items[] }
GET  /reports/{id}      ?report_type=general|netzdg|police&lang=de|en
```

Full interactive docs: http://localhost:8000/docs

---

## Roadmap (next steps)

### Classification
- [ ] Replace regex engine with fine-tuned German BERT model
- [ ] Add Claude API integration for legal analysis
- [ ] Multi-language detection (Turkish, Arabic common in DE harassment)

### Evidence ingestion
- [ ] Real Instagram scraping (public posts)
- [ ] Screenshot capture service
- [ ] archive.org integration for preservation

### Platform coverage
- [ ] X/Twitter
- [ ] TikTok
- [ ] Facebook

### Case management
- [ ] Encrypted case storage (server-side)
- [ ] Case sharing with lawyers/support orgs
- [ ] Timeline view

### Report generation
- [ ] PDF export
- [ ] Direct NetzDG submission via platform APIs
- [ ] Integration with HateAid case management

### Legal coverage
- [ ] Austria (§ 107 StGB)
- [ ] Switzerland (Art. 173 StGB)
- [ ] EU DSA reporting

---

## Legal note

SafeVoice documents evidence and provides legal context as general information.
It does not constitute legal advice. For individual legal advice, contact
HateAid (hateaid.org) or a qualified attorney.
