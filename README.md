# SafeVoice 🛡️

**Evidence-first AI for documenting digital harassment and preparing a human-reviewable case package.**

SafeVoice turns text, URLs and screenshots into a structured record: what happened, what evidence exists, which legal context may be relevant and what a person can review next.

**[Open the live beta →](https://safevoice-vert.vercel.app)** · [Portfolio](https://mikelninh.github.io/)

## Try the workflow

```text
text / URL / screenshot
          ↓
structured extraction
          ↓
classification + legal context
          ↓
evidence hash + source metadata
          ↓
case-level review
          ↓
report / submission draft
          ↓
human review before external action
```

The goal is not to replace a lawyer, police officer or court. It is to reduce the distance between **“this happened”** and **“I have an organised, inspectable record.”**

## Proof at a glance

| Signal | Current prototype |
| --- | --- |
| Evaluation corpus | **35 curated cases** |
| Full-pass cases | **30 / 35** |
| Severity agreement | **94%** |
| Category agreement | **89%** |
| Law-set agreement | **86%** |
| Forbidden-law false-positive check | **100%** |

These are curated evaluation cases — **not 35 real users or validated police cases**.

## What is implemented

- structured Pydantic outputs rather than unconstrained legal prose
- text, URL and screenshot intake
- SHA-256 evidence hashes, timestamps and source metadata
- browser-side integrity verification with Web Crypto
- multi-evidence case analysis
- reviewable PDF / export workflows
- bounded agent runtime with explicit tools, iteration limits and audit records
- approval checkpoint before any external action

## Architecture

```text
React / TypeScript
       ↓
FastAPI + Pydantic
       ↓
structured AI + vision
       ↓
evidence + case services
       ↓
bounded tool loop
       ↓
reviewable output
```

## Stack

**Python · FastAPI · Pydantic · React · TypeScript · Postgres · OpenAI structured outputs · Vision · SHA-256 · ReportLab**

## Why the boundaries matter

SafeVoice can help prepare and organise. It does **not** determine guilt, provide qualified legal advice or autonomously file consequential legal actions.

Before broader production use, the important next proof is not another feature. It is:

**real users → qualified reviewer corrections → regression cases → measurable outcomes**

## Run locally

```bash
# backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# frontend
cd ../frontend
npm install
npm run dev
```

LLM paths require an `OPENAI_API_KEY`.

---

Built by [Michael Ninh](https://mikelninh.github.io/) in Berlin.
