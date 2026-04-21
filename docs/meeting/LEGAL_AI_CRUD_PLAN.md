# Legal-AI — Demonstrating DB + CRUD for the next tutor check-in
*Drafted 2026-04-21 · action item from today's meeting*

The mentor is asking: **does Legal-AI actually understand the database,
and can it perform CRUD operations across a case?** Today `legal_ai.py`
reads. The next check-in should show it reading *and* shaping the
record in a way that obviously uses the schema.

This is the shortest walkable path — keep the surface small, the story
clear.

---

## What the mentor wants to see

1. Legal-AI **reads** a case end-to-end (evidence + classifications) —
   already shipped.
2. Legal-AI **writes** something useful back to the DB — case-level
   fields derived from its analysis. This is the missing piece.
3. Legal-AI **updates** gracefully when new evidence arrives — the
   same case can be re-analyzed and the write target is an update,
   not a duplicate.
4. Legal-AI is **aware of the schema** in the analysis itself — the
   output references the structure, not just raw content.

---

## Target demo at next check-in

Under five minutes, walk the mentor through this sequence:

1. `POST /analyze/ingest` with one piece of evidence → case created,
   single classification.
2. `POST /analyze/ingest` with a second piece that changes severity
   — now the case has two classifications, new overall_severity.
3. `POST /analyze/case` — legal_ai reads all evidence + classifications
   for that case, synthesizes a case-level analysis, **writes**
   `case.summary`, `case.summary_de`, and a new
   `case_analyses` row (or field) with the structured output.
4. `GET /cases/{id}` — the mentor sees the synthesized analysis
   directly in the case record. The AI has left a measurable
   imprint on the DB.

---

## Concrete steps

### 1 · Add a `case_analyses` table

Store the full case-level analysis as a first-class row, not just a
cached string on the case. Preserves history when re-analyzed.

```python
class CaseAnalysis(Base):
    __tablename__ = "case_analyses"

    id = Column(String, primary_key=True, default=gen_uuid)
    case_id = Column(String, ForeignKey("cases.id"), nullable=False, index=True)
    strategy_summary = Column(Text, nullable=False)          # AI_POPULATED
    strategy_summary_de = Column(Text, nullable=False)       # AI_POPULATED
    applicable_paragraphs = Column(Text, nullable=False)     # AI_POPULATED (JSON array of §-refs)
    risk_assessment = Column(String, nullable=False)         # AI_POPULATED (low/medium/high)
    recommended_next_steps = Column(Text, nullable=False)    # AI_POPULATED (bullet list)
    evidence_gap_notes = Column(Text)                        # AI_POPULATED — what's missing?
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    model_used = Column(String, nullable=False)              # system_generated — audit trail
    prompt_version = Column(String, nullable=False)          # system_generated — v1, v2, ...
```

Add it to `database.py`, add the corresponding ALTER to
`_lightweight_migrations()` if the table doesn't exist — same pattern
we used for the auth columns.

### 2 · Expand `services/legal_ai.py`

Current `analyze_case_legally()` is read-only. Add a write path:

```python
def analyze_case_legally(case_id: str, db: Session) -> CaseAnalysis:
    # 1. RETRIEVE
    case = db.query(Case).filter_by(id=case_id).first()
    evidence = db.query(EvidenceItem).filter_by(case_id=case_id).all()
    classifications = db.query(Classification).join(EvidenceItem).filter(
        EvidenceItem.case_id == case_id
    ).all()

    # 2. AUGMENT
    context = _format_case_context(case, evidence, classifications)

    # 3. GENERATE (schema-enforced via Pydantic)
    result = client.chat.completions.parse(
        model="gpt-5",
        reasoning_effort="medium",
        verbosity="low",
        response_format=CaseAnalysisSchema,
        messages=[
            {"role": "system", "content": CASE_SYSTEM_PROMPT},
            {"role": "user",   "content": context},
        ],
    )
    parsed = result.choices[0].message.parsed

    # 4. WRITE BACK — this is the CRUD demonstration the mentor wants
    row = CaseAnalysis(
        case_id=case_id,
        strategy_summary=parsed.strategy_summary,
        strategy_summary_de=parsed.strategy_summary_de,
        applicable_paragraphs=json.dumps([p.value for p in parsed.paragraphs]),
        risk_assessment=parsed.risk_assessment.value,
        recommended_next_steps=parsed.recommended_next_steps,
        evidence_gap_notes=parsed.evidence_gap_notes,
        model_used="gpt-5",
        prompt_version=CASE_PROMPT_VERSION,
    )
    db.add(row)

    # 5. UPDATE the case itself — the human-facing surface
    case.summary = parsed.strategy_summary
    case.summary_de = parsed.strategy_summary_de
    case.overall_severity = parsed.risk_assessment.value  # recomputed
    case.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(row)
    return row
```

### 3 · Wire the router

`POST /analyze/case` — already exists, now returns the `case_analyses`
row. `GET /cases/{id}` — already joins classifications, extend to join
the latest `case_analysis` row so the frontend can show the synthesized
legal strategy.

### 4 · Script the demo — three curls the mentor can watch

```bash
# 1. First evidence
curl -X POST https://.../api/analyze/ingest \
  -H "Content-Type: application/json" \
  -d '{"content": "Ich bringe dich um", "victim_context": "..."}'
# → returns case_id

# 2. Second evidence for same case
curl -X POST https://.../api/cases/$CASE/evidence \
  -H "Content-Type: application/json" \
  -d '{"content_type": "text", "text": "Ich weiß wo du arbeitest"}'

# 3. Case-level analysis — this is the CRUD demonstration
curl -X POST https://.../api/analyze/case/$CASE
# → reads all evidence + classifications, writes new case_analysis row,
#   updates case.summary, returns the synthesized analysis

# 4. Verify the write happened
curl https://.../api/cases/$CASE
# → case.summary is now AI-populated from the case-level analysis
```

The mentor sees, in order: **read** → **think** → **write** → **update**.
That's CRUD demonstrated.

---

## Why this is the right demo

- Uses the table semantics you already labeled (USER INPUT / AI POPULATED
  / system generated) — the `case_analyses` row is AI_POPULATED end-to-
  end, with system_generated audit fields (`model_used`, `prompt_version`).
- Shows the same Structured Outputs pattern as the single-evidence
  classifier, just at a different granularity — consistency across the
  AI layer.
- Makes the schema visibly load-bearing: you can answer *"Why does
  `case_analyses` exist as a separate table?"* with the same argument
  we use for `classifications` — re-analysis without mutating history.
- Gives the tutor a tangible artifact to scroll through: three curl
  commands + a `GET /cases/{id}` showing the AI's imprint on the DB.

---

## Timeline

- **Tomorrow**: add the `case_analyses` model + the `analyze_case_legally`
  write path (~2 hours)
- **Day after**: update the prompt for case-level analysis, run the
  three-curl script end-to-end, capture outputs (~1 hour)
- **Day 3**: update `DEMO_SLIDES.html` slide for Action 5 to include
  the new CRUD arc (~30 min)

Total: ~3 hours of focused work. Fits inside next week's tutor action
items alongside the classifier experiments.
