# Changelog

## 2026-04-18

- Hara copy sweep: dropped decorative adjectives and emoji from CTAs
  (`Recommended` no longer prefixed with ✨; email/mailto/copy/upload
  buttons lost their 📧📋📨⬇🛡🌐 emoji).
- Replaced generic error states ("Something went wrong", "Unknown error",
  "Analysis failed", "Failed to send") with specific truth in DE/EN,
  naming the actual failure and the next step
  (e.g. "Classifier nicht erreichbar. Bitte erneut versuchen.").
- Loading states now name the step instead of showing "Loading…"
  (`Classifier läuft`, `Aggregat-Statistik wird geladen…`, `.eml wird
  vom Server gebaut…`, etc.).
- Footer rebuilt at Impressum-grade: operator name (from
  `VITE_OPERATOR_NAME`, falls back to `Mikel Ninh`), last-updated date,
  source link, license link, changelog link. Two-link legal footer
  replaced.
- Trailing `!` removed from copy-success toasts (`Kopiert!` → `Kopiert`,
  `Copied!` → `Copied`).
- "Now" / "Jetzt" stripped from the login CTAs
  (`Sign in now (Demo)` → `Sign in (Demo)`).
