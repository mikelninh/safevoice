# SafeVoice Kids — Branch README
*Branch: `safevoice-kids` · Parent: `main` · Created 2026-04-21*

This branch is the working surface for **SafeVoice Kids** — the
youth-protection variant of SafeVoice. Same classifier backbone, same
evidence chain, adapted for documenting digital violence against children
(cyberbullying, grooming, sexting pressure, Schulmobbing, §§ 184b / 131 /
180 StGB, Jugendschutzgesetz).

The adult SafeVoice remains live on `main`. This branch evolves in
parallel until the variant is ready to ship.

---

## Why a separate variant

| Dimension | SafeVoice (main) | SafeVoice Kids (this branch) |
|---|---|---|
| **Primary user** | Adult victim, self-service | Teacher / parent / Kinderschutzbund caseworker documenting on behalf of a child |
| **Legal scope** | StGB §§ 185, 186, 241, 238, 201a, 130 | + JSchG § 14, StGB §§ 131, 180, 184b/h; KJHG § 8a |
| **Consent model** | Adult self-consent | DSGVO Art. 8 — parental consent required under 16 |
| **Main categories** | threat, harassment, misogyny, scam | cyberbullying subtypes (exclusion, exposure, identity theft, sexting pressure, outing, violent content) |
| **Report destination** | Polizei · Strafanzeige | Jugendamt · Schulsozialdienst · Polizei-Jugendschutz |
| **Distribution** | NGO partners (HateAid, Weisser Ring) | Schools · Kinderschutzbund · Jugendämter |
| **Crisis-path link** | HateAid Beratung | Nummer gegen Kummer (116 111) + Krisentelefon |
| **Grant-fit** | BMJ, Prototype Fund | Aktion Mensch, BMFSFJ, BZgA, Länder |

## Code impact

**~80% reused** from main.

- ✅ Keep identical: classifier pipeline, Pydantic Structured Outputs, evidence hash chain, magic-link auth, PDF generator
- 🔄 Replace: category + law enums (different StGB paragraphs + JSchG)
- 🔄 Replace: system prompt (age-aware tone, youth-specific examples)
- ➕ Add: parental-gate component (DSGVO Art. 8 compliance)
- ➕ Add: school-dashboard view (one teacher handling many cases)
- ➕ Add: Jugendamt export format (KJHG § 8a report template)

## Milestones

| # | What | When |
|---|---|---|
| M1 | Branch + scope doc + landing-page concept | 2026-04-21 ✓ |
| M2 | Category + law enum replacement + system prompt variant | +1 week |
| M3 | Frontend brand variant (logo, hero, tone) | +2 weeks |
| M4 | Parental-gate + school-dashboard components | +3 weeks |
| M5 | Jugendamt/Polizei-Jugendschutz export templates | +4 weeks |
| M6 | Partner pilot (one Kinderschutzbund Ortsverein) | +6 weeks |
| M7 | Grant submission — Aktion Mensch + BMFSFJ | +8 weeks |

## Visual concept

Open `docs/meeting/safevoice-kids-concept.html` in your browser to see
the proposed landing-page tone for Kids — softer palette, youth-protection
framing, parent/teacher entry point.

## Decision authority

This branch exists as a living prototype, not a production deploy.
Merging to `main` is a policy decision — do not merge without a
partner-pilot letter of intent.

---

*Part of the `MASTER_PLAN_impact.md` vulnerable-population initiative.
Any new feature here must pass the three-question decision filter:*
1. *Who cannot defend themselves, and will this help them?*
2. *Will they actually use it — or is it for us to feel good?*
3. *Can we build it by extending what we already have?*
