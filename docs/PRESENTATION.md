# SafeVoice — Full Presentation

## Changing the Game in Digital Justice

---

## PART 1: THE CRISIS

### The Scale

- **Every 3 minutes**, someone in Germany is harassed online (HateAid, 2024)
- **78% of women** under 30 have experienced digital violence (EU FRA Survey)
- **90% goes unreported** — not because victims don't care, but because the system fails them
- **€50M+ in NetzDG fines** remain uncollected because reporting is too hard

### The Three Barriers

**Barrier 1: Legal Literacy**
```
Victim sees: "Ich bringe dich um, du Schlampe"
Victim thinks: "Is this even illegal?"
Reality: This is § 241 StGB (threat, 2 years) + § 185 StGB (insult, 1 year)
         + NetzDG violation (platform must remove in 24 hours)
```
Victims shouldn't need a law degree to report a crime.

**Barrier 2: Evidence Disappears**
```
Day 1: Threat posted on Instagram
Day 3: Victim decides to report
Day 4: Post deleted by perpetrator
Day 5: Police say "We need the original post"
```
Without timestamped, hashed, archived evidence — cases collapse.

**Barrier 3: Reporting Friction**
```
To file one NetzDG report:
1. Find the platform's NetzDG page (buried in settings)
2. Identify which law applies (requires legal knowledge)
3. Write a structured description (in legal German)
4. Repeat for each post
5. Wait 24h-7d for response
6. If no response: file with BNetzA (different form)
7. Separately: file police report (Onlinewache — different form per Bundesland)
8. Separately: contact HateAid for counseling (another form)

Total time: 3-8 hours per incident
Most people give up at step 1.
```

### Who Suffers Most

| Group | Digital violence rate | Reporting rate |
|-------|---------------------|----------------|
| Women in public life (journalists, politicians) | 73% | 18% |
| LGBTQ+ individuals | 64% | 12% |
| People of color in Germany | 58% | 9% |
| Women under 30 (general) | 52% | 15% |

The people who need protection most are the least likely to get it.

---

## PART 2: THE SOLUTION

### SafeVoice in One Sentence

> Paste a link. Get a legal classification. File every report. In 30 seconds.

### The Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  PASTE       │     │  CLASSIFY    │     │  DOCUMENT    │     │  REPORT      │
│              │     │              │     │              │     │              │
│ Instagram URL│────▶│ AI identifies│────▶│ SHA-256 hash │────▶│ NetzDG       │
│ X/Twitter URL│     │ § 185 StGB   │     │ UTC timestamp│     │ Strafanzeige │
│ WhatsApp shot│     │ § 241 StGB   │     │ archive.org  │     │ BaFin        │
│ Raw text     │     │ NetzDG § 3   │     │ Hash chain   │     │ PDF / ZIP    │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
     10 sec               3 sec               instant              1 click
```

**Total time: 30 seconds.** Not 3 hours. Not 8 hours. 30 seconds.

---

## PART 3: DESIGN PHILOSOPHY

### Principle 1: Victim-First, Always

Every decision starts with: **"Would a scared person at 2am use this?"**

**Safe Exit Button**
- Fixed bottom-right corner, always visible
- One tap → replaces entire browser history with Google weather
- Why: abusers monitor victim devices. A "Report Harassment" tab in browser history is dangerous.

**No Account Required**
- Full analysis → classification → PDF export — zero login
- Cases stored in browser localStorage
- Why: "What if they find my account?" is a real fear

**Trauma-Informed Language**
- NOT: "Report abuse" / "Submit evidence" / "File complaint"
- YES: "What happened to you is not okay" / "You have the right to fight back" / "You are not alone"
- Every string reviewed for emotional safety in both DE and EN

**HateAid Referral**
- Appears automatically for HIGH/CRITICAL severity
- Shows phone number directly (no extra clicks when panicking)
- Technology alone isn't enough. Humans matter.

### Principle 2: Evidence That Holds Up in Court

German courts require:
1. **Timestamp with timezone** — we use UTC with ISO 8601
2. **Content integrity proof** — SHA-256 hash at capture time
3. **Independent verification** — archive.org Wayback Machine backup
4. **Chain of custody** — cryptographic hash chain linking all evidence

```
Evidence #1                Evidence #2                Evidence #3
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│ content_hash: a │       │ content_hash: b │       │ content_hash: c │
│ prev_hash: genesis──────│ prev_hash: A   │───────│ prev_hash: B    │
│ chain_hash: A   │       │ chain_hash: B   │       │ chain_hash: C   │
│ sequence: 0     │       │ sequence: 1     │       │ sequence: 2     │
└─────────────────┘       └─────────────────┘       └─────────────────┘

Tamper with any item → chain breaks from that point forward
```

A lawyer can download the court package (ZIP), verify every hash, and present it as admissible evidence.

### Principle 3: Three Lines of Defense (Classifier)

No single AI is trustworthy enough for legal classification. We use three:

```
┌──────────────────────────────────────────────────────┐
│  TIER 1: Claude API                                  │
│  ✓ Understands sarcasm, indirect threats, context    │
│  ✓ Knows German criminal law nuances                 │
│  ✓ Writes bilingual summaries                        │
│  ✗ Requires API key, costs $0.003/call, 200ms        │
│  When: ANTHROPIC_API_KEY is set                      │
├──────────────────────────────────────────────────────┤
│  TIER 2: Transformer (toxic-comment-model)           │
│  ✓ Works offline, no API key                         │
│  ✓ Good multilingual toxicity detection              │
│  ✗ Gives score, not legal category                   │
│  When: torch installed, no API key                   │
├──────────────────────────────────────────────────────┤
│  TIER 3: Regex Rules                                 │
│  ✓ Always works, zero deps, instant                  │
│  ✓ DE, EN, Turkish, Arabic patterns                  │
│  ✗ No context understanding                          │
│  When: Always (guaranteed fallback)                  │
└──────────────────────────────────────────────────────┘

SafeVoice NEVER returns "analysis unavailable."
```

### Principle 4: International by Design

Not "built for Germany, translated later." Built for 5 legal systems from day 1.

| Country | Laws | Classifier | UI | Reports |
|---------|------|-----------|-----|---------|
| Germany | 8 (StGB + NetzDG) | Full (DE) | Full | Full |
| Austria | 6 (StGB AT) | Full (DE) | Full | Full |
| Switzerland | 6 (StGB CH) | Full (DE) | Full | Full |
| United Kingdom | 7 (OSA + CMA + etc.) | Full (EN) | Full | Full |
| France | 6 (CP + Loi Avia) | Via API | Full | Full |

Languages classified: German, English, Turkish, Arabic — the top 4 harassment languages in Germany.

### Principle 5: Institutions as Partners, Not Gatekeepers

```
TRADITIONAL MODEL                    SAFEVOICE MODEL

Victim → Police → "Fill out this     Victim → SafeVoice → structured
form" → "Come back with evidence"    case + evidence → Police receives
→ weeks of back-and-forth            ready-to-process intake

                                     Victim → SafeVoice → HateAid
                                     referral with full context
                                     → Counselor has everything

                                     NGO → Partner API → submit cases
                                     on behalf of clients
                                     → Track SLA deadlines
```

---

## PART 4: TECHNICAL DEEP DIVE

### Architecture

```
                    ┌─────────────────────────────┐
                    │         FRONTEND             │
                    │   React + TypeScript + PWA   │
                    │   6 pages, 15 components     │
                    │   DE/EN, mobile-first        │
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────▼───────────────┐
                    │         BACKEND               │
                    │   FastAPI + Python 3.12       │
                    │   14 routers, 20+ services    │
                    │   30+ API endpoints           │
                    └──────────────┬───────────────┘
                                   │
          ┌────────────┬───────────┼───────────┬────────────┐
          ▼            ▼           ▼           ▼            ▼
    ┌──────────┐ ┌──────────┐ ┌────────┐ ┌────────┐ ┌──────────┐
    │Classifier│ │ Scraper  │ │Evidence│ │Reports │ │ Partner  │
    │ 3-tier   │ │ IG/X/Web │ │ Hash + │ │ PDF +  │ │ API key  │
    │ DE/EN/   │ │ + OCR    │ │ Chain  │ │ ZIP +  │ │ + assign │
    │ TR/AR    │ │          │ │ + UTC  │ │ NetzDG │ │ + SLA    │
    └──────────┘ └──────────┘ └────────┘ └────────┘ └──────────┘
```

### Test Coverage

| Test suite | Tests | What it covers |
|-----------|-------|---------------|
| test_classifier.py | 33 | 4-language classification, all categories |
| test_scraper.py | 27 | Instagram, X, generic URL parsing |
| test_evidence.py | 10 | SHA-256 hashing, UTC timestamps |
| test_pdf.py | 9 | PDF generation, all report types |
| test_bafin.py | 9 | BaFin scam report generation |
| test_chain.py | 26 | Cryptographic evidence chain |
| test_sla.py | 19 | NetzDG deadline tracking |
| test_upload.py | 22 | Screenshot OCR, WhatsApp detection |
| test_auth.py | 20 | Magic link auth, deletion |
| test_phase3.py | 24 | Partner API, dashboard, court export |
| test_phase4.py | 20 | Legal AI, offender DB, platform submit |
| test_international.py | 28 | Austrian + Swiss law mapping |
| test_laws_uk_fr.py | 123 | UK + French law validation |
| test_policy.py | 42 | DSA, research API, Europol SIENA |
| **TOTAL** | **412+** | |

### Security Model

| Layer | Protection |
|-------|-----------|
| Transport | TLS (production) |
| Authentication | Magic link tokens (15min expiry), session tokens (30-day) |
| Authorization | API keys for partners, Bearer tokens for users |
| Data at rest | AES-256 encryption (production) |
| Evidence integrity | SHA-256 content hashing + hash chain |
| PII protection | Research API strips all identifying data |
| Deletion | 7-day soft delete + emergency instant delete |
| Legal compliance | DSGVO Art. 6/15-21, NetzDG § 3, TMG § 5 |

---

## PART 5: BUSINESS MODEL

### Revenue Streams

**Tier 1: Free Forever (Victims)**
- Document evidence
- Classify content
- Export one report per case
- HateAid + Onlinewache referral

**Tier 2: SafeVoice Pro (€0-9/month, sliding scale)**
- Unlimited exports
- Pattern detection across cases
- PDF with custom letterhead
- Priority classification (Claude API tier)

**Tier 3: SafeVoice Institutional (€500-2,000/month)**
- Police departments: structured digital intake, case assignment, jurisdiction routing
- Law firms: evidence chain verification, court export packages, client management
- NGOs (HateAid, Weisser Ring): client intake, NetzDG tracking, reporting
- Universities: student harassment response, anonymous reporting

### Revenue Projection

| Year | Users | Institutional clients | ARR |
|------|-------|----------------------|-----|
| Year 1 | 10,000 | 10-20 | €100-300k |
| Year 2 | 100,000 | 50-100 | €1-3M |
| Year 3 | 500,000 | 200-500 | €5-15M |

### Funding Path

1. **BMJV grant** (Bundesministerium der Justiz) — digital justice innovation
2. **EU DSA implementation fund** — reference platform
3. **Open Society Foundation** — digital rights
4. **Prototype Fund** (BMBF) — civic tech
5. **Non-dilutive first, equity later** — maintain mission alignment

---

## PART 6: COMPETITIVE LANDSCAPE

| | SafeVoice | HateAid | Onlinewache | NetzDG forms |
|---|---|---|---|---|
| Classification | AI (3-tier) | Manual (human) | None | None |
| Evidence preservation | Hash + archive | Screenshot | None | None |
| Legal mapping | Automatic (33 laws) | Manual | None | None |
| Report generation | Automatic (6 formats) | Manual template | Structured form | Platform-specific |
| Time to report | 30 seconds | Days (counseling) | 30 min | 15 min per platform |
| Languages | DE/EN/TR/AR | DE/EN | DE | DE/EN |
| Countries | 5 | 1 (DE) | 1 (DE per state) | 1 (per platform) |
| Cost | Free | Free | Free | Free |
| API for partners | Yes | No | No | No |

**SafeVoice doesn't replace HateAid** — it feeds into HateAid. Victims get instant documentation, then warm handoff to human counseling. We make HateAid's job easier.

---

## PART 7: WHAT'S NEXT

### Production Deployment (Week 1-2)
- PostgreSQL on Hetzner (DSGVO-compliant German hosting)
- Docker deployment with docker-compose
- SendGrid integration for magic link emails
- Monitoring + alerting (Sentry + Uptime Robot)

### First Partnerships (Month 1-3)
- HateAid: warm handoff integration, API access
- LKA Berlin Cybercrime: pilot for structured intake
- Universität Bielefeld: research collaboration, anonymized data

### Public Launch (Month 3-6)
- Product Hunt launch
- Press: taz, Süddeutsche, SPIEGEL (digital violence angle)
- Conference: re:publica, CCC, Netzpolitik

### Scale (Month 6-12)
- Austria + Switzerland launch
- UK launch (English-speaking market)
- Mobile optimization
- 100 institutional clients

---

## APPENDIX: LIVE DEMO CHECKLIST

### Before the demo
```bash
cd /Users/mikel/safevoice/backend && source venv/bin/activate && uvicorn app.main:app --reload
cd /Users/mikel/safevoice/frontend && npm run dev
```

### Demo URLs
- Frontend: http://localhost:5173
- API docs: http://localhost:8000/docs
- Dashboard: http://localhost:5173/dashboard
- Health: http://localhost:8000/health

### Demo scenarios (in order)

1. **"The Threat"** — paste: `Frauen wie du sollten die Klappe halten. Ich weiß wo du wohnst.`
   → Show: CRITICAL severity, § 241 + § 185, immediate action banner, HateAid referral

2. **"The URL"** — paste an Instagram/X URL
   → Show: auto-fetch badge, author extracted, comments classified

3. **"The Screenshot"** — upload a WhatsApp screenshot
   → Show: OCR extraction, WhatsApp detection, classification

4. **"The Package"** — open case-002, show evidence chain, download court ZIP
   → Show: hash verification, chain of evidence, 3 PDF reports in one ZIP

5. **"The API"** — curl the partner API
   → Show: API key auth, case submission, structured response

6. **"The Dashboard"** — open /dashboard
   → Show: severity bars, category breakdown, platform stats

7. **"The Research"** — curl /policy/research-dataset
   → Show: zero PII, fully anonymized, ready for academic research

### Key talking points per demo
- "30 seconds, not 3 hours"
- "No legal knowledge required"
- "Evidence that holds up in court"
- "Free forever for victims"
- "Built for Germany, expanding across Europe"
