# SafeVoice — Demo Script (3 minutes)

## Setup

```bash
# Terminal 1
cd backend && source venv/bin/activate && uvicorn app.main:app --reload

# Terminal 2
cd frontend && npm run dev
```

Open http://localhost:5173

---

## Step 1: Classify text (1 min)

Go to **Neuer Fall / New Case** (http://localhost:5173/analyze)

Paste:
```
Women like you should shut up and stay in the kitchen. I know where you live. Watch yourself.
```

Click **Analyze**. Show the result:
- Severity badge: CRITICAL (red)
- Categories: Misogyny + Threat
- Laws: § 185 StGB, § 241 StGB, NetzDG § 3
- Bilingual summary (DE + EN)

**Say:** "From paste to legal classification in 3 seconds. No legal knowledge required."

---

## Step 2: View a case (1 min)

Go to **Meine Fälle** (http://localhost:5173/cases)

Open **"Death threat following opinion piece"**. Show:
- Evidence items with severity badges
- Escalation pattern detected
- Click **Bericht exportieren** → NetzDG tab → ready-to-submit text

**Say:** "Everything structured for police or platforms. One click."

---

## Step 3: API docs (1 min)

Open http://localhost:8000/docs

Show the endpoints. Click **POST /analyze/text** → Try it out:
```json
{"text": "I will kill you and your family"}
```

Show the JSON response: severity, categories, laws, summaries.

**Say:** "Structured JSON output from the AI — this is the prompt engineering part."

---

## If asked about the AI

"The app has a regex classifier working for keyword-based detection in German and English. I'm currently working on integrating OpenAI GPT-4o-mini with prompt engineering — a system prompt that acts as a German legal expert, with structured JSON output so the response is always parseable. The integration is functional and I'm refining the prompts. Next after that is a HuggingFace transformer as a middle tier for offline use."

## If asked about the database

"6 tables. Users, cases, evidence items, classifications, categories, and laws. Evidence is separate from classification because evidence is a fact, classification is an AI interpretation — I can re-classify without touching the original evidence."

## If asked about evidence integrity

"The system hashes content with SHA-256 at capture time and stores UTC timestamps. This is built and working — I'm currently exploring the details of how cryptographic hashing ensures evidence hasn't been tampered with. It's important for German courts."
