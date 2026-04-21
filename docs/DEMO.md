# SafeVoice — Demo Script & Presentation

---

## Elevator Pitch (30 seconds)

> SafeVoice makes reporting digital harassment as easy as sharing a post.
> Paste a link or screenshot. Get instant legal classification under German law.
> Download a court-ready report. File with police or platforms in one click.
> Built for Germany, expanding across Europe. Free for victims. Always.

---

## The Problem (2 minutes)

**Every 3 minutes**, someone in Germany is harassed online.

Three barriers stop victims from getting justice:

1. **"I don't know if this is illegal"** — Victims can't tell if a comment is § 185 (insult, 1 year) or § 241 (threat, 2 years). Legal literacy shouldn't be required to report a crime.

2. **"My evidence keeps disappearing"** — Posts get deleted. Screenshots aren't timestamped. When victims finally go to police, the evidence is gone.

3. **"The reporting process is too complicated"** — NetzDG forms are buried. Police require structured reports. Filing takes hours. Most people give up.

**Result:** 90% of digital harassment in Germany goes unreported.

---

## The Solution: SafeVoice (5 minute demo)

### Demo 1: Paste → Classify → Report (2 min)

**Setup:** Open http://localhost:5173 → Click "Vorfall melden"

**Script:**
1. Paste this text:
   ```
   Frauen wie du sollten die Klappe halten. Ich weiß wo du wohnst.
   ```
2. Click "Analysieren"
3. Show the result:
   - **Severity: CRITICAL** (red badge)
   - **Categories:** Misogyny + Threat
   - **Laws:** § 185 StGB (Insult), § 241 StGB (Threat), NetzDG § 3
   - **Immediate action required** banner with police + HateAid links
4. Click "Zu Fall hinzufügen" → case saved locally
5. Open the case → click "Bericht exportieren"
6. Show the NetzDG tab: ready-to-submit text with legal references
7. Show the Strafanzeige tab: complete police report template
8. Click "PDF Export" → download court-ready PDF

**Key message:** *"From paste to police report in 30 seconds. No legal knowledge required."*

### Demo 2: URL Scraping (1 min)

**Script:**
1. Paste an Instagram or X URL into the URL field
2. Show the "Auto-fetch" badge that appears
3. Click "Analysieren"
4. Show: author extracted, content fetched, comments classified individually
5. Platform badge shows "Fetched from Instagram"

**Key message:** *"Victims don't need to copy text. Paste the link, we do the rest."*

### Demo 3: Screenshot Upload (1 min)

**Script:**
1. Click the screenshot upload section
2. Upload a WhatsApp screenshot
3. Show: OCR extracts the text, detects WhatsApp format, classifies content
4. WhatsApp badge appears

**Key message:** *"WhatsApp is where most harassment happens in Germany. We handle that."*

### Demo 4: Court Evidence Package (1 min)

**Script:**
1. Open any mock case (e.g. "Death threat following opinion piece")
2. Show evidence items with severity + laws
3. Show pattern flags (escalation detected)
4. Show HateAid referral (appears automatically for severe cases)
5. Show Onlinewache panel → select "Berlin" → copy text → link to police
6. Click "Bericht exportieren" → PDF Export
7. Visit http://localhost:8000/reports/case-002/court-package?lang=de
8. Download and unzip: PDFs, evidence files, hash verification, chain of evidence

**Key message:** *"This is what a lawyer needs. This is what police need. Generated in one click."*

---

## For Institutions (2 minutes)

### Partner API Demo

```bash
# Create an organization
curl -X POST http://localhost:8000/partners/organizations \
  -H "Content-Type: application/json" \
  -d '{"name": "LKA Hamburg", "org_type": "police", "contact_email": "cyber@polizei.hamburg.de"}'

# Submit a case via API
curl -X POST http://localhost:8000/partners/cases/submit \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sv_[key_from_above]" \
  -d '{"text": "I will kill you", "platform": "instagram", "author_username": "threat_user"}'
```

### Dashboard Demo

Open http://localhost:5173/dashboard
- Total cases, evidence items, urgent actions
- Severity distribution (visual bars)
- Top offense categories
- Platform breakdown

### SLA Tracking

```bash
# File a NetzDG report and start deadline tracking
curl -X POST http://localhost:8000/sla/report \
  -H "Content-Type: application/json" \
  -d '{"case_id": "case-002", "evidence_id": "ev-002-b", "platform": "instagram", "severity": "critical"}'

# Check: 24-hour deadline started
curl http://localhost:8000/sla/dashboard
```

**Key message:** *"Police get structured digital intake. NGOs get case management. We track platform compliance."*

---

## Technical Differentiators

| Feature | SafeVoice | Manual reporting |
|---------|-----------|-----------------|
| Time to report | 30 seconds | 2+ hours |
| Legal classification | Automatic (3-tier AI) | Requires lawyer |
| Evidence preservation | SHA-256 hash + archive.org | Screenshots (forgeable) |
| Tamper detection | Cryptographic hash chain | None |
| Platform coverage | Instagram, X, WhatsApp, TikTok | Manual per platform |
| Languages | DE, EN, TR, AR | Single language |
| Legal jurisdictions | DE, AT, CH, UK, FR | Single country |
| Report formats | NetzDG, Strafanzeige, BaFin, PDF, ZIP | Freeform text |

---

## Traction & Numbers

| Metric | Value |
|--------|-------|
| Backend tests | 366+ passing |
| API endpoints | 30+ |
| German laws covered | 7 StGB + NetzDG |
| Countries covered | 5 (DE, AT, CH, UK, FR) |
| Classifier languages | 4 (DE, EN, TR, AR) |
| Report formats | 6 (general, NetzDG, police, BaFin, PDF, ZIP) |
| Frontend components | 15+ React components |
| Phase 1-4 | Complete |

---

## Business Model

### Free forever (victim-facing)
- Document evidence, classify, export one report per case

### SafeVoice Pro (€0-9/month, sliding scale)
- Unlimited exports, pattern detection, PDF letterhead

### SafeVoice Institutional (€500-2,000/month)
- Police → structured digital intake portal
- Law firms → case management + evidence chain
- NGOs → client management + reporting
- Universities → student harassment response

### Revenue path
- Year 1: €50k-150k (grants + early institutional)
- Year 2: €500k-1.5M ARR (10-50 institutional clients)
- Year 3: €3M-8M ARR (DACH + UK, 200+ clients)

---

## What's Next (Phase 5)

- Bundestag evidence format standard
- EU Digital Services Act reference implementation
- Academic research API (anonymized)
- Digitale-Gewalt-Gesetz policy consultation
- Europol cross-border flagging

---

## Live API Explorer

All endpoints documented at: http://localhost:8000/docs

Key URLs for demo:
- Frontend: http://localhost:5173
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health
- Dashboard stats: http://localhost:8000/dashboard/stats
- Evidence standard: http://localhost:8000/policy/evidence-standard
- Research dataset: http://localhost:8000/policy/research-dataset
- Court package: http://localhost:8000/reports/case-002/court-package?lang=de

---

## Contact

SafeVoice — Digital justice. One report at a time.
