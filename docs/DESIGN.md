# SafeVoice — Architecture & Design Decisions

This document explains the key technical and product decisions behind SafeVoice, why they were made, and how they interact.

---

## 1. Why this exists

Digital harassment in Germany is a legal problem with a technical gap. The law exists (StGB, NetzDG), but victims face three barriers:

1. **They don't know which laws apply** — is it § 185 (insult) or § 241 (threat)?
2. **Evidence disappears** — posts get deleted, screenshots aren't legally strong
3. **Reporting is hard** — NetzDG forms are confusing, police reports are intimidating

SafeVoice closes all three gaps in one flow: paste → classify → report.

---

## 2. Victim-first design

Every design decision starts with: **"Would a scared person at 2am use this?"**

### Safe Exit button
- Fixed bottom-right, always visible
- One tap → replaces browser history with Google weather search
- Why: victims may be monitored by their abuser

### No account required
- Full flow works without signup, login, or email
- Cases stored in browser localStorage
- Why: accounts create fear ("what if they find my account?")

### Trauma-informed language
- "What happened to you is not okay" — not "Report abuse"
- "You have the right to fight back" — not "Submit evidence"
- German and English, formal-but-warm tone

### HateAid referral
- Appears automatically for HIGH/CRITICAL cases
- Shows phone number directly (no extra clicks when panicking)
- Why: technology alone isn't enough — humans matter

---

## 3. 3-tier classifier

We don't trust any single classifier. Three tiers with automatic fallback:

### Tier 1: Claude API
- **Why**: Best accuracy. Understands sarcasm, indirect threats, context, German legal nuance
- **When**: `ANTHROPIC_API_KEY` environment variable is set
- **Cost**: ~$0.003 per classification (Sonnet)
- **Prompt**: System prompt instructs it to respond victim-centered, never minimize threats

### Tier 2: Transformer model
- **Why**: Works offline, good toxicity detection, multilingual
- **Model**: `martin-ha/toxic-comment-model` (DistilBERT-based)
- **When**: `torch` + `transformers` installed, no API key needed
- **Limitation**: Gives toxicity score, not legal categories — we map scores to categories with heuristics

### Tier 3: Regex rules
- **Why**: Always works, zero dependencies, zero latency
- **Coverage**: DE, EN, Turkish, Arabic signal patterns
- **Limitation**: No context understanding — "I'll kill it at the gym" would match death threats
- **Role**: Guaranteed fallback so the app never fails

### Why not just use Claude API?
- Cost at scale (millions of classifications)
- Latency (200-500ms vs instant)
- Availability (API outages)
- Privacy (some users don't want text sent to an API)

### Why not just use the transformer?
- It gives toxicity scores, not legal classification
- It can't reason about which specific German law applies
- It can't write nuanced summaries in both DE and EN

### Why keep regex at all?
- It's the only tier that works with zero network, zero GPU, zero cost
- It catches obvious patterns (death threats, slurs) reliably
- It's the safety net — SafeVoice must never return "analysis unavailable"

---

## 4. Evidence integrity

Evidence must be tamper-proof for courts. Three mechanisms:

### SHA-256 content hashing
- Every evidence item gets `sha256:` + hex digest at capture time
- Deterministic: same content always produces same hash
- Verification function confirms integrity at any time

### UTC timestamps with timezone
- Legal requirement in Germany: evidence must have timezone-aware timestamps
- We use `datetime.now(timezone.utc)` — never naive datetimes
- ISO 8601 format for interoperability

### Hash chain
- Each evidence item's chain_hash = SHA-256(content_hash + previous_hash + sequence_number)
- First item uses "genesis" as previous_hash
- Tampering with any item breaks the chain from that point forward
- Inspired by blockchain, but simpler — no distributed consensus needed

### archive.org integration
- Submits URL to Wayback Machine for independent third-party archival
- Non-blocking: failure doesn't stop the analysis flow
- Provides a URL that proves the content existed at capture time

---

## 5. German law mapping

We map to 7 StGB paragraphs + NetzDG. Each law object contains:

- Paragraph number and title (DE + EN)
- Description of the offense (DE + EN)
- Maximum penalty
- Specific reason this law applies to the content (DE + EN)

### Why these specific laws?
- § 185 (Insult): covers most online harassment
- § 186 (Defamation): false factual claims
- § 241 (Threat): threats of harm
- § 126a (Criminal threat): death threats, serious threats
- § 263 (Fraud): scams, investment fraud
- § 263a (Computer fraud): digital-specific fraud
- § 269 (Data falsification): fake profiles, impersonation
- NetzDG § 3: platform removal obligation (always applies to social media)

### Why NetzDG is always included
Instagram and X have >2M German users → NetzDG applies. Every report automatically includes NetzDG as an applicable framework with the correct deadline (24h for clearly illegal, 7d for other illegal content).

---

## 6. Report generation

Three report types, each optimized for its audience:

### NetzDG report
- Addressed to the platform's legal department
- References specific NetzDG obligations
- Includes removal deadline
- Lists all evidence with archive links
- Formal German letter format

### Police report (Strafanzeige)
- Template for Onlinewache (online police report)
- Structured: Sachverhalt, Tatzeit, Tatort, Beweismittel
- References specific StGB paragraphs
- Includes what to bring to the police station
- Onlinewache URLs for all 16 Bundeslaender

### BaFin report
- Only generated for scam/fraud cases
- Extracts financial indicators: wallet addresses, amounts, fake platform names
- Formatted for the financial regulator's intake process

### Court export package
- ZIP file containing:
  - PDF reports (all three types)
  - Individual evidence text files
  - JSON manifest with structured metadata
  - Hash verification report
  - Chain of evidence timeline
  - README explaining the package

---

## 7. Social media scraping

### Why scrape instead of using APIs?
- Instagram's API requires business account approval (weeks)
- X's API costs $100+/month
- Victims need help NOW, not after API approval
- Public content is publicly accessible — we just parse what's already visible

### How it works
1. Detect platform from URL (regex on domain)
2. Fetch page with mobile User-Agent (mobile pages have simpler HTML)
3. Extract from `og:` meta tags (most reliable), `twitter:` meta, JSON-LD
4. Parse author, content, timestamp, comments
5. Fallback: generic og:description extraction for unknown platforms

### Limitations
- Private posts/accounts can't be scraped
- Platforms may block automated requests
- Comments only available if embedded in JSON-LD (Instagram does this for popular posts)

---

## 8. Frontend decisions

### Why React PWA (not native app)?
- Installable on Android via "Add to Home Screen"
- No app store approval needed (faster deployment)
- Share target integration for receiving URLs/text from other apps
- Works on any device with a browser

### Why Tailwind CSS?
- Rapid prototyping — victim-facing UI changes frequently based on feedback
- Dark theme (slate-900) — less intimidating than bright white
- Indigo accent color — conveys trust without being cold

### Why localStorage instead of a database?
- Phase 1-3 decision: no server-side storage means no data breach risk
- Cases stay on the victim's device
- Migration path: localStorage → encrypted server storage in Phase 4
- Legacy migration built in for when we transition

### Why bilingual from day 1?
- Many harassment victims in Germany are not native German speakers
- Legal terms need precise translation
- 190+ translation strings in i18n/index.ts
- Classifier works in DE, EN, Turkish, Arabic

---

## 9. Institutional architecture

### Partner API
- API key authentication via `X-API-Key` header
- Keys are `sv_` + 32 bytes of `secrets.token_urlsafe`
- Organizations have types: police, NGO, law firm, university, employer
- Members have roles: admin, analyst, viewer

### Case assignment
- Cases can be assigned to organizations with jurisdiction + unit type
- Status flow: assigned → in_review → resolved/declined
- Auto-suggest jurisdiction based on Bundesland

### Anonymized dashboard
- Aggregate stats only — no PII, no individual case details
- Category distribution, severity distribution, platform breakdown
- Designed for BKA statistical analysis and academic research

### SLA tracking
- NetzDG mandates removal deadlines: 24h (clearly illegal) or 7d (other)
- SLA records track: reported → acknowledged → removed/expired
- Dashboard shows compliance rate and average removal time

---

## 10. What's NOT built yet (and why)

### User accounts (2.1)
- Deferred because it needs PostgreSQL, auth system, encryption at rest
- The app works fully without accounts — adding them is additive, not blocking
- Will be built alongside institutional accounts in production deployment

### Real-time Instagram/X scraping
- Current scraper fetches public page HTML — works for most posts
- Some pages require JavaScript rendering (Playwright/Puppeteer)
- Will add headless browser for JS-heavy pages when needed

### Database
- Everything is in-memory (mock data + partner store + SLA records)
- Production: PostgreSQL on Hetzner (DSGVO-compliant, German hosting)
- Migration path is clean — all services use Pydantic models, just swap storage layer

### CI/CD
- No pipeline yet — tests run locally
- Plan: GitHub Actions with pytest + tsc + build on every PR

---

## 11. Security considerations

### What we protect
- Victim data stays on their device (localStorage, not server)
- No analytics, no tracking cookies, no third-party scripts
- Evidence hashes prove integrity without storing content server-side

### What we don't protect yet
- localStorage is not encrypted (browser-level security only)
- Partner API keys are in-memory (production needs encrypted storage)
- No rate limiting on API endpoints yet

### DSGVO compliance
- No personal data collected without consent
- No data leaves Germany (Hetzner hosting planned)
- Right to deletion: cases can be deleted from localStorage
- Anonymized dashboard never exposes individual case data

---

## 12. User accounts & authentication

### Magic link auth (no passwords)
- User enters email → receives a login link (15-minute expiry)
- Clicking the link creates a 30-day session
- No passwords to leak, breach, or brute-force
- Email is the only identifier — minimal PII

### Why NOT passwords?
- Victims are stressed — they forget passwords
- Password resets create another attack surface
- Magic links are phishing-resistant (one-time use, short expiry)
- Simpler UX: one field, one click

### Why NOT OAuth (Google/Facebook login)?
- Victims may be harassed on those platforms — logging in via the abuser's platform feels unsafe
- Third-party auth means data flows through Google/Facebook
- We want zero dependency on platforms we're helping people report

### Database strategy: PostgreSQL + SQLite
- SQLite for development (zero setup, file-based)
- PostgreSQL for production (Hetzner, German hosting, DSGVO)
- Repository pattern: same code, swappable storage layer

### Encryption: server-side at rest (AES-256)
- NOT full E2E — because institutional features require server-side access
- Protects against: database theft, hosting provider access, unauthorized DB access
- Allows: legitimate law enforcement cooperation (with warrant), data recovery, pattern analysis
- Transparent to users: "Your cases are encrypted. Only you and orgs you share with can access them."

### Deletion model
| Action | What happens | Recovery? |
|--------|-------------|-----------|
| Delete case | Hidden immediately, hard-deleted in 7 days | Yes, within 7 days |
| Delete account | Soft delete, hard-deleted in 7 days | Yes, within 7 days |
| Emergency delete | **Immediate hard delete. Everything gone.** | No. By design. |
| DSGVO erasure request | Hard delete within 72 hours | No |

Emergency delete exists because a victim may discover their abuser found SafeVoice. One tap, everything gone, no trace.

---

## 13. Tech stack summary

| Layer | Technology | Why |
|-------|-----------|-----|
| Backend | Python + FastAPI | Fast, typed, auto-generated OpenAPI docs |
| Frontend | React + TypeScript + Vite | Type safety, fast builds, PWA support |
| Styling | Tailwind CSS | Rapid iteration, dark theme, responsive |
| PDF | ReportLab | Pure Python, no external dependencies |
| OCR | Tesseract (via pytesseract) | Open source, supports German + English |
| AI - Tier 1 | Claude API (Anthropic) | Best accuracy for legal classification |
| AI - Tier 2 | HuggingFace Transformers | Offline multilingual toxicity detection |
| Hashing | SHA-256 (hashlib) | Standard, fast, cryptographically secure |
| HTTP | httpx | Async-capable, modern Python HTTP client |
| PWA | vite-plugin-pwa | Service worker, installability, share target |
