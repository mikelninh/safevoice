# SafeVoice — MVP Demo Script (3 minutes)

## Setup

```bash
# Terminal 1
cd backend && source venv/bin/activate && uvicorn app.main:app --reload

# Terminal 2
cd frontend && npm run dev
```

Open http://localhost:5173

---

## Demo (3 steps)

### Step 1: Classify text (1 min)

Go to http://localhost:5173/analyze

Paste:
```
Frauen wie du sollten die Klappe halten. Ich weiß wo du wohnst.
```

Click "Analysieren". Show:
- CRITICAL severity badge (red)
- Categories: Misogyny + Threat
- Laws: § 185 StGB, § 241 StGB, NetzDG § 3
- "Immediate action required" banner
- HateAid referral with phone number

**Say:** "From paste to legal classification in 3 seconds. No legal knowledge needed."

### Step 2: View a case (1 min)

Go to http://localhost:5173/cases

Open "Death threat following opinion piece". Show:
- Evidence items with severity badges
- Escalation pattern flag
- Onlinewache panel (select Berlin)
- Click "Bericht exportieren" → show NetzDG tab

**Say:** "Everything a lawyer or police officer needs, structured and ready to file."

### Step 3: API docs (1 min)

Open http://localhost:8000/docs

Show the endpoint list. Click on POST /analyze/text, hit "Try it out":
```json
{"text": "I will kill you and your family"}
```

Show the structured JSON response: severity, categories, laws, summaries in DE+EN.

**Say:** "The same AI classification is available as an API for partners — police, NGOs, law firms."

---

## If asked about the AI

- 3-tier classifier: Claude API (best accuracy) → transformer (offline) → regex (guaranteed fallback)
- System prompt engineered with legal expert persona + JSON schema enforcement
- Compared 4 prompting techniques — JSON schema approach won for consistency
- Supports German, English, Turkish, Arabic
- Never returns "analysis unavailable" — always falls back

## If asked about ethics

- Victim-centered: never minimizes threats, errs on side of protection
- "Not legal advice" disclaimer on every output
- Emergency delete: one tap, everything gone, no recovery — for victims in danger
- No tracking, no cookies, data stays on device
- Research API strips all PII before sharing
