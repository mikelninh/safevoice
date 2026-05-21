"""
Court-Prep Agent — composes the court-prep tools with an opinionated system
prompt and a guarded `run_agent` invocation.

The agent's job is *preparation*: load case, compute Fristen, pick the right
Staatsanwaltschaft, archive at-risk URLs, draft per-platform NetzDG eml files,
and produce the final Strafanzeige PDF. It never sends. The caller (and the
caller's UI) is responsible for the human-in-loop step.

Why a dedicated module per agent: the system prompt is a piece of legal
engineering. Putting it next to the tools makes ownership obvious, lets the
eval set diff prompt revisions, and keeps `agent_loop.py` framework-shaped.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.services import agent_loop
from app.services.court_prep_tools import build_tools

logger = logging.getLogger(__name__)


# Bumped whenever the system prompt changes materially. Stored on the
# agent_runs row would be a nice future addition; for now lives next to the
# eval set so prompt-version + eval-pass-rate stay aligned.
PROMPT_VERSION = "court_prep_v1"


SYSTEM_PROMPT = """Du bist der Court-Prep-Agent für SafeVoice.

Deine Aufgabe: Aus einem dokumentierten Fall digitaler Gewalt ein vollständiges
Anzeige-Paket vorbereiten — Strafanzeige-PDF, ggf. NetzDG-Meldungen je Plattform,
Frist-Warnungen, zuständige Staatsanwaltschaft, Hinweis auf § 200a StPO. Du sendest
nichts; du baust nur die Artefakte zusammen. Die Anwält:in oder das Opfer reviewt
und sendet manuell.

ARBEITSWEISE
1. IMMER zuerst `read_case` aufrufen, um Case + Evidence + Klassifikationen zu laden.
2. Aus dem Read-Result extrahierst du:
   - Liste aller `applicable_laws` über alle Evidence-Items (deduplizieren)
   - Liste aller `categories` (deduplizieren)
   - `overall_severity` aus dem Case
   - `earliest_evidence_iso` = das früheste `timestamp_utc`
   - Plattform-zu-URL-Mapping für Re-Archivierung und NetzDG-Drafts
3. `check_strafantrag_frist` aufrufen mit `earliest_evidence_iso` + den deduplizierten Laws.
   Wenn `warning_level == "expired"` oder `"urgent"` → das ist eine Headline-Warnung
   im finalen Output.
4. `detect_anonymisierung_needed` aufrufen mit Categories + Severity.
5. `re_archive_urls` aufrufen mit allen Evidence-URLs, die ein `source_url` haben
   und (kein `archived_url` haben ODER auf einer High-Risk-Plattform liegen).
   Tool sortiert intern nach Risiko — übergib einfach alle Kandidaten.
6. Für jede einzigartige Plattform mit Evidence im Case → `draft_netzdg_email`.
   Wenn der User keinen Namen mitgegeben hat, ist das ok — die Email enthält
   dann Platzhalter, die später ausgefüllt werden.
7. Wenn der User einen Bundesland-Code mitgegeben hat → `determine_jurisdiction`.
   Wenn nicht → nicht aufrufen, der User wählt das später im UI.
8. `generate_strafanzeige_pdf` aufrufen mit den vorhandenen victim_*-Daten.
9. NUR wenn `bundesland_code` im User-Input als 2-Buchstaben-Code (BE, BY,
   NW, HE, …) tatsächlich vorhanden ist → `build_onlinewache_text` aufrufen.
   Wenn kein Bundesland gegeben ist (null, leerer String, "UNKNOWN", "—"):
   diesen Schritt **überspringen** und in der Zusammenfassung erwähnen:
   "Bundesland nicht gewählt — Onlinewache-Link wurde nicht generiert.
   Der User kann das später im UI nachholen." NIE mit Platzhaltern oder
   geratenen Codes aufrufen — der Tool-Output mit "UNKNOWN" ist nutzlos
   und verwirrt den User.

WENN DU FERTIG BIST
Antworte in 2-3 kurzen, FLIESS-TEXT-Sätzen auf Deutsch. WICHTIG:
- KEIN Markdown. KEINE **Sterne**. KEINE - Bullet-Listen. Keine Aufzählungen.
- WIEDERHOLE NICHT: Severity, Vorfall-Anzahl, Frist-Datum, StA-Adresse, §§-Liste.
  Die UI zeigt das alles bereits als eigene Karten — Wiederholung ist Lärm.
- Statt-dessen: 1 Satz zum Wesentlichen am Fall (z.B. "Beleidigung + Drohung
  über Instagram, einzelne Täter:in"), 1 Satz mit Hinweis auf besondere
  Aufmerksamkeit wenn relevant (Frist <14 Tage / doxxing / kritisch),
  1 abschließender Satz "Nichts wurde versendet — du wählst unten den Weg."

WICHTIG
- Keine Halluzinationen: nur Daten verwenden, die Tools dir geliefert haben.
- Wenn ein Tool einen `error` zurückgibt: erwähne den Fehler kurz in der Zusammen-
  fassung, bricht aber nicht ab. Andere Tools weiter ausführen.
- Maximal eine Tool-Aufruf-Runde pro Tool — du musst nicht 3x archive aufrufen.
"""


def run_court_prep(
    *,
    db: Session,
    case_id: str,
    victim_name: str | None = None,
    victim_email: str | None = None,
    victim_address: str | None = None,
    victim_phone: str | None = None,
    bundesland_code: str | None = None,
    relationship: str = "self",
    represented_name: str | None = None,
    user_id: str | None = None,
    max_iterations: int = 10,
    max_cost_usd: float = 0.50,
) -> agent_loop.AgentRunResult:
    """Run the Court-Prep agent for one case.

    The model is given the case_id and any victim data the caller supplies.
    Everything else flows through tools. The agent returns artefacts as base64
    blobs inside `tool_trace` — the calling route stores or returns them.
    """

    tools = build_tools(db)

    victim_block_parts = []
    if victim_name:
        victim_block_parts.append(f"- Name: {victim_name}")
    if victim_address:
        victim_block_parts.append(f"- Adresse: {victim_address}")
    if victim_email:
        victim_block_parts.append(f"- Email: {victim_email}")
    if victim_phone:
        victim_block_parts.append(f"- Telefon: {victim_phone}")
    if bundesland_code:
        victim_block_parts.append(f"- Bundesland: {bundesland_code}")
    victim_block = (
        "\n".join(victim_block_parts)
        if victim_block_parts
        else "(keine Opfer-Daten übergeben — Platzhalter im PDF bleiben)"
    )

    user_message = f"""Bereite das Strafanzeige-Paket für folgenden Fall vor.

case_id: {case_id}

Opfer-Daten:
{victim_block}

Beginne mit read_case und folge der Arbeitsweise aus den Anweisungen."""

    input_payload = {
        "case_id": case_id,
        "victim_name": victim_name,
        "victim_email": victim_email,
        "victim_address": victim_address,
        "victim_phone": victim_phone,
        "bundesland_code": bundesland_code,
        "relationship": relationship,
        "represented_name": represented_name,
        "prompt_version": PROMPT_VERSION,
    }

    return agent_loop.run_agent(
        db=db,
        agent_name="court_prep",
        system_prompt=SYSTEM_PROMPT,
        user_message=user_message,
        tools=tools,
        case_id=case_id,
        user_id=user_id,
        max_iterations=max_iterations,
        max_cost_usd=max_cost_usd,
        input_payload=input_payload,
    )


def summarise_artefacts(tool_trace: list[dict]) -> dict[str, Any]:
    """Distill the verbose tool_trace into a tidy artefacts dict for the
    response. Strips base64 blobs from the trace itself (kept only in the
    artefacts) so the trace is light enough to render in a UI."""
    artefacts: dict[str, Any] = {
        "strafanzeige_pdf_base64": None,
        "strafanzeige_filename": None,
        "netzdg_emls": [],
        "archived_urls": [],
        "frist": None,
        "anonymisierung": None,
        "jurisdiction": None,
        "onlinewache": None,
    }
    for call in tool_trace:
        out = call.get("output") or {}
        if call.get("error"):
            continue
        name = call.get("tool")
        if name == "generate_strafanzeige_pdf" and out.get("ok"):
            artefacts["strafanzeige_pdf_base64"] = out.get("pdf_base64")
            artefacts["strafanzeige_filename"] = out.get("filename")
        elif name == "draft_netzdg_email" and out.get("ok"):
            artefacts["netzdg_emls"].append(
                {
                    "platform": out.get("platform"),
                    "recipient": out.get("recipient"),
                    "subject": out.get("subject"),
                    "eml_base64": out.get("eml_base64"),
                    "filename": f"netzdg-{out.get('platform')}.eml",
                }
            )
        elif name == "re_archive_urls":
            artefacts["archived_urls"] = out.get("results") or []
        elif name == "check_strafantrag_frist":
            artefacts["frist"] = out
        elif name == "detect_anonymisierung_needed":
            artefacts["anonymisierung"] = out
        elif name == "determine_jurisdiction" and "staatsanwaltschaft" in out:
            artefacts["jurisdiction"] = out
        elif name == "build_onlinewache_text" and out.get("ok"):
            artefacts["onlinewache"] = {
                "bundesland_code": out.get("bundesland_code"),
                "bundesland_name": out.get("bundesland_name"),
                "onlinewache_url": out.get("onlinewache_url"),
                "text_for_paste": out.get("text_for_paste"),
                "instructions_de": out.get("instructions_de"),
            }

    return artefacts
