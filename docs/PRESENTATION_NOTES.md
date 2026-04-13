# Tutor Presentation — Walkthrough Notes

**Date:** 2026-04-20
**Tutor:** Zisis Batzos
**Goal:** demonstrate *deep architectural understanding*, not just working code.

> Zisis's frame: "Can you tell me *why* each decision was made, and what would break if we did it differently?" Be ready to defend every line.

## Structure of the Session (plan 30-45 min)

| # | Topic | Doc | Time |
|---|-------|-----|------|
| 1 | Project overview & problem | README + DESIGN | 3 min |
| 2 | Database attributes — user_input vs AI | `docs/DB_ATTRIBUTES.md` | 5 min |
| 3 | AI flow — 3-tier classifier | `docs/AI_FLOW.md` | 10 min |
| 4 | User CRUD — magic links, emergency delete | `docs/USER_CRUD.md` | 5 min |
| 5 | Case CRUD — evidence chain, hash invariants | `docs/CASE_CRUD.md` | 5 min |
| 6 | Classification API — endpoints | `docs/CLASSIFICATION_API.md` | 3 min |
| 7 | Structured outputs — v1 → v2 | `classifier_llm.py` → `classifier_llm_v2.py` | 5 min |
| 8 | Q&A | — | rest |

## Key Defenses (the "why this, not that" answers)

### On 3-tier classifier

- **"Why not just use OpenAI?"** → Because users might be classifying evidence in a country with no API access, because the API might be down, because tier 3 (regex) is always reproducible for audit. Fallback is not redundancy, it's resilience.
- **"Why not just a bigger model?"** → A bigger model is the *ceiling*. We also need a *floor* that always works. Tier 3 is the floor.
- **"Why GPT-4o-mini and not GPT-4o?"** → 4o-mini is ~15x cheaper with 85% of the classification accuracy for this task. Money matters at scale (NGO budget).

### On structured outputs

- **"Why not parse free-text?"** → We tried free-text in an earlier iteration. Got ~2% malformed-JSON rate. That's 1 in 50 cases silently failing. Structured output enforcement on OpenAI's side is zero.
- **"Why v1 uses raw JSON schema, v2 uses Pydantic `.parse()`?"** → v1 was written when `.parse()` was new; works but still requires manual JSON parsing + enum mapping. v2 eliminates that entire code path. Same behavior, less surface for bugs.
- **"Why fallback to None on error, not raise?"** → The orchestrator above (tier 2/3) is the safety net. Raising would couple the caller to tier-1-specific error handling.

### On database attributes

- **"Why distinguish user_input from AI_populated?"** → Legal evidence: a judge needs to know which fields came from a human (subjective) vs a machine (verifiable). Same for DSGVO Art. 16 (rectification applies to user input, not AI fields).
- **"Why store `classifier_tier`?"** → Audit trail. If we're ever asked "which classifier produced this verdict?" we can answer. Also: if someone re-runs with a better classifier, we know which results to prefer.
- **"Why is `metadata_json` a TEXT column and not JSON?"** → SQLite compatibility for development. Migrate to `JSONB` column on Postgres in Sprint 1.

### On magic links

- **"Why not passwords?"** → No password database to breach, no password reuse attacks, simpler UX. Same model as Slack magic-link, Medium.
- **"Why single-use tokens?"** → Prevents replay if the email is intercepted.
- **"Why 24-hour token expiry?"** → Balances "user opens link later" with phishing-window shrinking. Industry norm.

### On emergency delete

- **"Isn't instant deletion dangerous?"** → Yes — it's a feature, not a bug. A victim whose abuser is approaching the device needs the escape hatch. Three-step confirmation flows would get someone hurt.
- **"What about legal preservation of evidence?"** → If the victim exported a court packet before deleting, that packet contains the full chain — evidence preserved where it matters. User control over their own data is the higher principle.

### On hash chain

- **"Why SHA-256 over SHA-1 or MD5?"** → Collision-resistance required for legal integrity. SHA-1 is broken. SHA-256 is the current standard for evidentiary integrity.
- **"Why chain hashes, not just per-evidence?"** → Per-evidence prevents tampering with one item. Chain prevents *reordering* or *deletion* — because the chain breaks. Tamper-evident beyond just tamper-detecting.
- **"Why store `hash_chain_previous` instead of computing on read?"** → Performance. A case with 100 evidence items would require 100 hash recomputations on every read. Store once, read fast.

## Likely Tutor Trap Questions — With Answers

**Q:** If OpenAI changes the model behavior (silent update), do your tests catch it?
**A:** Partially — we use `temperature=0` + structured outputs to reduce variance, but model updates can shift outputs. What we DO have: integration tests that classify known-bad phrases and check they hit the right categories. If a model update breaks them, we see it. What we don't have: property-based tests that bound worst-case drift. *Future work.*

**Q:** What happens if two users submit the same evidence independently? Are they linked?
**A:** No. Each submission is its own evidence item with its own hash. Same content → same hash, but different `case_id`, different `timestamp_utc`. By design — privacy. Linking cases across users would require inter-user data sharing, which DSGVO makes complicated.

**Q:** The regex tier doesn't know German law. How does it assign a paragraph?
**A:** Conservative heuristic: patterns map to the narrowest applicable statute. A death-threat pattern triggers §241 + §126a. A harassment pattern with no threat triggers only §185. When uncertain, we always include NetzDG §3 (platform obligation, always applies to social media). This under-classifies some cases (intentional — tier 3 is the floor, not the ceiling).

**Q:** Your schema has `user_id` on cases as nullable. Why?
**A:** Anonymous MVP mode. Some victims won't create an account — they just want to paste content and get a PDF. Cases without `user_id` can't be retrieved after the session closes, but they can still produce the court-ready PDF in the moment. *Design smell:* this means cases can orphan. Sprint 1: require user_id, deprecate anonymous flow, or formally support "session-owned" cases.

**Q:** In `/analyze/chat`, you set temperature=0.3 but classifier uses 0. Why?
**A:** Classification needs determinism — same input, same answer. Chat advice is conversational — temperature 0 makes it sound robotic. 0.3 is warm enough to feel human, cold enough to stay grounded. Both are defended with explicit comments in code.

**Q:** How do you prevent prompt injection in `/analyze/text`?
**A:** The classifier's system prompt is in a closed-world schema — it can only output categories from an enum and laws from an enum. Prompt injection can make the model produce different *wording* in `summary`, but it can't make it classify as a new category or invent a law. Our structured output is the defense.

**Q:** Why is `services/` full of small files?
**A:** Single-responsibility. `classifier_llm.py` does LLM calls, `classifier_transformer.py` does transformer, `pattern_detector.py` does aggregation. Each file is testable in isolation. The alternative (one big `classifier.py` with 2000 lines) would be harder to test and extend.

## What I'd Flag Proactively

Zisis values seeing you think about limitations honestly. Mention these unprompted:

1. "We don't version the system prompt. A change today silently affects tomorrow's classifications. We should record `prompt_version` alongside `classifier_tier`."
2. "Classifications are overwritten on re-classification, not versioned. For audit trail, we should keep history."
3. "The `/analyze/url` endpoint scrapes up to 20 comments synchronously. A 200-comment post blocks the request. Future: async batch classification."
4. "The hash chain protects against tampering but only within a case. If someone deletes an entire case, they've destroyed the chain. We rely on court-export PDFs for cross-case integrity."

## On the Structured-Outputs Upgrade (v2)

Walk Zisis through the actual diff:

**v1 (`classifier_llm.py`):**
- `response_format = {"type": "json_schema", "json_schema": {...}}`
- Call `.create()`, get raw string, `json.loads()` it, manually map enums
- Errors caught broadly

**v2 (`classifier_llm_v2.py`):**
- Define `LLMClassification(BaseModel)` with typed fields
- Call `client.chat.completions.parse(response_format=LLMClassification)`
- Get `completion.choices[0].message.parsed` — typed Pydantic object
- Map to domain via simple dict lookups

**Why both exist:** v1 is proven in production. v2 is the refactor. We'd A/B them in a staging environment before flipping, then retire v1.

**The test file (`tests/test_classifier_llm_v2.py`):** 14 tests, all passing, covering schema validation, domain mapping, API mocking, refusal handling. Run it live if Zisis wants.

## Close

If time permits, 3 slides on the roadmap:
1. **Sprint 1 (next 6 weeks):** NGO-grade — multi-tenant orgs, admin dashboard, legal-grade PDF, DSGVO docs
2. **HateAid pitch** scheduled for end of Sprint 1 (political moment of digitale Gewalt debate)
3. **Ecosystem:** SafeVoice is part of Democracy Säule with Deutschland 2030, GitLaw, Path to Peace, PMM

Frame: "This is a course project that's already a real tool. Here's how it keeps being one after the course ends."
