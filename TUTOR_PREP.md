# SafeVoice — Tutor Prep (20th April)

Action items from Zisis Batzos (AI Lead), 27 March 2026.

---

## 1. DB Table Attributes: User Input vs AI-Populated

### users
| Attribute | Source |
|-----------|--------|
| email | **User input** |
| display_name | **User input** (optional) |
| lang | **User input** (de/en) |
| id, created_at, status | **System-generated** |

### cases
| Attribute | Source |
|-----------|--------|
| title | **System-generated** (from first evidence categories) |
| victim_context | **User input** (optional — "what happened?") |
| overall_severity | **AI-populated** (highest severity across all evidence) |
| status | **User input** (open → reported → resolved) |
| id, created_at, updated_at | **System-generated** |

### evidence_items
| Attribute | Source |
|-----------|--------|
| content_text | **User input** (pasted text or scraped from URL) |
| url | **User input** (optional link) |
| author_username | **User input** or **scraped** from URL |
| platform | **System-detected** from URL (instagram/x/web) |
| content_hash | **System-generated** (SHA-256 of content_text) |
| captured_at | **System-generated** (UTC timestamp) |
| archived_url | **System-generated** (archive.org submission) |
| id | **System-generated** |

### classifications
| Attribute | Source |
|-----------|--------|
| severity | **AI-populated** (low/medium/high/critical) |
| confidence | **AI-populated** (0.0 - 1.0) |
| requires_immediate_action | **AI-populated** (true/false) |
| summary | **AI-populated** (English) |
| summary_de | **AI-populated** (German) |
| potential_consequences | **AI-populated** (English) |
| potential_consequences_de | **AI-populated** (German) |
| id, evidence_id | **System-generated** |

### classification_categories
| Attribute | Source |
|-----------|--------|
| category | **AI-populated** (harassment, threat, misogyny, scam...) |

### classification_laws
| Attribute | Source |
|-----------|--------|
| law_paragraph | **AI-populated** (§ 185 StGB, § 241 StGB, NetzDG § 3...) |

### Summary
```
User provides:   email, language, text content, URL, victim context
System generates: IDs, timestamps, hashes, platform detection
AI populates:    severity, categories, laws, confidence, summaries, consequences
```

---

## 2. User Endpoints (CRUD)

```
POST   /auth/login          — create user (if new) + send magic link
                               Input: { "email": "user@example.com" }

POST   /auth/verify          — activate session
                               Input: { "token": "abc123..." }

GET    /auth/me              — read user profile
                               Auth: Bearer <session_token>

PUT    /auth/me              — update user profile
                               Input: { "display_name": "Maria", "lang": "en" }

DELETE /auth/me              — soft delete (7-day recovery)

DELETE /auth/me/emergency    — hard delete (immediate, no recovery)

POST   /auth/logout          — end session
```

**Design decision:** No passwords. Magic link only. Why:
- Victims are stressed — they forget passwords
- No password database to breach
- One-time use tokens (15 min expiry) are phishing-resistant

---

## 3. Case Endpoints (CRUD)

```
POST   /analyze/ingest       — CREATE evidence + classification → auto-creates case
                               Input: { "text": "...", "author_username": "...", "url": "..." }

POST   /analyze/url          — CREATE evidence from URL → scrape + classify
                               Input: { "url": "https://instagram.com/..." }

POST   /upload/screenshot    — CREATE evidence from image → OCR + classify
                               Input: multipart file upload (image/png, image/jpeg)

GET    /cases/               — READ all cases

GET    /cases/{id}           — READ single case with all evidence + classifications

GET    /reports/{id}         — READ generated report (text format)

GET    /reports/{id}/pdf     — READ generated report (PDF format)

DELETE /cases/{id}           — DELETE a case (not yet implemented — planned)
```

**Design decision:** Cases are created implicitly when evidence is ingested. The user never "creates a case" explicitly — they paste content, and the system structures it.

---

## 4. !!! THE AI FLOW !!!

### What is the INPUT?

Raw text from the user. Examples:
```
"Women like you should shut up and stay in the kitchen. I know where you live."
"Ich bringe dich um, du Schlampe"
"Guaranteed 30% monthly returns! Send Bitcoin to my wallet now!"
```

The text can arrive via:
- Direct paste (user copies a comment)
- URL scrape (we fetch the post caption from Instagram/X)
- Screenshot OCR (we extract text from an uploaded image)

By the time it reaches the classifier, it's always a string.

### What is the CONTEXT?

The system prompt provides the context — it tells the AI:
1. **Who you are:** "You are SafeVoice's legal classification engine"
2. **What to analyze:** "digital content (social media posts, DMs, comments)"
3. **What offenses to look for:** "harassment, threats, scams under German criminal law"
4. **The exact categories to use:** harassment, threat, death_threat, misogyny, scam, phishing...
5. **The exact laws to reference:** § 185, § 186, § 241, § 126a, § 263 StGB, NetzDG § 3
6. **Behavioral rules:** "Be victim-centered. Never minimise threats."
7. **The exact JSON output format** (structured output)

### What is the SYSTEM PROMPT?

```
You are SafeVoice's legal classification engine. You analyse digital content
(social media posts, DMs, comments) for harassment, threats, scams, and other
offenses under German criminal law.

Your job:
1. Classify the content into one or more categories
2. Assess severity (low / medium / high / critical)
3. Map to applicable German criminal law paragraphs
4. Provide a concise summary in BOTH English and German
5. Assess whether immediate action is needed

Categories (use value strings exactly):
- harassment, threat, death_threat, defamation, misogyny, body_shaming
- coordinated_attack, false_facts, sexual_harassment
- scam, phishing, investment_fraud, romance_scam, impersonation

Applicable German laws (use paragraph strings exactly):
- § 185 StGB (Beleidigung / Insult)
- § 186 StGB (Üble Nachrede / Defamation)
- § 241 StGB (Bedrohung / Threat)
- § 126a StGB (Strafbare Bedrohung / Criminal threat)
- § 263 StGB (Betrug / Fraud)
- § 263a StGB (Computerbetrug / Computer fraud)
- § 269 StGB (Fälschung beweiserheblicher Daten / Data falsification)
- NetzDG § 3 (Network Enforcement Act)

Respond with ONLY valid JSON in this exact schema:
{
  "severity": "low|medium|high|critical",
  "categories": ["category1", "category2"],
  "confidence": 0.0-1.0,
  "requires_immediate_action": true/false,
  "summary": "English summary",
  "summary_de": "German summary",
  "applicable_laws": ["§ 185 StGB", "NetzDG § 3"],
  "potential_consequences": "English consequences",
  "potential_consequences_de": "German consequences"
}

Be precise. Be victim-centered. When in doubt about severity, err on the
side of protecting the victim. Never minimise threats.
```

### Why this prompt works:
1. **Role assignment** — "You are SafeVoice's legal classification engine" (not a chatbot)
2. **Explicit categories** — AI can only use these exact strings (parseable)
3. **Explicit laws** — AI can only cite these exact paragraphs (verifiable)
4. **JSON schema enforcement** — "Respond with ONLY valid JSON in this exact schema"
5. **Behavioral guardrails** — "victim-centered", "never minimise threats"
6. **Bilingual output** — both summary and summary_de required in one call

---

## 5. Classification Endpoint Design

### The API call (classifier_llm.py):

```python
client = OpenAI(api_key=api_key)
response = client.chat.completions.create(
    model="gpt-4o-mini",
    temperature=0,           # Deterministic — same input → same output
    max_tokens=1024,
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Classify this content:\n\n{text}"},
    ],
)
```

**Key decisions:**
- `temperature=0` — legal classification must be deterministic, not creative
- `gpt-4o-mini` — good enough for classification, much cheaper than gpt-4o
- `max_tokens=1024` — enough for the JSON response, prevents waste

### 3-tier fallback:
```
classify(text):
    1. Try OpenAI GPT-4o-mini  → if API key set and call succeeds
    2. Try HuggingFace model   → if torch installed, works offline
    3. Use regex patterns      → always works, guaranteed fallback

    → NEVER returns "unavailable"
```

---

## 6. Parsing Structured Output

The AI returns raw JSON text. We parse it into a Pydantic model:

```python
# 1. Get raw response
raw = response.choices[0].message.content.strip()

# 2. Handle markdown code blocks (AI sometimes wraps in ```)
if raw.startswith("```"):
    raw = raw.split("\n", 1)[1]
    raw = raw.rsplit("```", 1)[0]

# 3. Parse JSON
data = json.loads(raw)

# 4. Map to typed Pydantic model
result = ClassificationResult(
    severity=SEVERITY_MAP[data["severity"]],        # "critical" → Severity.CRITICAL
    categories=[CATEGORY_MAP[c] for c in data["categories"]],  # ["threat"] → [Category.THREAT]
    confidence=data["confidence"],                   # 0.95
    requires_immediate_action=data["requires_immediate_action"],
    summary=data["summary"],
    summary_de=data["summary_de"],
    applicable_laws=[LAW_MAP[l] for l in data["applicable_laws"]],  # ["§ 241 StGB"] → [LAW_241]
    ...
)
```

**Why Pydantic?** Type safety. If the AI returns `"severity": "extreme"` (not in our enum), Pydantic catches it. We default to MEDIUM instead of crashing.

**Why not use OpenAI's native structured outputs?** We could (via `response_format`), but our approach works with ANY LLM (Claude, Gemini, local models). The JSON schema in the system prompt is more portable than vendor-specific features.

---

## Complete AI Flow Diagram

```
USER                          BACKEND                         OPENAI
  │                              │                               │
  │  paste text / URL / image    │                               │
  ├─────────────────────────────►│                               │
  │                              │  (if URL: scrape content)     │
  │                              │  (if image: OCR extract text) │
  │                              │                               │
  │                              │  system_prompt + user_text    │
  │                              ├──────────────────────────────►│
  │                              │                               │
  │                              │         JSON response         │
  │                              │◄──────────────────────────────┤
  │                              │                               │
  │                              │  parse JSON → Pydantic model  │
  │                              │  hash content (SHA-256)       │
  │                              │  timestamp (UTC)              │
  │                              │  store classification         │
  │                              │                               │
  │   severity + categories      │                               │
  │   + laws + summaries         │                               │
  │◄─────────────────────────────┤                               │
```

---

## Files that implement each action item

| Action item | File |
|-------------|------|
| DB tables (user vs AI) | `backend/app/models/evidence.py` + `backend/app/models/user.py` |
| User CRUD endpoints | `backend/app/routers/auth.py` |
| Case CRUD endpoints | `backend/app/routers/analyze.py` + `backend/app/routers/cases.py` |
| System prompt | `backend/app/services/classifier_llm.py` (line ~36: SYSTEM_PROMPT) |
| Classification endpoint | `backend/app/services/classifier_llm.py` (classify_with_llm) |
| Structured output parsing | `backend/app/services/classifier_llm.py` (_parse_result) |
| 3-tier fallback | `backend/app/services/classifier.py` (classify function) |
