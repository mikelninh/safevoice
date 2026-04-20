# SafeVoice — Tutor Demo Script

Meeting: 20 April 2026 · Zwischencheck with Zisis Batzos · about 15 minutes total. Goal: show the work, walk the six action items from 27 March, discuss what is open.

This document is the playbook for the live demo. The study reference is `MEETING_20_APR.md`. The self-test is `QUIZ.html`.

---

## 60-second opener

Read this out loud tonight. Say it in your own words the fourth time.

> SafeVoice helps victims of digital harassment document an incident in 30 seconds and export a court-ready report. The flow is: paste text, a link, or a screenshot — the LLM classifies it under German criminal law — the evidence is hashed with SHA-256 and timestamped — and we generate a PDF ready for the police or the platform.
>
> Since our last meeting, I've implemented the six action items you gave me: real SQLAlchemy database instead of in-memory, user endpoints with magic-link auth, case endpoints, the AI flow documented, structured outputs via Pydantic, and I removed the 3-tier classifier fallback. I'll explain why.
>
> Let me show a short demo, then walk the six items, then we can discuss what is open for next week.

---

## Setup, 10 minutes before the meeting

Terminal 1:
```bash
cd /Users/mikel/safevoice/backend && source venv/bin/activate && uvicorn app.main:app --reload
```

Terminal 2:
```bash
cd /Users/mikel/safevoice/frontend && npm run dev
```

Browser tabs, in this order:
1. `http://localhost:5173` — the app
2. `http://localhost:8000/docs` — API docs
3. `https://safevoice-production-0847.up.railway.app` — live fallback

Final check: `OPENAI_API_KEY` is loaded. Classify once to confirm.

---

## The 3-minute demo

### Step 1 · Paste and classify (45s)

Navigate: `http://localhost:5173/analyze`

Paste:
```
Women like you should shut up. I know where you live.
```

Click `Analyze`.

Say:
> Three seconds. The LLM classified this as CRITICAL — misogyny plus threat. It mapped the text to § 185 StGB (insult), § 241 StGB (threat), and NetzDG § 3 (platform obligation). English and German summaries are generated in the same call. No legal knowledge required from the user.

### Step 2 · Case and report (60s)

Navigate: `/cases` → open any case → `Export report`.

Say:
> Every piece of evidence is hashed with SHA-256 at capture time with a UTC timestamp. That hash chain is what makes the evidence admissible in a German court. The PDF is A4, bilingual, and contains the classification, the original content, the hash, and the timestamp. Victims can send it directly to the police or to a platform's NetzDG inbox as an .eml attachment.

### Step 3 · API docs and Structured Outputs (60s)

Navigate: `http://localhost:8000/docs` → `POST /analyze/text` → `Try it out`.

Paste:
```json
{ "text": "I will kill you" }
```

Click `Execute`.

Say:
> This is the AI-engineering layer. The response is always a shape-conformant JSON — severity, categories, confidence, applicable_laws. I use OpenAI's Structured Outputs API with a Pydantic schema. The schema is enforced server-side — if the model tries to return something invalid, OpenAI refuses before we see it. This replaced the earlier manual `json.loads()` approach.

---

## Walk the six action items — one sentence each

1. **DB input vs AI vs system.** Users provide email, language, content, optional victim-context. The system generates IDs, hashes, timestamps. The AI populates severity, categories, laws, summaries.

2. **User CRUD — seven endpoints under `/auth`.** `POST /login`, `POST /verify`, `GET/PUT/DELETE /me`, `DELETE /me/emergency`, `POST /logout`. Magic link only, no passwords. Soft delete has a 7-day recovery window; emergency delete is immediate.

3. **Case CRUD.** Cases are created implicitly — the user pastes content via `POST /analyze/ingest` and the system creates both evidence and case in one call. Read, export, and PDF follow standard REST.

4. **AI flow — input, context, prompt.** The classifier path has no RAG — input is always a string, context is the whole system prompt (role, categories enum, laws enum, severity definitions, "err on the side of the victim"), user message is `"Klassifiziere diesen Inhalt:\n\n{text}"`. The second layer, `services/legal_ai.py`, DOES use RAG: it retrieves all evidence in a case from the DB, structures them as context, and sends to Claude for aggregate legal analysis. Two layers, two jobs.

5. **Classification endpoint.** `gpt-4o-mini`, `temperature=0` for determinism, `max_tokens=1024`, `response_format=LLMClassification` — a Pydantic model enforced by Structured Outputs.

6. **Parse structured output.** `msg.parsed` returns a typed `LLMClassification` instance or `None` if OpenAI refused or failed to conform. No manual `json.loads()`, no code-fence stripping, no try/except around malformed JSON.

---

## Questions Zisis may ask, prepared answers

### "Tell me about your database."
> Real SQLAlchemy ORM with Alembic migrations. SQLite locally, Postgres on Railway in production. Eight tables — users, cases, evidence_items, classifications, categories, laws, and two junction tables. Categories and laws are seeded on startup. Orgs and org_members were added last week for NGO multi-tenancy.

### "Why magic link and not passwords?"
> Three reasons. Victims under stress forget passwords. No password database means no breach risk. One-time tokens with 15-minute expiry are phishing-resistant. It's also a victim-centred choice — a password is one more thing to remember in a crisis.

### "Why did you remove the 3-tier fallback?"
> A weak classification is worse than no classification. If a victim sees severity MEDIUM on a real death threat, they might close the tab thinking it's minor — harm we caused. The regex tier couldn't handle obfuscation; the transformer under-classified German legal specifics. An honest 503 "please try again" is safer than a misleading result.

### "What happens if OpenAI is down?"
> The API returns 503 Service Unavailable. By design — no fallback. The user sees "classifier unavailable, please retry" and nothing is persisted.

### "Structured Outputs versus manual JSON parsing?"
> Three wins. OpenAI validates my Pydantic schema server-side — invalid outputs refused before I see them. I get a typed Python object back, not a string to parse. Enum values are enforced — an invented severity is refused. The old code had defensive try/except around malformed JSON. The new code checks `msg.parsed is None` and returns.

### "Why temperature = 0?"
> Legal classification must be deterministic. Same content today and tomorrow must produce the same result — otherwise we lose trust and court-admissibility. We give up creativity, we gain reproducibility. Classification is a mapping task, not a creative one.

### "Why gpt-4o-mini over gpt-4o?"
> ~15× cheaper, ~90% of the accuracy on classification tasks. Classification isn't a reasoning task where the extra capacity of gpt-4o pays off. For a free-for-victims tool with viral-cost risk, mini is the right trade-off.

### "What about GDPR?"
> Three mechanisms. Magic link means no password storage, no breach risk. Soft delete sets `deleted_at` with a 7-day recovery window. Emergency delete is immediate — the Safe-Exit pattern, for cases where the perpetrator has access to the victim's device. Art. 20 data export is promised in the privacy policy; the endpoint is on next week's list.

### "What are you working on next week?"
> Three things. The Art. 20 GDPR export endpoint. A cleanup job that hard-deletes soft-deleted users after the 7-day window. And the first draft of the Prototype Fund application — €47,500 from BMBF via OKFN for 6 months of runway to move from pilot to NGO licensing.

### "What would you change with infinite time?"
> Replace LocalStorage session tokens with HttpOnly cookies. Ship a second LLM behind a feature flag as a cross-check for high-severity classifications. Build a bias-evaluation suite against a gold-standard set of 100 real cases. The bias work is what I'd start first.

---

## What is honestly open

**This week:**
- Set `VITE_OPERATOR_*` on Railway so Impressum and Datenschutz show real operator details instead of "— nicht konfiguriert —".
- Ship the Art. 20 data-export endpoint.
- Add the 7-day cleanup job.

**This month:**
- Resend integration for magic-link email.
- HttpOnly session cookie replacing LocalStorage.
- Bulk-import CSV integration tests.

---

## If something breaks during the demo

- Fall back to the live Railway URL: `https://safevoice-production-0847.up.railway.app`.
- Name it honestly: "Something is misbehaving locally — let me show you the live version." Not a failure, a normal engineering moment.
- If both break, walk the architecture in `TUTOR_PREP.md` or `CLAUDE.md`. 533 tests pass — the code works, the demo is optional.

---

## The close

> Next week I'll focus on the Art. 20 export endpoint, the cleanup job, and the first draft of the Prototype Fund application. Any questions, or anything you'd like me to prioritise differently?

Then stop talking. Let him answer.

---

## Tonight, 90 minutes

1. 30 min — read `MEETING_20_APR.md` and this file, twice, out loud.
2. 20 min — take the quiz in `QUIZ.html`.
3. 30 min — run the demo locally, opener to close.
4. 10 min — sleep.
