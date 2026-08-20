# Abuse-Safety Digest — 2026-08-20

Watchdog-Lauf über deutsches Belästigungs-/Cybercrime-Recht (StGB, NetzDG/DSA, BNetzA).
**Ergebnis: 3 relevante Vorgänge, 6 betroffene Paragraphen. Noch kein Gesetz in Kraft — Vorbereitung nötig, keine sofortige Schema-Änderung.**

---

## Fund 1 — Drei neue Straftatbestände gegen digitale Gewalt (§§ 184k, 201b, 202e StGB-E)

- **Was ändert sich:** Der Referentenentwurf „Gesetz zur Stärkung des zivilrechtlichen und strafrechtlichen Schutzes vor digitaler Gewalt“ schafft drei neue Tatbestände: **§ 184k StGB** („Verletzung der Intimsphäre durch Bildaufnahmen“ — unbefugtes Herstellen und Verbreiten von intimem Bildmaterial, egal ob echt oder KI-generiert, egal ob privat oder öffentlich aufgenommen; erfasst pornografische Deepfakes, digitalen Voyeurismus/Upskirting, Vergewaltigungsvideos, „Rache-Pornos“), **§ 201b StGB** („Verletzung von Persönlichkeitsrechten durch täuschende Inhalte“ — unbefugtes Zugänglichmachen sonstiger Deepfakes, die dem Ansehen erheblich schaden können; Satire ist ausgenommen; Herstellung allein ist nicht erfasst) und **§ 202e StGB** („Unbefugte Überwachung mittels Informations- oder Kommunikationstechnik“ — insbesondere Cyberstalking per GPS-Tracker und Spyware).
- **Betroffener Paragraph:** neu §§ 184k, 201b, 202e StGB; Abgrenzung zu bestehendem § 201a StGB (Bildaufnahmen) und § 238 StGB (Nachstellung).
- **Warum:** Bildbasierte sexualisierte Gewalt und Cyberstalking waren nach geltendem Recht nur lückenhaft strafbar; das Vorhaben ist im Koalitionsvertrag vereinbart.
- **Inkrafttreten:** offen. Stand 20.08.2026 liegt nur der Referentenentwurf vom 17.04.2026 vor; die Verbändeanhörung endete am 22.05.2026, die Stellungnahmen wurden am 03.06.2026 veröffentlicht. Ein Kabinettsbeschluss ist nicht belegt.
- **Frist:** Stellungnahmefrist 22.05.2026 (abgelaufen). Für Betroffene gilt weiterhin die Strafantragsfrist von 3 Monaten (§ 77b StGB) bei Antragsdelikten.
- **Wer ist betroffen:** Betroffene von Deepfakes, heimlichen Intimaufnahmen und GPS-/Spyware-Stalking; Täter; Plattformen.
- **Impact auf SafeVoice Court-Prep:** **hoch, aber noch nicht scharf.** Sobald das Gesetz verkündet ist, müssen drei Paragraphen in den Schemas ergänzt werden. Zu aktualisierende Dateien: `backend/app/services/law_mapper.py` (Mapping Vorfallstyp → Paragraph, aktuell u. a. §§ 185, 186, 187, 201a, 238, 240, 241), `backend/app/services/law_text.py` (Gesetzestexte), `backend/app/services/court_prep_tools.py` und `backend/app/services/pdf_generator.py` (Strafanzeigen-Vorlage). Neue Klassifikator-Kategorien nötig: `deepfake_sexual` → § 184k, `deepfake_reputation` → § 201b, `tracking_surveillance` → § 202e.
- **Bürger-Tipp:** Deepfakes und heimliche Intimaufnahmen sind schon heute oft über §§ 201a, 185 ff. StGB und das Kunsturhebergesetz angreifbar — Beweise (URL, Screenshot, Zeitstempel) sofort sichern, nicht auf das neue Gesetz warten.

**Quellen:**
- https://www.bmjv.de/SharedDocs/Pressemitteilungen/DE/2026/0417_Gesetz_gegen_digitale_Gewalt.html
- https://www.bmjv.de/SharedDocs/Gesetzgebungsverfahren/DE/2026_Gesetz_gegen_digitale_Gewalt.html
- https://netzpolitik.org/2026/gesetz-gegen-digitale-gewalt-diese-deepfakes-sollen-kuenftig-strafbar-sein/
- https://www.tagesschau.de/inland/innenpolitik/hubig-digitale-gewalt-102.html

### EN
- **Headline:** Three new criminal offences against digital violence planned (§§ 184k, 201b, 202e StGB-draft)
- **What changed:** The ministerial draft "Act to strengthen civil and criminal protection against digital violence" creates three new offences: **§ 184k StGB** ("violation of intimate privacy through images" — unauthorised creation and distribution of intimate imagery, whether real or AI-generated, taken in private or in public; covers pornographic deepfakes, digital voyeurism/upskirting, rape videos, "revenge porn"), **§ 201b StGB** ("violation of personality rights through deceptive content" — unauthorised making available of other deepfakes capable of seriously damaging a person's reputation; satire is excluded; mere creation is not covered) and **§ 202e StGB** ("unauthorised surveillance by means of information or communication technology" — in particular cyberstalking via GPS trackers and spyware). Paragraphs affected: new §§ 184k, 201b, 202e StGB; delimitation from existing § 201a StGB (image recordings) and § 238 StGB (stalking).
- **Why:** Image-based sexualised violence and cyberstalking were only patchily punishable under current law; the project is agreed in the coalition treaty.
- **Effective:** Open. As of 20 Aug 2026 only the ministerial draft of 17 April 2026 exists; the consultation of associations ended on 22 May 2026 and the statements were published on 3 June 2026. A cabinet decision is not documented.
- **Deadline:** Consultation deadline 22 May 2026 (expired). For victims the 3-month criminal-complaint deadline under § 77b StGB continues to apply for complaint-dependent offences.
- **Who's affected:** Victims of deepfakes, secret intimate recordings and GPS/spyware stalking; perpetrators; platforms.
- **How:** Impact on SafeVoice court-prep is **high but not yet binding.** Once the act is promulgated, three paragraphs must be added to the schemas. Files to update: `backend/app/services/law_mapper.py` (incident type → paragraph mapping, currently incl. §§ 185, 186, 187, 201a, 238, 240, 241), `backend/app/services/law_text.py` (statutory texts), `backend/app/services/court_prep_tools.py` and `backend/app/services/pdf_generator.py` (criminal-complaint template). New classifier categories needed: `deepfake_sexual` → § 184k, `deepfake_reputation` → § 201b, `tracking_surveillance` → § 202e.
- **Citizen tip:** Deepfakes and secret intimate recordings can often already be attacked today via §§ 201a, 185 ff. StGB and the Art Copyright Act — secure evidence (URL, screenshot, timestamp) immediately, do not wait for the new law.

---

## Fund 2 — Neue zivilrechtliche Durchsetzungsinstrumente: Auskunft, Beweissicherung, Accountsperre (GgdG-E)

- **Was ändert sich:** Der Entwurf enthält ein eigenständiges „Gesetz gegen digitale Gewalt“ (GgdG-E) mit vier Instrumenten unter Richtervorbehalt: (1) **Auskunftsanspruch** über die Identität von Rechtsverletzern gegen Plattformen und Internetzugangsanbieter (auch Nutzungsdaten), (2) **gerichtliche Anordnung zur Beweissicherung**, (3) **zeitweilige Accountsperre** bei schwerwiegenden Rechtsverletzungen und Wiederholungsgefahr, (4) **Pflicht zur Benennung eines inländischen Zustellungsbevollmächtigten** für Betreiber sozialer Netzwerke mit Sitz außerhalb der EU; bei Sitz in einem anderen EU-Mitgliedstaat kann ein Gericht dies im Einzelfall anordnen.
- **Betroffener Paragraph:** §§ 2 und 4 GgdG-E (Auskunft über Daten, Sperrung von Nutzerkonten); ergänzt die bisherige Praxis nach § 21 Abs. 2 TDDDG/DSA statt NetzDG-Meldewegen.
- **Warum:** Betroffene scheitern bislang an der Anonymität der Täter und an der Zustellung an ausländische Plattformen.
- **Inkrafttreten:** offen (Referentenentwurf-Stadium, 17.04.2026).
- **Frist:** keine Bürgerfrist; Verbändefrist 22.05.2026 abgelaufen.
- **Wer ist betroffen:** Betroffene digitaler Gewalt, soziale Netzwerke, Internetzugangsanbieter, Zivilgerichte.
- **Impact auf SafeVoice Court-Prep:** **mittel.** Der Court-Prep-Agent gibt heute primär Strafanzeigen aus. Künftig sollte er einen zweiten Pfad „zivilrechtlicher Antrag“ anbieten (Auskunft + Accountsperre). Kritikpunkte der Verbände (djb: Accountsperre soll auch private Nachrichten umfassen; BRAK: viele offene Fragen) zeigen, dass die Ausgestaltung noch wackelt — **noch nicht implementieren, nur vormerken.**
- **Bürger-Tipp:** Wer den Täter nicht kennt: Screenshots mit Profil-URL und Nutzernamen sichern — genau diese Angaben braucht ein späteres Auskunftsverfahren.

**Quellen:**
- https://www.bmjv.de/SharedDocs/Gesetzgebungsverfahren/DE/2026_Gesetz_gegen_digitale_Gewalt.html
- https://www.djb.de/presse/stellungnahmen/detail/st26-13
- https://www.brak.de/newsroom/newsletter/nachrichten-aus-berlin/2026/ausgabe-11-2026-v-2752026/gute-ziele-aber-viele-offene-fragen-brak-kritisiert-gesetzentwurf-gegen-digitale-gewalt/
- https://www.taylorwessing.com/de/insights-and-events/insights/2026/04/german-act-against-digital-violence-new-obligations-for-online-service-providers

### EN
- **Headline:** New civil enforcement tools: disclosure, evidence preservation, temporary account block (GgdG draft)
- **What changed:** The draft contains a stand-alone "Act against Digital Violence" (GgdG draft) with four instruments subject to judicial approval: (1) a **right to disclosure** of the identity of infringers against platforms and internet access providers (including usage data), (2) a **court order to preserve evidence**, (3) a **temporary account block** in cases of serious infringements and risk of repetition, (4) an **obligation to appoint a domestic agent for service** for operators of social networks based outside the EU; where the seat is in another EU member state a court may order this in an individual case. Paragraphs affected: §§ 2 and 4 GgdG draft (disclosure of data, blocking of user accounts); it supplements current practice under § 21(2) TDDDG/DSA rather than NetzDG reporting channels.
- **Why:** Until now victims fail because of perpetrator anonymity and because of service of documents on foreign platforms.
- **Effective:** Open (ministerial draft stage, 17 April 2026).
- **Deadline:** No deadline for citizens; the associations' deadline of 22 May 2026 has expired.
- **Who's affected:** Victims of digital violence, social networks, internet access providers, civil courts.
- **How:** Impact on SafeVoice court-prep is **medium.** Today the court-prep agent primarily outputs criminal complaints. In future it should offer a second path, "civil application" (disclosure + account block). Criticism from associations (djb: the account block should also cover private messages; BRAK: many open questions) shows the design is still unstable — **do not implement yet, just flag it.**
- **Citizen tip:** If you do not know the perpetrator: save screenshots including the profile URL and username — those are exactly the details a later disclosure procedure needs.

---

## Fund 3 — Bundestag: Umsetzung der EU-Richtlinie gegen Gewalt an Frauen / digitale Gewalt (Drucksache 21/7054)

- **Was ändert sich:** Eine parlamentarische Anfrage/Drucksache (21/7054) prüft, ob der Referentenentwurf die EU-Richtlinie zur Bekämpfung von Gewalt gegen Frauen und häuslicher Gewalt vollständig umsetzt; parallel debattierte der Bundestag in Kalenderwoche 13/2026 über die Strafbarkeit bildbasierter sexualisierter Gewalt. Ergebnis: Nachschärfungen am Entwurf sind wahrscheinlich, insbesondere bei der Erheblichkeitsschwelle und bei kurzzeitiger Überwachung.
- **Betroffener Paragraph:** §§ 184k, 202e StGB-E, mittelbar § 238 StGB (Erheblichkeitsschwelle „nicht unerhebliche Beeinträchtigung der Lebensgestaltung“) und das Gewaltschutzgesetz.
- **Warum:** Die EU-Richtlinie verlangt Mindeststandards für Cyberstalking, Cyber-Harassment und nicht-einvernehmliches Teilen intimer Bilder.
- **Inkrafttreten:** offen; die Richtlinien-Umsetzungsfrist läuft unabhängig vom nationalen Verfahren.
- **Frist:** keine Bürgerfrist.
- **Wer ist betroffen:** vor allem Frauen, Mädchen und queere Personen, Journalistinnen, Politikerinnen, Aktivistinnen (djb: geschlechtsspezifische Dimension wird im Entwurf zu wenig anerkannt).
- **Impact auf SafeVoice Court-Prep:** **niedrig heute, Beobachtung.** Falls die Erheblichkeitsschwelle des § 238 StGB auf digitale Formen übertragen oder das Gewaltschutzgesetz erweitert wird, muss die Nachstellungs-Logik in `backend/app/services/law_mapper.py` (§ 238) und der Begründungstext im Court-Prep-Output angepasst werden.
- **Bürger-Tipp:** Bei Stalking zählt das Muster: alle Vorfälle chronologisch mit Datum protokollieren — genau darauf stützt § 238 StGB die „nicht unerhebliche Beeinträchtigung der Lebensgestaltung“.

**Quellen:**
- https://dserver.bundestag.de/btd/21/070/2107054.pdf
- https://www.bundestag.de/presse/hib/kurzmeldungen-1194878
- https://www.bundestag.de/dokumente/textarchiv/2026/kw13-de-strafgesetzbuch-1157670
- https://hateaid.org/wp-content/uploads/2026/04/hateaid-pressemitteilung-gesetz-gegen-digitale-gewalt.pdf

### EN
- **Headline:** Bundestag: implementation of the EU directive against violence towards women / digital violence (printed paper 21/7054)
- **What changed:** A parliamentary question/printed paper (21/7054) examines whether the ministerial draft fully implements the EU directive on combating violence against women and domestic violence; in parallel the Bundestag debated the criminal liability of image-based sexualised violence in calendar week 13/2026. Result: tightening of the draft is likely, in particular regarding the materiality threshold and short-term surveillance. Paragraphs affected: §§ 184k, 202e StGB draft, indirectly § 238 StGB (materiality threshold "not insignificant impairment of the conduct of life") and the Protection against Violence Act.
- **Why:** The EU directive requires minimum standards for cyberstalking, cyber harassment and non-consensual sharing of intimate images.
- **Effective:** Open; the directive's transposition deadline runs independently of the national procedure.
- **Deadline:** No deadline for citizens.
- **Who's affected:** Above all women, girls and queer persons, female journalists, politicians and activists (djb: the gender-specific dimension is insufficiently recognised in the draft).
- **How:** Impact on SafeVoice court-prep is **low today, monitoring only.** If the materiality threshold of § 238 StGB is transferred to digital forms or the Protection against Violence Act is extended, the stalking logic in `backend/app/services/law_mapper.py` (§ 238) and the reasoning text in the court-prep output must be adapted.
- **Citizen tip:** With stalking the pattern is what counts: log every incident chronologically with its date — that is exactly what § 238 StGB bases the "not insignificant impairment of the conduct of life" on.

---

## Keine Änderungen festgestellt bei

- §§ 185, 186, 187 StGB (Beleidigung, üble Nachrede, Verleumdung) — Wortlaut unverändert.
- § 241 StGB (Bedrohung), § 240 StGB (Nötigung) — unverändert.
- §§ 303a, 303b StGB (Datenveränderung, Computersabotage) — unverändert.
- NetzDG — weiterhin durch den DSA überlagert; keine neuen BNetzA-Durchsetzungsregeln in diesem Lauf gefunden.

**Empfehlung an das Team:** Schema jetzt **nicht** ändern. Stattdessen Feature-Flag / Platzhalter für §§ 184k, 201b, 202e vorbereiten und den Kabinettsbeschluss abwarten.
