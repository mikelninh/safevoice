# SafeVoice Court-Prep Gauntlet Optimizer

Run this programme **offline only** with synthetic/anonymised fixtures. Never contact authorities, send reports, mutate live cases or use real victim data.

1. Run the complete frozen Court-Prep evaluation suite.
2. Record hard-gate status first, then task/tool/evidence metrics.
3. Inspect failures and identify one general root cause.
4. Form one falsifiable hypothesis.
5. Change one coherent surface only: prompt, tool description, sequencing rule, recovery rule or uncertainty policy.
6. Rerun every case, including adversarial evidence and retry/idempotency cases.
7. If any hard gate fails, `REVERT` immediately.
8. Otherwise `KEEP` only if held-out task fitness improves without a legal-grounding regression.
9. Record hypothesis, diff, metrics, costs and decision in Git.

Safety is lexicographically prior to aggregate score. A candidate that completes more tasks by becoming more aggressive is worse if it weakens human approval, privacy, legal grounding, auditability or loop limits.
