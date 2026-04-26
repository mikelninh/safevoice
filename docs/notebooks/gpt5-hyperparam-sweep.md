# SafeVoice — `gpt-5-mini` reasoning_effort × verbosity sweep

Hyperparameter sweep on `gpt-5-mini` only, using the production few-shot CoT system prompt (the one that achieves 100% accuracy for every model in the main comparison). Isolates the *hyperparameter effect* from the *prompt effect*.

- Grid: **3 reasoning_effort levels** × **3 verbosity levels** × **6 test cases** = 54 calls
- Model: **gpt-5-mini**, `max_completion_tokens=4096`
- Pricing (EUR / 1M tokens): in=€0.233 · out=€1.860 · EUR/USD=0.93

## Accuracy heatmap (correct / 6)

| reasoning ↓ verbosity → | low | medium | high |
|---|---|---|---|
| **low** | 6/6 (100%) | 6/6 (100%) | 6/6 (100%) |
| **medium** | 6/6 (100%) | 6/6 (100%) | 6/6 (100%) |
| **high** | 6/6 (100%) | 6/6 (100%) | 6/6 (100%) |

## Cost heatmap (EUR for 6-case run)

| reasoning ↓ verbosity → | low | medium | high |
|---|---|---|---|
| **low** | €0.00618 | €0.00654 | €0.00662 |
| **medium** | €0.01030 | €0.01074 | €0.01326 |
| **high** | €0.02351 | €0.02903 | €0.03604 |

## Avg latency heatmap (ms)

| reasoning ↓ verbosity → | low | medium | high |
|---|---|---|---|
| **low** | 7397 ms | 8475 ms | 6964 ms |
| **medium** | 11001 ms | 12639 ms | 13143 ms |
| **high** | 29765 ms | 36795 ms | 32098 ms |

## Output tokens (total, 6-case run)

| reasoning ↓ verbosity → | low | medium | high |
|---|---|---|---|
| **low** | 2,150 | 2,343 | 2,383 |
| **medium** | 4,365 | 4,598 | 5,954 |
| **high** | 11,465 | 14,435 | 18,203 |

## Per-call details

| Case | R | V | Severity | Latency | In/Out tokens | Cost |
|---|---|---|---|---|---|---|
| `01-baseline` | low | low | low | 5659 ms | 1563/304 | €0.000929 |
| `02-soft-insult` | low | low | low | 5485 ms | 1563/349 | €0.001013 |
| `03-obfuscated-insult` | low | low | medium | 5966 ms | 1562/368 | €0.001048 |
| `04-implicit-threat` | low | low | high | 8720 ms | 1564/367 | €0.001046 |
| `05-death-threat` | low | low | critical | 10640 ms | 1570/412 | €0.001131 |
| `06-obfuscated-death` | low | low | critical | 7913 ms | 1567/350 | €0.001015 |
| `01-baseline` | low | medium | low | 6415 ms | 1563/241 | €0.000812 |
| `02-soft-insult` | low | medium | low | 9391 ms | 1563/422 | €0.001148 |
| `03-obfuscated-insult` | low | medium | medium | 8103 ms | 1562/458 | €0.001215 |
| `04-implicit-threat` | low | medium | high | 9020 ms | 1564/379 | €0.001069 |
| `05-death-threat` | low | medium | critical | 9116 ms | 1570/435 | €0.001174 |
| `06-obfuscated-death` | low | medium | critical | 8808 ms | 1567/408 | €0.001123 |
| `01-baseline` | low | high | low | 5236 ms | 1563/262 | €0.000851 |
| `02-soft-insult` | low | high | low | 8816 ms | 1563/499 | €0.001292 |
| `03-obfuscated-insult` | low | high | medium | 7384 ms | 1562/428 | €0.001159 |
| `04-implicit-threat` | low | high | high | 8012 ms | 1564/428 | €0.001160 |
| `05-death-threat` | low | high | critical | 6268 ms | 1570/379 | €0.001070 |
| `06-obfuscated-death` | low | high | critical | 6070 ms | 1567/387 | €0.001084 |
| `01-baseline` | medium | low | low | 9941 ms | 1563/635 | €0.001544 |
| `02-soft-insult` | medium | low | low | 8449 ms | 1563/576 | €0.001435 |
| `03-obfuscated-insult` | medium | low | medium | 10063 ms | 1562/629 | €0.001533 |
| `04-implicit-threat` | medium | low | high | 14104 ms | 1564/992 | €0.002209 |
| `05-death-threat` | medium | low | critical | 8745 ms | 1570/625 | €0.001528 |
| `06-obfuscated-death` | medium | low | critical | 14709 ms | 1567/908 | €0.002053 |
| `01-baseline` | medium | medium | low | 10986 ms | 1563/705 | €0.001675 |
| `02-soft-insult` | medium | medium | low | 11474 ms | 1563/756 | €0.001770 |
| `03-obfuscated-insult` | medium | medium | medium | 11473 ms | 1562/648 | €0.001568 |
| `04-implicit-threat` | medium | medium | high | 15649 ms | 1564/904 | €0.002045 |
| `05-death-threat` | medium | medium | critical | 14511 ms | 1570/762 | €0.001782 |
| `06-obfuscated-death` | medium | medium | critical | 11744 ms | 1567/823 | €0.001895 |
| `01-baseline` | medium | high | low | 9101 ms | 1563/611 | €0.001500 |
| `02-soft-insult` | medium | high | low | 12039 ms | 1563/802 | €0.001855 |
| `03-obfuscated-insult` | medium | high | medium | 12779 ms | 1562/897 | €0.002032 |
| `04-implicit-threat` | medium | high | high | 18122 ms | 1564/1423 | €0.003010 |
| `05-death-threat` | medium | high | critical | 13068 ms | 1570/1113 | €0.002435 |
| `06-obfuscated-death` | medium | high | critical | 13752 ms | 1567/1108 | €0.002425 |
| `01-baseline` | high | low | low | 16633 ms | 1563/1276 | €0.002737 |
| `02-soft-insult` | high | low | low | 19296 ms | 1563/1656 | €0.003444 |
| `03-obfuscated-insult` | high | low | medium | 82623 ms | 1562/1883 | €0.003866 |
| `04-implicit-threat` | high | low | high | 20565 ms | 1564/2209 | €0.004472 |
| `05-death-threat` | high | low | critical | 18997 ms | 1570/2032 | €0.004145 |
| `06-obfuscated-death` | high | low | critical | 20479 ms | 1567/2409 | €0.004845 |
| `01-baseline` | high | medium | low | 13928 ms | 1563/1419 | €0.003003 |
| `02-soft-insult` | high | medium | low | 17658 ms | 1563/1754 | €0.003626 |
| `03-obfuscated-insult` | high | medium | medium | 30006 ms | 1562/2691 | €0.005368 |
| `04-implicit-threat` | high | medium | high | 31771 ms | 1564/3355 | €0.006604 |
| `05-death-threat` | high | medium | critical | 101450 ms | 1570/2754 | €0.005487 |
| `06-obfuscated-death` | high | medium | critical | 25957 ms | 1567/2462 | €0.004944 |
| `01-baseline` | high | high | low | 28251 ms | 1563/2678 | €0.005344 |
| `02-soft-insult` | high | high | low | 43155 ms | 1563/3779 | €0.007392 |
| `03-obfuscated-insult` | high | high | medium | 27931 ms | 1562/2817 | €0.005603 |
| `04-implicit-threat` | high | high | high | 33959 ms | 1564/3368 | €0.006628 |
| `05-death-threat` | high | high | critical | 34717 ms | 1570/3083 | €0.006099 |
| `06-obfuscated-death` | high | high | critical | 24578 ms | 1567/2478 | €0.004973 |

## Conclusion

On this 6-case German harassment corpus, the cheapest `gpt-5-mini` configuration that maintains the production prompt's 100% accuracy is **reasoning_effort=low, verbosity=low** — €0.00618 for 6 calls, avg latency 7397 ms.

**What this tells us about gpt-5-mini for SafeVoice:**

- Best gpt-5-mini configuration costs **3.6× more** than `gpt-4o-mini + Production` (€0.00618 vs €0.00171 baseline).
- Latency vs baseline: -5878 ms (`gpt-4o-mini` baseline = 13,275 ms).
- **Reasoning_effort interpretation:** if `low` ties accuracy with `medium`/`high`, the reasoning premium adds nothing for this short-text classification. If `high` strictly improves accuracy, there's a ceiling that benefits from extra thinking.
- **Verbosity interpretation:** lower verbosity should reduce output tokens linearly. If accuracy is invariant to verbosity, always run with `verbosity=low` to cut output cost.
- **Production recommendation:** if no gpt-5-mini cell beats `gpt-4o-mini + Production` on the cost/accuracy frontier, `gpt-4o-mini` remains the production choice. Re-run this sweep on a larger (30-50 case) corpus before changing production model — 6 cases is too small a base to make irreversible decisions.

_Generated by `scripts/sweep_gpt5_hyperparams.py` · 54 calls._