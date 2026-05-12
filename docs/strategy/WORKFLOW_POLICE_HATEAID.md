# Wer profitiert wirklich? — Polizei + HateAid Workflow-Analyse

*Stand: 2026-05-12. Schreibt sich aus Sicht der Empfänger:innen einer SafeVoice-Strafanzeige bzw. einer HateAid-Beratungsanfrage.*

> SafeVoice ist auf der Opferseite überzeugend. Die wirkliche Frage ist: **schaffen wir Mehrwert auf der Empfängerseite — oder erzeugen wir nur einen weiteren Stack PDFs, den irgendjemand abarbeiten muss?**

---

## 1. Polizei — Workflow heute vs. mit SafeVoice

### 1.1 Heutiger Ablauf (ohne SafeVoice)

1. **Eingang.** Anzeige kommt per Onlinewache (Web-Formular pro Bundesland), per E-Mail, oder persönlich. Im Online-Fall: Freitext im "Sachverhalt"-Feld, oft 3–6 Sätze, manchmal mit Screenshots als Anlage.
2. **Sichtung (~10–20 Min).** Sachbearbeiter:in liest. Häufige Probleme:
   - Welche §§ sind einschlägig? — muss aus dem Freitext rekonstruiert werden
   - Sind die Screenshots manipuliert? — ohne Hash kein automatischer Integritätscheck
   - Welche Plattform? Welcher Account? — oft unklar formuliert
   - Mehrere Vorfälle in einer Anzeige? — Zeitachse fehlt
3. **Recherche (~30–60 Min).** §§ nachschlagen, Plattform-Kontakt eruieren, Tatzeit/Tatort verifizieren, Screenshots auf Plausibilität prüfen.
4. **Klassifizierung + Aktenvermerk (~20 Min).** Sachverhalt strukturieren, in interne Maske eintragen, juristische Bewertung vermerken.
5. **Weiterleitung.** ZAC (Zentralstelle Cybercrime) wenn überregional · Staatsanwaltschaft · ggf. Plattform-Auskunftsersuchen.

**Gesamtaufwand pro Fall: ~60–120 Min** in der Sichtungs-/Erstbewertungsphase. Bei Massenphänomenen (Volksverhetzungs-Wellen, koordinierte Stalking-Kampagnen) skaliert das linear — Sachbearbeiter:innen ertrinken in Freitext-Sachverhalten.

### 1.2 Mit SafeVoice — was sich ändert

| Schritt | Heute | Mit SafeVoice-PDF |
|---|---|---|
| Sichten der Anzeige | Freitext lesen, 3–6 Sätze, oft unstrukturiert | **Exec-Summary-Karte in 3 s** — Schweregrad, Anzahl Vorfälle, einschlägige §§ |
| §§ identifizieren | Manuell aus Freitext extrahieren, ggf. nachschlagen | Bereits klassifiziert mit Strength-Score (strong/medium/weak) |
| Beweise prüfen | Screenshots auf Manipulation visuell prüfen | **SHA-256 pro Beweis** — Integritätscheck mit `shasum -a 256` |
| Zeitachse | Aus Freitext rekonstruieren | Nummerierte Exhibit-Karten mit Zeitstempel, sortierbar |
| Plattform-Identifikation | Aus Sachverhalt erraten | Im Header pro Beweis + @-Handle der Verfasser:innen |
| Eskalationsbewertung | Bauchgefühl + Erfahrung | KI-Vorab-Einschätzung als zweite Meinung (klar als KI markiert) |
| Nächste Schritte | Routine pro Sachbearbeiter:in | Empfohlene Schritte mit Deadlines im PDF (immediate · 24h / soon · 7d / when_ready) |

### 1.3 Konkrete Zeitersparnis (Schätzung, zu validieren)

| Phase | Vorher | Nachher | Gespart |
|---|---|---|---|
| Sichtung + erste Klassifizierung | 15 Min | **3 Min** | -12 Min |
| §§-Recherche | 30 Min | **5 Min** (nur Verifikation) | -25 Min |
| Beweis-Plausibilitäts-Check | 10 Min | **2 Min** (Hash-Verifikation) | -8 Min |
| Strukturierung des Aktenvermerks | 20 Min | **8 Min** (Inhalte übernehmen) | -12 Min |
| **Summe pro Fall** | **75 Min** | **18 Min** | **-57 Min** |

**Hochgerechnet** auf eine Polizeidienststelle mit z. B. 5 Hass-Anzeigen pro Tag: **~5 Stunden Polizei-Arbeitszeit eingespart pro Tag**. Bei einer Cybercrime-Zentralstelle (50+ Fälle pro Tag): zweistelliger Personen-Tag-Wert pro Woche.

**Wichtig:** Das sind Annahmen, keine Messungen. Die Zahlen sind eine Hypothese, die wir mit einer einzelnen Dienststelle in einem 4-Wochen-Pilot überprüfen sollten.

### 1.4 Was SafeVoice NICHT ersetzt

- Die juristische Letzt-Entscheidung — die KI-Bewertung ist explizit als Vorab-Einordnung markiert.
- Die Ermittlungstätigkeit — Identifikation der Täter:innen, Auskunftsersuchen an Plattformen, Vernehmungen.
- Den menschlichen Filter — eine Maschine soll bei einer Todesdrohung nicht alleine entscheiden, was passiert.

### 1.5 Risiken aus Polizei-Sicht

1. **Vertrauen ins Format.** Polizei muss SafeVoice-PDFs einmal kennenlernen. Mehrwert hängt davon ab, dass das Format bei den Empfänger:innen verlässlich wiedererkannt wird.
2. **KI-Halluzination.** Pydantic-Enums verhindern erfundene §§, aber die Freitext-Bewertung muss vor der Akte geprüft werden. Disclaimer im PDF ist die Mindest-Voraussetzung; Schulung wäre besser.
3. **Hash-Verifikation muss gelernt sein.** `shasum -a 256` ist trivial, aber nicht jede Dienststelle hat das Reflex. Mitgelieferte 1-Pager-Anleitung im PDF-Anhang würde helfen.

---

## 2. HateAid — Beratungs-Workflow heute vs. mit SafeVoice

### 2.1 Heutige Anfrage bei HateAid

1. **Erstkontakt** (Hotline / Mail / Web-Formular).
2. **Aufnahme (~30 Min).** Berater:in fragt Sachverhalt ab, sortiert: NetzDG-Beschwerde, Strafanzeige, Prozesskostenhilfe?
3. **Beweis-Sicherung-Coaching (~30 Min).** Wenn Beweise noch nicht gesichert sind: Anleitung wie Screenshots gemacht, wie Archive-Links erstellt werden.
4. **§§-Recherche (~20 Min).** Welche Tatbestände? Welche Erfolgsaussichten?
5. **Schriftsatz-Entwurf oder Vermittlung an Anwält:in.**
6. **Folge-Kommunikation.** Status-Updates, Plattform-Antworten, Polizei-Rückmeldung.

**Gesamtaufwand pro Erstkontakt: 1,5–2,5 Stunden.** HateAid hat begrenzte Berater:innen — jede Stunde, die in Beweis-Sicherung-Coaching fließt, fehlt bei der inhaltlichen Beratung.

### 2.2 Mit SafeVoice — was sich ändert

| Schritt | Heute | Mit SafeVoice |
|---|---|---|
| Aufnahme-Gespräch | 30 Min, alles abfragen | Klient:in bringt SafeVoice-PDF mit → 10 Min Verifikation, restliche Zeit für inhaltliche Beratung |
| Beweis-Sicherung-Coaching | 30 Min Anleitung | **Entfällt** — Beweise bereits mit SHA-256 + archive.org gesichert |
| §§-Recherche | 20 Min | 5 Min — KI-Klassifizierung als Startpunkt verifizieren |
| Prozesskostenhilfe-Antrag | Daten erneut abfragen | Daten + Belege bereits strukturiert vorhanden |
| Eskalations-Einschätzung | Erfahrung + Akteneinsicht | KI-Risk-Score als Vorabeinordnung, dann anwaltliche Prüfung |
| Schriftsatz-Entwurf | Manuell aus Notizen | Strafanzeige-Vorlage bereits da, anwaltliche Anpassung statt Neuerstellung |

### 2.3 Konkrete Zeitersparnis (Schätzung)

| Phase | Vorher | Nachher | Gespart |
|---|---|---|---|
| Erstkontakt-Aufnahme | 30 Min | 10 Min | -20 Min |
| Beweis-Sicherung-Coaching | 30 Min | 0 Min | -30 Min |
| §§-Recherche | 20 Min | 5 Min | -15 Min |
| Schriftsatz-Vorbereitung | 30 Min | 10 Min | -20 Min |
| **Summe pro Klient:in (Erstphase)** | **110 Min** | **25 Min** | **-85 Min** |

Bei ~20 Klient:innen pro Woche und Berater:in: **~28 Stunden Beratungs-Zeit pro Woche frei** — die für inhaltliche Beratung, Anwalts-Vermittlung, Prozessbegleitung genutzt werden kann.

**Indirekter Effekt:** HateAid hat heute oft Schwellenwerte (Mindest-Schwere für Prozesskostenhilfe), weil Berater:innen-Kapazität endlich ist. Mit weniger Aufnahme-Zeit pro Fall könnten mehr Betroffene überhaupt durch den Trichter.

### 2.4 Was HateAid besonders interessieren dürfte

1. **Trägerschaft als Reputations-Schutz.** SafeVoice ist heute ein Solo-Projekt. Eine HateAid-Trägerschaft (oder zumindest -Endorsement) gibt Betroffenen das Vertrauen, das Tool zu nutzen.
2. **Aggregat-Daten zu Mustern.** Mit Opfer-Einwilligung könnte SafeVoice anonymisierte Statistiken über Hass-Trends an HateAid liefern — täter-handle-Cluster, regionale Schwerpunkte, neue extremistische Codes — als Frühwarnsystem.
3. **NGO-Branding im PDF.** Custom-Letterhead-Funktion wäre bei einer formellen Trägerschaft naheliegend — die Strafanzeige geht dann mit HateAid-Briefkopf raus, was ihre Wirksamkeit erhöht.
4. **Prozesskostenhilfe-Vorbereitung.** Wenn SafeVoice das ePKH-Antrag-Datenformat unterstützt, ist die Übergabe von SafeVoice → Anwält:in für PKH-Verfahren trivial.

### 2.5 Risiken aus HateAid-Sicht

1. **Markenrisiko.** Wenn ein Tool, das HateAid trägt, juristisch falsch klassifiziert, fällt das auf sie zurück. Schema-Drift (§§-Änderungen) muss überwacht werden.
2. **Erwartungsmanagement.** Betroffene könnten denken, eine SafeVoice-Anzeige sei ein automatisches Verfahren. Klare Kommunikation: das ist Vor-Arbeit, kein Auto-Pilot.
3. **DSGVO-Verantwortung.** Wer ist Auftragsverarbeiter? Die OpenAI-API-Calls für Klassifizierung sind die kritische Stelle. Eine Auftragsverarbeitungsvereinbarung mit HateAid und ein klarer Datenfluss-Plan sind Voraussetzungen.

---

## 3. Ist es wirklich nützlich? — ehrliches Fazit

**Ja, wahrscheinlich — aber die Zahlen sind Hypothesen, kein Beweis.**

Was wir empirisch zeigen können:
- Klassifikator-Genauigkeit auf 27 realen Test-Szenarien: 100% korrekt zugeordnete §§, 0 erfundene Paragraphen, 0 False Positives auf Idiomen
- PDF-Größe ~9 KB, lesbar in 3 Sekunden (Exec Summary), enthält allen relevanten Inhalt einer 30-Minuten-Strafanzeige
- Zwei-Tier-OCR funktioniert (Vision live verifiziert)
- DSGVO-Posture: anonymous-first, lokale Datenhaltung, kein Tracking

Was wir empirisch **noch nicht** zeigen können (und in einem Pilot messen sollten):
- Wieviel Zeit Polizei/HateAid tatsächlich pro Fall einsparen — die Schätzungen in Abschnitt 1.3 und 2.3 müssen mit echten Sachbearbeiter:innen kalibriert werden
- Ob SafeVoice-PDFs in der Praxis akzeptiert werden, oder ob Dienststellen sie nur als Anlage zur eigenen Akte nehmen
- Ob die KI-Bewertung im PDF von Empfänger:innen als Hilfe oder als Ablenkung erlebt wird
- Ob Betroffene das Tool ohne Anleitung benutzen können (Mobile-UX-Test fehlt noch)

**Konkrete nächste Schritte zur Validierung:**

1. **Pilot mit einer Berliner Polizeidienststelle (ZAC oder LKA Hassrede)** — 4 Wochen, 20 echte Fälle, Vorher/Nachher-Zeitmessung. Output: belastbare Zahl Minuten-pro-Fall.
2. **Pilot mit zwei HateAid-Berater:innen** — gleicher Aufbau, 30 Klient:innen, Vorher/Nachher-Zeit + qualitatives Berater:innen-Feedback.
3. **Polizei-A4-Review-Sheet im PDF** — eine 1-seitige Anleitung im PDF-Anhang: "Wie lese ich diesen Bericht in 3 Schritten" + "Wie verifiziere ich SHA-256". Senkt die Einstiegshürde.
4. **NGO-Custom-Letterhead** als Feature umsetzen — Voraussetzung für HateAid-Trägerschaft-Diskussion.

Diese vier Schritte sind das Mindeste, um beim nächsten Tutor-Gespräch nicht mehr nur "wir glauben es ist nützlich" sagen zu müssen, sondern eine erste Zahl zu haben.
