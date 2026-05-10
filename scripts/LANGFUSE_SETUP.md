# Langfuse setup — see your LLM calls in action

5-minute one-time setup, then both demos work.

## Step 1 · Sign up (3 min)

Go to **https://eu.cloud.langfuse.com** (EU region — good DSGVO posture for SafeVoice). The `.com` site is the US region; pick whichever you prefer for testing, but use EU for SafeVoice production.

- Sign up with GitHub or email
- Create an organisation (any name)
- Create a project: e.g. "Mikel-Demos" — one project can host traces from both SafeVoice and Luck Lab

## Step 2 · Generate API keys (1 min)

- Project Settings → **API Keys** → **Create new API keys**
- Copy both:
  - `LANGFUSE_PUBLIC_KEY` (starts `pk-lf-`)
  - `LANGFUSE_SECRET_KEY` (starts `sk-lf-`)

## Step 3 · Add to `.env`

### SafeVoice — `/Users/mikel/safevoice/.env`

```
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://eu.cloud.langfuse.com
```

### Luck Lab — `/Users/mikel/kairos/.env.local`

Same three lines.

## Step 4 · Install the SDK (1 min)

### SafeVoice

```bash
cd /Users/mikel/safevoice
source backend/venv/bin/activate
pip install langfuse
```

### Luck Lab

```bash
cd /Users/mikel/kairos
npm install langfuse
```

## Step 5 · Run the demos

### SafeVoice (6 classifier calls, ~80 seconds)

```bash
cd /Users/mikel/safevoice
source backend/venv/bin/activate
python scripts/langfuse_demo.py
```

What you'll see in the Langfuse UI:
- **Traces tab**: 6 calls named `classify · <case_id>`
- Each trace shows the full system prompt (~1.6k tokens), the user message, the parsed Pydantic output, tokens, latency, cost
- **Tags**: `prompt-v2`, `demo`, plus the case category — click to filter
- **Scores**: each trace gets a `severity_match` score (1 or 0). Open the Scores tab to see aggregate accuracy.

### Luck Lab (3 quiz reads through the live endpoint)

In one terminal:
```bash
cd /Users/mikel/kairos
npm run dev
```

In another terminal once the dev server is up:
```bash
cd /Users/mikel/kairos
node scripts/langfuse-demo.mjs
```

What you'll see:
- 3 traces named `tyche-read · <archetype-id>` — the analyser, wanderer, connector personas
- Tags: `tyche-read`, `free-teaser`, `archetype:<id>` — filter to compare across archetypes
- Metadata: archetype name, growth edge, dominant axes, normalised scores, personal-context-present flag, answer count
- Filter `tag:tyche-read` in the dashboard to see roll-up cost + latency

## Step 6 · Look at the data

Once you have traces:

- **Traces tab**: drill into any single call, see the full prompt + response side-by-side. This is the "I never have to wonder what the model saw" moment.
- **Sessions tab**: groups multi-call flows. SafeVoice demo creates one session per run; Luck Lab demo creates one trace per quiz. Useful when a case has multiple LLM calls (case-level analysis = retrieve + classify + analyse).
- **Costs**: filter by date range or tag, see cost-per-archetype, cost-per-prompt-version.
- **Datasets** (next step, not in v0 demo): version your eval set, run any prompt against it, see diffs in a UI rather than a markdown report.

## Going further — production wiring

The Luck Lab production endpoints (`/api/tyche/read` and `/api/preview-reading`) **already** use the `tracedOpenAI()` helper. That means **any real user request** is automatically traced — not just demo synthetic data. The helper falls back to plain OpenAI when Langfuse env vars are absent, so deploying to environments without keys is safe.

For SafeVoice, the demo script uses `langfuse.openai` to wrap calls. To extend this to production, the next step is to swap `client.chat.completions.parse(...)` in `classifier_llm_v2.py` for the wrapped version — same pattern as Luck Lab's helper. Suggested for **after** the end-of-May tutor mock interview; the eval-set + v1→v2 prompt-iteration story is the demo focus until then.

## When traces don't appear

1. Confirm both `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` are set in the right `.env*` file.
2. SafeVoice: confirm the venv has `langfuse` installed (`pip show langfuse`).
3. Luck Lab: confirm `node_modules/langfuse` exists, and **restart the dev server** after editing `.env.local`.
4. Confirm `LANGFUSE_HOST` matches the region you signed up for (`eu.` vs no prefix).
5. Check the Langfuse UI's project ID matches the keys — if you have multiple projects, it's easy to view the wrong one.
