# Tutor Meeting — 20 April 2026

Zwischencheck with Zisis Batzos. Six action items from 27 March, all implemented. This sheet is the study reference — what you need in your head so you can answer any question. The live demo script lives in `DEMO_EN.md`. The quiz is `QUIZ.html`.

Language note: Zisis is English-speaking, so everything here is in English. Practise answering in English out loud.

---

## Meeting shape

- Zwischencheck — a checkpoint, not a final. The final presentation is 29 May.
- Goal: show the work, be honest about what is open, ask for direction.
- Format: 60-second opener → 3-minute demo → walk the six action items → Q&A → next week's plan.

---

## Topic A · Database

Real SQLAlchemy ORM with Alembic migrations. SQLite locally (`safevoice.db`), Postgres in production via Railway's `DATABASE_URL`. The file is `backend/app/database.py`. Categories and laws are seeded on startup.

### The eight tables

| Table | Purpose | Key fields |
|---|---|---|
| `users` | Who documents | email (unique), language, created_at, deleted_at |
| `cases` | One incident, groups evidence | user_id, org_id, assigned_to, status, overall_severity |
| `evidence_items` | One piece of content | case_id, raw_content, content_hash, hash_chain_previous |
| `classifications` | AI output per evidence | evidence_item_id, severity, confidence, summary, summary_de |
| `categories` | 15 reference values | name, name_de |
| `laws` | 11 German paragraphs | code, section, name, max_penalty |
| `classification_categories` | Junction, many-to-many | classification_id + category_id |
| `classification_laws` | Junction, many-to-many | classification_id + law_id |

Plus multi-tenancy tables added 12 April:
- `orgs` — NGO partners (HateAid-style intake).
- `org_members` — user-to-org with role (owner / admin / caseworker / viewer).

### Likely questions

**"Evidence and classification — what's the relationship?"**

One-to-one, separated by purpose. Evidence is a fact: the text was posted, the hash and timestamp prove it. Classification is an interpretation: the LLM thinks it's a threat. Keeping them apart lets us re-classify without touching the original evidence — important for court admissibility.

**"Why are categories and laws separate tables?"**

A single classification can match many categories and many laws. A comment can be misogyny and a threat at once — triggering § 185 and § 241 at once. Junction tables are the clean many-to-many shape. It also lets me maintain reference data centrally; `seed_categories_and_laws()` runs on startup.

**"What happens on a fresh deploy with an empty database?"**

The Docker entrypoint does three things in order: `Base.metadata.create_all()` for the base tables, `alembic upgrade head` for any migrations, then `seed_categories_and_laws()`. A fresh Postgres gets 11 laws and 15 categories immediately.

---

## Topic B · User authentication

### Design decision: magic link, no passwords

Three reasons:
1. Victims under stress forget passwords.
2. No password database = no breach risk.
3. One-time tokens with 15-minute expiry are phishing-resistant.

### The flow

```
1. User enters email              POST /auth/login { "email": "…" }
2. Server creates magic link      Token (UUID), 15-min lifetime
3. Token sent via email           MVP returns it directly in the response
4. User clicks the link           POST /auth/verify { "token": "…" }
5. Server validates the token     Returns session token (30-day lifetime)
6. Frontend stores the session    Authorization: Bearer <session_token>
7. Subsequent requests use it     e.g. GET /auth/me
```

### The seven endpoints

```
POST   /auth/login            Request magic link
POST   /auth/verify           Exchange magic link for session
GET    /auth/me               Read profile
PUT    /auth/me               Update display_name, lang
DELETE /auth/me               Soft delete with 7-day recovery
DELETE /auth/me/emergency     Hard delete, immediate, no recovery
POST   /auth/logout           End session
```

### Files

- `routers/auth.py` — endpoints
- `services/auth.py` — magic-link generation, sessions, soft/hard delete
- `database.py` — the `User` ORM model with `deleted_at`

### Likely questions

**"How is this GDPR-compliant?"**

Three mechanisms. Magic link means no password storage, so no breach risk. Soft delete sets `deleted_at` with a 7-day recovery window. Emergency delete is immediate — the Safe-Exit pattern from victim-support software, for cases where the perpetrator has access to the victim's device.

**"What makes the session secure?"**

Session tokens are UUIDs in the database, not JWTs, with an expiry timestamp. `_require_user()` in `routers/auth.py` extracts the Bearer token, validates against the DB, returns 401 when expired. Tokens currently live in LocalStorage — that's a P1 to move to an HttpOnly cookie.

**"How would you harden this for production?"**

Three steps. HttpOnly + SameSite=Strict + Secure cookie replacing LocalStorage. Resend-or-equivalent email delivery instead of returning the token directly. Rate-limit on `/auth/login` to prevent enumeration. All on next week's list.

---

## Topic C · Endpoint design

### Principles

1. Flat resource paths — `/cases`, `/evidence`, `/analyze/text`. No `/users/{id}/cases/{id}/evidence` nesting.
2. HTTP verb matches CRUD intent — POST create, GET read, PUT update, DELETE delete.
3. Cases are created implicitly. The user never says "create a case" — they paste content, the system structures it.
4. Stateless analyze — `POST /analyze/text` returns a classification without persisting. Good for testing, demos, API probing.
5. Centralised auth — every protected endpoint reads `Authorization: Bearer <token>` through the same `_require_user()` helper.

### The eight MVP endpoints

```
GET  /health                  Health check + active classifier tier
POST /analyze/text            Classify statelessly
POST /analyze/ingest          Classify and persist → evidence + case
POST /analyze/url             Scrape Instagram/X, then classify
GET  /cases/                  List the user's cases
GET  /cases/{id}              Case detail with evidence and classifications
GET  /reports/{id}            Text report (general / netzdg / police)
GET  /reports/{id}/pdf        PDF download (court-ready A4)
```

Behind these, 30+ further endpoints (auth, orgs, partners, dashboard, SLA, legal AI, policy export) — available on request in the demo.

### Likely questions

**"Why POST for analyze and not GET?"**

Two reasons. POST signals "create" — even a stateless classification is a new resource. And text content can exceed 10,000 characters, while URL query strings top out near 2 KB.

**"How do you structure errors?"**

FastAPI raises `HTTPException(status_code=…, detail=…)`. 400 for invalid input, 401 for missing or invalid token, 403 for missing rights, 404 for not found, 503 when the classifier is unreachable — by design, no fallback. Clients always receive `{ "detail": "…" }` — one consistent format.

---

## Topic D · The AI flow

Zisis's core question from 27 March was "design the AI flow." Work through the five layers.

### 1. Input

Always a string. It can arrive three ways — direct paste, URL scrape, or OCR from a screenshot — but by the time `classify()` is called, it is a string. One input format, one classification path.

### 2. Context — and where RAG fits

The system has **two AI layers**, and the answer to "do you use RAG?" differs by layer.

**The classifier (`/analyze/*`)** — no RAG. The context lives entirely in the system prompt: who the model is, what it analyses, which law applies, which categories are valid, which paragraphs it may cite, how to handle obfuscation, how severity is defined. System prompt + user text, one turn, structured out.

**The legal-analysis layer (`services/legal_ai.py`)** — this *is* RAG. Triggered after a case has multiple evidence items. The function `analyze_case_legally(case)` does:

1. **Retrieve** — pulls every evidence item for the case from the DB, plus each item's classification (severity, categories, applicable laws).
2. **Augment** — structures them into a context block *("Evidence (N items): …")* inside a prompt.
3. **Generate** — sends to Claude (Anthropic) for aggregate legal reasoning across the whole case: strategy, precedents, cross-references, risk assessment for the victim.

Two jobs, two layers:

| Layer | Job | RAG? | Model |
|---|---|---|---|
| Classifier | One piece of content → severity, categories, laws | No | gpt-4o-mini (structured outputs) |
| Legal AI | Whole case → strategy + precedents + recommendations | **Yes** | Claude Sonnet (JSON) |

This is the Week 9–10 deliverable in `COURSE_SUBMISSION.md`: *"Applied RAG pattern: case evidence as retrieval context."*

### 3. The system prompt

File `backend/app/services/classifier_llm_v2.py`, lines 130–147. The prompt is in German — this measurably improves classification of German content because the model stays in the German legal register.

```
Du bist SafeVoice — ein juristischer Klassifikator für digitale Gewalt
in Deutschland.

Du analysierst Texte aus sozialen Medien (Kommentare, DMs, Posts) und
klassifizierst sie nach deutschem Strafrecht.

WICHTIG:
- Verstehe Tippfehler, Slang, absichtliche Verschleierung
  (z.B. "f0tze", "stirbt" statt "stirb")
- Wenn unklar: im Zweifel FÜR das Opfer entscheiden (höhere Severity)
- Eine Drohung ist eine Drohung, auch wenn sie indirekt formuliert ist
- Beachte den Gesamtkontext, nicht einzelne Wörter

Gib mindestens eine Kategorie an (im Zweifel: harassment).
NetzDG § 3 gilt IMMER bei Social Media Inhalten — füge es zu
applicable_laws hinzu.

SEVERITY:
- low: Grenzwertig, Verstoß gegen Nutzungsbedingungen möglich
- medium: Wahrscheinlicher Rechtsverstoß
- high: Klarer Rechtsverstoß, Anzeige empfohlen
- critical: Schwere Straftat, sofortige Anzeige + Beweissicherung
```

Why it works: role assignment ("legal classifier", not chatbot); behavioural rule ("err on the side of the victim" favours false positives over false negatives, which is victim-safe); invariant ("NetzDG § 3 always applies" prevents omission); severity definitions keep the scale consistent; German keeps the model in the right legal register.

### 4. The classification call

Same file, lines 171–180.

```python
completion = client.chat.completions.parse(
    model="gpt-4o-mini",
    temperature=0,
    max_tokens=1024,
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Klassifiziere diesen Inhalt:\n\n{text}"},
    ],
    response_format=LLMClassification,
)
```

Four decisions to know:

| Decision | Reason |
|---|---|
| `gpt-4o-mini` | ~15× cheaper than gpt-4o, ~90% of the accuracy for classification |
| `temperature=0` | Legal classification must be deterministic |
| `.parse()` over `.create()` | Modern Structured Outputs API, server-side schema enforcement |
| `response_format=LLMClassification` | Pydantic class, type-safe, no JSON-schema string |

### 5. Parsing the output

The old code (`classifier_llm.py`) used a JSON schema inside the system prompt and `json.loads(raw)`. The new code uses Pydantic `.parse()`.

```python
class LLMClassification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    severity: LLMSeverity
    categories: list[LLMCategory] = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)
    requires_immediate_action: bool
    summary: str
    summary_de: str
    applicable_laws: list[LLMLaw]
    potential_consequences: str
    potential_consequences_de: str
```

What the schema buys:
- Server-side enforcement — OpenAI refuses malformed outputs before we see them.
- Type safety — `completion.choices[0].message.parsed` is a validated instance or `None`.
- Enum validation — an invented severity is refused.
- Refusal handling — `msg.refusal` signals a safety-based decline.

The handler:

```python
msg = completion.choices[0].message

if msg.refusal:
    return None

llm_result = msg.parsed
if llm_result is None:
    return None

return _to_domain(llm_result)
```

### Likely questions

**"Do you use RAG?"**

Yes, in one place. The classifier does not — it's prompt-in, structured-out, single-turn. RAG lives in `services/legal_ai.py`: when a case has multiple evidence items, we retrieve them all plus their classifications from the database, structure them as a context block inside the prompt, and send the aggregate to Claude for legal reasoning across the whole case. That's the Week 9–10 deliverable. The split is deliberate: classification must be deterministic and single-input; case-level legal analysis is reasoning across a set of facts — that's where retrieval earns its place.

**"Why Structured Outputs instead of manual JSON parsing?"**

The model sometimes wraps JSON in markdown fences, or omits a field, or invents an enum value. Structured Outputs enforces the schema server-side — OpenAI refuses to return an invalid object. No defensive try/except, no code-fence stripping. I get a validated Pydantic instance or `None`.

**"What if OpenAI can't produce the object?"**

Two cases. `msg.refusal` — safety decline. `msg.parsed is None` — conformance failure. Both log and return `None`. The orchestrator in `classifier.py` raises `ClassifierUnavailableError`; the router returns 503 with "please try again." Better than a weak fallback.

**"Why temperature = 0?"**

Legal content must be reproducible. Same input today and next month must produce the same classification, or we lose court-admissibility and user trust. We give up creativity, we gain determinism. Classification is a mapping task, not a creative one.

### The full flow

```
USER                    BACKEND                             OPENAI
  │                        │                                   │
  │  text / URL / image    │                                   │
  ├───────────────────────►│                                   │
  │                        │  if URL: scrape                   │
  │                        │  if image: OCR                    │
  │                        │                                   │
  │                        │  system_prompt + user_text        │
  │                        ├──────────────────────────────────►│
  │                        │                                   │
  │                        │        Pydantic-parsed object     │
  │                        │◄──────────────────────────────────┤
  │                        │                                   │
  │                        │  _to_domain → ORM save            │
  │                        │  hash (SHA-256)                   │
  │                        │  timestamp (UTC)                  │
  │                        │                                   │
  │  severity + categories │                                   │
  │  + laws + summaries    │                                   │
  │◄───────────────────────┤                                   │
```

---

## Open for next week

State this directly to Zisis:

1. **Cleanup job for the 7-day soft delete.** The code sets `deleted_at`; no background job hard-deletes after the window. Plan: a simple cron task.
2. **Art. 20 GDPR data export.** The privacy policy promises it; the endpoint doesn't exist. Plan: `GET /auth/me/export` returning JSON of all user data.
3. **Magic link via a real email provider.** The MVP returns the token in the response for convenience; production needs Resend or equivalent.
4. **HttpOnly session cookie replacing LocalStorage.** SameSite=Strict, Secure, to neutralise XSS.
5. **Bulk-import CSV integration tests.** NGO partners will use this path; current coverage is minimal.

---

## Red-flag questions and honest answers

**"How many tests do you have?"**

Last verified count: 533 passing out of 534 as of yesterday's run. One LLM-integration test is flaky — temperature drift at the model level, not a code bug. You can verify tonight with `pytest --tb=no -q`.

**"Is it running on Railway?"**

Yes, live at `https://safevoice-production-0847.up.railway.app`. Deployed yesterday. The `VITE_OPERATOR_*` build-time env vars still need to be set before the Impressum and Datenschutz pages stop showing "— nicht konfiguriert —" placeholders.

**"Why no transformer fallback anymore?"**

A weak classification is worse than no classification. A MEDIUM badge on a real death threat could lead the victim to close the tab thinking the case is minor — that's harm we caused. An honest 503 "try again" is safer than a misleading result.

**"How do you handle bias in gpt-4o-mini?"**

Not yet evaluated systematically. The strongest current mitigation is the victim-centred rule in the prompt. A bias evaluation against a gold-standard set of real cases is on the roadmap — a topic I'd like to discuss with you.

**"How do you validate classification correctness?"**

Manual checks against known cases in `data/mock_data.py`. No automated accuracy test against a gold standard yet — that's an open item.

---

## Checklist — before the meeting

- [ ] Run `pytest --tb=no -q` and note the count
- [ ] Walk the demo locally once end-to-end
- [ ] Confirm `OPENAI_API_KEY` in `.env`
- [ ] Confirm the 14 recent commits are on origin/main (they are — pushed yesterday)
- [ ] Two browser tabs: `http://localhost:5173` and `http://localhost:8000/docs`
- [ ] Two terminals running `uvicorn` and `npm run dev`
- [ ] Read this sheet and `DEMO_EN.md` once more
- [ ] Take the quiz in `QUIZ.html`
