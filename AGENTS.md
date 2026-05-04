# SafeVoice Agent Guide

## Mission
- Build SafeVoice as a protected evidence-to-action workflow for digital violence.
- Optimize for trust, reproducibility, and useful legal/NGO outputs.

## Product Thesis
- SafeVoice is not an open-ended AI playground.
- SafeVoice is a controlled pipeline:
  - intake / evidence capture
  - classification
  - case-level legal analysis
  - report / legal PDF / action output
- The goal is to produce reliable next steps for victims, NGOs, and legal partners.

## Priorities
- Controlled pipelines beat open-ended autonomy.
- Reproducibility beats novelty.
- Legal and evidence integrity beat stylistic polish.
- End-to-end usefulness matters more than isolated model outputs.
- If an AI layer is not visible in the final workflow, it is incomplete.

## Agent / AI Philosophy
- Use AI where it improves structured reasoning or actionability.
- Keep audit trails for important legal outputs.
- Prefer schema-validated outputs over loose text.
- Human review and downstream accountability must remain clear.

## Engineering Rules
- Preserve evidence integrity and chain-of-custody logic.
- Preserve multilingual clarity and legal disclaimers.
- When changing the legal layer, verify that the output is reflected in the final report surface.
- Prefer end-to-end tests for pipeline steps, not just unit tests in isolation.
- Do not introduce architectural complexity unless it clearly improves safety or workflow value.

## What Not To Build First
- Overly free-form agent orchestration without controls.
- Feature branches that bypass evidence integrity.
- Cosmetic AI layers that do not affect final case outputs.
- Premature scaling abstractions before the core legal/report path is strong.

## Collaboration Style
- Work autonomously by default.
- Ask fewer permission questions.
- Proceed directly with:
  - code changes
  - docs updates
  - local tests
  - build checks
  - non-destructive commands
- Only interrupt for approval when:
  - a destructive action is required
  - credentials, billing, or external systems are affected
  - there is a real product ambiguity
  - existing user changes create a direct conflict

## Expected Output Style
- Be concrete, direct, and test-oriented.
- Prefer verified changes over broad speculation.
- Report what works, what does not, and what remains open.
