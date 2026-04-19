# SafeVoice — Tutor Demo Script (English)

> **Meeting:** 20 April 2026 · Zwischencheck with Zisis Batzos · ~15 min total
> **Goal:** show progress on the 6 action items from 27 March. Demo, explain, discuss what's open.

---

## The 60-second opener — **memorize this**

> *"SafeVoice helps victims of digital harassment document an incident in 30 seconds and export a court-ready report. The flow is: paste text, a link, or a screenshot — the LLM classifies it under German criminal law — the evidence is hashed with SHA-256 and timestamped — and we generate a PDF ready for police or the platform.*
>
> *Since our last meeting, I've implemented all six action items you gave me: real SQLAlchemy database instead of in-memory, full user endpoints with magic-link auth, case endpoints, the AI flow fully documented, structured outputs via Pydantic, and I removed the 3-tier classifier fallback — I can explain why.*
>
> *Let me show you a quick demo, then walk through the six items, then we can discuss what's open for next week."*

Read it out loud 3 times tonight. Say it in your own words the 4th time.

---

## Before the meeting (10 min setup)

**Terminal 1:**
```bash
cd /Users/mikel/safevoice/backend && source venv/bin/activate && uvicorn app.main:app --reload
```

**Terminal 2:**
```bash
cd /Users/mikel/safevoice/frontend && npm run dev
```

**Browser tabs (in this order):**
1. `http://localhost:5173` — the app
2. `http://localhost:8000/docs` — API docs
3. `https://safevoice-production-0847.up.railway.app` — live fallback if localhost breaks

**Check before you join:**
- `OPENAI_API_KEY` loaded (try classifying once — you'll see if it works)
- Say the opener once out loud

---

## The 3-minute demo

### Step 1 — Paste + Classify (45 sec)

**Go to:** `http://localhost:5173/analyze`

**Paste:**
```
Women like you should shut up. I know where you live.
```

**Click:** `Analyze`

**What to say:**
> *"Three seconds. The LLM classified this as CRITICAL — misogyny plus threat. It mapped the text to § 185 StGB (insult), § 241 StGB (threat), and NetzDG § 3 (platform obligation). Both English and German summaries are generated in the same call. No legal knowledge required from the user."*

---

### Step 2 — Case + Report (1 min)

**Go to:** `/cases` → open any case

**Click:** `Export report`

**What to say:**
> *"Every piece of evidence is hashed with SHA-256 at capture time with a UTC timestamp. That hash chain is what makes the evidence admissible in a German court. The PDF is A4, bilingual, contains the classification, the original content, the hash, and the timestamp. Victims can send this directly to the police or to a platform's NetzDG inbox as a .eml attachment."*

---

### Step 3 — API docs + Structured Outputs (1 min)

**Go to:** `http://localhost:8000/docs`

**Click:** `POST /analyze/text` → `Try it out`

**Paste:**
```json
{ "text": "I will kill you" }
```

**Click:** `Execute`

**What to say:**
> *"This is the AI-engineering heart of the system. Notice the response is always a perfectly-shaped JSON — severity, categories, confidence, applicable_laws. I'm using OpenAI's Structured Outputs API with a Pydantic schema. The schema is enforced server-side — if the model tries to return something invalid, OpenAI refuses before we see it. This replaced my earlier manual `json.loads()` approach from last month."*

---

## Walk through the six action items — **1 sentence each**

If Zisis asks you to walk through the action items, give each one in a single crisp sentence. Don't over-explain.

1. **DB user vs AI vs system.** Users provide email, language, content, and optional victim-context. System generates IDs, hashes, timestamps. AI populates severity, categories, laws, summaries.

2. **User CRUD — 7 endpoints under `/auth`.** `POST /login`, `POST /verify`, `GET/PUT/DELETE /me`, `DELETE /me/emergency`, `POST /logout`. Magic link only, no passwords. Soft-delete has 7-day recovery window; emergency is immediate.

3. **Case CRUD.** Cases are created *implicitly* — the user never says "create a case." They paste content via `POST /analyze/ingest` and the system creates both evidence and case in one call. Read/export/PDF follow standard REST.

4. **AI flow — input, context, prompt.** Input is always a string (from paste, URL scrape, or OCR). Context lives in the system prompt: role, categories enum, laws enum, severity definitions, and the core rule "err on the side of the victim." User message is simply `"Classify this content: …"` plus the text.

5. **Classification endpoint.** `gpt-4o-mini`, `temperature=0` (legal classification must be deterministic), `max_tokens=1024`, and `response_format=LLMClassification` — a Pydantic model enforced by OpenAI Structured Outputs.

6. **Parse structured output.** `msg.parsed` returns a typed `LLMClassification` Pydantic instance, or `None` if OpenAI refused or failed to conform. No manual `json.loads()`, no markdown code-fence stripping, no try/except around malformed JSON.

---

## Questions Zisis might ask — **prepared answers**

Read these out loud tonight so your mouth knows the shape of the answer.

### "Tell me about your database."
> *"Real SQLAlchemy ORM with Alembic migrations. SQLite locally, Postgres on Railway in production. Eight tables — users, cases, evidence_items, classifications, categories, laws, and two junction tables. Categories and laws are seeded on startup so a fresh database has reference data. Orgs and org_members were added last week for NGO multi-tenancy."*

### "Why magic link and not passwords?"
> *"Three reasons. Victims are stressed and forget passwords. No password database means no breach risk. One-time tokens with 15-minute expiry are phishing-resistant. It's also a victim-centered choice — a password is one more thing you have to remember in a crisis."*

### "Why did you remove the 3-tier fallback?"
> *"A weak classification is worse than no classification. If a victim sees severity MEDIUM and § 185 on a real death threat, they might close the tab thinking it's minor — we caused harm. The regex tier couldn't handle obfuscation; the transformer under-classified German legal specifics. An honest 503 'please try again' is safer than a misleading result."*

### "What happens if OpenAI is down?"
> *"The API returns 503 Service Unavailable with a clear message. By design — no fallback. The user sees 'classifier unavailable, please retry' and nothing is persisted. We never emit a result we don't trust."*

### "How does Structured Outputs compare to manual JSON parsing?"
> *"Three wins. One: OpenAI validates my Pydantic schema server-side — invalid outputs are refused before I see them. Two: I get a typed Python object back, not a string to parse. Three: enum values are enforced — if the model tries to return a severity I don't define, the call is refused. The old code had defensive try/except around malformed JSON. The new code has `msg.parsed is None` and that's it."*

### "Why temperature = 0?"
> *"Legal classification must be deterministic. The same content today and tomorrow must produce the same result — otherwise we lose trust and court-admissibility. We give up creativity, we gain reproducibility. Classification is a mapping task, not a creative one."*

### "Why gpt-4o-mini over gpt-4o?"
> *"Fifteen times cheaper, about 90 percent of the accuracy for a classification task. Classification isn't a reasoning task where the extra IQ pays off. For a free-for-victims tool with viral risk on the cost side, mini is the right trade-off."*

### "What about GDPR?"
> *"Three mechanisms. Magic link means no password storage — no breach risk. Soft delete sets a `deleted_at` flag with 7-day recovery. Emergency delete is immediate, for cases where the perpetrator has access to the victim's device — this is the 'safe exit' pattern from victim-support software. Art. 20 data export is on the roadmap for next week — it's promised in the privacy policy but I haven't shipped the endpoint yet."*

### "What are you working on next week?"
> *"Three things: the Art. 20 GDPR export endpoint, a cleanup job that hard-deletes soft-deleted users after the 7-day window, and the first draft of the Prototype Fund application — €47,500 from BMBF-via-OKFN for 6 months of runway to move from pilot to NGO licensing."*

### "What would you change about your current architecture if you had infinite time?"
> *"I'd replace LocalStorage session tokens with HttpOnly cookies, ship a second LLM behind a feature flag as a cross-check for high-severity classifications, and build a bias-evaluation suite against a gold-standard set of 100 real cases. The bias work is the one I wish I could start tomorrow."*

---

## What's honestly open (be honest, Zisis respects it)

- **P1 this week:**
  - Set `VITE_OPERATOR_*` on Railway so Impressum/Datenschutz show real operator details
  - Ship the Art. 20 data-export endpoint
  - Add the 7-day cleanup job
- **P1 this month:**
  - Resend integration so magic link is actually emailed, not returned in the response
  - HttpOnly session cookie replacing LocalStorage
  - Bulk-import CSV integration tests

---

## If something breaks mid-demo

**Option A.** Railway live URL: `https://safevoice-production-0847.up.railway.app`

**Option B.** Tell the truth: *"Something's misbehaving locally — let me show you the live version."* It's not a failure; it's a normal engineering moment. Zisis will respect transparency over panic.

**Option C.** Pivot to architecture: open `TUTOR_PREP.md` or `CLAUDE.md` and walk through the code structure instead of the live app. You have 533 tests passing — the code works, the demo is optional.

---

## The close

> *"Next week I'll focus on the Art. 20 export endpoint, the cleanup job, and the first draft of the Prototype Fund application. Any questions, or anything you'd like me to prioritize differently?"*

**Then shut up.** Let him talk. That's where the real feedback comes from.

---

**Tonight's plan (90 min):**

1. 30 min — read this file twice, out loud.
2. 20 min — do the interactive quiz (`QUIZ.html` in this folder).
3. 30 min — run the demo locally once, from opener to close.
4. 10 min — sleep early.

You are ready.
