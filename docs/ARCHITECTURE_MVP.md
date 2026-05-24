# SafeVoice — MVP Architecture (for re-reading / interview prep)

A plain-language walkthrough of how the MVP is built, the technical design
decisions, and why each one was made. Grounded in the actual codebase.

---

## 1. The shape

```
 Browser (anonymous, localStorage-first, PWA)
   React 19 + TypeScript + Vite + Tailwind · BrowserRouter
        │  fetch /api/...
        ▼
 Vercel  (one project, one bill, Frankfurt/EU)
   ├─ static frontend (frontend/dist)
   └─ api/proxy.py  ──> the FastAPI backend runs *inside* the serverless
                        function (maxDuration 300s, 1 GB)
        │
        ▼
 FastAPI backend (Python · SQLAlchemy)
   ├─ classifier  (per-evidence)      gpt-4o-mini + Pydantic Structured Outputs
   ├─ legal_ai    (per-case)          2nd layer: assessment, risk, charges
   ├─ court_prep agent (tool-calling) builds the full Strafanzeige package
   ├─ llm_gateway (central)           one place for model calls + cost/telemetry
   └─ report/pdf  (ReportLab)         court-ready PDF
        │
        ▼
 Neon Postgres (eu-central / Frankfurt)
   cases · evidence · classifications · legal_analysis · llm_usage · agent_runs
```

## 2. The two main request flows

**A. Classify one piece of evidence** (`POST /analyze/text` or add evidence):
1. Text comes in → `classify()` (single-tier LLM classifier).
2. gpt-4o-mini with a Pydantic schema (`ClassificationResult`) returns severity,
   categories (enum), confidence, applicable §§, DE+EN summaries.
3. Low confidence / LLM down → **503, not a weak guess**.
4. Evidence is hashed (SHA-256), chained to the previous hash, optionally
   archived (archive.org), and persisted.

**B. Prepare the court package** (`POST /agent/court-prep/{case_id}`):
1. The Court-Prep **agent** runs a native tool-calling loop (`agent_loop.py`).
2. It calls tools in the order the model chooses: `read_case` →
   `check_strafantrag_frist` → `detect_anonymisierung_needed` →
   `re_archive_urls` → `draft_netzdg_email` → `determine_jurisdiction` →
   `generate_strafanzeige_pdf` → `build_onlinewache_text`.
3. Each LLM round is metered (tokens, cost) and capped (iterations + €budget).
4. Returns artefacts (PDF, NetzDG emails, Onlinewache text) + a short summary
   in the user's language. **Nothing is sent** — the human files it.

## 3. The design decisions (the defensible ones)

1. **Schema-first, not prompt-first.** Categories + §§ are a Pydantic enum,
   enforced server-side via OpenAI Structured Outputs. The model *cannot*
   return a value outside the schema → it can never invent a statute.
   *Implementation:* `classifier_llm_v2.py`, `models/evidence.py`.

2. **Two layers, not one big call.** A narrow per-evidence classifier + a
   per-case aggregator (`legal_ai.py`). Smaller scope = higher accuracy +
   cheaper; each call validates the other. Architecture beats prompting.

3. **No silent fallback.** Old design had 3 tiers (LLM → transformer → regex).
   Removed tiers 2-3: a weak classification is worse than an honest error for a
   criminal complaint. `ClassifierUnavailableError` → 503. (`classifier.py`)

4. **Anonymous-first — the threat model drove the schema.** A stalking victim
   can't safely create an account. So: no login required, browser localStorage
   by default. This forced the DB pivot: `cases.user_id` became **nullable** +
   an `anonymous_token`; login is an optional upgrade for NGOs. Also GDPR
   Art. 25 (data minimization).

5. **Cheapest model that passes the eval.** Eval showed gpt-4o-mini =
   gpt-4.1-mini = gpt-5-mini at 100% on the production prompt → took gpt-4o-mini
   (7.4× cheaper than gpt-5-mini). Cost is a design constraint. One provider =
   one SDK, one bill, one failure mode.

6. **Native tool-calling agent, capped.** `agent_loop.py` runs the OpenAI
   tool-calling loop with an iteration cap and a €budget cap (a runaway agent
   costs a coffee, not a meal). Per-round telemetry (tokens/cost/tools).

7. **Evidence integrity.** Each piece gets a SHA-256 hash over the exact
   captured content + a UTC timestamp + a hash chain to the previous piece +
   an archive.org backup. A browser-side verifier lets police recompute the
   hash without trusting our server.

8. **Central LLM gateway.** `llm_gateway.py` is the one place model calls go
   through — it estimates cost, records usage to `llm_usage`, and is where a
   multi-provider failover would slot in. Telemetry by construction.

9. **GDPR / EU by design.** Backend + Neon Postgres in Frankfurt
   (eu-central). Data minimization, right to erasure, JSON export,
   no content logging on the server path.

## 4. The data model (case-centric)

```
cases            id, user_id NULL, anonymous_token, title, overall_severity
evidence_items   id, case_id, raw_content, content_type, platform, source_url,
                 archived_url, content_hash, hash_chain_previous, timestamp_utc
classifications  id, evidence_id, severity, confidence,
                 categories[] (M:N), laws[] (M:N), summary_de/en
legal_analysis   case_id, assessment, risk, strongest_charges, recommended_actions
llm_usage        per-call tokens + cost (route, case, agent_run)
agent_runs       per-run status, iterations, total_cost, tool-call audit
```
Cases live without a user (browser-local). `user_id` optional = the whole
anonymous-first principle expressed in one nullable column.

## 5. Why this is "real engineering", not a GPT wrapper

- Structured outputs (can't hallucinate a §) + an eval harness (66%→86%) +
  no-silent-fallback = a *reliable* classifier, not a vibe.
- A capped, audited, metered tool-calling agent = a system you can defend in
  front of a court (every tool call logged) and to a funder (every euro logged).
- Anonymous-first + Frankfurt + hash-chain = built for the actual users
  (victims) and the actual reader (police), not for a demo.

## 6. What's deliberately deferred (post-MVP)

- M1 reusable Civic-AI toolkit (extract the pipeline into a library)
- M2 GitLaw-as-API (authoritative law instead of prompt-embedded §§)
- M3 in-house analytics + the Lagebild aggregate page + feedback→eval loop
- Multi-provider LLM gateway failover (the seam exists in `llm_gateway.py`)
