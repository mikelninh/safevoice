# AI Flow — Single-Tier LLM Classifier

**Purpose:** How SafeVoice classifies text. Input, context, system prompt, structured output, failure handling.

For every design choice: *what it is* → *why we chose it* → *what would break without it*.

## The Big Picture

```
User input (text, URL, screenshot)
        │
        ▼
   Pre-processing
        │
        ├─ OCR if screenshot       (services/ocr.py)
        ├─ Scrape if URL           (services/scraper.py)
        └─ Extract text otherwise
        │
        ▼
  LLM Classifier     (services/classifier.py::classify)
        │
        └─→ OpenAI GPT-4o-mini     (classifier_llm_v2.py)
               │  is_available() = OPENAI_API_KEY present
               │  returns ClassificationResult
               │  OR raises ClassifierUnavailableError
        │
        ▼
  Error handling
        │
        ├─ If LLM fails: raise ClassifierUnavailableError
        ├─ Router catches it and returns HTTP 503 with clear message
        └─ User sees "Unable to classify right now. Try again in a moment."
        │
        ▼
  Persistence (if classification succeeded + case_id provided)
        │
        ├─ hash_content(text)              — SHA-256
        ├─ get_last_hash(case_id)          — previous in chain
        ├─ archive_url_sync(url)           — archive.org backup
        └─ add_evidence_with_classification  — DB write in single transaction
        │
        ▼
   Response (ClassificationResult + evidence_id)
```

## Why Single-Tier — and What We Removed

**Previous architecture had 3 tiers:** LLM → Transformer → Regex. We removed tiers 2 and 3. The decision trace matters for the tutor:

| Removed | Why it failed the bar |
|---------|----------------------|
| Transformer (`unitary/xlm-roberta`) | Under-trained on German legal language. "Übergriffig" or "Nachstellung" don't map cleanly to toxicity scores. Classifying as "HARASSMENT + NetzDG §3" catches nothing specific — worse than useless for court. |
| Regex rules | Can't handle unseen obfuscation. "Stirb" is caught; "5t1rb" is not. Gives victims a false sense of certainty. A weak "medium/harassment" classification from regex misleads more than it helps. |

**Core principle:** *a weak classification is more harmful than an honest error.* A victim filing Strafanzeige based on a regex verdict that misses § 241 (Bedrohung) is worse off than one who gets a "please try again" message and waits 30 seconds.

**What we do instead:** surface failures honestly.
- If no API key: health check returns `"degraded"`, analyze endpoints return 503
- If API call fails: return 503 with `"Please try again in a moment"`
- If rate limited: return 503; user retries when limit resets

The legacy regex module (`classifier_regex.py`) remains in the codebase for backward-compat with existing tests and as a reference pattern library, but it is **not wired into the production `classify()` path**.

## LLM Flow Deep Dive

## LLM Flow Deep Dive

`services/classifier_llm_v2.py::classify_with_llm`

### Input

```python
text: str  # 1 to ~10,000 chars
```

No other context yet. This is a deliberate scope: the LLM sees only the content to classify, not the victim's name, case history, or other identifying info. This is a **data-minimization** choice (DSGVO Art. 5 principle).

### System Prompt Construction

The system prompt (`classifier_llm.py::SYSTEM_PROMPT`) has 4 parts:

1. **Role definition** — `"Du bist SafeVoice — ein juristischer Klassifikator für digitale Gewalt in Deutschland."` Sets the model into legal-classifier mode, not general chatbot.

2. **Rules for interpretation:**
   - Handle typos, slang, obfuscation (`f0tze`, `stirbt` instead of `stirb`)
   - In doubt, err toward higher severity (victim-first bias)
   - Threats are threats even if indirect
   - Consider context, not isolated words

3. **Category enumeration** — 18 allowed categories with German one-line descriptions. Prevents the model from inventing new categories.

4. **Law enumeration** — 12 statutes (§ 130, 185, 186, 187, 201a, 238, 241, 126a, 263, 263a, 269 StGB + NetzDG § 3). Each paragraph has its maximum penalty. The model picks from this closed set.

5. **Severity scale** — 4 levels with concrete criteria tied to real actions (`critical` = sofortige Anzeige + Beweissicherung).

**Why this prompt works:** it's closed-world. No hallucination space. Every allowed output is enumerated. This is what makes structured output reliable.

### Structured Output

Current implementation (`classifier_llm.py::RESPONSE_SCHEMA`):

```python
response_format = {
    "type": "json_schema",
    "json_schema": {
        "name": "classification",
        "strict": True,   # OpenAI enforces schema server-side
        "schema": {
            "type": "object",
            "properties": {
                "severity":   {"type": "string", "enum": ["low","medium","high","critical"]},
                "categories": {"type": "array", "items": {"type": "string"}},
                "confidence": {"type": "number"},
                "requires_immediate_action": {"type": "boolean"},
                "summary":     {"type": "string"},
                "summary_de":  {"type": "string"},
                "applicable_laws": {"type": "array", "items": {"type": "string"}},
                "potential_consequences":    {"type": "string"},
                "potential_consequences_de": {"type": "string"},
            },
            "required": [...],
            "additionalProperties": False,
        }
    }
}
```

**Why structured output** (not free-text + parsing):
- OpenAI validates the schema server-side before streaming. If the model would produce malformed JSON, the API retries internally.
- No fragile regex parsing. No "the model forgot the field" bugs.
- Schema changes propagate automatically.

**Current limitation & next upgrade:** using the raw JSON schema with `.create()` works, but the modern best practice (OpenAI SDK 1.40+, Aug 2024) is `client.chat.completions.parse()` with a **Pydantic model**. This gives:
- Automatic `ClassificationResult` typing
- Rejection of invalid Pydantic enums at SDK level
- Cleaner code

See `classifier_llm_v2.py` for the upgraded implementation (shipped as part of tutor item #6).

### Post-processing (`_parse_result`)

The LLM returns strings for enums (`"high"`). We:
1. Map strings → Python enums (`Severity.HIGH`). Unknown values fall back to `Severity.MEDIUM` — *not* `.LOW`, because under-classification is the dangerous error.
2. Drop unknown categories, ensuring at least `HARASSMENT` (the catch-all). A classification with empty categories is meaningless.
3. Map law strings → `GermanLaw` objects. If NetzDG isn't in the returned list, we **append it** — every piece of platform content in Germany triggers NetzDG § 3 platform obligations by default. This is a legal invariant, not an AI choice.
4. Clamp confidence to [0, 1]. Defaults to 0.85 if missing.

### Failure Handling

The function catches `Exception` broadly. On any failure (API down, JSON malformed, network timeout, refusal), we log a warning and return `None`. The orchestrator (`classifier.py::classify`) converts `None` to `ClassifierUnavailableError`, which the API layer translates to HTTP 503.

**Why broad exception catch:** all LLM errors should be routed through one honest error path. We don't want different failure modes leaking different HTTP codes to clients.

## The `classifier_tier` Field

Stored in `classifications.classifier_tier`. Single-tier LLM architecture means it is always `1`.

**Why keep it in the schema:** forward compatibility. If we later add a second model (e.g., a locally hosted Llama for sensitive content we don't want to send to OpenAI), the column already exists to distinguish them. Removing and re-adding would require a DB migration.

## Pattern Detection (separate from classification)

`services/pattern_detector.py::detect_patterns` runs **after** individual evidence classification, **across** all evidence in a case.

Looks for:
- Repeated author (same username attacking repeatedly)
- Coordinated attack (multiple accounts, similar timing, similar content)
- Escalation (severity increasing over time)
- Temporal clustering (many attacks in short window)

Outputs `PatternFlag` objects that enrich the case. This is case-level analysis, not evidence-level.

## Security / Data Flow Invariants

1. **No user data in system prompt.** Only the content to classify, plus reusable rules.
2. **No cross-user contamination.** Each classify() call is stateless. No conversation history between classifications.
3. **Archive before classify.** If URL is provided, `archive.org` is called BEFORE classification — this preserves evidence even if the classifier fails.
4. **Hash before classification persists.** `content_hash` is computed from raw input before any AI runs. The hash is the tamper-evident anchor; the classification is the interpretation layer on top.

## Cost Model

- Tier 1 (GPT-4o-mini): ~600 tokens in + 200 tokens out per classification = €0.00018 per call
- Tier 2 (HF transformer): free, self-hosted
- Tier 3 (regex): free
- Current per-case average: 1-5 evidence items → €0.001-0.005 in AI cost

At 10,000 cases/month (optimistic), AI cost = ~€40-50/month. Negligible next to hosting.

## Known Gaps & Future Work

1. **Context windowing** — currently each evidence item is classified independently. A case-level LLM pass that sees the full context (victim's description, prior evidence, pattern flags) would improve nuance. Trade-off: more tokens, more cost, slower.
2. **Multi-modal** — image classification (deepfakes, manipulated screenshots) is OCR → text only today. A vision model (GPT-4o-vision) would classify the image directly. Next phase.
3. **Feedback loop** — lawyers reviewing court-exports could flag misclassifications. This feedback should feed into prompt refinement or a fine-tuned model. Not yet built.
4. **Language autodetect** — currently we trust the system to understand DE/EN/TR/AR without language detection. A language-detect step could route to language-specific prompts.

## Open Questions for Tutor

1. Should we version the system prompt? Today a prompt change silently affects all future classifications. Versioning would let us say "this case was classified with prompt v1.2".
2. Should the LLM see the existing case's pattern flags as context? Pro: richer classification. Con: data minimization principle.
3. Temperature 0 makes Tier 1 *more* deterministic but not fully. Should we also seed? OpenAI supports `seed` param for reproducibility.
