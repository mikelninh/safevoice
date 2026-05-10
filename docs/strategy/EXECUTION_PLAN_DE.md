# SafeVoice Execution Plan

## Company goal

Build the default supervised agentic evidence workflow for digital harm cases.

## Success definition

SafeVoice wins if a partner says:

- "Wir verlieren weniger Beweise."
- "Wir triagieren schneller."
- "Unsere Exporte und Reports sind endlich konsistent."
- "Eine Fachkraft schafft mehr Faelle mit weniger Chaos."

## North star

`Time from incident intake to export-ready case file`

Secondary metrics:

- percentage of incidents converted into structured case files
- percentage of critical cases triaged within target SLA
- report/export generation rate
- partner retention after 90 days
- average evidence items processed per caseworker
- percentage of cases with complete evidence chain

## Revenue model

### Phase 1: partner pilots

Sell:

- onboarding/setup
- organization pilot
- support and workflow tailoring

Example:

- `Setup`: EUR 1k - 5k
- `Pilot`: EUR 300 - 2,000 / month depending on partner size and workflow depth

Why:

- NGOs and institutions often buy through pilots first
- creates trust and real workflow signal

### Phase 2: organization subscription

Charge for:

- org base plan
- active caseworker seats
- evidence / storage / export volume
- premium partner modules

Example shape:

- `Org base`: EUR 199 - 799 / month
- `Seat`: EUR 29 - 99 / month
- `Premium exports / child-safety / legal modules`

### Phase 3: vertical modules and API

Upsells:

- SafeVoice Kids / child protection
- legal handoff pack
- school safety pack
- NGO coalition dashboard
- partner API / intake embeds

## Product roadmap

### Phase 0: wedge MVP

Goal:

Prove the evidence-to-action workflow for one strong partner type.

Must-have:

- text and upload intake
- classification
- case and evidence model
- evidence hash chain
- structured report export
- basic org access

Status:

- much of this already exists in early form

### Phase 1: production foundation

Goal:

Make the product safe for real partner use.

Must-have:

- org auth and roles
- tenant isolation
- strong audit trail
- secure storage
- data export / deletion basics
- privacy-ready intake and consent paths

### Phase 2: evidence intelligence

Goal:

Make SafeVoice dramatically better than manual documentation.

Must-have:

- OCR / screenshot text extraction
- link and media ingestion
- timeline reconstruction
- duplicate detection
- severity escalation logic
- multilingual classification and summarization

This is likely the biggest value unlock.

### Phase 3: agentic orchestration

Goal:

Move from isolated classification to supervised multi-agent case handling.

Must-have:

- intake agent
- evidence agent
- classification agent
- triage agent
- export/report agent
- follow-up recommendation agent

Output:

- next best action
- recommended export type
- urgency signals
- missing evidence checklist

### Phase 4: organization memory and network effects

Goal:

Make the product better inside each partner over time.

Must-have:

- pattern memory
- common escalation paths
- partner-specific playbooks
- repeated-harm clustering
- cross-case similarity retrieval

## Go-to-market

### Wedge market

Start with one of these, not all:

- NGOs / Opferhilfe
- child-safety partners
- legal aid / specialist law partners

My recommendation:

`NGOs and victim-support orgs first`

Why:

- strongest acute need
- less procurement friction than some public institutions
- more trust in pilot collaboration

### Sales motion

Initial:

- founder-led outreach
- 10-20 partner conversations
- 2-3 design partners
- 1-3 paid pilots

Message:

- less evidence loss
- faster triage
- cleaner escalation
- more cases handled without losing trust

### Best demo story

1. abusive message / screenshot comes in
2. SafeVoice extracts and hashes it
3. severity and categories are classified
4. timeline and case file are structured
5. report is generated for the right destination
6. partner sees next action and missing evidence

That is much stronger than just "AI detects harassment".

## 12-month execution plan

### Months 0-2

- sharpen company thesis and partner pitch
- choose first wedge partner type
- close 2-3 design partners
- audit current product against real workflow needs
- instrument core events

Deliverable:

- first paid or funded pilot

### Months 2-4

- auth / org / role foundations
- secure storage and evidence handling
- improved intake and report generation
- partner onboarding loop

Deliverable:

- real partner use on limited live cases

### Months 4-6

- OCR / media / multilingual evidence layer
- faster triage views
- export templates refined by partner feedback
- first case studies and proof

Deliverable:

- obvious product advantage over manual process

### Months 6-9

- agentic orchestration v1
- missing-evidence suggestions
- priority queues
- better follow-up workflows

Deliverable:

- caseworker productivity and response quality both improve

### Months 9-12

- pricing polish
- referral and partnership engine
- vertical modules
- stronger analytics and compliance exports

Deliverable:

- repeatable partner acquisition and retention

## Moat-building priorities

In order:

1. evidence integrity
2. workflow depth
3. secure partner trust
4. case memory
5. vertical specialization

Do not mistake "better classifier" for company moat.

## What to implement next

### Immediate company-building priorities

1. partner-facing pitch and pricing
2. org/tenant foundation gap sheet
3. strongest evidence-to-report demo flow
4. OCR/media ingestion
5. one clear export destination flow

### Product priorities in plain English

- stop treating it as just an analyzer
- finish the evidence workflow
- make it safe for partners
- make the reports and escalation path unreasonably better

## Risks

### Risk 1: too many buyer types

Mitigation:

- choose one wedge partner first

### Risk 2: AI overclaims

Mitigation:

- supervised workflow, visible confidence, human review

### Risk 3: trauma / trust mismatch

Mitigation:

- careful UX, partner-informed flows, privacy-first handling

### Risk 4: slow institutional adoption

Mitigation:

- start with NGOs and specialist partners before heavier public procurement

## One-sentence operating principle

`Turn fragile digital evidence into trusted, actionable case files.`
