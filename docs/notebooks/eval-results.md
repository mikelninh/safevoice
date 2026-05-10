# SafeVoice classifier eval — `v1`

_Run: 2026-04-26 10:42:56 UTC · Prompt version: `v2` · 35 cases · 10 categories_

SafeVoice harassment classifier eval corpus — 35 cases across 10 categories. Designed for tutor-grade defence: covers calibration, edge cases, idiom traps, obfuscation, dog-whistles, stalking-with-context, and cross-language. Each case lists expected_severity (exact match), expected_categories (subset match), expected_law_codes (subset, MUST be present), forbidden_law_codes (MUST NOT appear — false-positive guard).

## Headline

- **Pass rate (all 4 dimensions): 30/35 (86%)**
- Severity exact-match: 33/35 (94%)
- Expected categories present: 31/35 (89%)
- Expected laws present: 30/35 (86%)
- Forbidden laws absent (false-positive guard): 35/35 (100%)
- Avg latency: 3126 ms

## Per-category pass rate

| Category | Cases | Passed | Severity | Categories | Laws-present | Forbidden-absent |
|---|---|---|---|---|---|---|
| A · baseline non-harassment | 3 | **3/3** | 3/3 | 3/3 | 3/3 | 3/3 |
| B · soft / borderline | 3 | **3/3** | 3/3 | 3/3 | 3/3 | 3/3 |
| C · direct insult § 185 | 4 | **2/4** | 3/4 | 3/4 | 2/4 | 4/4 |
| D · misogyny + obfuscation | 4 | **4/4** | 4/4 | 4/4 | 4/4 | 4/4 |
| E · implicit threats § 241 | 4 | **4/4** | 4/4 | 4/4 | 4/4 | 4/4 |
| F · explicit death threats | 4 | **4/4** | 4/4 | 4/4 | 4/4 | 4/4 |
| G · idiom traps | 4 | **4/4** | 4/4 | 4/4 | 4/4 | 4/4 |
| H · Nazi dog-whistles · § 130 | 4 | **3/4** | 4/4 | 3/4 | 3/4 | 4/4 |
| I · stalking § 238 with victim_context | 3 | **2/3** | 2/3 | 2/3 | 2/3 | 3/3 |
| J · cross-language | 2 | **1/2** | 2/2 | 1/2 | 1/2 | 2/2 |

## Failing cases (5)

Cases marked with the dimension they failed on. Use this list to drive prompt iteration.

| Case | Text | Expected | Got | Failed dimensions |
|---|---|---|---|---|
| `C3-public-defamation` | _Diese Person ist ein notorischer Lügner und Betrüger_ | **medium** | medium | missing-law |
| `C4-knowingly-false-claim` | _Ich habe gesehen, wie er Geld aus der Kasse genommen hat — d…_ | **high** | medium | severity (medium), categories, missing-law |
| `H4-volksverhetzung-direct` | _Diese Migranten sind alle Vergewaltiger und gehören vergast_ | **critical** | critical | categories, missing-law |
| `I2-stalking-pattern` | _Wieder so ein süßes Foto. Ich sehe dich auch gerne im roten …_ | **high** | low | severity (low), categories, missing-law |
| `J1-english-death-threat` | _I will find you and kill you, bitch_ | **critical** | critical | categories, missing-law |

## Per-case detail

| Case | Severity | Categories | Laws | Latency |
|---|---|---|---|---|
| `A1-baseline-greeting` | ✓ low (exp low) | ✓ got 1 | ✓ got NetzDG § 3 | 3675 ms |
| `A2-baseline-compliment` | ✓ low (exp low) | ✓ got 1 | ✓ got NetzDG § 3 | 2277 ms |
| `A3-baseline-disagreement` | ✓ low (exp low) | ✓ got 1 | ✓ got NetzDG § 3 | 3250 ms |
| `B1-soft-insult` | ✓ low (exp low) | ✓ got 1 | ✓ got § 185 StGB, NetzDG § 3 | 3199 ms |
| `B2-rude-but-not-criminal` | ✓ low (exp low) | ✓ got 1 | ✓ got NetzDG § 3 | 3590 ms |
| `B3-mild-mockery` | ✓ low (exp low) | ✓ got 1 | ✓ got NetzDG § 3 | 2289 ms |
| `C1-direct-insult` | ✓ medium (exp medium) | ✓ got 1 | ✓ got § 185 StGB, NetzDG § 3 | 3093 ms |
| `C2-arschloch` | ✓ medium (exp medium) | ✓ got 1 | ✓ got § 185 StGB, NetzDG § 3 | 3504 ms |
| `C3-public-defamation` | ✓ medium (exp medium) | ✓ got 1 | ✗ got § 185 StGB, NetzDG § 3 | 3076 ms |
| `C4-knowingly-false-claim` | ✗ medium (exp high) | ✗ got 1 | ✗ got § 185 StGB, NetzDG § 3 | 3434 ms |
| `D1-misogyny-slur` | ✓ medium (exp medium) | ✓ got 2 | ✓ got § 185 StGB, NetzDG § 3 | 2283 ms |
| `D2-misogyny-obfuscated-asterisk` | ✓ medium (exp medium) | ✓ got 2 | ✓ got § 185 StGB, NetzDG § 3 | 2845 ms |
| `D3-misogyny-leetspeak` | ✓ medium (exp medium) | ✓ got 2 | ✓ got § 185 StGB, NetzDG § 3 | 2588 ms |
| `D4-misogyny-coded-slut` | ✓ medium (exp medium) | ✓ got 2 | ✓ got § 185 StGB, NetzDG § 3 | 3285 ms |
| `E1-implicit-threat-address` | ✓ high (exp high) | ✓ got 1 | ✓ got § 241 StGB, NetzDG § 3 | 2316 ms |
| `E2-implicit-threat-workplace` | ✓ high (exp high) | ✓ got 2 | ✓ got § 238 StGB, § 241 StGB, NetzDG § 3 | 4331 ms |
| `E3-implicit-threat-family` | ✓ high (exp high) | ✓ got 1 | ✓ got § 241 StGB, NetzDG § 3 | 2633 ms |
| `E4-conditional-threat` | ✓ high (exp high) | ✓ got 1 | ✓ got § 241 StGB, NetzDG § 3 | 2508 ms |
| `F1-explicit-death-threat` | ✓ critical (exp critical) | ✓ got 1 | ✓ got § 241 StGB, § 126a StGB, NetzDG § 3 | 3296 ms |
| `F2-death-threat-with-misogyny` | ✓ critical (exp critical) | ✓ got 2 | ✓ got § 241 StGB, § 126a StGB, § 185 StGB… | 2518 ms |
| `F3-death-threat-obfuscated` | ✓ critical (exp critical) | ✓ got 2 | ✓ got § 241 StGB, § 185 StGB, NetzDG § 3 | 2617 ms |
| `F4-suicide-incitement` | ✓ critical (exp critical) | ✓ got 2 | ✓ got § 241 StGB, NetzDG § 3 | 3561 ms |
| `G1-idiom-bringt-mich-um` | ✓ low (exp low) | ✓ got 1 | ✓ got NetzDG § 3 | 3163 ms |
| `G2-idiom-koennte-sterben` | ✓ low (exp low) | ✓ got 1 | ✓ got NetzDG § 3 | 2546 ms |
| `G3-idiom-tot-fuer-mich` | ✓ low (exp low) | ✓ got 1 | ✓ got NetzDG § 3 | 3017 ms |
| `G4-hyperbole-headshot` | ✓ low (exp low) | ✓ got 1 | ✓ got NetzDG § 3 | 2770 ms |
| `H1-nazi-88` | ✓ high (exp high) | ✓ got 1 | ✓ got § 130 StGB, NetzDG § 3 | 2393 ms |
| `H2-nazi-1488` | ✓ high (exp high) | ✓ got 1 | ✓ got § 130 StGB, NetzDG § 3 | 3731 ms |
| `H3-nazi-14-words` | ✓ high (exp high) | ✓ got 1 | ✓ got § 130 StGB, NetzDG § 3 | 3668 ms |
| `H4-volksverhetzung-direct` | ✓ critical (exp critical) | ✗ got 1 | ✗ got § 130 StGB, NetzDG § 3 | 4182 ms |
| `I1-stalking-ex-partner` | ✓ high (exp high) | ✓ got 2 | ✓ got § 238 StGB, § 241 StGB, NetzDG § 3 | 2960 ms |
| `I2-stalking-pattern` | ✗ low (exp high) | ✗ got 1 | ✗ got NetzDG § 3 | 2620 ms |
| `I3-coworker-pressure` | ✓ high (exp high) | ✓ got 2 | ✓ got § 185 StGB, § 241 StGB, NetzDG § 3 | 4734 ms |
| `J1-english-death-threat` | ✓ critical (exp critical) | ✗ got 2 | ✗ got § 241 StGB, § 185 StGB, NetzDG § 3 | 3334 ms |
| `J2-mixed-de-en` | ✓ critical (exp critical) | ✓ got 2 | ✓ got § 241 StGB, § 185 StGB, NetzDG § 3 | 4152 ms |

## Conclusion

**86% pass rate is shippable but improvable.** Failing cases are the actionable list.

Re-run after prompt changes:
```bash
cd /Users/mikel/safevoice && source backend/venv/bin/activate && python scripts/run_eval.py
```

_Generated by `scripts/run_eval.py` · classifier prompt version `v2`._