# SafeVoice

**A working closed-beta prototype for documenting online harassment, preserving evidence and preparing a human-reviewable case package.**

[Live beta](https://safevoice-vert.vercel.app) · [Portfolio](https://mikelninh.github.io/) · [Source](https://github.com/mikelninh/safevoice)

## What it does

SafeVoice turns text, URLs or screenshots into a structured workflow:

```text
INPUT
  ↓
CLASSIFY + EXTRACT
  ↓
PRESERVE EVIDENCE
  ↓
LEGAL CONTEXT
  ↓
REVIEWABLE REPORT / COURT-PREP PACKAGE
  ↓
HUMAN REVIEW BEFORE EXTERNAL ACTION
```

The goal is not to replace a lawyer or police decision. It is to reduce the friction between **“this happened to me”** and **“I have a structured, inspectable record I can review and use.”**

## Current state — August 2026

| Area | What works today | Boundary |
| --- | --- | --- |
| **Input** | Paste text, public URL intake and screenshot upload | Platform scraping is intentionally limited; screenshots are the reliable path for blocked platforms |
| **Classification** | Structured LLM output across the supported offence categories | Model output can still be wrong; high-stakes classifications require review |
| **Evidence** | SHA-256 content hashes, timestamps and browser-side hash verification | Hashes prove content consistency, not that the underlying allegation is true |
| **Case workflow** | Multi-evidence cases, legal context and follow-up analysis | Not a substitute for qualified legal advice |
| **Reports** | Reviewable PDF / export workflows and prepared submission text | External filing remains a human action |
| **Agent runtime** | Bounded court-prep workflow with tool audit, iteration/cost limits and approval gates | Not autonomous legal representation |

**Important:** SafeVoice is a working prototype / closed beta, not a broadly validated production service. Real-user and professional review is the next major proof.

## Evaluation — what the numbers actually mean

The classifier has a **35-case curated evaluation corpus** covering edge cases, obfuscation, stalking, threats and cross-language examples.

- **30 / 35 full-pass cases** in the stored evaluation run
- severity agreement: **94%**
- category agreement: **89%**
- law-set agreement: **86%**
- forbidden-law false-positive check: **100%**

These are **evaluation cases, not 35 real users or 35 validated police cases**. Failures remain important: for example, context-heavy stalking scenarios can be mis-scored, which is exactly why the product keeps a human-review boundary.

See the repository evaluation files for the exact cases and failure details.

## Why the system is interesting technically

### 1. Structured classification

The model returns constrained Pydantic outputs rather than free-form legal prose. Unsupported schema output fails closed instead of silently degrading to a weaker classifier.

### 2. Evidence integrity

Each evidence item can carry:

- SHA-256 content hash
- UTC timestamp
- source metadata
- archived URL when available
- browser-side verification with Web Crypto

### 3. Case-level analysis

Multiple evidence items can be reviewed together so the system can surface escalation patterns, stronger / weaker legal hypotheses and next-step deadlines while keeping the source material visible.

### 4. Human-supervised agent workflow

The court-prep agent uses explicit tools and runtime limits:

- bounded iterations
- bounded model cost
- idempotent tool calls
- `agent_runs` / `tool_calls` audit records
- approval checkpoint before external send

The design principle is simple: **prepare aggressively, act conservatively.**

## Main product flow

1. Add text, URL or screenshot.
2. Extract and classify the content.
3. Review severity, categories and supported legal context.
4. Save evidence with an integrity hash.
5. Combine evidence into a case.
6. Generate a reviewable report / court-prep package.
7. Human checks the result before any external submission.

## Stack

| Layer | Technology |
| --- | --- |
| Frontend | React · TypeScript · Vite |
| Backend | Python · FastAPI · Pydantic |
| AI | OpenAI structured outputs + Vision |
| Data | Postgres / SQLAlchemy |
| Evidence | SHA-256 + Web Crypto verifier |
| Reports | ReportLab + RFC 5322 email export |
| Agent runtime | bounded native tool loop + audit records |
| Deployment | Vercel; alternative container path retained |

## Useful repository paths

```text
backend/app/services/
  classifier*.py       structured classification
  legal_ai.py          case-level analysis
  evidence.py          evidence hashing
  agent_loop.py        bounded agent runtime
  court_prep_agent.py  orchestration
  court_prep_tools.py  explicit tools

frontend/src/
  pages/               product flows
  components/          evidence, reports, submission UX

evals/                 classifier / agent evaluation cases
docs/                  architecture, deployment and roadmap
```

## Run locally

```bash
# backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# frontend
cd ../frontend
npm install
npm run dev
```

The LLM paths require an `OPENAI_API_KEY`. Database configuration can use the documented local or hosted setup.

## Safety and legal boundary

SafeVoice provides structured information and evidence-preparation support. It does **not** determine guilt, replace legal advice, or make consequential legal decisions autonomously.

Before broader production use, I would want:

1. review on anonymised historical cases with qualified legal / NGO partners;
2. explicit agreement on severity and escalation criteria;
3. stronger regression coverage for context-heavy failures;
4. privacy / security review and operational procedures;
5. measurement of whether the resulting package actually saves reviewers time and improves evidence completeness.

## What I owned

I built the product end to end across the frontend, FastAPI backend, structured LLM flows, evidence model, reports, agent runtime, evaluation cases and deployment paths.

The next quality jump is not another feature. It is **real users → reviewer corrections → regression cases → measurable outcomes.**

---

Built by [Michael Ninh](https://mikelninh.github.io/) in Berlin.
