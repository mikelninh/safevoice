# SafeVoice — Polizei-Bridge: Feature Design

**Status:** Design proposal — hypothesis-driven. Needs validation with a Polizei or Staatsanwaltschaft contact before any implementation begins.
**Owner:** Mikel
**Date:** 2026-04-10
**Audience:** Mikel + a police officer friend / BMJ contact for feedback

---

## 1. Executive Summary

SafeVoice wurde als Opfer-Tool gebaut: Betroffene dokumentieren, SafeVoice klassifiziert, ein gerichtsfestes PDF geht zur Polizei. Das ist nützlich — aber es löst nur die erste Meile des Problems. Die zweite Meile ist die eigentliche Flaschenhals-Stelle: Wenn eine Strafanzeige bei der Polizei oder Staatsanwaltschaft eingeht, beginnt manueller Aufwand. Ein Sachbearbeiter öffnet ein PDF, transkribiert Inhalte in ein IT-System, prüft Links manuell, versucht Plattformdaten anzufordern — oft nachdem der Zeitpuffer für IP-Adress-Daten bereits abgelaufen ist. Verfahren werden eingestellt nicht weil kein Beweis vorliegt, sondern weil der Beweis nicht schnell genug verarbeitet wurde.

Die zentrale These dieser Analyse: SafeVoice sitzt bereits an dem Punkt im Prozess, wo die kritischen Entscheidungen über die Qualität späterer Ermittlungen fallen — nämlich beim Opfer, vor der Anzeigeerstattung. Ein strukturiertes, maschinenlesbares Datenpaket aus SafeVoice, das der Polizei übergeben wird, könnte 30–90 Minuten Sachbearbeiterzeit pro Fall einsparen und gleichzeitig die Trefferquote bei Täteridentifizierung erhöhen. Dieses Paket muss technisch einfach, rechtlich sauber und für den Sachbearbeiter ohne Systemwechsel nutzbar sein.

Der wichtigste Baustein, den wir zuerst bauen sollten, ist nicht ein komplexes API-Integration, sondern ein strukturiertes **Polizei-Exportpaket**: ein ZIP-Archiv mit maschinenlesbarem JSON, PDF mit Hashkette und einer kurzen Triage-Checkliste in tabellarischer Form — alles, was ein Sachbearbeiter braucht, um in 5 Minuten zu entscheiden, ob er ein Eilverfahren einleitet oder den Fall an eine Schwerpunktstaatsanwaltschaft weiterleitet. Dieser Export existiert technisch bereits in Ansätzen (`/reports/{id}/court-package`). Er muss nur auf den Polizei-Workflow zugeschnitten werden.

---

## 2. Aktueller Polizei-Workflow (forschungsbasiert)

### 2.1 Wie eine Strafanzeige verarbeitet wird

Die folgende Beschreibung basiert auf öffentlich verfügbaren Quellen. Detaillierte interne Abläufe der Landespolizeien sind nicht öffentlich. Wo wir spekulieren, ist das markiert.

**Schritt 1 — Anzeigeerstattung**
Das Opfer erstattet Strafanzeige: persönlich bei der Dienststelle, schriftlich per Post/E-Mail, oder über das bundesländerspezifische Online-Portal (`online-strafanzeige.de`). Die Dienststelle vergibt ein Aktenzeichen. (Quelle: polizei-beratung.de)

**Schritt 2 — Aufnahme und Triage durch Sachbearbeiter**
Die Anzeige landet beim zuständigen Sachbearbeiter, typischerweise am nächsten Werktag (Quelle: BKA-Informationsseite Cybercrime). Der Sachbearbeiter öffnet das eingereichte Dokument (meist ein PDF oder handschriftliches Protokoll), liest den Sachverhalt und entscheidet:
- Handelt es sich um einen Privatklagedelikt (§185 StGB Beleidigung — nur auf Antrag verfolgbar) oder ein Offizialdelikt (§241 Bedrohung, §238 Stalking — von Amts wegen)?
- Liegt ein klarer Tatverdacht vor?
- Ist ein Täter identifizierbar?

**Schritt 3 — IP-Adress-Anfrage an Plattform** *(Zeitkritisch)*
Wenn ein Täter anonym ist, muss die Staatsanwaltschaft oder Polizei bei der Plattform eine Herausgabe von IP-Adressen und Accountdaten beantragen. Das erfordert in Deutschland einen richterlichen Beschluss (§100j StPO). Dieses Verfahren dauert Tage bis Wochen. Das kritische Problem: Plattformen speichern IP-Adressen oft nur sehr kurz (X/Twitter: nicht klar; Meta: nach eigenen Angaben für Emergency Requests bis 90 Tage, für reguläre Requests kürzer). In der Praxis sind die digitalen Spuren oft bereits gelöscht, wenn der Antrag eintrifft. (Quelle: HateAid, "Mit dem Strafrecht gegen digitale Gewalt"; DSGVO-Reform-Diskussion, Bundestag Drucksache 20/9170)

**Schritt 4 — Beweismittelprüfung**
Der Sachbearbeiter prüft Screenshots, URLs, Nachrichten. Fragen: Ist das Screenshot authentisch? Gibt es eine Archiv-Kopie? Ist der Hash dokumentiert? Bei SafeVoice-Exporten wäre das bereits beantwortet — aber nur wenn der Sachbearbeiter weiß, dass er einen SafeVoice-Export vor sich hat und wie er die Hash-Chain-Tabelle liest.

**Schritt 5 — Weiterleitung oder Einstellung**
Die Staatsanwaltschaft entscheidet über Anklageerhebung (§170 StPO) oder Einstellung. Bei anonymen Tätern ohne IP-Adresse: Einstellung mangels Tatverdacht (§170 Abs. 2 StPO). Bei identifizierbaren Tätern: Weiterleitung an Schwerpunktstaatsanwaltschaft oder Verhandlung.

### 2.2 Spezialisierte Strukturen (Stand 2025/2026)

Mehrere Bundesländer haben Schwerpunktzuständigkeiten für Online-Hass eingerichtet:

| Bundesland | Einrichtung |
|---|---|
| Bayern | Zentralstelle Cybercrime Bayern (ZCB) bei GenStA Bamberg (seit 2015) |
| Hessen | ZIT (Zentralstelle zur Bekämpfung der Internet- und Computerkriminalität), GenStA Frankfurt |
| NRW | ZAC NRW, StA Köln |
| Niedersachsen | ZHIN (Zentralstelle Hasskriminalität im Internet), StA Göttingen |
| Sachsen | Zentralstelle Hasskriminalität im Internet |
| Sachsen-Anhalt | Zentralstelle bei StA Halle |
| Baden-Württemberg | Spezialabteilungen in allen Staatsanwaltschaften (seit 2022) |

(Quelle: stark-im-amt.de, justiz.bayern.de, staatsanwaltschaften.hessen.de, sta-koeln.nrw.de)

Diese Strukturen existieren, sind aber nicht flächendeckend gleichmäßig ausgebaut. Lokal bearbeitende Polizeidienststellen ohne Spezialisierung sind der häufige Erstkontakt.

### 2.3 Wo Zeit verloren geht

Die folgenden Probleme sind öffentlich belegt oder plausibel erschlossen:

1. **IP-Adress-Zeitfenster wird verpasst** (belegt): Bis die Anzeige beim Sachbearbeiter liegt, oft 2–5 Tage nach der Tat, sind Plattform-IP-Logs häufig gelöscht. Das Gesetz gegen digitale Gewalt (BMJ-Entwurf, Dez. 2024) sieht eine Pflicht zur 3-Monats-Speicherung vor — noch nicht in Kraft. (Quelle: HateAid-Stellungnahme, netzpolitik.org 2026)

2. **Manuelle Transkription in Polizei-IT** (erschlossen): Sachbearbeiter müssen Inhalte aus PDF-Anzeigen in interne Systeme (INPOL, landesspezifische Systeme wie ViVA in Bayern) übertragen. Das ist repetitiv und fehleranfällig. Kein standardisiertes Import-Format für digitale Beweise existiert.

3. **Qualität der eingereichten Beweise variiert stark** (belegt): Viele Opfer reichen handyabfotografierte Screenshots ohne Metadaten ein. Ohne URL, Plattform, Datum und Täter-Handle kann kein Ermittlungsansatz gebildet werden. (Quelle: BSI, HateAid Ratgeber)

4. **Mangelnde Schulung für digitale Gewalt** (belegt): Netzpolitik.org (Feb. 2026), das Nettz und Frauenhauskoordinierung fordern verpflichtende Fortbildungen für Polizei und Justiz zu digitaler Gewalt. Viele Dienststellen haben keine spezialisierten Sachbearbeiter.

5. **Kein einheitliches digitales Anzeige-Portal** (belegt): HateAid fordert ein bundesweit einheitliches digitales Anzeigeverfahren. Aktuell gibt es 16 Bundesländer-Portale mit unterschiedlichen Formularen und Akzeptanzgrenzen.

6. **Verfahrensdauer schreckt Opfer ab** (belegt): Lange Laufzeiten, niedrige Erfolgschancen, hohe Anforderungen an Opferpersistenz sorgen dafür, dass nur ~5 % der Betroffenen überhaupt Anzeige erstatten. (Quelle: Kompetenznetzwerk Hass im Netz, zitiert aus Bundestag-Unterlagen)

7. **Fehlende Ressourcen** (belegt): Bundestag-Dokument (Drucksache 20/9170): "Verfahren werden schnell eingestellt, technische Geräte oft nicht forensisch untersucht — es fehlen Ressourcen bei Polizei und Justiz." (Quelle: Bundestag Drucksache 20/9170, Nds. Landesjustizportal)

---

## 3. Wo SafeVoice Zeit einsparen kann

Geschätzte Einsparungen pro Fall — alle Zahlen sind Hypothesen ohne empirische Validierung. Sie basieren auf den beschriebenen Workflow-Schritten. Bitte mit einem Sachbearbeiter validieren.

| Aufgabe heute | Aufwand heute (geschätzt) | Mit SafeVoice-Export | Einsparung |
|---|---|---|---|
| Sachverhalt manuell aus PDF lesen und in System eingeben | 20–40 min | Strukturiertes JSON, direktes Einlesen | ~25–35 min |
| URL manuell archivieren / auf Verfügbarkeit prüfen | 10–20 min | Archive.org-Link bereits im Export | ~10–15 min |
| Hash-Integrität prüfen | 15–30 min (oder gar nicht) | SHA-256 Hash + Chain bereits dokumentiert | ~15–30 min |
| StGB-Paragraph zuordnen | 15–30 min (juristisches Wissen nötig) | Automatische Klassifikation mit Begründung | ~10–20 min |
| Triage-Entscheidung (Privatklag. vs. Offiziald.) | 10–20 min | Triage-Block im Export (requires_immediate_action, severity) | ~8–15 min |
| Schwerpunkt-StA identifizieren | 5–10 min | Handlungsempfehlung im Export (welche StA zuständig) | ~3–5 min |
| **Gesamt** | **75–150 min** | **~15–30 min** | **~60–120 min** |

**Wichtiger Caveat:** Diese Einsparung gilt nur, wenn der SafeVoice-Export direkt in das Polizei-Workflow integriert wird — nicht als zusätzliches Dokument neben der normalen Anzeige. Das erfordert entweder eine Systemintegration (hoher Aufwand) oder einen sehr klar strukturierten Export, den der Sachbearbeiter ohne Schulung versteht (machbar ohne Integration).

---

## 4. Vorgeschlagene Bridge-Features (3-5 Capabilities)

### Feature 1 — Polizei-Exportpaket (Priorität: HOCH, MVP-Kandidat)

**Was es tut:**
Der Victim-Nutzer oder NGO-Mitarbeiter generiert ein Polizei-spezifisches Export-ZIP aus einem SafeVoice-Fall. Das ZIP enthält:
- `strafanzeige_bericht.pdf` — das bestehende Legal-PDF, erweitert um eine erste Seite "Polizei-Zusammenfassung" (Triage-Block: Severity, Paragraph-Mapping, requires_immediate_action, empfohlene nächste Schritte)
- `evidenz_metadata.json` — maschinenlesbares JSON mit allen Beweisstücken, URLs, Hashes, Plattforminfos, Zeitstempeln und dem Klassifikationsergebnis
- `hash_chain.csv` — Tabelle aller SHA-256 Hashes in Kettenreihenfolge, prüfbar ohne Software
- `platform_request_guide.txt` — automatisch generierte Checkliste: welche Plattform, welche Rechtsgrundlage (§100j StPO), welche Frist, an wen senden

**Warum es Zeit spart:**
Sachbearbeiter erhält alle strukturierten Daten auf einem Blatt. Kein manuelles Extrahieren. Die `platform_request_guide.txt` spart die Recherche nach dem richtigen Ansprechpartner bei Meta/X/TikTok.

**Geschätzte Einsparung:** 40–60 Minuten pro Fall.

**Technischer Aufwand:**
Klein bis mittel. Der `/reports/{id}/court-package`-Endpoint existiert bereits und generiert ein ZIP. Neue Komponenten:
- `services/police_export.py` — neues JSON-Schema (`PoliceExportSchema`) und Platform-Request-Guide-Generator
- `services/legal_pdf.py` — bestehend, Erweiterung um Triage-Seite 1 (ca. 50 Zeilen)
- `routers/reports.py` — neuer Endpoint `GET /reports/{id}/police-package`
Geschätzt: 2–4 Tage Entwicklung.

**DSGVO / Rechtliches:**
- Das Export-ZIP verlässt SafeVoice nicht automatisch. Es wird heruntergeladen vom Opfer und physisch zur Polizeidienststelle mitgebracht oder per Online-Anzeige-Portal hochgeladen.
- Rechtsgrundlage für das Opfer: Art. 6(1)(f) DSGVO — berechtigtes Interesse an Strafverfolgung; Art. 9(2)(f) — Geltendmachung von Rechtsansprüchen.
- Das Opfer ist juristisch der "Datenübermittler" an die Polizei, nicht SafeVoice. SafeVoice ist Werkzeugersteller. Diese Konstruktion ist DSGVO-konform, sofern das Opfer explizit zustimmt, dass es das Paket zu Strafverfolgungszwecken exportiert.
- **Risiko:** Wenn das ZIP sensible Daten Dritter enthält (Zeugen, andere Betroffene), muss der Export das dokumentieren.

**Dependencies:**
- Kein Polizei-System-Integration nötig für v1
- Rechtsanwalt sollte die Formulierungen in `platform_request_guide.txt` (§100j StPO Formulierungen) prüfen
- Kein Abkommen mit Polizei nötig — es ist ein verbesserter Benutzerexport

---

### Feature 2 — Zeitkritischer Schnell-Export mit IP-Alarm

**Was es tut:**
Wenn ein neues Beweisstück erfasst wird und requires_immediate_action = true ist (z.B. Todesdrohung §241, Stalking §238), zeigt SafeVoice sofort einen Banner:

> "Achtung: Bei dieser Art von Straftat sind IP-Adressen nur wenige Tage verfügbar. Exportieren Sie das Polizei-Paket **jetzt** und erstatten Sie die Anzeige **heute**, nicht morgen."

Das Banner berechnet einen konkreten "IP-Deadline-Schätzwert" (z.B. "Plattform X speichert IP-Adressen typischerweise 7 Tage. Deadline: 2026-04-17").

**Warum es Zeit spart:**
Nicht für den Sachbearbeiter — für die Gesamtqualität des Falls. Ein frühzeitiger, vollständiger Export erhöht die Chance, dass die IP-Adresse noch vorhanden ist, wenn die Polizei die Anfrage stellt. Das ist der häufigste Grund für Einstellungen. (Quelle: HateAid, "Mit dem Strafrecht gegen digitale Gewalt")

**Geschätzte Wirkung:** Reduktion von Einstellungen mangels Täteridentifizierung um X% — nicht schätzbar ohne Daten. Hypothetisch signifikant.

**Technischer Aufwand:**
Klein. Frontend-Banner + neue Felder in `ClassificationResult` (`ip_deadline_days_by_platform`, `requires_immediate_police_action`). Plattform-Datenbank mit bekannten IP-Speicherfristen (pflegbar als JSON-Config-Datei).
Geschätzt: 1–2 Tage Entwicklung.

**DSGVO:**
Kein neues Datenproblem — Information an den Nutzer, keine Daten an Dritte.

**Dependencies:**
- Plattform-IP-Speicherfristen-Datei muss gepflegt werden (recherchierbar aus Plattform-Transparenzberichten)
- Ggf. Rechtsanwalt prüft Formulierungen

---

### Feature 3 — Maschinenlesbares Übergabeformat (Police Handoff Schema)

**Was es tut:**
SafeVoice veröffentlicht ein offenes JSON-Schema (`PoliceHandoffV1`) mit folgenden Feldern:

```json
{
  "schema_version": "1.0",
  "export_timestamp": "ISO8601",
  "case_id": "UUID",
  "overall_severity": "high|critical",
  "stgb_paragraphs": ["§241", "§238"],
  "requires_immediate_action": true,
  "ip_request_deadline": "2026-04-17",
  "evidence_count": 5,
  "evidence_items": [
    {
      "id": "UUID",
      "platform": "instagram",
      "author_username": "@user",
      "source_url": "https://...",
      "archived_url": "https://web.archive.org/...",
      "captured_at": "ISO8601",
      "content_hash_sha256": "abc123...",
      "previous_hash": "def456...",
      "classification": {...}
    }
  ],
  "hash_chain_valid": true,
  "suggested_specialized_office": "ZAC NRW (StA Köln) für NRW-Fälle"
}
```

Dieses Schema wird:
- Intern von Feature 1 genutzt (als `evidenz_metadata.json`)
- Öffentlich dokumentiert (damit Polizei-IT-Abteilungen es in eigene Systeme importieren könnten)
- Versioniert (V1 → V2 bei Weiterentwicklung)

**Warum es Zeit spart:**
Mittel- bis langfristig: Wenn eine Polizei-Dienststelle oder ein Bundesland das Schema in ihr System importiert, entfällt manuelle Eingabe vollständig. Kurzfristig: Einheitlichkeit macht den Export für Sachbearbeiter vertraut (sie kennen das Format nach dem zweiten Fall).

**Technischer Aufwand:**
Mittel. Pydantic-Modell `PoliceHandoffV1` in `models/`, JSON-Schema-Export für Dokumentation.
Geschätzt: 1–2 Tage für Schema + Dokumentation, plus Abstimmung mit Polizei-Kontakt über Schema-Felder.

**Dependencies:**
- Idealer Weise Feedback von einer Polizei-Dienststelle oder ZAC/ZIT bevor Versionierung beginnt
- Schema-Änderungen nach V1.0 sind aufwändig

---

### Feature 4 — Polizei-Reviewer-Portal (Zugang ohne Opfer-Account)

**Was es tut:**
Ein Staatsanwalt oder Polizei-Sachbearbeiter bekommt vom Opfer (oder von der NGO) einen zeitbegrenzten, read-only Zugangscode zu einem spezifischen Fall. Der Reviewer sieht:
- Alle Beweisstücke mit Hash-Kette
- Klassifikation und StGB-Mapping
- Zeitlinie der Ereignisse
- Plattform-Anfrage-Checkliste
- Status: "Hash-Kette intakt / Manipulation erkannt"

Er kann keinen Fall verändern. Er kann einen Kommentar hinterlassen: "Akte vollständig — IP-Anfrage eingeleitet" (für das Opfer sichtbar).

**Warum es Zeit spart:**
Der Sachbearbeiter muss nicht zwischen PDF, Screenshots und eigenem IT-System wechseln. Alles in einer strukturierten Ansicht. Für die NGO-Caseworkerin: Sie sieht, dass der Fall bei der Polizei angekommen ist, ohne nachfragen zu müssen.

**Technischer Aufwand:**
Mittel bis hoch. Neues Rollenmodell (`reviewer`), Token-basierter Zugang (kein User-Account), neues Frontend-View "Polizei-Reviewer".
Geschätzt: 5–8 Tage Entwicklung.

**DSGVO / Rechtliches:**
Dies ist das komplexeste Feature rechtlich. Wenn SafeVoice einem staatlichen Organ direkten Datenzugang ermöglicht, verändert sich die Rolle von SafeVoice: Wir werden ggf. zum Auftragsverarbeiter für eine Behörde, nicht nur für die NGO. Das erfordert:
- Separaten AVV mit der Behörde
- Prüfung ob Polizei-Zugang unter das Justiz-Datenschutzgesetz (JDG) fällt statt DSGVO
- Rechtsanwalt-Review zwingend vor Implementierung

**Dependencies:**
- Formelle Vereinbarung mit mindestens einer Polizeidienststelle oder ZAC
- Rechtsanwalt zwingend
- Opfer muss explizit zustimmen (der Code ist ein aktiver Sharing-Act des Opfers)

---

### Feature 5 — Schwerpunktstaatsanwaltschaft-Routing

**Was es tut:**
Nach Klassifikation zeigt SafeVoice: "Für diesen Fall ist folgende Stelle zuständig und hat Erfahrung:" basierend auf:
- Bundesland des Opfers (aus Anmeldedaten oder Freifeld)
- Straftatbestand (§241 Bedrohung → ZAC; §130 Volksverhetzung → oft LKA; §184b → BKA zuständig)
- Schwere (critical → direkt Schwerpunkt-StA empfehlen)

Das Routing-Ergebnis wird in den Polizei-Export (Feature 1) eingebettet.

**Warum es Zeit spart:**
Opfer wissen oft nicht, wo sie Anzeige erstatten sollen. Sachbearbeiter bei der Wache müssen selbst nachschlagen, welche Schwerpunktstaatsanwaltschaft für Online-Hasskriminalität zuständig ist. SafeVoice macht das einmal gut und korrekt für alle.

**Technischer Aufwand:**
Klein. JSON-Config mit Bundesland → Zuständige Stelle + Ansprechpartner-URL. Neue Funktion `suggest_authority(stgb_paragraphs, bundesland)` in einem neuen Service `services/authority_routing.py`.
Geschätzt: 1–2 Tage für Implementierung, laufende Pflege der Kontaktdaten.

**DSGVO:**
Kein Datenproblem — statische Routing-Tabelle, keine personenbezogenen Daten.

**Dependencies:**
- Kontaktdaten-Tabelle muss initial recherchiert und dann regelmäßig gepflegt werden
- Bundesland-Feld muss im User-Profil oder Case vorhanden sein (Schema-Erweiterung nötig)

---

## 5. DSGVO / Rechtlicher Weg für Datenfluss

### 5.1 Grundprinzip: Das Opfer ist der Übermittler

DSGVO (Art. 2(2)(d)) gilt nicht für die Polizei als Empfänger — Strafverfolgungsbehörden unterliegen der JI-Richtlinie (Richtlinie 2016/680/EU), die in Deutschland als Datenschutzgesetz der Justiz (BDSG Teile + Landesgesetze) umgesetzt ist. SafeVoice selbst unterliegt DSGVO.

Solange das Opfer einen SafeVoice-Export herunterlädt und selbst zur Polizei bringt, ist SafeVoice nicht Übermittler an die Polizei. SafeVoice ist Werkzeugersteller. Der Export ist eine Dienstleistung für das Opfer, kein Datentransfer an Behörden.

```
Opfer → SafeVoice (Daten eingeben, DSGVO-konform)
Opfer → [herunterlädt Export]
Opfer → Polizei (übergibt Export physisch oder per Online-Portal)
         ↑ Dieser Schritt liegt außerhalb SafeVoice's DSGVO-Verantwortung
```

**Rechtsgrundlagen für das Opfer beim Übermitteln an Polizei:**
- §161 StPO: Polizei darf Informationen zur Ermittlung entgegennehmen
- §158 StPO (geändert 2024): Anzeige kann elektronisch erstattet werden — das schließt Dateianhänge ein
- Art. 6(1)(c) DSGVO i.V.m. §163 StPO: Wenn das Opfer rechtlich zur Kooperation verpflichtet oder berechtigt ist

(Quelle: Bundestag WD 3-087-19 zur Datenverarbeitung durch Polizei; it-recht-kanzlei.de zur Datenweitergabe an Ermittlungsbehörden)

### 5.2 Szenario mit Direktzugang (Feature 4 — komplexes Szenario)

Wenn SafeVoice einem Polizei-Reviewer direkten Portal-Zugang gibt:
- SafeVoice wird zum "Verantwortlichen" für die Datenverarbeitung gegenüber der Behörde
- Möglicherweise Art. 6(1)(c) oder (f) DSGVO — aber strittig bei Behördenzugang
- Zwingend: AVV mit der Behörde oder Einordnung als Joint Controller
- **Empfehlung:** Vor Implementierung Beratung durch einen auf Datenschutzrecht spezialisierten Anwalt, der Erfahrung mit Behörden-Kooperationen hat. Mehrkosten: geschätzt 2.000–5.000 € Rechtsberatung.

### 5.3 Szenario mit API-Integration (hypothetisches zukünftiges Szenario)

Wenn SafeVoice eine API an ein Polizei-System anschließt (z.B. automatischer Push eines Falles an ViVA Bayern oder INPOL):
- Dieser Fall ist kurz- bis mittelfristig nicht realistisch ohne formelle Kooperationsvereinbarung mit einer Landespolizei oder dem BKA
- Würde Zertifizierungsanforderungen für Polizei-IT-Schnittstellen auslösen (TR-03116, BSI-Grundschutz)
- Mindestzeitraum bis zur Umsetzung: 12–18 Monate, wenn eine willige Landespolizei vorhanden ist

---

## 6. Admin-Dashboard Audience Matrix

| Rolle | Was sie sehen müssen | Was sie nicht brauchen |
|---|---|---|
| **Opfer (Einzelnutzer)** | Eigene Fälle + Beweiskette; Exportoptionen (Legal-PDF, Polizei-Paket); IP-Deadline-Alarm; Handlungsempfehlungen; Status "Anzeige erstattet" (Selbst-Flag) | Andere Fälle; Org-Statistiken; Prüftools |
| **Org-Admin (NGO-Direktor)** | Alle Fälle der Org; Caseworker-Auslastung; Statistiken (Fälle nach Severity, StGB-Paragraph, Status); Exportübersicht; Team-Management; AVV-Status | Rohe Beweisinhalte (Datenschutz); Einzelfall-Details ohne Freigabe |
| **Org-Caseworker** | Zugewiesene Fälle; Evidenz-Details; Polizei-Export generieren; Kommentarfunktion; Nächste Aktionen; Deadline-Kalender | Finanzielle/Admin-Daten der Org |
| **Auditor / Stiftung** | Aggregierte Impact-Statistiken (pseudonymisiert/anonymisiert): Anzahl Fälle, Severity-Verteilung, StGB-Mapping-Häufigkeit, durchschnittliche Zeit bis Anzeige; kein Zugang zu Fallinhalten | Alle Fallinhalte; Nutzerdaten; Org-Interna |
| **Polizei-Reviewer** *(Feature 4, wenn gebaut)* | Spezifischer Fall per Token (read-only): Beweiskette, Hashes, Klassifikation, Plattform-Anfrage-Checkliste, Zeitlinie; Kommentar hinterlassen ("IP-Anfrage eingeleitet") | Andere Fälle; Nutzerprofile; Org-Daten; Admin-Funktionen |

---

## 7. Action-Recommendation-Engine

Wenn ein Fall klassifiziert ist, soll SafeVoice konkrete Handlungsempfehlungen ausgeben. Die folgende Tabelle definiert das Verhalten nach Severity × StGB-Paragraph.

### 7.1 Empfehlungen an das Opfer

| Severity | StGB | Empfehlung an Opfer |
|---|---|---|
| CRITICAL | §241 (Bedrohung), §126a (Qualifizierte Bedrohung) | Sofort Polizei anrufen (110). Anzeige noch heute. IP-Frist beginnt sofort. Notruf wenn akute Gefahr. Rechtsbeistand: HateAid (kostenlos), Weißer Ring |
| CRITICAL | §238 (Stalking) | Polizei informieren — §238 ist Offizialdelikt, keine Antragsfrist. Beweissicherung sofort exportieren. Alle Beweisstücke sichern. Kontakte: LKA-Stalking-Beratungsstellen, Weißer Ring |
| HIGH | §185/186/187 (Beleidigung/Verleumdung/üble Nachrede) | Strafantrag innerhalb 3 Monate seit Kenntnis. Exportieren, Anzeige bei Schwerpunkt-StA bevorzugt. Cave: §185 ist Antragsdelikt — Frist versäumen = automatische Einstellung. Kostenloser Rechtsbeistand: HateAid Rechtshilfe |
| HIGH | §130 (Volksverhetzung) | Offizialdelikt — keine Antragsfrist. Bei Polizei oder Staatsanwaltschaft anzeigen. Ggf. auch beim NetzDG-Meldepunkt. BKA-Meldestelle: www.bka.de/DE/IhreSicherheit |
| HIGH | §201a (Verletzung des Bildnisses), Deepfakes | Sofortiger Antrag auf Löschung bei Plattform (NetzDG/DSA). Gleichzeitig Anzeige. 3-Monats-Antragsfrist. Archivierung JETZT, vor Löschung. |
| HIGH | §263/263a (Betrug/Computerbetrug) | Anzeige bei Polizei. Bei Finanzbetrug: BaFin-Meldung (SafeVoice hat bereits `/reports/{id}/bafin`). Kontoverbindung sofort sperren lassen. Verbraucherzentrale informieren. |
| MEDIUM | §185 (Beleidigung) | 3-Monats-Frist beachten. Online-Strafanzeige per online-strafanzeige.de möglich. Alternativ: Abmahnung zivilrechtlich (schneller, günstiger bei bekanntem Täter). |
| LOW | Allgemein | Beweise sichern. Kein sofortiger Handlungsdruck. Beratung bei Beratungsstellen empfohlen, bevor Anzeige erstattet wird. |

### 7.2 Empfehlungen an die Org (NGO-Caseworker)

| Trigger | Empfehlung |
|---|---|
| requires_immediate_action = true | Sofort einem erfahrenen Caseworker zuweisen. Opfer-Check-In innerhalb 24h. IP-Deadline im Kalender eintragen. |
| overall_severity = CRITICAL + Kategorie DEATH_THREAT | Fall priorisieren. Polizei-Exportpaket generieren. Ggf. persönlich Anzeige begleiten. Sicherheitsberatung anbieten. |
| overall_severity = HIGH + mehrere Beweisstücke | Pattern-Analyse anfordern (`/analyze/case`). Ggf. koordinierter Angriff — dann mehrere Täter → eigene Ermittlungsstrategie |
| Kategorie COORDINATED_ATTACK | Ggf. Anzeige gegen Unbekannt mit allen Profilen. BKA-Meldung in Erwägung ziehen. Interne Eskalation im Org |
| Kategorie INTIMATE_IMAGES | Sofort Plattform-Takedown initiieren (DMCA/DSA-Notfall). Parallel Strafanzeige §201a. Sensible Begleitung des Opfers |

### 7.3 Empfehlungen an Polizei-Reviewer (wenn Feature 4 gebaut)

| Trigger | Automatische Hinweiskarte im Reviewer-Portal |
|---|---|
| requires_immediate_action = true | "Zeitkritisch: IP-Adress-Anfrage sollte heute gestellt werden. Plattform: [Name]. Rechtsgrundlage: §100j StPO. Musterschreiben: [Link]." |
| Paragraph §241 oder §238 | "Offizialdelikt — keine Antragsfrist des Opfers nötig. Eigeninitiative möglich." |
| Paragraph §185 | "Antragsdelikt — Opfer muss innerhalb 3 Monate Antrag stellen. Datum der Tatkenntnis: [Datum aus Akte]. Frist läuft ab: [Datum]." |
| Hash-Kette valide | "Beweismittelintegrität: SHA-256-Kette geprüft — keine Manipulation erkannt. Dokumentiert für Gerichtsakte." |
| Hash-Kette ungültig | "WARNUNG: Hash-Kette unterbrochen. Mögliche Manipulation oder fehlerhafte Erfassung. Beweismittel vor Verwendung manuell prüfen." |
| archived_url vorhanden | "Archivkopie bei Archive.org verfügbar: [URL]. Verfügbar auch wenn Original gelöscht." |
| archived_url fehlt | "Keine Archivkopie. Original-URL möglicherweise nicht mehr verfügbar. Sofortige Plattform-Anfrage empfohlen." |

---

## 8. Risiken & Offene Fragen

### 8.1 Rechtliche Risiken

**R1 — Falsch-positive Klassifikation**
Das LLM kann StGB-Paragraph falsch zuordnen. Wenn ein Sachbearbeiter die Klassifikation ohne eigene Prüfung übernimmt und ein Beschluss auf Basis eines Fehlers beantragt wird, entsteht ein Problem. Mitigation: Exportpaket muss deutlich kennzeichnen: "Diese Klassifikation ist KI-generiert und dient nur als Arbeitshilfe. Rechtliche Einschätzung obliegt der Staatsanwaltschaft."

**R2 — Doppelrolle SafeVoice**
SafeVoice ist Opfer-Tool. Wenn es gleichzeitig Polizei-Tool wird, entsteht ein potenzieller Interessenkonflikt: Was wenn das Opfer die Daten nicht an die Polizei übermitteln möchte, die NGO aber schon? Klare Governance nötig: Das Opfer entscheidet, nie die Org oder SafeVoice.

**R3 — Scope Creep zu Strafverfolgungssoftware**
Wenn SafeVoice zu einem Tool wird, das Strafverfolgungsbehörden direkt unterstützt (Feature 4), könnte es als Strafverfolgungssoftware eingestuft werden. Das löst andere Regulierungsanforderungen aus (BSI-Zertifizierung, Vergaberecht, ggf. AI Act Hochrisiko-Klassifikation). Mitigation: Klar als "Bürger-Tool mit optionalem Reviewer-Zugang" positionieren, nicht als Polizei-Software.

**R4 — Haftung bei Fehlleitung**
Wenn SafeVoice empfiehlt, Anzeige bei der falschen Stelle zu erstatten (z.B. falsche Schwerpunkt-StA), und das Verfahren scheitert deshalb, könnte das Opfer Ansprüche geltend machen. Mitigation: Empfehlungen als "Hinweise, keine Rechtsberatung" kennzeichnen. Anwalt prüft Texte.

### 8.2 Technische Risiken

**T1 — Polizei-IT ist heterogen**
Jedes Bundesland hat andere Systeme. Ein JSON-Export, der in Bayern nützlich ist, wird in Berlin anders verarbeitet. Ein einheitliches Schema wird erst langfristig nützlich sein, wenn mehrere Stellen es adoptieren.

**T2 — Plattform-Speicherfristen ändern sich**
Die `platform_request_guide.txt` und der IP-Deadline-Alarm (Feature 2) basieren auf aktuellen Speicherfristen, die sich ändern können (Meta, X etc.). Eine veraltete Fristangabe könnte Opfer in falscher Sicherheit wiegen. Mitigation: Feature 2 mit Disclaimer "Fristen können sich ändern, bitte aktuell prüfen" und regelmäßige Pflege der Config-Datei.

**T3 — Missbrauch des Reviewer-Zugangs**
Ein Zugangscode für Feature 4 könnte kompromittiert werden. Mitigation: Kurze Gültigkeit (7 Tage), Single-Use, Audit-Log aller Reviewer-Zugriffe, Opfer wird bei jedem Zugriff informiert.

### 8.3 Offene Fragen für Validierung

1. Wie lange dauert es tatsächlich, eine Strafanzeige bei einer regulären Polizeidienststelle zu bearbeiten? (Benchmarks nötig — Gespräch mit Sachbearbeiter)
2. Nutzen Sachbearbeiter bei Cybercrime-Fällen überhaupt strukturierte Daten, oder drucken sie alles aus? (Workflow-Analyse nötig)
3. Gibt es Bundesländer, die bereits ein strukturiertes Daten-Eingangsformat für digitale Gewalt haben? (ZAC NRW, ZCB Bayern ansprechen)
4. Wie reagiert eine Schwerpunktstaatsanwaltschaft auf einen SafeVoice-Export? Würden sie das `hash_chain.csv` als gerichtsverwertbaren Beweis akzeptieren?
5. Gibt es Pilotprojekte beim BKA oder BMJ, die ähnliche Ansätze testen?

---

## 9. Empfohlene Nächste Schritte

**Sofort (diese Woche):**
1. Polizei-Kontakt (Mikel's Freund oder ZAC-Kontakt) ansprechen: 30-minütiges Gespräch — Workflow-Validierung der Annahmen in §2 und §3.
2. Fragen aus §8.3 als Gesprächsleitfaden vorbereiten.

**Sprint 2 (nächste 2–4 Wochen):**
3. Feature 1 bauen: Polizei-Exportpaket. Neuer Endpoint `GET /reports/{id}/police-package`. Pydantic-Modell `PoliceHandoffV1`. Triage-Seite im Legal-PDF.
4. Feature 5 bauen: Authority-Routing-Service mit Bundesland-Tabelle. 1–2 Tage.
5. Feature 2 bauen: IP-Deadline-Alarm. Frontend-Banner + Platform-Fristen-Config.

**Sprint 3 (4–8 Wochen):**
6. Feature 3 fertigstellen: Schema publizieren, Dokumentation, Feedback von einem Polizei-Kontakt einholen.
7. Action-Recommendation-Engine (§7) implementieren: Regel-basiert auf Severity × Paragraph, kein neues ML nötig.

**Langfristig (3–6 Monate):**
8. Feature 4 (Reviewer-Portal): Nur starten wenn ein formeller Polizei-Partner gefunden wurde und ein Rechtsanwalt die Konstruktion geprüft hat.
9. BMJ-Kontakt: Polizei-Exportpaket als Beitrag zum "Gesetz gegen digitale Gewalt"-Konsultationsprozess einbringen — SafeVoice könnte als Referenzimplementierung für maschinenlesbaren Anzeigestandard dienen.
10. Prototype Fund / Stiftungsantrag: Bridge-Features als Forschungs- und Entwicklungsprojekt mit Polizei als Partner positionieren — erhöht Förderchancen erheblich.

---

## Quellen

- HateAid: "Mit dem Strafrecht gegen digitale Gewalt" — https://hateaid.org/strafrecht-trifft-digitale-gewalt/
- HateAid: "Angegriffen & alleingelassen" (TUM-Studie 2025) — https://hateaid.org/wp-content/uploads/2025/01/hateaid-tum-studie-angegriffen-und-alleingelassen-2025.pdf
- HateAid: Tätigkeitsbericht 2024 — https://hateaid.org/taetigkeitsbericht-2024/
- netzpolitik.org: "Fachleute fordern: Das fehlt beim Schutz vor digitaler Gewalt" (Feb. 2026) — https://netzpolitik.org/2026/fachleute-fordern-das-fehlt-beim-schutz-vor-digitaler-gewalt/
- Bundestag Drucksache 20/9170 (Digitale Gewalt) — https://dserver.bundestag.de/btd/20/091/2009170.pdf
- Bundestag WD 3-087-19 (Datenverarbeitung durch Polizei) — https://www.bundestag.de/resource/blob/648416/c5d906ae86351a39cb9d9e7f8d213dea/WD-3-087-19-pdf-data.pdf
- HateAid-Stellungnahme Bundestag (Schriftformerfordernis) — https://www.bundestag.de/resource/blob/1002782/22b14f92066e8d3475782f0971135d46/Stellungnahme-Benning_HateAid.pdf
- Niedersächsisches Landesjustizportal (Ermittlungsverfahren-Ablauf) — https://justizportal.niedersachsen.de/startseite/gerichte_und_staatsanwaltschaften/staatsanwaltschaften/ablauf_des_ermittlungsverfahrens/
- ZCB Bayern — https://www.justiz.bayern.de/gerichte-und-behoerden/generalstaatsanwaltschaft/bamberg/spezial_1.php
- ZIT Hessen — https://staatsanwaltschaften.hessen.de/staatsanwaltschaften/generalstaatsanwaltschaft-frankfurt-am-main/aufgabengebiete/zentralstelle-zur-bekaempfung-der-internet-und-computerkriminalitaet-zit
- ZAC NRW — https://www.sta-koeln.nrw.de/aufgaben/geschaefte-stak_1_zac/index.php
- ZHIN Niedersachsen (StA Göttingen) — https://staatsanwaltschaft-goettingen.niedersachsen.de/cybercrime/cybercrime-195740.html
- Stark im Amt (Unterstützung nach Bundesland) — https://www.stark-im-amt.de/unterstuetzung-in-ihrem-bundesland/
- BKA Elektronische Fahndungs- und Informationssysteme — https://www.bka.de/DE/UnsereAufgaben/Ermittlungsunterstuetzung/ElektronischeFahndungsInformationssysteme/polizeilicheInformationssysteme.html
- EU-Lex: JI-Richtlinie 2016/680 — https://eur-lex.europa.eu/DE/legal-content/summary/protecting-personal-data-that-is-used-by-police-and-criminal-justice-authorities-from-2018.html
- it-recht-kanzlei.de: DSGVO Datenweitergabe an Polizei — https://www.it-recht-kanzlei.de/dsgvo-datenweitergabe-polizei-staatsanwaltschaft-ermittlung.html
- BMJ Gesetzentwurf digitale Gewalt / ZDF (Dez. 2024) — https://www.zdfheute.de/politik/deutschland/digitale-gewalt-deepfake-gesetz-entwurf-hubig-100.html
- HateAid: Gesetz gegen digitale Gewalt (Zeitlinie) — https://hateaid.org/gesetz-gegen-digitale-gewalt/
- polizei-beratung.de: Ablauf Strafverfahren — https://www.polizei-beratung.de/infos-fuer-betroffene/ablauf-des-strafverfahrens/
- legalnerd.de: Was passiert nach einer Strafanzeige — https://legalnerd.de/rechtswissen/was-passiert-nach-einer-strafanzeige/

---

*Alle geschätzten Zeitangaben in §3 sind unvalidierte Hypothesen. Keine dieser Angaben ist durch empirische Polizei-Workflow-Studien belegt. Validierung durch ein direktes Gespräch mit einem Sachbearbeiter oder einer Schwerpunktstaatsanwaltschaft ist vor jeder Produktentscheidung zwingend.*
