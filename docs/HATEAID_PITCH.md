# HateAid Partnership Proposal

*Draft — prepared 2026-04-12. Polish narrative / tone before sending. Owner: Mikel.*

---

## 0. Einstieg (für das Erstgespräch)

**Wer ich bin.** Mikel, AI-Engineering-Student, gerade in HCMC, komme nach Deutschland zurück im Mai 2026. Ich baue SafeVoice — ein Tool, das digitalen Gewaltopfern hilft, innerhalb von 30 Sekunden aus einer belastenden Nachricht ein gerichtsfestes Dokument zu machen.

**Warum ich euch kontaktiere.** Nicht um euch ein Produkt zu verkaufen. Um zu verstehen, **wo eure Teams gerade die meiste Zeit an Routine verlieren** — und zu prüfen, ob SafeVoice einen Teil davon übernehmen kann. Euer Wissen über Opferbetreuung ist unersetzlich. Meine Arbeit ist Infrastruktur, die euer Team skaliert.

**Die Frage, die ich mitbringe.** Wenn ihr 10 Fälle pro Woche bearbeitet, wie viele davon sind ähnlich genug, dass ein vorklassifizierter Bericht euch ~60 % der Dokumentationszeit spart?

---

## 1. Das Problem, das wir beide sehen

Die digitale Gewalt in Deutschland skaliert schneller als Beratungsstellen skalieren können:

- **Ricarda Lang Deepfake-Debatte (April 2026)** hat digitale Gewalt politisch in den Fokus gerückt
- **NetzDG § 3** verpflichtet Plattformen, aber die Durchsetzung bleibt schwach
- **HateAid bearbeitet tausende Fälle/Jahr** — viele bleiben in Dokumentationsschleifen stecken, bevor sie überhaupt bei der Staatsanwaltschaft landen

Die Engpässe sind nicht rechtlicher Natur. Sie sind **operativ**:
- Beweissicherung muss manuell passieren (Screenshot, Datum, URL archivieren)
- Klassifizierung nach StGB erfordert juristisches Wissen → meist erste Hürde für Betroffene
- PDF-Erstellung für Strafanzeige ist repetitive Tipparbeit
- Mehrere Beweisstücke als Kette zu dokumentieren ist fehleranfällig

**SafeVoice löst genau diese operative Schicht.**

## 2. Was SafeVoice heute ist

Eine bilinguale (DE/EN) Webapp + FastAPI Backend:

| | Status |
|-|--------|
| KI-Klassifizierung (GPT-4o-mini, strukturierte Ausgabe) mit StGB-Mapping | ✅ live |
| 12 deutsche Paragraphen abgedeckt (§ 185, 186, 187, 130, 241, 126a, 201a, 238, 263, 263a, 269, NetzDG § 3) | ✅ live |
| SHA-256 Hash-Kette für Beweisintegrität | ✅ live |
| Archive.org Backup für jede URL | ✅ live |
| Gerichtsfestes PDF (mit Chain-of-Custody Anhang) | ✅ live |
| Multi-Tenant (Org-Accounts mit Rollen) | ✅ live — *neu seit April 2026* |
| Bulk-Import (CSV/ZIP → Batch-Klassifizierung) | ✅ live — *neu* |
| DSGVO-Compliance-Pack (AVV-Template, DPIA-Framework) | ✅ draft |

**Code-Basis:** Python/FastAPI + React/TypeScript, 485+ Tests, Open-Source-ähnlich (Lizenz noch zu klären).

**Was noch fehlt** (nächste 6 Wochen):
- Supabase-Integration für Auth/RLS (geplant)
- Admin-Dashboard für Team-Ansichten (geplant)
- Rechtliche Review aller DSGVO-Dokumente durch eure/unsere Juristen

## 3. Konkret: Wie HateAid SafeVoice nutzen könnte

**Szenario A — Eingehende Fallbearbeitung:**
Ein Opfer schildert per E-Mail einen Vorfall, schickt 12 Screenshots.
- Ohne SafeVoice: Praktikant tippt alles ab, ordnet manuell Paragraphen zu, ~90 Min/Fall
- Mit SafeVoice: CSV-Import der 12 Items → Batch-Klassifizierung → PDF in ~3 Min
- **Zeitersparnis pro Fall: ~85 Min. Bei 500 Fällen/Jahr = 700 h = 4 Monate Vollzeit-Praktikant**

**Szenario B — Koordinierter Angriff:**
Eine Klientin wird von 30+ Accounts simultan angegriffen.
- Ohne SafeVoice: Pattern-Erkennung per Hand, kein gemeinsames Dokument
- Mit SafeVoice: alle 30 Items in 1 Fall, `/analyze/case` erkennt Pattern-Flags automatisch, generiert eine konsolidierte Strafanzeige
- **Output: Ein Dokument, das Staatsanwälte tatsächlich bearbeiten können**

**Szenario C — Forensische Beweissicherung:**
Eine politische Aktivistin wird bedroht, die Bedrohung wird nach einer Stunde gelöscht.
- Ohne SafeVoice: Wenn Screenshot nicht rechtzeitig gemacht wurde — Beweis weg
- Mit SafeVoice: Archive.org-Backup greift sofort beim Submit, SHA-256 Hash macht Manipulation nachweisbar
- **Output: Gerichtsfeste Spur auch nach Plattform-Löschung**

## 4. Was ich von HateAid bräuchte

Nicht Geld. **Feedback und Validierung.**

1. **2-3 Mitarbeitende**, die 2 Wochen lang real Fälle durch SafeVoice laufen lassen und sagen: "diese Klassifizierung stimmt nicht / das PDF ist so nicht brauchbar / diese Funktion fehlt"
2. **Eine Juristin**, die einmal über die DSGVO-Dokumente (AVV, DPIA) schaut und sagt: "das reicht für HateAid als Auftragsverarbeiter" oder "das braucht Änderung X"
3. **Einen Briefkopf/Logo**, damit die PDFs unter HateAid-Branding rausgehen können (Org-Setting)

Als Gegenleistung:
- **HateAid-Namensrecht** — Ihr könnt SafeVoice-powered Reports unter euerem Logo versenden
- **Keine Gebühren** im MVP-Jahr. Längerfristig über Stiftungen finanziert (Prototype Fund + Schöpflin geplant)
- **Feedback-Loop in die Produktrichtung** — wir bauen, was ihr tatsächlich braucht

## 5. Was das für euch nicht bedeutet

- **Nicht** Ersatz für eure juristische Beratung
- **Nicht** automatisierte Entscheidungsfindung (Art. 22 DSGVO) — ihr reviewt jede KI-Klassifizierung manuell, bevor gefiled wird
- **Nicht** neue Prozesse, die euer Team lernen muss — SafeVoice fügt sich in bestehende E-Mail-Workflows ein (CSV rein, PDF raus)

## 6. Der politische Moment

Digitale Gewalt ist 2026 politisch verhandelbar wie seit Jahren nicht mehr. Der Moment zum Skalieren ist **jetzt**, nicht Q3 2026 wenn die Aufmerksamkeit wieder beim nächsten Thema liegt.

Wenn HateAid und SafeVoice zusammenarbeiten, haben wir bis Herbst:
- Zwei Fallstudien (Deepfake-Fall + Koordinierte Kampagne)
- Eine Stiftungsbewerbung (Prototype Fund, Deadline Q2)
- Ein Medienstory, das euer Team positioniert (HateAid adoptiert KI-Werkzeug zur Eindämmung digitaler Gewalt)

## 7. Nächste Schritte

1. **30-Minuten-Call** — Ich zeige Screen, ihr stellt Fragen zu Daten, Rechten, Workflow. Zeitlich wann auch immer passt.
2. **Wenn Interesse besteht:** Ich schicke einen AVV-Entwurf + DPIA-Framework. Rechtliche Review parallel zu meinem MVP-Feintuning.
3. **Pilot (optional):** 2 Wochen Echtfälle mit 2-3 euerer Mitarbeitenden.

## 8. Kontakt

Mikel [Nachname]
E-Mail: [contact]
LinkedIn: [link]
SafeVoice Repo: [private repo, Zugriff auf Anfrage]
GitLaw (verwandtes Projekt): https://github.com/mikelninh/gitlaw

---

**P.S.** Ich weiß, dass HateAid täglich Anfragen von Tech-Leuten bekommt, die "eine Lösung gebaut haben". Ich verstehe, wenn ihr skeptisch seid. Deswegen frage ich nicht nach Ressourcen von euch — ich frage nach Feedback. Wenn das Feedback ist "braucht kein Mensch", ist das auch eine wertvolle Antwort.
