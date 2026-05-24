# Mock Interview Prep — AI Fullstack Engineer

> Source document for NotebookLM. Built for Mikel Ninh's mock interview prep for the
> **AI Fullstack Developer** role at **EVERLAST AI (Corporate LLM)**. Everything here is
> grounded in real, shipped work — primarily SafeVoice, with GitLaw Pro and Public Money
> Mirror as supporting evidence. Numbers are from real evals; do not inflate them in the room.

---

## 1. The role and what they actually value

**Role:** AI Fullstack Developer, building "Corporate LLM" at EVERLAST AI. 100% remote, Claude Max + unlimited tokens, small A-Player team. Founder/lead: Leonard Schmedding. Backed by EVERLAST AI (270k+ subscribers, 2.1k+ customers).

**Mission areas (what I'd be building):**
- **Agent Runtime** — tool-calling, RAG, multi-step agents
- **LLM Gateway** — GPT-5 / Claude / Gemini behind one API, with failover
- **EU Data Layer** — GDPR-compliant data residency
- **Multi-Tenant Platform** — many orgs on one system

**Stack:** Claude, OpenAI, Gemini, Azure, Mistral, AWS · Next.js, TypeScript, Tailwind · Supabase, Postgres, Drizzle · Vercel, Stripe.

**Career path:** Ship (1–3 mo) → Own (3–9 mo) → Lead (9–18 mo) → Found (18+ mo, optional co-founder of a follow-on venture).

**Their hiring filter (their own "Du bist richtig wenn…" list) — and my honest match:**
- "Shipped something nobody asked for in the last 30 days" → 8 production agents across SafeVoice + GitLaw + PMM in ~14 days.
- "First reflex: how do I automate this?" → the Court-Prep agent literally automates 3h of human work into ~30s.
- "Agentic coding so deep that coding without it feels one-handed" → Claude Code is my daily primary tool on real production systems.
- "Portfolio = systems solving real problems, not tutorials or wrappers" → SafeVoice (digital-violence victims), GitLaw Pro (a paying law firm), PMM (open government).
- "Can ship in 48h with no standup/ticket/PM" → solo founder, 5+ parallel projects.
- "Re-evaluated their stack in the last 12 months" → migrated from single-LLM calls to native function-calling agent loops.

**What this means for the interview:** they are not looking for credentials, they are looking for *shipping evidence + systems thinking*. Lead with shipped systems, real users, and architectural decisions I can defend — not with framework trivia.

---

## 2. The 60-second "tell me about yourself"

> I'm a solo founder in Berlin building civic-tech with AI. In the last two weeks I shipped eight production agents across three real systems — SafeVoice, which turns a screenshot of online harassment into a court-ready criminal complaint in about 30 seconds; GitLaw Pro, where a Berlin law firm pays for an agent that saves a paralegal ~2.7 hours a day; and Public Money Mirror, for budget transparency. I don't ship GPT wrappers — I ship systems with real users, cost caps from day one, and audit trails that hold up in front of a court. I do this solo today; I want to do it in a team with bigger leverage.

Why it works: concrete number + concrete person + concrete time-saving in the first breath. Proves "shipped > sold."

---

## 3. The flagship project deep-dive — SafeVoice (expect them to dig here)

**One-liner:** Document online harassment → AI classifies it under German criminal law → generate a court-ready complaint PDF. Anonymous, GDPR-by-design, open source.

**The pipeline (be able to draw this on a whiteboard):**
```
Evidence (text / URL / screenshot)
   → Layer 1: per-evidence classifier (gpt-4o-mini, Pydantic Structured Outputs)
   → Layer 2: per-case aggregator (all evidence + victim_context → one legal assessment)
   → Evidence preservation (SHA-256 hash + archive.org + UTC timestamp)
   → Court-ready complaint PDF (ReportLab)
```

**The numbers (real, from the eval — memorize these):**
- 35-case eval corpus, 10 categories (idioms, obfuscation, dog-whistles, stalking-with-context, cross-language).
- Prompt iteration: **66% → 86%** pass rate (all 4 dimensions) after moving from a zero-shot prompt to few-shot + chain-of-thought + victim_context.
- Severity exact-match: 74% → 94%. Latency: 10.8s → 3.1s.
- **Forbidden-laws guard: 35/35 (100%)** — the model never invented a statute it shouldn't. This is the headline reliability number.
- Model comparison (6-case, same production prompt): gpt-4o-mini, gpt-4.1-mini, gpt-5-mini **all hit 100%**. gpt-4o-mini is **7.4× cheaper** than gpt-5-mini → chose it. The reasoning-model premium doesn't pay on short-text classification.

**Five architectural decisions I can defend (the tutor drilled me on exactly this):**

1. **Schema-first, not prompt-first.** The 16 legal categories are a Pydantic enum enforced server-side via OpenAI Structured Outputs. The model *cannot* return a value outside the enum — so it can never invent a § that doesn't exist. The schema is the safety belt, not the prompt.

2. **Two layers, not one big call.** A narrow per-evidence classifier + a per-case aggregator beats one giant prompt: smaller scope = higher accuracy = cheaper, and each call validates the other. Architecture beats prompting.

3. **No silent fallback.** Low confidence returns a 503, never a quiet downgrade to a weaker guess. In a criminal complaint, a wrong answer is worse than no answer — the failure mode must be *visible*.

4. **Anonymous-first — the threat model drove the architecture.** A stalking victim told me: "I can't create another account my abuser might find." The login *was* the threat model. So: no account required, browser localStorage by default. This forced a DB rewrite (below) and is also GDPR Art. 25 (data minimization) by design.

5. **Cost discipline as a design constraint.** Picked gpt-4o-mini on the cost/accuracy frontier, not the strongest model. At NGO scale the delta is real money; the accuracy delta changes zero legal outcomes.

**The DB pivot (great "tell me about a hard design decision" story):**
- v1: login-first. `users.email NOT NULL`, `cases.user_id` required, redundant FKs.
- Problem: a victim without an account = no case. Email verification as a barrier for someone in crisis.
- v2: case-centric. `cases.user_id` is now **nullable** + an `anonymous_token`; cases live purely browser-local; login became an optional upgrade path for NGOs/lawyers. Evidence rows carry `sha256_hash`, `archive_url`, `classification_json`; a separate `legal_analysis` table holds the 2nd-layer output.

**Why open source:** victims shouldn't have to trust a black box; NGOs (e.g. HateAid) need to audit and self-host; prosecutors can verify the hash-chain logic line by line.

---

## 4. Technical question bank (with grounded answers)

**Q: How do you stop an LLM from hallucinating?**
Structured Outputs with a constrained schema (enum for categories, typed fields). The model physically cannot emit an out-of-schema value. Then a confidence threshold: below it, return an error, don't guess. SafeVoice's forbidden-laws guard hit 35/35 because of this, not because of prompt pleading.

**Q: How do you evaluate an LLM feature?**
Fixed eval corpus with expected outputs across multiple dimensions (severity exact-match, categories present, required laws present, forbidden laws absent). Pass = all dimensions. I iterate the prompt against the failing cases — that's how SafeVoice went 66% → 86%. The "forbidden absent" dimension is a false-positive guard; for a legal tool that matters more than raw accuracy.

**Q: How do you choose a model?**
On the cost/accuracy frontier for the *specific task*, not by raw capability. I ran the same production prompt across gpt-4o-mini / gpt-4.1-mini / gpt-5-mini — all 100% on the corpus, so I took the one that's 7.4× cheaper. Reasoning models earn their cost on long-context reasoning, not short-text classification. I'd re-run that comparison whenever a new mini-tier model ships.

**Q: How would you build a multi-provider LLM gateway?** (their actual mission area)
One internal API, provider behind it. Normalize request/response shapes; map each provider's structured-output / tool-calling dialect to a common interface. Failover chain with health checks (primary → secondary → tertiary), per-request cost + latency + token logging, and a circuit breaker so a provider outage degrades gracefully instead of failing the request. I'm mid-way extending SafeVoice from OpenAI-only to Anthropic + Gemini failover as a portfolio piece — same pattern.

**Q: RAG vs fine-tuning vs prompt engineering — when?**
Prompt eng first (cheapest, fastest to iterate — got me +20pp). RAG when the model needs facts it doesn't have or that change (e.g. current law text — that's exactly my planned GitLaw-as-API: an authoritative legal source the classifier queries instead of hardcoding statutes in a prompt). Fine-tuning last, only when prompt + RAG plateau and I have volume + a stable task.

**Q: How do you do cost control in production?**
Cost caps from day one. Per-request token + cost logging. Cheapest model that passes the eval. Cache where inputs repeat. (Honest gap I'm closing: I return usage but don't yet log it *per case* — that's a day of work and it makes cost observable per tenant, which is exactly what a multi-tenant platform needs.)

**Q: Tool-calling / agents — how do you keep them reliable?**
Constrain the tool schema, validate every tool result before feeding it back, cap the step count, and make each step's failure visible rather than silently retried. Same "no silent fallback" principle as classification — an agent that quietly does the wrong thing is worse than one that stops and says it's stuck.

**Q: How do you handle GDPR / EU data?** (their EU Data Layer mission)
Data minimization by design (collect only what the task needs — SafeVoice is anonymous-first), data residency in-region (Frankfurt: backend + Neon Postgres eu-central), right to erasure + data export built in, no content logging on the server path. SHA-256 + archive.org for independent verifiability without trusting the server.

---

## 5. System design prompt I should be ready for

**"Design a multi-tenant Corporate LLM platform."**
- **Tenancy:** row-level isolation in Postgres (tenant_id on every row) + per-tenant API keys; consider schema-per-tenant only if compliance demands hard isolation.
- **LLM Gateway:** single internal API, provider adapters behind it, failover + circuit breaker, per-tenant rate limits + cost budgets enforced at the gateway.
- **Observability:** per-request + per-tenant token/cost/latency logging (this is the metering layer billing depends on).
- **Data layer:** EU residency, encryption at rest, per-tenant data export + erasure.
- **Agent runtime:** sandboxed tool execution, step caps, structured-output validation at every hop.
- **Caching:** prompt/response cache keyed by tenant + input hash to cut cost.
Tie each piece back to something I've actually built in SafeVoice (cost caps, structured output, no silent fallback, Frankfurt residency).

---

## 6. Honest gaps and how I frame them

- **Next.js** — I use Vite SPA + Vercel Functions. Mental model is identical; ~1–2 weeks to daily-driver. (Mitigation: port one GitLaw route to Next.js before the interview so there's a real Next commit on GitHub.)
- **Drizzle / Supabase / Stripe** — not in my stack (I use Neon Postgres). Learnable in days. Don't claim them.
- **Multi-provider gateway** — currently OpenAI-only; actively extending to Anthropic + Gemini failover.
- **Big-OSS PRs** — my repos are my own; a small targeted PR to the Anthropic SDK or LangChain would prove "reads code, not just ships own repos."
- **Framing rule:** name the gap, give the bridge timeline, pivot to a transferable strength. Never bluff a checkbox they can verify against my GitHub.

---

## 7. Behavioral / STAR stories ready to tell

- **Hard design decision:** the anonymous-first DB pivot (threat model → schema rewrite).
- **Shipped under pressure:** 8 agents in 14 days; the Court-Prep agent (3h → 30s).
- **Real user impact:** GitLaw Pro saves the law firm's paralegal ~2.7h/day; SafeVoice built to HateAid-grade so an NGO would trust it.
- **Changed my mind from data:** assumed the strongest model would win → eval showed gpt-4o-mini ties gpt-5-mini at 7.4× less cost → switched.
- **Quality over shipping:** held SafeVoice to "professional NGO tool" bar, not "portfolio demo" — the tutor pushed me to explain *why* every design choice, not just that it works.

---

## 8. Questions I should ask them (signals seniority + de-risks the offer)

- How many of your people have actually become co-founders of follow-on ventures in the last 24 months? (Tests whether the "Found" path is real or a carrot.)
- What's the probation length and average tenure? ("A-Player team" can mean "hire fast, fire fast.")
- How do you transition a solo founder into a team contributor — what does the first 90 days look like?
- What does the LLM Gateway look like today — greenfield or already serving traffic?
- How do you measure quality of an AI feature internally — do you have eval infrastructure, or would I be building it?

---

## 9. One-line reminders for the room

- Lead with shipped systems + numbers, not credentials.
- "Schema is the safety belt." "No silent fallback." "Architecture beats prompting." "Cost is a design constraint."
- Name gaps honestly + give the bridge. A-Player teams reward honesty.
- 66% → 86%. 35/35 forbidden-laws guard. 7.4× cheaper, same accuracy. 3h → 30s. 2.7h/day saved.
