# Abuse-Safety Digest — 2026-08-13

**Status-Update:** Dieser Digest meldet eine **anhängige Reform**, die das SafeVoice-Court-Prep direkt betrifft. Es handelt sich (noch) nicht um geltendes Recht — aber SafeVoice deckt die betroffenen Tatbestände heute gar nicht ab und sollte vor Inkrafttreten nachrüsten.

---

## 🔴 FUND 1 — Gesetz gegen digitale Gewalt (BMJV-Referentenentwurf v. 17.04.2026)

**Änderung:** Das Bundesministerium der Justiz (BMJV) hat am 17.04.2026 den Referentenentwurf eines *Gesetzes zur Stärkung des zivilrechtlichen und strafrechtlichen Schutzes vor digitaler Gewalt* veröffentlicht. Der Entwurf führt drei neue/erweiterte StGB-Tatbestände ein, die Bild- und KI-basierte digitale Gewalt sowie technikgestützte Überwachung erfassen:

- **§ 184k StGB (neu gefasst — Verletzung der Intimsphäre durch Bildaufnahmen):** Erfasst künftig die unbefugte Herstellung und Verbreitung von intimem Bildmaterial **unabhängig von der Herstellungsform** (echte *oder* KI/deepfake-erzeugte Aufnahmen) und **unabhängig vom Ort** (privat oder öffentlich). Betrifft pornographische Deepfakes, digitalen Voyeurismus (Upskirting/Downblousing), Vergewaltigungsvideos und „Rache-Pornos“.
- **§ 201b StGB (NEU — Verletzung von Persönlichkeitsrechten durch täuschende Inhalte):** Strafbarerklärung des unbefugten Zugänglichmachens **ansehensschädigender (auch nicht-sexualisierter) Deepfakes** und vergleichbarer KI-Manipulationen (z. B. gefälschte Videos/Redeaufnahmen einer Person).
- **§ 202e StGB (NEU — Unbefugte Überwachung mittels Informations- oder Kommunikationstechnik):** Strafbarerklärung der wiederholten/ständigen digitalen Überwachung des Aufenthaltsorts oder der Tätigkeiten einer Person (z. B. Cyberstalking per GPS-Tracker). Setzt nach Satz 2 voraus, dass wahrscheinlich ein schwerer Schaden eintritt. Orientiert sich an Art. 6 der EU-Richtlinie (EU) 2024/1385.

**Betroffene Paragraphen:** § 184k StGB, § 201b StGB, § 202e StGB — sowie **§ 201a StGB indirekt** (die Entwurfsbegründung erklärt § 201a Abs. 3/4 für den neuen § 201b für entsprechend anwendbar; § 184k steht zu § 201a in Tateinheit/Konkurrenz).

**Inkrafttreten:** Noch nicht in Kraft. Referentenentwurf, Anhörung der interessierten Kreise lief bis **22.05.2026**. Voraussichtliches Inkrafttreten: **2. Halbjahr 2026** (Stand der Recherche: noch nicht im Bundeskabinett/Bundestag beschlossen).

**Auswirkung auf SafeVoice Court-Prep:** SafeVoice bildet diese Tatbestände **aktuell gar nicht ab**. Der `law_mapper` kennt nur § 185/186/241/126a/263/263a/269 sowie NetzDG § 3; Stalking wird auf § 238 gemappt (siehe `backend/app/services/law_mapper.py`). Opfer von KI-Deepfakes, Image-based Abuse oder tracker-gestütztem Cyberstalking erhielten im erzeugten Strafanzeigen-Entwurf **nicht den passendsten, demnächst neuen Paragraphen** zitiert. Die Court-Prep-Ausgabe wäre in diesen Fällen rechtlich unvollständig.

**Konkrete Schema-Updates nötig (Datei/Paragraph):**
- `backend/app/data/mock_data.py`: neue `GermanLaw`-Objekte `LAW_184k`, `LAW_201b`, `LAW_202e` anlegen (Titel, max_penalty, applies_because_de).
- `backend/app/services/law_mapper.py`: `LAW_184k/201b/202e` importieren und neue Kategorien (z. B. `DEEPFAKE`, `IMAGE_ABUSE`, `CYBER_SURVEILLANCE`) in `GERMAN_LAW_MAP` eintragen; ggf. bestehende Stalking-/Misogynie-Mappings um § 202e ergänzen.
- `evals/harassment_eval_set.json`: Eval-Cases für Deepfake / Bildmaterial / GPS-Tracking nachrüsten, damit der Classifier die neuen Codes lernt.

**Quellen:**
- BMJV-Pressemitteilung 28/2026 (17.04.2026): https://www.bmjv.de/SharedDocs/Pressemitteilungen/DE/2026/0417_Gesetz_gegen_digitale_Gewalt.html
- BMJV-Gesetzgebungsverfahren (Referentenentwurf + FAQ): https://www.bmjv.de/SharedDocs/Gesetzgebungsverfahren/DE/2026_Gesetz_gegen_digitale_Gewalt.html
- Morrison Foerster Analyse (30.04.2026): https://www.mofo.com/resources/insights/260429-germany-s-draft-act-against-digital-violence
- netzpolitik.org Detailanalyse (§ 184k, § 201b, § 202e): https://netzpolitik.org/2026/gesetz-gegen-digitale-gewalt-diese-deepfakes-sollen-kuenftig-strafbar-sein/
- Deutscher Juristinnenbund Stellungnahme 26-13: https://www.djb.de/presse/stellungnahmen/detail/st26-13
- BRAK Stellungnahme Nr. 30 (Mai 2026): https://www.brak.de/fileadmin/05_zur_rechtspolitik/stellungnahmen-pdf/stellungnahmen-deutschland/2026/stellungnahme-der-brak-2026-30.pdf

### EN
- **Headline:** Germany's Draft "Digital Violence Act" adds new StGB offences for deepfakes, image-based abuse and tech surveillance
- **What changed:** The Federal Ministry of Justice (BMJV) published a draft bill on 17 Apr 2026 strengthening civil and criminal protection against digital violence. It creates/revises three StGB offences: § 184k StGB (broadened — intimate-image abuse, now covering AI/deepfake and real imagery, anywhere); § 201b StGB (NEW — personality-rights violation via deceptive/non-sexualised deepfakes); § 202e StGB (NEW — unauthorised surveillance using ICT, e.g. GPS-trackers for cyberstalking, aligned with Art. 6 of EU Directive (EU) 2024/1385). § 201a StGB is indirectly affected (§ 201a(3)-(4) made applicable to new § 201b).
- **Why:** Closes prosecution gaps for pornographic/non-sexualised deepfakes, digital voyeurism and tech-enabled stalking — phenomena SafeVoice victims routinely report.
- **Effective:** Not yet in force. Referentenentwurf; consultation closed 22 May 2026. Expected entry into force H2 2026 (not yet adopted by Cabinet/Bundestag as of research date).
- **Deadline:** SafeVoice should add these paragraphs to its schema before entry into force so court-prep output cites them.
- **Who's affected:** Survivors of AI/deepfake abuse, image-based abuse (revenge porn, upskirting) and tracker-based cyberstalking who use SafeVoice to generate a Strafanzeige.
- **How:** Update backend/app/data/mock_data.py (new GermanLaw objects LAW_184k/201b/202e), backend/app/services/law_mapper.py (import + new categories DEEPFAKE/IMAGE_ABUSE/CYBER_SURVEILLANCE in GERMAN_LAW_MAP), and add eval cases to evals/harassment_eval_set.json.
- **Citizen tip:** If someone shares a fake sexual or defamatory video/photo of you, or tracks you with a GPS device, save the evidence now — these acts are becoming explicitly criminal and will strengthen your future Strafanzeige.

---

## 🟡 FUND 2 — NetzDG / BNetzA: kein neuer Änderungsbefund in diesem Scan

**Änderung:** In diesem Lauf wurden **keine neuen, in Kraft getretenen Änderungen** am Netzwerkdurchsetzungsgesetz (NetzDG) oder an den BNetzA-Meldepflicht-Regeln identifiziert. Die letzte relevante NetzDG-Novelle (Hasskriminalitätsbekämpfung) stammt aus 2021/2022 und ist bereits im SafeVoice-Schema als `NetzDG § 3` abgebildet.

**Betroffene Paragraphen:** NetzDG § 3 (unverändert); BNetzA-Meldepflicht (§ 5 Abs. NetzDG, unverändert).

**Inkrafttreten:** — (keine Änderung).

**Auswirkung auf SafeVoice Court-Prep:** Keine. Das `PLATFORM_LAWS["de"] = [NETZ_DG]`-Mapping bleibt gültig.

**Quellen (Recherche-Stand):**
- Bundesregierung Archiv NetzDG-Änderung: https://www.bundesregierung.de/breg-en/service/archive/bekaempfung-hasskriminalitaet-1738462
- BNetzA Meldepflicht: https://www.bundesnetzagentur.de/DE/Fachthemen/Telekommunikation/Unternehmenspflichten/Meldepflicht/start.html

### EN
- **Headline:** NetzDG / BNetzA: no new change found in this scan
- **What changed:** No newly enacted amendment to the Network Enforcement Act (NetzDG) or BNetzA reporting-duty rules was identified in this run. The last relevant NetzDG amendment (hate-crime combat) dates to 2021/2022 and is already reflected as `NetzDG § 3` in SafeVoice.
- **Why:** Routine monitoring — no active reform touching platform-enforcement duties was found.
- **Effective:** — (no change).
- **Deadline:** None.
- **Who's affected:** None currently.
- **How:** No schema change required; `PLATFORM_LAWS["de"] = [NETZ_DG]` remains valid.
- **Citizen tip:** NetzDG takedown rights are unchanged — you can still demand platforms remove obviously illegal content within 24h/7 days.
