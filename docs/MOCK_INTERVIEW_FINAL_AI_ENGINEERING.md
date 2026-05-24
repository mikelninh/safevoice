# Final Mock Interview — AI Engineering Track (Prep)

> NotebookLM source doc for Mikel Ninh. Mirrors the program's final mock-interview structure:
> 40–50 min, external coach, pass = 70+. Four parts: **HR · AI concepts · AI system-design
> scenarios · live LeetCode (Python, AI autocomplete OFF)**. Answers below are interview-length —
> say them out loud, don't read them. Concept answers are written to be correct *and* concise.

---

## PART 1 — HR questions

They'll ask: tell me about yourself, your training journey, your final project, motivations.

**"Tell me about yourself" (60 sec):**
> I came into software through building, not a CS degree — I'm a solo founder in Berlin and I learned by shipping real systems. My final project is SafeVoice: it turns a screenshot of online harassment into a court-ready criminal complaint in about 30 seconds, using an LLM to classify the message under German criminal law. Through the program I went deep on GenAI engineering — structured outputs, evaluation, prompt iteration, cost control. What drives me is using AI for things that actually matter to people, not demos.

**"Walk me through your final project" (SafeVoice — the academic version):**
- Problem: 90% of online-harassment victims never file a complaint — too complex, too expensive (a lawyer is ~€120/h).
- Solution: document the evidence → an LLM classifies severity + applicable statutes → generate a court-ready PDF. Anonymous, GDPR-by-design.
- The AI core (this is what they'll grade): gpt-4o-mini with **OpenAI Structured Outputs** (a Pydantic schema), a **two-layer** design (per-evidence classifier + per-case aggregator), and an **eval corpus** of 35 cases. Prompt iteration took it from **66% → 86%** pass rate; the model never invented a statute (35/35 forbidden-laws guard) because the categories are a constrained enum.
- One hard decision: anonymous-first. A stalking victim can't safely create an account — so no login required, browser-local storage. The threat model drove the architecture.

**Motivation:** I want to do AI engineering on systems with real users and real stakes. SafeVoice is proof I can take a fuzzy human problem and ship a reliable, evaluated, cost-controlled AI system.

**Tips:** Keep answers structured (situation → what I did → result with a number). Always land on a concrete number. Be honest about being self-taught — frame it as "I learn by shipping," backed by a live project.

---

## PART 2 — AI concept questions (theory)

**Q: Purpose of tokenization, and the types?**
Tokenization splits text into tokens — the units a model actually processes — and maps them to integer IDs from a fixed vocabulary. It exists because models need a bounded vocabulary and numeric input. Types:
- **Word-level** — simple, but huge vocab and breaks on unseen words.
- **Character-level** — tiny vocab, but very long sequences and weak semantics.
- **Subword** — the modern standard, a balance: **BPE (Byte-Pair Encoding)** used by GPT (`tiktoken`), **WordPiece** used by BERT, **SentencePiece/Unigram**. Subword handles out-of-vocabulary words by composing them from pieces (e.g. "tokenization" → "token" + "ization").

**Q: What are word embeddings?**
Dense vector representations of tokens/words where semantic similarity = geometric closeness (king–man+woman ≈ queen). **Static** embeddings (Word2Vec, GloVe) give one vector per word. **Contextual** embeddings (from transformers) give a different vector depending on surrounding context — "bank" in "river bank" vs "bank account." They turn discrete text into continuous space a model can compute over, and power similarity search / RAG.

**Q: Fine-tuning vs zero-shot learning?**
Fine-tuning = continuing to *train* the model on task-specific labeled data, which **updates its weights** and specializes it. Zero-shot = the model performs a task it was never explicitly trained on, using **only the prompt instruction**, no examples, **no weight update**. Fine-tuning costs data + compute and gives a specialized model; zero-shot is instant and free but relies on the model's general capability.

**Q: How does a model like GPT generate text?**
It's **autoregressive**: a decoder-only transformer predicts a probability distribution over the next token given all previous tokens, samples one (controlled by temperature/top-p), appends it, and repeats until a stop token or max length. Self-attention lets each position attend to all earlier positions. It doesn't "plan" the whole answer — it generates one token at a time.

**Q: Limitations of LLMs?**
Hallucination (confident wrong answers), knowledge cutoff / no live data, fixed context window, weak at exact math/logic, sensitive to prompt phrasing, training-data bias, no persistent memory between calls, can't verify truth, and cost/latency at scale. Mitigations: structured outputs, RAG for fresh/proprietary facts, confidence thresholds, evals.

**Q: Significance of pretraining and fine-tuning?**
**Pretraining** is self-supervised learning on a massive general corpus (predict the next token) — the model learns language, facts, reasoning patterns. **Fine-tuning** is supervised training on a smaller task-specific dataset to specialize it. This is transfer learning: pretrain once (expensive), fine-tune many times cheaply. Most app work today skips fine-tuning entirely and uses prompting + RAG.

**Q: Zero-shot, one-shot, few-shot?**
All are **in-context learning** — no weight updates, just what's in the prompt. Zero-shot = instruction only. One-shot = instruction + one worked example. Few-shot = instruction + several examples. More examples usually improve accuracy on tricky/edge cases (in my SafeVoice eval, going to few-shot + chain-of-thought drove 66% → 86%).

**Q: What is temperature?**
A sampling parameter that scales the logits before the softmax, controlling randomness. **Low (→0)** = near-deterministic, always picks the highest-probability token — right for classification and factual tasks. **High (~0.8–1+)** = flatter distribution, more diverse/creative output — right for brainstorming or slogans. It trades reliability for creativity.

**Q: How does the OpenAI API handle context?**
The Chat Completions API is **stateless** — it does not remember previous calls. You resend the full conversation as a `messages` array (system + prior user/assistant turns + new user message) on every request. The model attends to everything inside the context window; tokens beyond the window must be truncated or summarized. State (memory) is the application's job, not the API's.

**Q: Explain chain-of-thought prompting.**
Asking the model to **reason step-by-step before giving the final answer** ("Let's think step by step" / show your working). Generating intermediate reasoning tokens improves accuracy on multi-step / reasoning tasks because each step conditions the next. Trade-off: more tokens = more cost + latency. I used it in SafeVoice so the classifier reasons about context before assigning a statute.

**Q: What is RAG?**
**Retrieval-Augmented Generation.** Instead of relying only on what's baked into the model's weights, you **retrieve relevant documents at query time** — usually by embedding the query and doing similarity search in a vector database — and inject them into the prompt as context. The model then answers grounded in that retrieved text. Benefits: up-to-date / proprietary knowledge, fewer hallucinations, citations, cheaper than fine-tuning. Pipeline: chunk docs → embed → store in vector DB → at query time embed the question → top-k retrieve → stuff into prompt → generate.

---

## PART 3 — AI system-design scenarios (no coding, describe the approach)

These reward a clear, structured walk-through. Use the same 6-beat template for any scenario:
**(1) endpoint shape → (2) API call + mandatory args → (3) error handling → (4) prompt strategy → (5) temperature/max_tokens → (6) token usage + cost.**

### Template answer — applies to BOTH example scenarios

**(1) Endpoint design.**
`POST /generate-slogan` (or `/classify-ticket`). JSON request body with the inputs; JSON response with the result + metadata.
- Slogan scenario body: `{ "product_name", "description", "tone"? , "audience"? }` → response `{ "slogan", "model", "usage": { "prompt_tokens", "completion_tokens" }, "cost_usd" }`.
- Ticket scenario body: `{ "subject", "body" }` → response `{ "category", "summary", "model", "usage": {...}, "cost_usd" }`.
Validate inputs first (non-empty, length caps) and return 400 on bad input.

**(2) Interaction with the GenAI API (OpenAI).**
- Init client with API key (from env, never hardcoded).
- Build `messages`: a **system** message defining the role/task/constraints + a **user** message with the input.
- Call `client.chat.completions.create(...)`. **Mandatory args: `model` and `messages`.** Optional but important here: `temperature`, `max_tokens`, and `response_format` (for structured output).
- For the ticket classifier, use **Structured Outputs** (`response_format` with a JSON schema / Pydantic model) so `category` is forced to come from the predefined list.

**(3) Error handling.**
Wrap the call in try/except. Handle: `RateLimitError` (429) with **exponential backoff + retry**, `APITimeoutError` (set a timeout, retry once), `APIError`/5xx (retry then fail gracefully), and validation/parse errors (if JSON came back malformed). Return a clean 4xx/5xx with a message, never leak the stack trace. Optionally a fallback model. Log the failure with request id.

**(4) Prompt strategy.**
- System prompt states the task, the constraints, and the **exact allowed categories** (for classification).
- Use **few-shot examples** covering edge cases (e.g. an ambiguous ticket, an idiomatic message).
- For classification: **structured output** so the category is schema-constrained and can't drift. For the summary: instruct "one concise sentence, factual."
- For the slogan: specify brand voice, length limit ("≤ 8 words"), and that it must be original; give 1–2 example slogans in the tone wanted.

**(5) Temperature and max_tokens.**
- **Strict classification → temperature 0–0.2** (deterministic, repeatable).
- **Creative slogan → temperature ~0.8–0.9** (diversity); more humorous → push higher (~1.0), more professional → lower (~0.5).
- **Empathetic summary → ~0.4–0.6** (some warmth, still grounded).
- `max_tokens` sized to the expected output: a slogan ~30–50, a one-sentence summary ~60, the category a handful. Keeping it tight controls cost and stops rambling.

**(6) Token usage + cost.**
Read `response.usage.prompt_tokens` and `response.usage.completion_tokens`. Cost = `(prompt_tokens / 1_000_000) * input_price_per_1M + (completion_tokens / 1_000_000) * output_price_per_1M`, using that model's pricing (e.g. gpt-4o-mini ≈ $0.15/1M input, $0.60/1M output). Return it in the response metadata and log it per request — that's what makes cost observable per tenant in production.

**Worked code sketch (be ready to write this live if asked):**
```python
from openai import OpenAI
client = OpenAI()

PRICES = {"gpt-4o-mini": {"in": 0.15/1e6, "out": 0.60/1e6}}

def classify_ticket(subject: str, body: str) -> dict:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.1,                 # strict classification
        max_tokens=120,
        messages=[
            {"role": "system", "content":
             "Classify the support ticket into exactly one of: "
             "Billing, Technical Support, Account Issue. "
             "Then write a one-sentence summary. Return JSON: "
             '{"category": ..., "summary": ...}'},
            {"role": "user", "content": f"Subject: {subject}\n\nBody: {body}"},
        ],
        response_format={"type": "json_object"},
    )
    import json
    data = json.loads(resp.choices[0].message.content)
    u = resp.usage
    p = PRICES["gpt-4o-mini"]
    cost = u.prompt_tokens * p["in"] + u.completion_tokens * p["out"]
    return {**data,
            "usage": {"prompt_tokens": u.prompt_tokens,
                      "completion_tokens": u.completion_tokens},
            "cost_usd": round(cost, 6)}
```

---

## PART 4 — Live coding (LeetCode-easy, Python). Turn OFF AI autocomplete.

Write the code, then say the time/space complexity and walk through an example. Talk while you type.

**1. find_duplicates(nums) — duplicates, each once.**
```python
def find_duplicates(nums):
    seen, dupes = set(), set()
    for n in nums:
        if n in seen:
            dupes.add(n)
        else:
            seen.add(n)
    return list(dupes)
# O(n) time, O(n) space. Two sets: one for seen, one to dedupe the result.
```

**2. count_occurrences(words) — word → count dict.**
```python
def count_occurrences(words):
    counts = {}
    for w in words:
        counts[w] = counts.get(w, 0) + 1
    return counts
# O(n) time, O(k) space (k = distinct words). Could also use collections.Counter.
```

**3. two_sum(nums, target) — indices of the pair.**
```python
def two_sum(nums, target):
    seen = {}                      # value -> index
    for i, n in enumerate(nums):
        if target - n in seen:
            return [seen[target - n], i]
        seen[n] = i
    return []
# O(n) time, O(n) space. One pass, hash map of complements.
```

**4. find_missing_number(nums) — 0..n with one missing.**
```python
def find_missing_number(nums):
    n = len(nums)
    return n * (n + 1) // 2 - sum(nums)
# O(n) time, O(1) space. Expected sum of 0..n minus actual sum.
# (Alt: XOR all indices and values.)
```

**5. second_largest(nums) — second largest value.**
```python
def second_largest(nums):
    first = second = float("-inf")
    for n in nums:
        if n > first:
            first, second = n, first
        elif n > second and n < first:
            second = n
    return second if second != float("-inf") else None
# O(n) time, O(1) space. Track top two in one pass; handles duplicates of the max.
```

**Live-coding habits that score points:** clarify the input (can it be empty? negatives? duplicates?), state your approach before typing, name the complexity, run through one example out loud, mention an alternative. Brute-force-then-optimize is fine — say "naive is O(n²), let me improve with a hash map."

---

## Quick-reference cheat sheet

- Tokenization → subword (BPE for GPT). Embeddings → semantic vectors, static vs contextual.
- Zero/one/few-shot = in-context, no weight change. Fine-tuning = updates weights.
- Temperature: low = deterministic (classification), high = creative (slogans).
- API is stateless → resend full `messages`. Mandatory args: `model`, `messages`.
- CoT = reason step-by-step before answering. RAG = retrieve → inject → generate.
- Cost = prompt_tokens·in_price + completion_tokens·out_price (per 1M).
- Structured Outputs = schema-constrained classification (can't drift off the list).
- My numbers: 66% → 86% eval, 35/35 forbidden-laws guard, gpt-4o-mini 7.4× cheaper than gpt-5-mini at equal accuracy.
