# DSGVO Compliance — Documentation Pack

**Status:** draft. Must be reviewed by a qualified Datenschutzbeauftragte(r) / Rechtsanwalt before deployment with real org users.

**Purpose:** docs needed by NGOs (HateAid, etc.) before they can deploy SafeVoice under DSGVO Art. 28 (Auftragsverarbeitung).

## Contents

1. [Processing overview (Art. 30 Verzeichnis)](#1-processing-overview)
2. [Data Processing Agreement template (AVV)](#2-data-processing-agreement-avv)
3. [Data Protection Impact Assessment framework (DSFA)](#3-data-protection-impact-assessment)
4. [Data subject rights — how we honor them](#4-data-subject-rights)
5. [Sub-processors](#5-sub-processors)
6. [Deletion & retention](#6-deletion--retention)
7. [Breach notification procedure](#7-breach-notification-procedure)

---

## 1. Processing Overview

### Purposes of processing
1. **Classification of harassment content** under German criminal law (legitimate interest / user consent)
2. **Evidence preservation** with cryptographic integrity (court-ready PDFs)
3. **Organization-level case management** for NGOs supporting victims

### Data categories processed

| Category | Contents | Source | Sensitivity |
|----------|----------|--------|-------------|
| Identification | email, display_name | User | Standard |
| Evidence content | text, URLs, screenshots | User | Can contain Art. 9 sensitive data (political opinions, health, sexual orientation) because harassment often targets these traits |
| AI analysis | classifications, severity, summaries | System (AI) | Derived |
| Metadata | timestamps, hashes, session tokens | System | Standard |
| Session | IP addresses (logs), user-agent | System (limited retention) | Standard |

### Legal bases (Art. 6 DSGVO)

- **Art. 6(1)(a) Consent** — user explicitly agrees to terms during signup
- **Art. 6(1)(b) Contract** — processing necessary to provide the service
- **Art. 6(1)(f) Legitimate interests** — pursuit of criminal complaints, protection of data subjects from harm
- **Art. 9(2)(a) Explicit consent** — for sensitive data (classified as harassment often includes protected categories)
- **Art. 9(2)(f) Legal claims** — establishing, exercising, defending legal claims

### Data flows

```
User → Frontend (browser, no 3rd-party analytics)
     → Backend (FastAPI, our infra)
         → PostgreSQL (our infra)
         → OpenAI API (sub-processor, US w/ DPF)     ← see §5
         → Archive.org (sub-processor)
         → Supabase Auth (sub-processor, EU region)
         → Hetzner Object Storage (optional, screenshots)
```

---

## 2. Data Processing Agreement (AVV)

**Template** — to be filled out per deploying org.

### Parties
- **Controller:** [Org name, registered address, contact]
- **Processor:** SafeVoice [legal entity, registered address, contact]

### Scope
Controller uses SafeVoice to document and analyze digital harassment cases on behalf of data subjects who have consented to have their data processed.

### Processing instructions
The Processor processes personal data solely:
- as documented in this AVV
- on the Controller's written instructions (which may be given via the application configuration)
- in accordance with Art. 28(3) DSGVO

### Processor obligations
- Confidentiality of personnel (Art. 28(3)(b))
- Technical and organizational measures (Art. 28(3)(c) + §9)
- Engagement of sub-processors only with prior general written authorization (§6)
- Support Controller in fulfilling data subject requests (Art. 28(3)(e))
- Support Controller in Art. 32-36 obligations (Art. 28(3)(f))
- Delete or return all personal data at end of service (Art. 28(3)(g))
- Make available to Controller all information needed to demonstrate compliance (Art. 28(3)(h))

### Technical & Organizational Measures (TOMs)

| Area | Measure |
|------|---------|
| **Access control** | Role-based access (admin, caseworker, viewer); row-level security enforced at DB |
| **Transmission security** | TLS 1.3 required for all API + web traffic |
| **Input control** | Audit log of all writes (who, when, what) |
| **Availability** | Daily encrypted backups; RTO 24h, RPO 24h |
| **Separation** | Logical tenant isolation via org_id + RLS |
| **Encryption** | AES-256 at rest (PostgreSQL + object storage); keys managed by Supabase / Hetzner |
| **Pseudonymization** | Email used as identifier; no real names required |
| **Integrity** | SHA-256 hash chain on evidence (see `AI_FLOW.md`) |
| **Logging** | Application logs retained 30 days; audit logs retained 1 year |

### Sub-processors
See §5 below. Controller consents to listed sub-processors. Processor will notify Controller of changes with 30 days notice.

### Deletion
Upon contract termination, all Controller data is deleted within 30 days unless retention required by law (e.g., ongoing criminal proceedings). Deletion confirmed in writing.

---

## 3. Data Protection Impact Assessment

Because SafeVoice processes **Art. 9 sensitive data at scale** (harassment content often includes protected characteristics) and involves **new technology** (AI classification), a DSFA is mandatory (Art. 35 DSGVO).

### DSFA Scope
Required analysis:

1. **Systematic description of processing operations**
   - See §1 above
2. **Necessity and proportionality assessment**
   - Is processing necessary for the purpose? Yes — classification cannot be done without the content.
   - Is scope proportionate? Yes — only content the user submits is processed; no external data enrichment.
3. **Risk assessment**
   - See risks below
4. **Mitigation measures**
   - See §6 + TOMs

### Identified Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Unauthorized tenant access | Low | High | RLS + authorization checks + audit logs |
| OpenAI data retention | Medium | Medium | Use OpenAI enterprise tier (zero data retention) OR only process with user consent |
| Archive.org leaks | Low | Medium | Document the archival as part of consent flow |
| Re-identification from hashes | Very low | Low | SHA-256 of content, not of PII |
| Emergency delete misuse | Low | Low | Requires authentication; no recovery by design (intentional) |
| Classifier bias / wrongful conclusion | Medium | Medium | Tier disclosure (regex vs LLM); human review required before filing |

### Residual Risk Assessment

Medium-low residual risk given mitigations. Consultation with supervisory authority (LfDI) not required unless:
- Large-scale automated decisioning (we're not — human review required)
- Systematic monitoring of public spaces (we're not)

---

## 4. Data Subject Rights

| Right | How we implement |
|-------|------------------|
| **Art. 13/14 Information** | Privacy policy visible on every page; layered notice in onboarding |
| **Art. 15 Access** | `GET /auth/me` + `GET /cases/` returns all user data. Export as JSON available. |
| **Art. 16 Rectification** | `PUT /auth/me` for profile; evidence content cannot be edited (integrity) but user can delete + re-upload |
| **Art. 17 Erasure** | `DELETE /auth/me` (soft, 7 days) + `DELETE /auth/me/emergency` (immediate) |
| **Art. 18 Restriction** | Status field on cases; user can set to "restricted" (not implemented — Sprint 2) |
| **Art. 20 Portability** | JSON export of all user data via `/export` endpoint (MVP has PDF; JSON planned) |
| **Art. 21 Objection** | User can delete account; for legitimate-interest processing, we stop on objection |
| **Art. 22 Automated decisions** | Not applicable — classification is advisory, human reviews before acting |

### Response time
- Acknowledge within 3 business days
- Fulfill within 30 days (extendable once by 2 months per Art. 12(3))

### Contact
- **Data protection inquiries:** privacy@safevoice.example (placeholder — set up real mailbox)
- **Controller's DPO (per org):** filled by the org using SafeVoice

---

## 5. Sub-Processors

Current list — updated when changes occur.

| Sub-processor | Purpose | Location | Legal basis | Safeguards |
|--------------|---------|----------|------------|-----------|
| **OpenAI** | AI classification (tier 1) | US | DPF + SCCs | Zero-retention option for enterprise; user opt-out available |
| **Supabase** | Auth + DB hosting | EU (Frankfurt region) | AVV | EU-only infrastructure |
| **Hetzner** | Hosting + object storage | Germany | AVV | EU-only infrastructure |
| **Archive.org** | Evidence archival | US | Legitimate interest | Public-source archival only; no PII sent beyond URL |
| **Sentry** (if used) | Error monitoring | EU region | AVV | PII scrubbed from error payloads |

Changes to this list are notified 30 days in advance. Users/orgs can object.

---

## 6. Deletion & Retention

### Retention periods

| Data type | Retention | Trigger |
|-----------|-----------|---------|
| User account | Until deletion request | User-driven |
| Cases | Until case deletion | User-driven |
| Evidence | Until case deletion | Case deletion cascades |
| Audit logs | 1 year | Automatic rolling deletion |
| Application logs | 30 days | Automatic rolling deletion |
| Backups | 90 days | Rolling |
| Deleted account | 7 days (soft) then permanent | Two-stage soft delete |

### Emergency deletion
`DELETE /auth/me/emergency` — immediate hard delete of all user-owned data. No recovery. Designed for victims in immediate danger.

**Note:** Emergency delete does NOT propagate to backups immediately. Backup retention means data could exist in backup snapshots for up to 90 days. Document this in privacy policy.

---

## 7. Breach Notification Procedure

Per Art. 33/34 DSGVO.

### Detection & escalation

1. **Detection** — monitoring alerts (Sentry, DB audit logs, user reports)
2. **Assessment** — within 2 hours of detection
3. **Containment** — suspend affected systems if needed
4. **Notification to Controller** — within 24 hours if personal data involved
5. **Notification to supervisory authority** — within 72 hours if high risk
6. **Notification to data subjects** — without undue delay if high risk to them

### Breach categories (pre-classified)

| Type | Example | Severity |
|------|---------|----------|
| C1 Unauthorized access to tenant | Cross-org data leak via bug | High |
| C2 Credentials compromised | Session tokens leaked | High |
| C3 Backup exposure | Backup file unprotected | Medium |
| C4 Sub-processor breach | OpenAI incident | Varies |
| C5 Accidental disclosure | Email to wrong address | Low-medium |

### Notification template

(Fillable template to be created in `breach-notification-template.md` — not needed in MVP but required before HateAid deployment.)

---

## Checklist Before First Org Deployment

- [ ] Legal review of this document by qualified lawyer
- [ ] Privacy policy drafted and hosted (Impressum, Datenschutzerklärung in DE)
- [ ] AVV signed with deploying org
- [ ] DSFA completed and documented
- [ ] Technical measures verified (TLS, RLS, audit log, backups)
- [ ] Sub-processor agreements in place (OpenAI enterprise if available)
- [ ] Breach notification procedure tested (tabletop exercise)
- [ ] DPO contact published (or "no DPO required" justification documented — if org < 20 FTE + no special processing)
- [ ] Incident response runbook written

## Open Questions for Legal Review

1. Is our legitimate-interest basis for AI classification defensible given Art. 9 special categories? Or must we rely solely on explicit consent?
2. OpenAI's zero-retention tier requires Enterprise. Can we afford it, or must we use consent + accept the standard retention?
3. Archive.org archival creates a public URL of harassment content. Is this the right default, or should we offer opt-out?
4. Emergency delete breaks the hash chain for existing court exports. Does this create any legal issue for already-filed cases?

## Not in Scope for This Document

- Cookie consent banner (frontend only — Sprint 1 frontend work)
- Impressum text (standard German legal boilerplate — can copy from template)
- Insurance (D&O, cyber) — business operations, not technical
