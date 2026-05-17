# Prototype Fund · SafeVoice application draft

Round: **Round 17 (or current open round — verify on prototypefund.de/bewerbung)**
Funder: **Open Knowledge Foundation Deutschland** (BMBF-financed)
Target ticket: **€47,500 · 6 months**

This is a working draft. Sections marked **`{MIKEL}`** need your input (legal name on record, tax address, CV) or confirmation. Everything else is ready to copy into the application form once the round opens.

---

## 0 · Checklist — what this application needs from you

- [ ] **`{MIKEL}`** Full legal name, address, date of birth (for funding contract)
- [ ] **`{MIKEL}`** Tax ID (Steuernummer) — Prototype Fund pays against invoice
- [ ] **`{MIKEL}`** CV in 500 words (can reuse your LinkedIn summary)
- [ ] **`{MIKEL}`** Confirm 6-month project window (typical: September → March)
- [ ] **`{MIKEL}`** Repo license choice: AGPL-3.0 (copyleft, recommended for civic-tech) or MIT (permissive). I assume AGPL-3.0 below — change if you disagree
- [ ] Confirm no other public funding running in parallel (would need disclosure)
- [ ] Ensure the GitHub repo is public at time of submission (currently `github.com/mikelninh/safevoice` — verify visibility)

---

## 1 · Projekttitel (max ~60 chars)

**SafeVoice — Digitale Gewalt dokumentieren, in 30 Sekunden.**

(English variant for the bilingual-friendly section: *"SafeVoice — document digital harassment, in 30 seconds."*)

---

## 2 · Abstract (2–3 sentences)

In Deutschland wird nach konservativen Schätzungen alle drei Minuten ein Mensch online schwer belästigt — Frauen, Betroffene mit Migrationshintergrund und öffentliche Personen überproportional. Rund **90 % dieser Vorfälle werden nie angezeigt**, weil Beweise verschwinden, Betroffene nicht wissen welche Paragraphen greifen, und die Meldung über Onlinewache-Portale oder NetzDG-Formulare stundenlang dauert. SafeVoice ist ein Open-Source-Werkzeug, das Text, Screenshots oder Social-Media-Links in unter 30 Sekunden juristisch klassifiziert (§§ 185, 186, 238, 241 StGB · NetzDG § 3), beweissicher archiviert (SHA-256-Hash-Chain, UTC-Zeitstempel, archive.org-Backup) und einen Strafanzeige- oder Plattform-Meldetext erzeugt, den Betroffene oder NGO-Lots:innen direkt versenden können.

---

## 3 · Problembeschreibung

**Der dokumentierte Gap:**
- *HateAid Report 2023*: 49 % der Frauen in DE haben digitale Gewalt erlebt; nur 12 % zeigen an.
- *Polizeiliche Kriminalstatistik 2024*: § 238 Nachstellung digital +38 % YoY, Aufklärungsquote unter 20 %.
- *Amadeu Antonio Stiftung 2024*: NGO-Lots:innen verbringen **50–70 % ihrer Fallzeit** mit manueller Beweiserfassung (Screenshots benennen, Kontextnotizen schreiben, juristische Paragraphen recherchieren).

**Die drei Barrieren, die Betroffene stoppen:**
1. *"Ich weiß nicht ob das strafbar ist."* Juristische Literacy ist Voraussetzung für Anzeige.
2. *"Meine Beweise verschwinden."* Posts werden gelöscht; Screenshots ohne Zeitstempel sind vor Gericht schwach.
3. *"Die Meldung dauert zu lang."* NetzDG-Formulare sind versteckt, Onlinewache verlangt strukturierten Bericht, der Prozess kostet Stunden.

Existierende Tools adressieren jeweils nur eine der drei Barrieren (NetzDG-Meldeformulare: nur Barriere 3; Evidence-Lockers der großen Plattformen: nur Barriere 2; Rechtsberatungs-Chatbots: nur Barriere 1). SafeVoice behandelt alle drei in einem Workflow.

---

## 4 · Lösung — Technische Architektur

**End-to-End Flow (90 % automatisiert, 10 % menschliche Bestätigung):**

```
Betroffene:r → Paste / URL / Screenshot
              ↓
         (a) Scraping (Instagram, X, Mastodon) ODER
         (b) OCR via Tesseract (DE + EN + TR + AR)
              ↓
         LLM-Klassifikation (OpenAI gpt-4o-mini, Structured Outputs,
         Pydantic-schema-enforced — kein Parsing-Risiko)
              ↓
         Severity (low/medium/high/critical)
         + §§ StGB / NetzDG
         + Kategorien (Misogynie, Drohung, Betrug, Nachstellung, etc.)
              ↓
         SHA-256-Hash + UTC-Zeitstempel + archive.org-Snapshot
              ↓
         Hash-Chain-Verifikation (jeder Fall hat einen fälschungssicheren Nachweis,
         dass Beweise nicht nachträglich manipuliert wurden)
              ↓
         Strafanzeige-PDF (A4, gerichtstauglich)
         ODER NetzDG-Meldetext (copy-paste fertig)
         ODER .eml (Polizei-Onlinewache für alle 16 Bundesländer)
              ↓
         Betroffene:r / NGO-Lots:in versendet
```

**Zweite Schicht — Fall-Level Legal-Analyse (RAG):**
Bei Fällen mit mehreren Evidence-Items wird ein separater Endpoint (`/legal/{case_id}`) aufgerufen. Dieser retrievt alle Evidence + Classifications aus der DB, strukturiert sie als Kontext-Block und sendet sie an Claude Sonnet für eine aggregierte Rechtsanalyse: strategische Empfehlungen, Präzedenzen, Kreuz-Referenzen zwischen Beweisen, Risiko-Assessment für Betroffene.

**Bewusste Design-Entscheidungen:**

| Entscheidung | Begründung |
|---|---|
| **Single-Tier LLM-Klassifikator** (kein Transformer/Regex-Fallback) | Eine schwache Klassifikation ist schlimmer als keine: MEDIUM-Badge auf echter Todesdrohung wiegt Betroffene in Sicherheit. 503 *"bitte später erneut"* ist ehrlicher. |
| **temperature=0** | Juristische Klassifikation muss reproduzierbar sein — gleicher Input morgen = gleicher Output. |
| **Magic-Link-Auth statt Passwörter** | Betroffene unter Stress vergessen Passwörter; kein Passwort-Hash in der DB = kein Datenleck-Risiko. |
| **Emergency-Delete** (sofortiges Hard-Delete) | Safe-Exit-Pattern: Falls Täter Gerät-Zugriff bekommt, kann Betroffene:r alle Daten in einem Klick löschen. |
| **Hash-Chain auf SHA-256** | Gerichts-Zulässigkeit: Beweis-Kette ist fälschungssicher, jeder Link referenziert den vorherigen Hash. |

---

## 5 · Open-Source-Plan

- **Lizenz:** AGPL-3.0 (konsistent mit Civic-Tech-Standard; Erweiterungen müssen zurückfließen). *Änderbar auf MIT nach CEO-Entscheidung — siehe Checkliste.*
- **Repo:** `github.com/mikelninh/safevoice` (public, 533+ Tests, CHANGELOG.md, CLAUDE.md, DEPLOY.md).
- **CI:** GitHub Actions führt Pytest + Typecheck auf jedem PR aus.
- **Dokumentation:** `TUTOR_PREP.md`, `DEPLOY.md`, `CLAUDE.md` liegen im Repo. Jede neue Feature-Folie wird in der gleichen Impressum-Klarheit geschrieben.
- **Veröffentlichung:** Während der 6 Monate werden alle Commits öffentlich, mit dem Prototype-Fund-Logo im README.

---

## 6 · Zielgruppe und Nutzenbelege

**Primär:**
- Betroffene digitaler Gewalt (individuelle Nutzung, kostenlos, immer).
- NGO-Lots:innen bei HateAid, Weißer Ring, Frauenhauskoordinierung, Neue Deutsche Medienmacher:innen (Organisations-Tier — 2. Pilotphase).

**Sekundär (Folgefinanzierung Q3/Q4):**
- Opferanwält:innen (zur strukturierten Beweis-Übernahme von Mandant:innen).
- Polizeiliche ZAC-Einheiten (Zentrale Ansprechstellen Cybercrime) als Eingangs-Tool.

**Nutzen-Hypothesen (messbar während der Projektlaufzeit):**

| Metrik | Baseline heute | Ziel M+6 |
|---|---|---|
| Zeit pro Fall-Dokumentation (NGO-Lots:innen) | 45–90 min manuell | unter 10 min mit SafeVoice |
| Fälle pro Monat durch Pilot-NGO-Partner | 0 (pre-pilot) | 100+ |
| Rechtlich haltbare Beweise (SHA-256 + Timestamp) | ~10 % bei manuell erstellten Screenshots | 100 % bei SafeVoice-Dokumentationen |
| Zufriedenheit Betroffener (NPS bei NGO-vermittelten Fällen) | n/a | Ziel: >40 |

---

## 7 · Team · `{MIKEL}`

Mikel Ninh · Berlin · [hallo.chupi@gmail.com](mailto:hallo.chupi@gmail.com)

**Relevanter Hintergrund:** *{MIKEL — fülle diese Zeilen aus: deine bisherige technische Erfahrung, dein Studium/Kurs (AI Engineering), dein Motivationshintergrund falls relevant. 300–500 Wörter. Wenn du magst, schicke ich dir eine Version als Entwurf basierend auf dem was ich aus unseren Meetings weiß.}*

**Einzelentwickler-Ansatz:** Das Projekt ist bewusst auf ein Solo-Setup ausgelegt. Externe Expertise wird für drei spezifische Blöcke zugekauft (siehe Budget unten): Rechtsreview der Vorlagen, Accessibility-Audit, und UX-Beratung für NGO-Integration.

**Mentoren / Sparringspartner:**
- Zisis Batzos (AI Lead, Masterschool Berlin) — technische Architektur-Review, wöchentlich
- *{MIKEL: Name eines NGO-Kontakts einfügen, falls vorhanden — z.B. HateAid, Betroffenenberatung}*

---

## 8 · Zeitplan · 6 Monate

| Monat | Meilenstein | Deliverable |
|---|---|---|
| **M+1** | Deployment production-härten; Resend-Mail-Provider integrieren; HttpOnly-Session-Cookie | Public Release v1.1 · Railway live · SMTP-funktional |
| **M+2** | Art. 20 GDPR Export + 7-Tage-Soft-Delete-Cleanup-Job | DSGVO-konform v1.2 · Datenportabilität + Löschpflicht |
| **M+3** | 3 NGO-Pilot-Partner onboarded · strukturierte Partner-API | Pilot-Phase aktiv · Feedback-Loop läuft |
| **M+4** | Bulk-Import CSV (für NGO-Fallübergaben aus DATEV/advoware) · Org-Admin-Dashboard | NGO-Admin-Tier ready |
| **M+5** | Bias-Evaluation: 100-case Gold-Standard-Set · Confusion-Matrix-Test automatisiert | Veröffentlichter Evaluation-Report (im Repo) |
| **M+6** | Abschluss-Release v2.0 · Projekt-Dokumentation öffentlich · 2 NGO-Partnerschaften in Folge-Finanzierung geklärt | Final Report + Sustainability-Plan |

---

## 9 · Budget · 6 Monate · €47,500

| Posten | Betrag | Begründung |
|---|---|---|
| Entwicklerzeit (0,5 FTE × 6 Monate × €6,000) | **€36,000** | Hauptblock — Kern-Engineering, NGO-Onboarding, Dokumentation |
| Infrastruktur (OpenAI + Anthropic + Railway + Resend + Upstash) | **€1,800** | ~€300/Monat · Projektlaufzeit-Cap |
| Rechtsreview DSGVO + Impressum + NGO-Verträge (anwaltlich) | **€3,500** | Externe:r DSGVO-Expert:in · einmalig |
| Accessibility-Audit (WCAG 2.1 AA) | **€1,500** | Opferschutz-Tool muss barrierefrei sein · externe Prüfung |
| UX-Beratung für NGO-Integration (2 Workshop-Tage) | **€2,000** | Co-Design mit realen Lots:innen |
| Pilot-NGO-Reise + Onboarding (Berlin, Hamburg, Leipzig) | **€1,000** | 3 Vor-Ort-Termine mit Pilot-Partnern |
| Admin / Kontingenz (Buchhaltung, Domains, Zertifikate) | **€1,700** | ~4 % des Gesamtbudgets |
| **Summe** | **€47,500** | |

Keine versteckten Posten, keine "Marketing" oder "Community Building" Zeilen — das Projekt wächst durch NGO-Partner und Mund-zu-Mund, nicht durch bezahlte Reichweite.

---

## 10 · Expected outcomes · nach 6 Monaten

**Hard deliverables:**
1. SafeVoice v2.0 public auf `safevoice.app` (live, DSGVO-konform, barrierefrei).
2. Öffentliches Repo mit ≥ 600 Tests, CHANGELOG, CI, komplette Dokumentation.
3. Accessibility-Audit-Report im Repo (`docs/accessibility-audit.md`).
4. Bias-Evaluation-Report (`docs/bias-evaluation-m5.md`) mit Confusion-Matrix auf 100-case Gold-Standard-Set.
5. Mindestens **3 NGO-Pilot-Partner** haben Fälle live dokumentiert.
6. Mindestens **1 Letter-of-Intent** für Folgefinanzierung einer NGO oder eines Bundes-/Landesprogramms (z. B. Bundesstiftung Gleichstellung).

**Soft deliverables:**
- 1 Vortrag auf einer Fachtagung (Deutscher Präventionstag, Betroffenenkongress, re:publica civic-tech-Track).
- 1 journalistische Einordnung (netzpolitik.org oder SZ-Digital) über den Stand des Tools.

---

## 11 · Nachhaltigkeit — wie geht es nach M+6 weiter

Drei parallele Pfade, kein "eines davon muss klappen":

1. **Folgefinanzierung über Stiftungen** — Bundesstiftung Gleichstellung, Robert-Bosch-Stiftung Civic-Tech, Hertie (Tickets €20–100K).
2. **Organisations-Tier als bezahltes SaaS** für NGOs (€49–99/seat/mo, aktiviert nach Pilot-Ende, Modell: 80/20 — Opfer kostenfrei, Organisationen zahlen).
3. **EU-CERV-Programm** (Citizens, Equality, Rights, Values) für DACH-Skalierung (€75–500K, Konsortium).

Keiner dieser Pfade wird während der Prototype-Fund-Laufzeit aktiv beworben — M+6 endet mit **ein bis zwei LOIs in der Schublade**, die Skalierung startet in Monat 7.

---

## 12 · Prototype-Fund-spezifische Fragen (werden im Online-Formular abgefragt)

**Was ist der Innovationsgrad des Projekts?**
> Kombination aus: (a) deutsch-rechtsspezifische LLM-Klassifikation mit schema-enforced Structured Outputs, (b) kryptografischer Hash-Chain als gerichtstauglicher Beweis, (c) RAG-basierte Fall-Level-Analyse. Existierende Tools adressieren entweder nur Beweis-Archivierung (Page.ly, Archive.today) ODER nur Klassifikation (HateAid-Melde-Formular) — keine kombiniert alle Ebenen mit Hash-Chain-Verifikation.

**Warum Open Source?**
> Weil Opferhilfe-Software Vertrauen erfordert, und Vertrauen ohne Einsehbarkeit des Codes nicht möglich ist. Betroffene müssen nachprüfen können, dass ihre Daten nicht kommerziell verwendet werden. NGO-Partner müssen den Klassifikator auditieren können. Juristische Beweis-Kette muss peer-reviewable sein. Ohne AGPL: technisch ein Proprietär-Tool mit Datenschutz-Versprechen. Mit AGPL: ein Werkzeug, das sich selbst beweisen muss.

**Wie erreicht SafeVoice seine Zielgruppe?**
> (1) Direktkontakt mit 5 deutschen NGOs bereits laufend (HateAid, Weißer Ring, Frauenhauskoordinierung, Neue deutsche Medienmacher:innen, Betroffenenrat). (2) Warm-Handoff-Integration mit HateAid in v1.2 — Opfer-Klick verlinkt direkt in deren Hotline. (3) Fachtagung-Vortrag geplant M+5. Nicht über SEO/Marketing — ein Opfer in Not sucht nicht nach "digitaler Gewalt Tool", sondern wird über NGO-Lots:innen an SafeVoice verwiesen.

---

*Entwurf · Stand 2026-04-20 · zu verifizieren an Form-Fields des aktuellen Prototype-Fund-Rounds · PM + Claude*
