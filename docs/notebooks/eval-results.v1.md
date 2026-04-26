# SafeVoice classifier eval — `v1`

_Run: 2026-04-26 10:21:22 UTC · Prompt version: `v1` · 35 cases · 10 categories_

SafeVoice harassment classifier eval corpus — 35 cases across 10 categories. Designed for tutor-grade defence: covers calibration, edge cases, idiom traps, obfuscation, dog-whistles, stalking-with-context, and cross-language. Each case lists expected_severity (exact match), expected_categories (subset match), expected_law_codes (subset, MUST be present), forbidden_law_codes (MUST NOT appear — false-positive guard).

## Headline

- **Pass rate (all 4 dimensions): 23/35 (66%)**
- Severity exact-match: 26/35 (74%)
- Expected categories present: 29/35 (83%)
- Expected laws present: 26/35 (74%)
- Forbidden laws absent (false-positive guard): 34/35 (97%)
- Avg latency: 10788 ms

## Per-category pass rate

| Category | Cases | Passed | Severity | Categories | Laws-present | Forbidden-absent |
|---|---|---|---|---|---|---|
| A · baseline non-harassment | 3 | **3/3** | 3/3 | 3/3 | 3/3 | 3/3 |
| B · soft / borderline | 3 | **3/3** | 3/3 | 3/3 | 3/3 | 3/3 |
| C · direct insult § 185 | 4 | **0/4** | 1/4 | 3/4 | 0/4 | 4/4 |
| D · misogyny + obfuscation | 4 | **4/4** | 4/4 | 4/4 | 4/4 | 4/4 |
| E · implicit threats § 241 | 4 | **3/4** | 3/4 | 3/4 | 3/4 | 4/4 |
| F · explicit death threats | 4 | **4/4** | 4/4 | 4/4 | 4/4 | 4/4 |
| G · idiom traps | 4 | **2/4** | 2/4 | 3/4 | 3/4 | 3/4 |
| H · Nazi dog-whistles · § 130 | 4 | **1/4** | 2/4 | 3/4 | 3/4 | 4/4 |
| I · stalking § 238 with victim_context | 3 | **2/3** | 2/3 | 2/3 | 2/3 | 3/3 |
| J · cross-language | 2 | **1/2** | 2/2 | 1/2 | 1/2 | 2/2 |

## Failing cases (12)

Cases marked with the dimension they failed on. Use this list to drive prompt iteration.

| Case | Text | Expected | Got | Failed dimensions |
|---|---|---|---|---|
| `C1-direct-insult` | _Du bist eine erbärmliche Existenz_ | **medium** | low | severity (low), missing-law |
| `C2-arschloch` | _Du bist ein Arschloch_ | **medium** | low | severity (low), missing-law |
| `C3-public-defamation` | _Diese Person ist ein notorischer Lügner und Betrüger_ | **medium** | medium | missing-law |
| `C4-knowingly-false-claim` | _Ich habe gesehen, wie er Geld aus der Kasse genommen hat — d…_ | **high** | medium | severity (medium), categories, missing-law |
| `E3-implicit-threat-family` | _Hoffentlich ist deinen Kindern auf dem Schulweg nichts passi…_ | **high** | low | severity (low), categories, missing-law |
| `G3-idiom-tot-fuer-mich` | _Du bist tot für mich_ | **low** | medium | severity (medium) |
| `G4-hyperbole-headshot` | _Diese Niederlage hat mich umgehauen, voll der Headshot_ | **low** | ERR | severity (None), categories, missing-law, forbidden-law-present |
| `H1-nazi-88` | _Sieg, Brüder. 88!_ | **high** | medium | severity (medium) |
| `H2-nazi-1488` | _1488 forever, white pride_ | **high** | medium | severity (medium) |
| `H4-volksverhetzung-direct` | _Diese Migranten sind alle Vergewaltiger und gehören vergast_ | **critical** | critical | categories, missing-law |
| `I2-stalking-pattern` | _Wieder so ein süßes Foto. Ich sehe dich auch gerne im roten …_ | **high** | low | severity (low), categories, missing-law |
| `J1-english-death-threat` | _I will find you and kill you, bitch_ | **critical** | critical | categories, missing-law |

## Per-case detail

| Case | Severity | Categories | Laws | Latency |
|---|---|---|---|---|
| `A1-baseline-greeting` | ✓ low (exp low) | ✓ got 1 | ✓ got NetzDG § 3 | 3294 ms |
| `A2-baseline-compliment` | ✓ low (exp low) | ✓ got 1 | ✓ got NetzDG § 3 | 3197 ms |
| `A3-baseline-disagreement` | ✓ low (exp low) | ✓ got 1 | ✓ got NetzDG § 3 | 22246 ms |
| `B1-soft-insult` | ✓ low (exp low) | ✓ got 1 | ✓ got NetzDG § 3 | 2586 ms |
| `B2-rude-but-not-criminal` | ✓ low (exp low) | ✓ got 1 | ✓ got NetzDG § 3 | 2368 ms |
| `B3-mild-mockery` | ✓ low (exp low) | ✓ got 1 | ✓ got NetzDG § 3 | 2075 ms |
| `C1-direct-insult` | ✗ low (exp medium) | ✓ got 1 | ✗ got NetzDG § 3 | 3292 ms |
| `C2-arschloch` | ✗ low (exp medium) | ✓ got 1 | ✗ got NetzDG § 3 | 2760 ms |
| `C3-public-defamation` | ✓ medium (exp medium) | ✓ got 1 | ✗ got § 185 StGB, NetzDG § 3 | 15670 ms |
| `C4-knowingly-false-claim` | ✗ medium (exp high) | ✗ got 1 | ✗ got § 185 StGB, NetzDG § 3 | 16155 ms |
| `D1-misogyny-slur` | ✓ medium (exp medium) | ✓ got 2 | ✓ got § 185 StGB, NetzDG § 3 | 3298 ms |
| `D2-misogyny-obfuscated-asterisk` | ✓ medium (exp medium) | ✓ got 2 | ✓ got § 185 StGB, NetzDG § 3 | 14813 ms |
| `D3-misogyny-leetspeak` | ✓ medium (exp medium) | ✓ got 2 | ✓ got § 185 StGB, NetzDG § 3 | 15413 ms |
| `D4-misogyny-coded-slut` | ✓ medium (exp medium) | ✓ got 2 | ✓ got § 185 StGB, NetzDG § 3 | 15369 ms |
| `E1-implicit-threat-address` | ✓ high (exp high) | ✓ got 1 | ✓ got § 241 StGB, NetzDG § 3 | 3415 ms |
| `E2-implicit-threat-workplace` | ✓ high (exp high) | ✓ got 2 | ✓ got § 238 StGB, § 241 StGB, NetzDG § 3 | 14750 ms |
| `E3-implicit-threat-family` | ✗ low (exp high) | ✗ got 1 | ✗ got NetzDG § 3 | 14396 ms |
| `E4-conditional-threat` | ✓ high (exp high) | ✓ got 1 | ✓ got § 241 StGB, NetzDG § 3 | 14695 ms |
| `F1-explicit-death-threat` | ✓ critical (exp critical) | ✓ got 1 | ✓ got § 241 StGB, § 126a StGB, NetzDG § 3 | 2045 ms |
| `F2-death-threat-with-misogyny` | ✓ critical (exp critical) | ✓ got 2 | ✓ got § 241 StGB, § 126a StGB, § 185 StGB… | 14911 ms |
| `F3-death-threat-obfuscated` | ✓ critical (exp critical) | ✓ got 2 | ✓ got § 241 StGB, § 185 StGB, NetzDG § 3 | 14950 ms |
| `F4-suicide-incitement` | ✓ critical (exp critical) | ✓ got 2 | ✓ got § 241 StGB, NetzDG § 3 | 15728 ms |
| `G1-idiom-bringt-mich-um` | ✓ low (exp low) | ✓ got 1 | ✓ got NetzDG § 3 | 2267 ms |
| `G2-idiom-koennte-sterben` | ✓ low (exp low) | ✓ got 1 | ✓ got NetzDG § 3 | 15439 ms |
| `G3-idiom-tot-fuer-mich` | ✗ medium (exp low) | ✓ got 1 | ✓ got NetzDG § 3 | 15908 ms |
| `G4-hyperbole-headshot` | ✗ ERR (exp low) | ✗ got 0 | ✗ got  | 25471 ms |
| `H1-nazi-88` | ✗ medium (exp high) | ✓ got 1 | ✓ got § 130 StGB, NetzDG § 3 | 16167 ms |
| `H2-nazi-1488` | ✗ medium (exp high) | ✓ got 1 | ✓ got § 130 StGB, NetzDG § 3 | 3367 ms |
| `H3-nazi-14-words` | ✓ high (exp high) | ✓ got 1 | ✓ got § 130 StGB, NetzDG § 3 | 15602 ms |
| `H4-volksverhetzung-direct` | ✓ critical (exp critical) | ✗ got 1 | ✗ got § 130 StGB, NetzDG § 3 | 14929 ms |
| `I1-stalking-ex-partner` | ✓ high (exp high) | ✓ got 2 | ✓ got § 238 StGB, § 241 StGB, NetzDG § 3 | 2702 ms |
| `I2-stalking-pattern` | ✗ low (exp high) | ✗ got 1 | ✗ got NetzDG § 3 | 14920 ms |
| `I3-coworker-pressure` | ✓ high (exp high) | ✓ got 2 | ✓ got § 185 StGB, § 241 StGB, NetzDG § 3 | 15384 ms |
| `J1-english-death-threat` | ✓ critical (exp critical) | ✗ got 2 | ✗ got § 241 StGB, § 185 StGB, NetzDG § 3 | 14900 ms |
| `J2-mixed-de-en` | ✓ critical (exp critical) | ✓ got 2 | ✓ got § 241 StGB, § 185 StGB, NetzDG § 3 | 3115 ms |

## Conclusion

**66% pass rate is not yet defensible.** Iterate the prompt against the failing cases before claiming the model works.

Re-run after prompt changes:
```bash
cd /Users/mikel/safevoice && source backend/venv/bin/activate && python scripts/run_eval.py
```

_Generated by `scripts/run_eval.py` · classifier prompt version `v1`._