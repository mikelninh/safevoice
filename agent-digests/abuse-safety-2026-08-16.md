# Abuse-Safety Digest — 2026-08-16

**Watchdog:** ABUSE-SAFETY WATCH · **Repo:** safevoice (mikelninh) · **Branch:** agent/abuse-safety-2026-08-16

## Übersicht
Zwei relevante Gesetzgebungsvorhaben im deutschen Strafrecht数码ischer Gewalt sind
aktiv. Beide sind **noch nicht in Kraft**, betreffen aber direkt SafeVoices 12
StGB-/NetzDG-Paragraphen (§§ 185, 186, 187, 241, 126a, 238, 201a, 263, 263a, 269,
130 + NetzDG § 3). Die Schema-Aktualisierung sollte vorbereitet werden, **bevor**
die Gesetze verabschiedet werden, damit der Court-Prep-Agent nicht veraltet ist.

---

## Fund 1 — Gesetz gegen digitale Gewalt (GgdG): drei neue Straftatbestände

- **Änderung:** Der Referentenentwurf des BMJV (PM 28/2026, 17.04.2026) führt drei
  neue StGB-Paragraphen ein: **§ 184k StGB** (Verletzung der Intimsphäre durch
  Bildaufnahmen — pornographische Deepfakes, digitaler Voyeurismus, Rache-Pornos,
  Vergewaltigungsvideos; bis zu 2 Jahre), **§ 201b StGB** (Verletzung von
  Persönlichkeitsrechten durch täuschende Inhalte — ansehensschädigende Deepfakes,
  z. B. KI-Fake-Videos mit vermeintlichen Straftaten; nicht das bloße Herstellen),
  **§ 202e StGB** (Unbefugte Überwachung mittels Informations- oder
  Kommunikationstechnik — z. B. GPS-Tracker-Cyberstalking). Dazu neue
  zivilrechtliche Durchsetzungsrechte: **Auskunftsanspruch** (Richtervorbehalt),
  **beweissichernde Anordnungen**, **zeitweilige Accountsperre** und
  **Zustellungsbevollmächtigter** für Nicht-EU-Plattformen.
- **Paragraphen betroffen:** Neu: § 184k, § 201b, § 202e StGB. Überschneidung/Erweiterung
  zu bestehendem **§ 201a** (SafeVoice LAW_201A) und **§ 238** (Nachstellung).
  NetzDG § 3 bleibt unberührt.
- **Inkrafttreten:** Noch **nicht** in Kraft. Referentenentwurf 17.04.2026,
  Stellungnahmefrist der Länder/Verbände bis 22.05.2026. Danach: Kabinett →
  Bundestag → Bundesrat. Wirksamkeit offen (voraussichtlich Monate entfernt).
- **Auswirkung auf SafeVoice Court-Prep:** Der Agent deckt bildbasierte
  Deepfake-/Intimbereichs-Fälle bisher nur über § 201a ab; die neuen §§ 184k/201b
  schließen Lücken (z. B. ansehensschädigende, nicht-pornographische Deepfakes,
  GPS-Tracking). Die neuen zivilrechtlichen Rechtsbehelfe (Auskunft,
  Beweissicherung, Accountsperre) müssen in `recommended_actions` ergänzt werden,
  damit die Strafanzeige um zivilrechtliche Soforthilfe ergänzt wird.
- **Datei/Paragraph zur Aktualisierung:**
  - `backend/app/data/mock_data.py` — `LAW_201A` um § 184k ergänzen; neue
    `LAW_184K`, `LAW_201B`, `LAW_202E` anlegen.
  - `backend/app/services/law_mapper.py` — `GERMAN_LAW_MAP` erweitern:
    `IMPERSONATION` → § 201b; neue Kategorie (Intimbereich/Deepfake-Bild) → § 184k;
    `STALKING`/Nachstellung → § 202e.
  - `backend/app/services/court_prep_agent.py` — neue zivilrechtliche Rechtsbehelfe
    (Auskunftsanspruch, beweissichernde Anordnung, zeitweilige Accountsperre) in
    `recommended_actions` / `recommended_actions_de` aufnehmen.

### EN
- **Headline:** Germany's "Digital Violence Act" draft creates 3 new offences (§§ 184k, 201b, 202e StGB)
- **What changed:** BMJV draft (PM 28/2026, 17 Apr 2026) adds § 184k StGB (intimate-image/Deepfake offences incl. pornographic Deepfakes, digital voyeurism, revenge porn, rape videos; up to 2 yrs), § 201b StGB (reputation-damaging Deepfakes, e.g. AI fakes showing fake crimes; making accessible, not making), § 202e StGB (unauthorised surveillance via IT, e.g. GPS-trackers). Plus civil remedies: disclosure order (judicial warrant), evidence-preservation order, temporary account suspension, domestic agent for non-EU platforms.
- **Why:** Current law lags AI/device reality; many image-based and stalking harms had no dedicated offence. Closes gaps in SafeVoice's existing § 201a / § 238 coverage.
- **Effective:** Not yet in force. Referentenentwurf 17 Apr 2026; stakeholder comment deadline 22 May 2026. Requires Cabinet → Bundestag → Bundesrat. In force months away.
- **Deadline:** Stakeholder comment window closed 22 May 2026 (passed). Next: Cabinet bill, then parliamentary passage — no fixed date.
- **Who's affected:** Victims of Deepfakes, image-based sexual abuse, GPS-stalking; platforms; SafeVoice (court-prep schema).
- **How:** Monitor passage. Pre-build schema entries § 184k/§ 201b/§ 202e and add civil remedies to court-prep recommended actions so the Strafanzeige is current on day one.
- **Citizen tip:** Until enacted, still use § 201a, § 238, § 185 and the NetzDG route; preserve evidence now via SafeVoice. New §§ only apply once the law enters force.

---

## Fund 2 — § 188 StGB (Politikerbeleidigung): grundlegende Reform beschlossen

- **Änderung:** Die Justizministerkonferenz (JUMIKO) beschloss am 12.06.2026 auf Antrag
  von Sachsen und Baden-Württemberg, § 188 StGB ("Gegen Personen des politischen
  Lebens gerichtete Beleidigung, üble Nachrede und Verleumdung") deutlich zu
  beschränken: Die Sonderregelung des **§ 188 Abs. 1 StGB für Spitzenpolitiker soll
  entfallen**; der Anwendungsbereich soll auf **Kommunalpolitiker** begrenzt werden.
  Damit würde die 2021 vorgenommene Ausweitung (auch auf Beleidigung § 185, mit
  höherem Strafrahmen und Verfolgung ohne Strafantrag bei öffentlichem Interesse)
  für Spitzenpolitiker weitgehend rückgängig gemacht.
- **Paragraphen betroffen:** § 188 StGB (nicht in SafeVoices 12, aber modifiziert
  Anwendung von **§ 185** Beleidigung, **§ 186** üble Nachrede, **§ 187** Verleumdung
  — alle drei in SafeVoices 12).
- **Inkrafttreten:** Noch **nicht** Gesetz. JUMIKO-Beschluss 12.06.2026; Umsetzung
  bedarf eines Gesetzgebungsverfahrens (Bundestag/Bundesrat). Wirksamkeit offen.
- **Auswirkung auf SafeVoice Court-Prep:** Bei Beleidigungsfällen gegen
  Spitzenpolitiker entfiele künftig der Qualifikationstatbestand § 188; es bliebe
  der Regelweg über § 185/§ 186/§ 187 mit der **3-Monats-Strafantragsfrist**. Der
  Court-Prep-Agent muss die `potential_consequences`/`recommended_actions` für
  § 185/186/187 entsprechend konditional ausweisen (Hinweis auf § 188-Status).
- **Datei/Paragraph zur Aktualisierung:**
  - `backend/app/data/mock_data.py` — `LAW_185`/`LAW_186`/`LAW_187` Beschreibung um
    § 188-Status/Hinweis ergänzen.
  - `backend/app/services/court_prep_agent.py` — Logik für Beleidigungsfälle
    öffentlicher Personen um § 188-Reform-Hinweis erweitern.

### EN
- **Headline:** Germany to curb § 188 StGB special protection for top politicians
- **What changed:** On 12 Jun 2026 the Justice Ministers' Conference (JUMIKO) resolved to sharply restrict § 188 StGB ("insult, defamation, slander against persons in public life"): abolish the § 188(1) special rule for top politicians and limit scope to local/communal office-holders. This would reverse much of the 2021 expansion (which added § 185 insult, a higher penalty, and prosecution without complaint where public interest exists).
- **Why:** The 2021 expansion created legal uncertainty and the impression that criticism of leaders is punished more harshly; frees prosecution resources and strengthens freedom of speech for critique of top politicians.
- **Effective:** Not yet law. JUMIKO resolution 12 Jun 2026; needs legislation (Bundestag/Bundesrat). Effective date open.
- **Deadline:** None set. Legislative steps pending — monitor for a bill.
- **Who's affected:** Public figures, prosecutors, SafeVoice (assessment of § 185/186/187 insult cases).
- **How:** When enacted, the aggravated § 188 route disappears for top politicians; standard § 185/186/187 with the 3-month complaint deadline applies. Update court-prep logic conditionally.
- **Citizen tip:** Public figures should not assume the aggravated § 188 route will remain; file § 185/186/187 within the 3-month Strafantrag window. Document now via SafeVoice.

---

## Quellen (geteilt / shared)
1. BMJV Pressemitteilung 28/2026 (17.04.2026): https://www.bmjv.de/SharedDocs/Pressemitteilungen/DE/2026/0417_Gesetz_gegen_digitale_Gewalt.html
2. BMJV Gesetzgebungsverfahren "Gesetz gegen digitale Gewalt" (Stand: Entwurf): https://www.bmjv.de/SharedDocs/Gesetzgebungsverfahren/DE/2026_Gesetz_gegen_digitale_Gewalt.html
3. tagesschau (17.04.2026): https://www.tagesschau.de/inland/innenpolitik/hubig-digitale-gewalt-102.html
4. Sächsischer Medienservice — JUMIKO-Beschluss § 188 (12.06.2026): https://www.medienservice.sachsen.de/medien/news/1097968
5. LTO — Justizminister wollen Politikerbeleidigung beschränken: https://www.lto.de/recht/nachrichten/n/beschluesse-justizministerkonferenz-jumiko-2026-hamburg-sexualisierte-gewalt-politikerbeleidigung
6. Justizministerium Baden-Württemberg — Reform von § 188 StGB: https://jum.baden-wuerttemberg.de/de/presse-service/presse/pressemitteilung/pid/justizministerkonferenz-fordert-reform-von-188-stgb
