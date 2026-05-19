# Agent Masterplan — Mai 2026

> **Quergültig für SafeVoice · GitLaw · GitLaw Pro · PMM.**
> Stand: 2026-05-19. Single source of truth für die agentic-AI-Initiative.

---

## Why agentic now

Drei Gründe:

1. **Wir haben das Fundament schon.** LLM-Gateway mit cost-tracking, Structured Outputs mit Pydantic/Zod, Eval-Harness mit Retrieval@k+LLM-judge, audit-tables. Was fehlt ist nur der Agent-Loop *on top*.
2. **Die teuren Workflows sind die agentic Workflows.** Strafanzeige vorbereiten, Behörden-Brief beantworten, Sachstand schreiben — das sind multi-step Choreographien, die heute manuell stundenlang dauern.
3. **Demo-Story.** „Single LLM call" ist 2023. „Agent mit 6 Tool-Calls die in 30s ein juristisches Paket baut" ist 2026.

## Decision: native, kein LangChain

OpenAI native `tools` parameter + function-calling. Kein LangChain für die initialen Builds.

**Warum:**
- Less magic, mehr debug-bar — kritisch für legal-tech defensibility
- Der LLM-Gateway ist schon native — extending ist ~40 LOC
- LangChain v0 → v1 breaking changes, abandoned LangServe, etc. — wir bleiben portabel
- Interview-Antwort wird stärker: *„Ich habe den Loop nativ gebaut um zu verstehen was Frameworks abstrahieren, dann LangChain/LangGraph evaluiert."* Senior-tier vs. junior-tier.

**Trotzdem auf dem Radar:**
- **LangSmith für Tracing** — funktioniert auch mit native Loops, gute Wahl wenn wir skalieren
- **LangGraph** — wenn wir mehrere Agents komponieren (Strafanzeige-Agent ruft Recherche-Agent ruft Schreiben-Agent), dann ggf. switchen

## Shared Agent-Loop Architecture

Eine Implementierung — beide repos verwenden sie. SafeVoice in Python (`services/agent_loop.py`), GitLaw in TypeScript (`api/_agent.ts`).

### Kern-Contract

```python
def run_agent(
    *,
    system_prompt: str,
    user_message: str,
    tools: list[ToolDef],          # JSON-schema + handler-name
    tool_handlers: dict[str, Callable],
    db, agent_run_id: str,
    max_iterations: int = 10,
    max_cost_usd: float = 0.50,
    model: str = "gpt-4o-mini",
) -> AgentRunResult
```

### Eingebaute Safety-Guards (non-negotiable von Tag 1)

| Guard | Implementierung |
|---|---|
| **max_iterations** | Hart-Cap 10. Abbruch mit `agent_iteration_limit` error. |
| **max_cost_usd** | Default $0.50. Nach jedem Call summieren, bei Überschreitung abort. |
| **Idempotency** | Tool-Call key = `(agent_run_id, tool_name, sha256(input_json))`. In-run cache: gleicher key → cached result statt re-execute. |
| **agent_run_id in llm_usage** | LLM-Gateway extended um `agent_run_id` Spalte. Cost-Dashboard zeigt Strafanzeige-Run als 1 Zeile, nicht 7. |
| **Tool-Call audit log** | Jede Tool-Ausführung persistiert: input_json, output_json, latency_ms, cost_usd, error. Für legal-tech defensibility und debug. |
| **Human-in-loop checkpoint** | Agent baut Paket, sendet **nichts**. Externe Aktionen (email, Polizei) erfordern explizite User-Bestätigung. Non-negotiable für Legal. |
| **Eval-Set ab Tag 1** | `evals/agent_<name>.json` mit 5-10 Cases. Run nach jeder Prompt-Änderung. |

### Datenbank-Schemata (per repo, nicht shared)

```sql
-- agent_runs
CREATE TABLE agent_runs (
  id              text PRIMARY KEY,
  agent_name      text NOT NULL,        -- 'court_prep' | 'lebenslagen' | …
  user_id         text REFERENCES users(id),
  case_id         text,                 -- optional
  status          text NOT NULL,        -- 'running' | 'completed' | 'failed' | 'aborted_budget' | 'aborted_iterations'
  input_json      jsonb NOT NULL,
  output_json     jsonb,
  total_iterations integer DEFAULT 0,
  total_cost_usd  numeric(10, 6) DEFAULT 0,
  error           text,
  started_at      timestamptz NOT NULL DEFAULT now(),
  completed_at    timestamptz
);

-- tool_calls
CREATE TABLE tool_calls (
  id              text PRIMARY KEY,
  agent_run_id    text NOT NULL REFERENCES agent_runs(id),
  tool_name       text NOT NULL,
  input_json      jsonb NOT NULL,
  output_json     jsonb,
  input_hash      text NOT NULL,        -- for idempotency
  latency_ms      integer,
  cost_usd        numeric(10, 6) DEFAULT 0,
  cached          boolean DEFAULT false, -- true if idempotency hit
  error           text,
  called_at       timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_tool_calls_idempotency ON tool_calls(agent_run_id, tool_name, input_hash);
```

---

## Build Roadmap — was wir wann bauen

Sortiert nach **(impact × demoability) ÷ (effort × risk)**.

| # | Projekt | Agent | Geschätzter Aufwand | Status |
|---|---|---|---|---|
| **1** | **SafeVoice** | **Court-Prep Agent** | 1 Session (~3h) | **🔨 NOW** |
| 2 | GitLaw Citizen | Lebenslagen-Assistent | 1 Session (~4h) | spec'd |
| 3 | GitLaw Citizen | Gesetzes-Diff-Watcher | 1 Session (~3h, cron-basiert) | spec'd |
| 4 | GitLaw Pro | Behörden-Korrespondenz-Agent | 2 Sessions (~8h, OCR+DE/VI) | spec'd |
| 5 | GitLaw Pro | Fristen-Monitor + Untätigkeitsklage | 1 Session (~4h) | spec'd |
| 6 | GitLaw Pro | Document-Review-Agent (extend bulk) | 1 Session (~3h) | spec'd |
| 7 | GitLaw Pro | Mandant-Update-Agent (DE+VI weekly) | 1 Session (~4h) | spec'd |
| 8 | PMM | Steuerausgaben-Investigation | 2 Sessions (~8h, new data sources) | spec'd |

**Reihenfolge nicht zufällig:**
- #1 baut die Shared-Infra (agent_loop module, tables, eval pattern)
- #2 testet die Infra im zweiten repo (Python → TypeScript parity)
- #3 testet den Cron-getriebenen Pattern (nicht user-initiated)
- #4-#7 sind alle GitLaw-Pro-spezifisch → in einer „Pro Sprint" Woche bündeln
- #8 ist die PR-/Stiftungs-Bewerbungs-Story → eigenes Stück Arbeit

---

## #1 — SafeVoice Court-Prep Agent (now)

**Input:** `case_id`. Optional `victim_info` (Name, Adresse, Telefon, Email).

**Output:** `court_prep_package` mit:
- Strafanzeige-PDF (existing pdf_generator)
- NetzDG-Meldungs-emails als `.eml` Dateien pro Plattform
- Frist-Warnungen mit Dringlichkeit
- Zuständige Staatsanwaltschaft (Name, Adresse, Email)
- `§ 200a StPO Anonymisierungs-Antrag` als Anhang wenn nötig
- Liste re-archivierter URLs (für Beweissicherung)

**Tools (6):**

| Tool | Existing? | Notes |
|---|---|---|
| `read_case` | yes | DB read: case + evidence + classifications |
| `determine_jurisdiction` | new | PLZ Opfer + Plattform → StA. Tabelle StA pro Bundesland (16 entries). |
| `check_strafantrag_frist` | new | § 77 StGB Logik. 3-Monats-Frist für relative Antragsdelikte ab Kenntnis. |
| `detect_anonymisierung_needed` | new | Wenn evidence.classification.categories ∩ {doxxing, stalking} ≠ ∅ und severity ≥ high → true |
| `re_archive_urls` | yes | `evidence.archive_url_sync` für jede source_url |
| `draft_netzdg_email` | partial | per platform — existing eml_builder mit `report_type='netzdg'` |
| `generate_strafanzeige_pdf` | yes | existing pdf_generator |

**Agent Prompt-Schwerpunkt:**
- „Du bist ein juristischer Assistant für Opfer digitaler Gewalt."
- Zwingt zur Tool-Reihenfolge: read_case → check_frist → determine_jurisdiction → detect_anonymisierung → re_archive (parallel) → draft_emails → generate_pdf
- Output: structured summary mit allen Artefakten

**Endpoint:** `POST /agent/court-prep/{case_id}` → 200 mit `agent_run_id` + Polling-URL.

**Idempotency:** `re_archive_urls(url)` mit gleicher URL in einem Run → cached. Re-Run eines Cases → neuer `agent_run_id` aber `archive_url_sync` ist von sich aus idempotent (bestehender archive.org-Snapshot wird returned).

**Demo-Script:** `scripts/demo_court_prep.sh` — postet zu einem Test-Case, polled bis fertig, druckt Trace + Output.

**Eval:** `evals/agent_court_prep.json` mit 3 Cases (low/medium/high severity, je 1 doxxing-case für Anonymisierungs-Flag).

---

## #2 — GitLaw Citizen Lebenslagen-Assistent

**Input:** Free-text Beschreibung der Lebenslage (DE).

**Output:** Strukturiertes Paket:
- Identifizierte Lebenslage (`Mietrecht`, `Familienrecht`, …)
- Relevante §§ (mit Volltext + Verifikation)
- BGH/BVerfG-Leitsätze
- Frist-Calc wenn anwendbar
- Draft-Schreiben (aus Template, ausgefüllt)
- Empfehlung zur Eskalation (Mieterverein / Anwalt)

**Tools (5):**
- `detect_lebenslage(description)` — LLM classification gegen 12 Lebenslagen
- `search_laws(query, k=5)` — existing FAISS+BM25 hybrid
- `lookup_paragraph(law_abbr, paragraph)` — existing
- `search_leitsaetze(law_abbr, paragraph)` — existing curated DB
- `compute_frist(deadline_text, anchor_date)` — parse + add (new, ~30 LOC)
- `find_template(lebenslage, sub_type)` — match gegen 20 templates

**Endpoint:** `POST /api/agent/lebenslagen` (Vercel function in GitLaw repo)

**Implementation:** TypeScript version of agent_loop in `api/_agent.ts`.

---

## #3 — GitLaw Gesetzes-Diff-Watcher (cron-getrieben)

**Trigger:** weekly GitHub Action.

**Logic:**
1. `git diff` letzten 7 Tage gegen current `laws/` corpus
2. Für jeden geänderten §: LLM klassifiziert betroffene Lebenslagen
3. Match gegen User-Subscriptions (DB-Tabelle `gesetz_subscriptions`)
4. Pro User: aggregierte Email mit „Diese Woche relevant für deine abonnierten Themen"

**Tools:**
- `parse_law_diff(path_before, path_after)` — extracts changed paragraphs
- `classify_relevance(paragraph_diff, user_topics[])` — LLM
- `draft_user_digest(user, changes[])` — i18n

**Aufwand:** klein, weil 80% existing (du hast Reform-Diffs schon).

**Persistence:** `gesetz_subscriptions` Tabelle (user_id, topics[], email_freq).

---

## #4 — GitLaw Pro Behörden-Korrespondenz-Agent

**Input:** PDF-Drop in einer Akte (oder shared Drop-Zone).

**Output:**
- Akte-Match (welche Akte gehört das Dokument zu)
- Klassifizierung (`Nachforderung Dokumente` | `Anhörung` | `Bescheid` | `Terminladung` | `Sonstiges`)
- Draft-Antwort (DE) + Mandant-Notification-Email (DE oder VI je nach Mandant)
- Aktualisierte Checkliste (wenn z. B. „Reisepass angefordert" → markiert in der Pflichtdoc-Liste)
- Neue Frist im Heute-Widget
- **Status:** wartet auf Anwalt-Review im „Heute"-Panel

**Tools (8):**
- `ocr_pdf(file_id)` — existing
- `extract_aktenzeichen(text)` — LLM structured (regex backup)
- `match_akte(aktenzeichen, mandant_name)` — DB lookup
- `classify_letter_type(text)` — LLM enum
- `extract_demanded_documents(text)` — LLM structured (für Nachforderung)
- `update_checklist(akte_id, items_demanded)` — DB write
- `draft_mandant_notification(akte, demanded_docs, lang='de'|'vi')` — LLM with i18n template
- `draft_anwalt_response(akte, letter_type, content)` — LLM with branded letter template
- `set_frist(akte_id, days, type)` — DB write

**Endpoint:** `POST /api/pro/agent/behoerden-incoming`

**Critical safety:** Drafts only, no auto-send. „Bao reviews, 1-Klick send."

---

## #5 — GitLaw Pro Fristen-Monitor + Auto-Eskalations-Agent

**Trigger:** daily cron at 06:00 UTC.

**Logic:**
```
for akte in open_akten:
  for frist in akte.fristen:
    days_left = (frist.date - today).days
    if days_left == 14: draft_mandant_reminder(akte, lang=mandant.lang)
    if days_left == 3: draft_mandant_mahnung + queue_for_anwalt
    if days_left == 0 and frist.type == 'behoerden_frist_§75_VwVfG':
      draft_untaetigkeitsklage(akte, vg=zustaendig_for_bundesland(akte))
      queue_for_anwalt_with_red_flag
```

**Tools (4):**
- `walk_open_akten()` — DB read
- `draft_mandant_reminder(akte, days_left, lang)` — LLM templated
- `draft_untaetigkeitsklage(akte)` — LLM with Klage-Vorlage + Sachstand-Sync
- `notify_anwalt(task, priority)` — queue write

**Endpoint:** `/api/cron/fristen-monitor` (Vercel Cron).

---

## #6 — GitLaw Pro Document-Review-Agent (extend bulk-suggest)

Du hast `api/pro/document-bulk-suggest.ts` schon. Agentic erweiterung:

**New tools:**
- `extract_aktenzeichen_or_name(text)` — match gegen aktive Akten
- `gap_analysis(akte_id, current_docs[])` — welche Pflichtdocs fehlen jetzt
- `suggest_rename(text, doc_type)` — `Reisepass_Nguyen_2026-05-19.pdf`

**UI:** existing `BulkSuggestModal.tsx` erweitert um „Auto-route" Button.

---

## #7 — GitLaw Pro Mandant-Update-Agent

**Trigger:** Sunday 18:00 cron.

**Logic:**
```
for anwalt in active_anwaelte:
  for akte in anwalt.akten where status != closed:
    diff_since_last_update = get_changes(akte, since=last_update_sent)
    if diff is meaningful:
      sachstand = fill_template(akte.status, akte.mandatsart, lang=mandant.lang)
      queue_for_review_and_send(anwalt, akte, sachstand, attachments=diff.new_docs)
```

**Output:** „Diese Woche an Mandant:innen" panel mit 23 vorgeschlagenen Emails. Anwalt klickt „Alle 23 senden" oder reviewed einzeln.

---

## #8 — PMM Steuerausgaben-Investigation Agent

**Input:** Bürger:innen-Frage in natural language.

**Output:** Investigative report mit:
- Aggregierter Datentabelle
- Sankey diagram (visualisiert via D3/Plotly)
- Quellen-Liste mit Deep-Links zu bund.de Vergabe + BRH-Reports
- Auffälligkeiten („Top-3 Empfänger machen 35% aus")

**Tools (6):**
- `parse_haushaltsplan(year)` — PDF/JSON Quelle bund.de
- `search_vergabe(keyword, year)` — bund.de Vergabe-API
- `lookup_brh_report(thema, year)` — Bundesrechnungshof PDF-corpus
- `aggregate_recipients(transactions[])` — pandas-style group_by
- `build_sankey_data(transactions[])` — D3-format JSON
- `compose_report(question, findings)` — LLM with citation-strict prompt

---

## Investigative Journalism — Themen-Brainstorm

Weitere Ideen für PMM oder Spin-offs:

| Idee | Datenquellen | Killer-Story |
|---|---|---|
| **Bundestag-Vote-Tracker** | abgeordnetenwatch.de + Lobbyregister | Abweichler-Patterns, Mandant-Geld-Verbindungen |
| **Lobbyregister-Network** | lobbyregister.bundestag.de | Wer lobbyiert für wen, Verbindungen zu Gesetzgebungsverfahren |
| **Forschungsförderung-Flow** | DFG/BMBF + ORCID + Patente | Wo landet das Geld, was kommt raus |
| **Bauland-Bid-Tracker** | kommunale Bekanntmachungen | Preis vs. Marktwert, Käufer-Recherche |
| **Asylentscheid-Quoten** | BAMF-Statistik | Per Herkunft × Bundesland × Verfahrensart |
| **DSGVO-Bußgeld-Watcher** | LfDI-Pressemitteilungen | Wer bekommt Strafen, Branchen-Patterns |
| **Klima-Subventions-Cross-Check** | BMWi-Förderbescheide + Umweltbundesamt | Förder-Ziel vs. tatsächliche CO2-Reduktion |

**Top-2:** PMM Steuerausgaben + Bundestag-Vote-Tracker. Beide haben klare Datenquellen, beide haben visuelle Outputs, beide hätten Prototype-Fund-Förderfähigkeit.

---

## Interview-Story für Mikel (wenn alle 1-3 fertig sind)

> „Ich habe einen native Agent-Loop in Python + TypeScript gebaut — kein LangChain, weil ich verstehen wollte was Frameworks abstrahieren. Cost-Cap, Iteration-Cap, Idempotency-Keys und Tool-Call-Audit sind von Tag 1 dabei, weil das für legal-tech defensibility nicht optional ist.
>
> Der erste produktive Agent ist der Court-Prep-Agent in SafeVoice — gibt einer Person 30 Sekunden statt 3 Stunden Arbeit für eine Strafanzeige. 6 Tools, durchschnittlich 4-5 Iterationen, ~$0.05 pro Run, Human-in-Loop vor jedem externen Send.
>
> Eval-Set seit Tag 1, sodass Prompt-Änderungen messbar bessere/schlechtere Ergebnisse liefern. Cost-Dashboard zeigt pro `agent_run_id` aggregierte Kosten — wir können pro Feature und pro Tenant abrechnen."

---

## Konkrete nächste Schritte

1. **Today:** Court-Prep Agent fertig (siehe `#1`)
2. **Next session:** Lebenslagen-Assistent in GitLaw — re-uses pattern
3. **Next week:** Behörden-Korrespondenz für Pilot-Demo mit Bao
4. **Diese Quartal:** alle 8 produktiv

Status-Tracking via Commits. Kein Jira-Theater.
