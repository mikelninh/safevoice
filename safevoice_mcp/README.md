# SafeVoice MCP Server

**Model Context Protocol server for victim-of-digital-harassment tooling — classification, pattern detection, applicable statutes, Strafantrag-Fristen, jurisdiction, anonymisation.**

Built on top of the SafeVoice backend service layer. Same pattern as
[gitlaw-mcp](https://github.com/mikelninh/gitlaw/tree/main/gitlaw_mcp): a thin MCP
wrapper over a well-tested set of services, so any MCP client (Claude Desktop,
Cursor, custom agents) can call victim-protection logic as tools.

---

## Why this exists

When someone is being harassed online — cyberstalking, doxxing, coordinated
attacks, threats from an ex-partner — the path to legal protection is:

1. recognise *what kind* of harassment it is (categories, severity)
2. find *which statutes* apply in their jurisdiction (DE/AT/CH/UK)
3. compute *how much time* they have to file (Strafantragsfrist)
4. identify *who is responsible* for prosecution (Staatsanwaltschaft per Bundesland)
5. decide *whether to anonymise* the victim's identity in the filing (§ 68a StPO)

This is the workflow every Beratungsstelle, every Anti-Cyberbullying-NGO, every
pro-bono Anwältin does manually. SafeVoice MCP makes the LLM your assistant for
exactly that workflow — grounded in real German/Austrian/Swiss/UK statute data,
with deadlines computed deterministically (no hallucination).

---

## Tools exposed

| Tool | What it does |
|---|---|
| `classify(text, ...)` | LLM-based harassment classification → categories, severity, applicable §, audit-ready explanation. Bilingual (DE/EN), multi-jurisdiction. |
| `detect_patterns(evidence_items)` | Heuristic detection of coordinated attacks, escalation, repeat offenders across a case. No LLM call, sub-millisecond per item. |
| `get_applicable_laws(categories, country, severity)` | Map categories × country × severity → list of statutes with full reference, title, description, max penalty, official URL. |
| `check_strafantrag_frist(earliest_evidence_iso, applicable_laws)` | Compute Strafantragsfrist per §, flag urgent (<7 days) and expired. Pure date math. |
| `determine_jurisdiction(bundesland_code)` | Bundesland → responsible Staatsanwaltschaft (name, address, email, phone) + Rechtsgrundlage. |
| `detect_anonymisierung_needed(categories, severity)` | Flag whether the victim's identity should be anonymised in the filing per § 68a StPO. |

**Out of scope for v0.1** (db-coupled — these need a SQLAlchemy session and a case row, so they live in the backend for now):
- `generate_strafanzeige_pdf` — court-ready Strafanzeige with hashes/timestamps
- `draft_netzdg_email` — RFC 2822 NetzDG complaint per platform
- `build_onlinewache_text` — Polizei online-form payload

---

## Quickstart — Claude Desktop in one minute

The MCP server lives inside the SafeVoice monorepo because it imports the
backend service layer directly. Setup:

```bash
git clone https://github.com/mikelninh/safevoice
cd safevoice
pip install -e safevoice_mcp
pip install -r backend/requirements.txt    # service-layer deps
```

Then add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "safevoice": {
      "command": "safevoice-mcp",
      "env": {
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

Restart Claude Desktop. Try:

> *"Klassifiziere diesen Text auf Cyberstalking: 'Wenn du nochmal etwas postest, weiß ich wo du wohnst.' Welche Paragraphen greifen?"*

Five of the six tools work without `OPENAI_API_KEY` — only `classify` needs it. The
deterministic tools (laws, Fristen, jurisdiction, anonymisation, pattern detection)
run offline.

---

## Test coverage

```
23 passed, 1 skipped (llm-only) in ~1s
```

- **6 wrapper-contract tests** — every tool returns a dict, JSON-serialisable, never raises
- **4 classify tests** — graceful degradation when LLM unavailable, schema pinned when reachable
- **4 detect_patterns tests** — empty input, single item, multiple items, malformed input → clean error envelope
- **3 get_applicable_laws tests** — happy path + unknown country handling + shape pinning
- **4 check_strafantrag_frist tests** — 3-month window for § 185, expired detection, unparseable timestamp, unknown laws skipped
- **6 determine_jurisdiction tests** — Berlin specifics, all major Bundesländer resolve, case normalisation, unknown code → error envelope
- **3 detect_anonymisierung tests** — real schema (`needed/rechtsgrundlage/begruendung/triggering_categories`), low severity gate, empty categories handled

The wrapper contract is what we test here. The underlying service-layer correctness
lives in the [backend test suite](../backend/tests/).

---

## Architecture

```
┌──────────────────────┐
│  MCP Client          │  Claude Desktop, Cursor, custom agent
└──────────┬───────────┘
           │ tool call
           ▼
┌──────────────────────┐
│  safevoice_mcp       │  thin wrapper (this package)
│  /server.py          │  • request-id + latency logging per call
│                      │  • clean error envelopes (never leak exceptions)
│                      │  • Pydantic → plain dict at the MCP boundary
└──────────┬───────────┘
           │ direct import
           ▼
┌──────────────────────┐
│  backend/app/services/  ←  the actual intelligence
│  ├── classifier.py
│  ├── pattern_detector.py
│  ├── law_mapper.py
│  └── court_prep_tools.py
└──────────────────────┘
```

**Why this layout.** The MCP server is *deliberately not its own repo*. It lives
beside the backend it wraps. That means:

- No version drift between the wrapper and the services it exposes
- One PR updates both sides at once
- The wrapper stays small (one file, ~360 lines)
- The interesting code stays in the backend, where the tests already are

---

## Roadmap

- [ ] `generate_strafanzeige_pdf` — wire the db-coupled tools via a session factory
- [ ] `draft_netzdg_email` — same
- [ ] Hosted SSE deployment for non-local agents (Fly.io Frankfurt)
- [ ] Eval harness: GPT-4 with vs. without SafeVoice on N real harassment cases
      → measurable reduction in misclassification + missed Fristen
- [ ] Anthropic MCP directory submission

---

## License

MIT.
