# SafeVoice — Product Roadmap

> "There is no way to peace, peace is the way."
> Digital justice. One report at a time.

---

## Mission

Make reporting digital harassment, threats and scams as easy as sharing a post.
Make evidence so structured that police, platforms and courts can act on it immediately.
Build the infrastructure Germany — and Europe — needs for digital justice.

---

## Phases

### PHASE 1 — Foundation (NOW)
*Goal: Solid, tested, deployable MVP. Every feature has a definition of done.*

- [x] 1.1 Core classifier — harassment, threats, misogyny, scams
- [x] 1.2 German law mapping — § 185, 186, 241, 126a, 263, 263a, 269 StGB + NetzDG
- [x] 1.3 Pattern detection — coordination, escalation, repeat offenders
- [x] 1.4 Report generator — NetzDG, Strafanzeige, general (DE/EN)
- [x] 1.5 React PWA — mobile-first, bilingual, share target
- [x] 1.6 Mock data — 4 realistic cases covering all categories
- [x] 1.7 Emotional UI — victim-first language, safe exit, progress
- [x] 1.8 Classifier upgrade — 3-tier: Claude API → transformer → regex
- [x] 1.9 Evidence archiving — SHA-256 hash + UTC timestamps + archive.org
- [x] 1.10 Persistent local storage — localStorage CRUD + legacy migration
- [x] 1.11 PDF export — court-ready A4 PDF, 3 report types, DE+EN

### PHASE 2 — Trust & Reach (Month 2-3)
*Goal: Real users. Real cases. Real reports filed.*

- [ ] 2.1 User accounts — encrypted, DSGVO-compliant, Hetzner-hosted
- [ ] 2.2 Instagram scraping — fetch public posts/comments by URL
- [ ] 2.3 X/Twitter support
- [ ] 2.4 WhatsApp evidence upload — screenshot + metadata extraction
- [ ] 2.5 Anonymous reporting mode — no account needed
- [ ] 2.6 HateAid integration — warm handoff to human counselor
- [ ] 2.7 BaFin reporting — structured scam reports to financial regulator
- [ ] 2.8 Onlinewache integration — pre-fill police report form
- [ ] 2.9 Android share target — native share sheet integration
- [ ] 2.10 Multilingual classifier — Turkish, Arabic (top DE harassment languages)

### PHASE 3 — Institutional (Month 4-6)
*Goal: Police, NGOs, law firms use SafeVoice as their intake tool.*

- [ ] 3.1 Receiver portal — structured case intake for police / NGOs
- [ ] 3.2 Case assignment — route cases to right jurisdiction / unit
- [ ] 3.3 API for partners — HateAid, Weißer Ring, law firms
- [ ] 3.4 Anonymized data dashboard — aggregate patterns for BKA / research
- [ ] 3.5 Evidence chain verification — cryptographic proof of integrity
- [ ] 3.6 Court export format — structured evidence package
- [ ] 3.7 Institutional accounts — police departments, universities, employers
- [ ] 3.8 SLA reporting — NetzDG 24h/7d deadline tracking

### PHASE 4 — Scale (Month 7-12)
*Goal: Standard tool for digital justice across DACH + UK.*

- [ ] 4.1 Austria — § 107 StGB, Cybermobbing-Gesetz
- [ ] 4.2 Switzerland — Art. 173 StGB
- [ ] 4.3 United Kingdom — Online Safety Act
- [ ] 4.4 France — Loi Avia, Pinel law
- [ ] 4.5 AI legal analysis — Claude API for nuanced legal reasoning
- [ ] 4.6 Serial offender database — cross-case pattern matching (anonymized)
- [ ] 4.7 Platform API integrations — direct NetzDG submission
- [ ] 4.8 Mobile apps — iOS + Android native

### PHASE 5 — Policy Impact (Year 2+)
*Goal: SafeVoice shapes digital violence law in Germany and EU.*

- [ ] 5.1 Bundestag partnership — evidence format standard
- [ ] 5.2 DSA implementation reference — EU-wide documentation standard
- [ ] 5.3 Academic research API — anonymized data for criminology research
- [ ] 5.4 Digitale-Gewalt-Gesetz input — formal consultation participation
- [ ] 5.5 Europol connection — cross-border serial offender flagging

---

## Monetisation

### Free forever (victim-facing)
- Document evidence
- Get legal classification
- Export one NetzDG + one police report per case
- Basic case management

### SafeVoice Pro (€0–9/month, sliding scale)
- Unlimited cases + exports
- Pattern detection across all your cases
- PDF with official letterhead
- Priority counselor referral

### SafeVoice Institutional (B2B, €500–2,000/month)
- Police departments → structured digital intake portal
- Law firms → case management + evidence chain
- NGOs → client case management + reporting
- Universities → student harassment response
- Employers / HR → workplace digital abuse

### Grant funding (non-dilutive)
- BMJV digital justice programs
- EU Digital Services Act implementation funds
- Bundeszentrale für politische Bildung
- Open Society Foundations

### Revenue targets
- Year 1: €50k–150k (grants + early institutional)
- Year 2: €500k–1.5M ARR (10–50 institutional clients)
- Year 3: €3M–8M ARR (DACH + UK, 200+ clients)

---

## Definition of Done (global)

Every feature is DONE when:
1. Code written and reviewed
2. Unit test passes
3. Integration test passes (real API call or UI interaction)
4. Works on mobile (375px viewport)
5. Works in both DE and EN
6. Committed to main with passing CI

---

## Current Phase 1 Progress

| Step | Status | DoD |
|------|--------|-----|
| 1.1 Core classifier | ✅ 13/13 tests | Regex engine, all categories |
| 1.2 Law mapping | ✅ | § 185/186/241/126a/263/263a/269 + NetzDG |
| 1.3 Pattern detection | ✅ | Coordination, escalation, repeat |
| 1.4 Report generator | ✅ | NetzDG + Strafanzeige + general |
| 1.5 React PWA | ✅ | Builds clean, bilingual |
| 1.6 Mock data | ✅ | 4 cases, all categories |
| 1.7 Emotional UI | ✅ | SafeExit, Banner, Progress, StatsBar |
| 1.8 Classifier upgrade | ✅ 23/23 tests | Claude API → transformer → regex |
| 1.9 Evidence archiving | ✅ 10/10 tests | SHA-256 + UTC + archive.org |
| 1.10 Local persistence | ✅ | localStorage CRUD + migration |
| 1.11 PDF export | ✅ 9/9 tests | A4 PDF, general/NetzDG/police, DE+EN |
