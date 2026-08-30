# Abuse-Safety Digest — 2026-08-30

**Status:** Wachsamkeitslauf. 1 wesentliche Gesetzesentwicklung (Gesetz gegen digitale Gewalt) + 1 Parallelinitiative (§ 184k Bündnis 90/Die Grünen) gefunden. Keine der Änderungen ist bereits in Kraft getreten.

---

## Fund 1 — Gesetz gegen digitale Gewalt (GgdG) schreitet voran

- **Änderung:** Das BMJV (Justizministerin Hubig, SPD) hat den Referentenentwurf *„Entwurf eines Gesetzes zur Stärkung des zivilrechtlichen und strafrechtlichen Schutzes vor digitaler Gewalt“* fertiggestellt (11 Paragrafen). Er schafft drei neue Straftatbestände und eine zivilrechtliche Säule.
  - *Strafrecht:* (1) Das Herstellen **und** Verbreiten pornografischer Deepfakes wird ausdrücklich strafbar (an § 201a StGB angelehnt, bis zu 2 Jahre Haft oder Geldstrafe). (2) Auch nicht-sexualisierte, Persönlichkeitsrechte verletzende Deepfakes werden beim Verbreiten erfasst. (3) Die heimliche digitale Überwachung (z. B. GPS-Tracker beim Partner/Ex-Partner) wird strafbar (Erweiterung von § 238 StGB Nachstellung).
  - *Zivilrecht (Kernstück):* Neues gerichtliches **Auskunftsverfahren** beim Landgericht, um anonyme Täter zu enttarnen. Gerichte können Beweissicherung bei Plattformen anordnen und in schweren Fällen **Accountsperren** verhängen (Richtervorbehalt). Internetzugangsanbieter sollen IP-Adressen für 3 Monate „vorsorglich“ speichern (Wiederbelebung der Vorratsdatenspeicherung). Ein eigenes Verbandsantragsrecht wurde gestrichen.
- **Betroffener Paragraph:** § 201a StGB, § 238 StGB, § 184k StGB (parallele Reform), NetzDG § 3 (Plattformpflichten).
- **Inkrafttreten:** Noch nicht in Kraft. Stand: Referentenentwurf abgeschlossen; nun Ressortabstimmung, dann Bundeskabinett, Bundestag, Bundesrat. Realistisch frühestens 2027.
- **Auswirkung auf SafeVoice Gerichtsvorbereitung (Schema-Update nötig, sobald in Kraft):**
  - `backend/app/data/mock_data.py` → `LAW_201A` (§ 201a): Umfang auf KI-erzeugte/gefälschte intime Bilder ausweiten; ggf. neuen `LAW_184K`-Eintrag ergänzen.
  - `LAW_238` (§ 238 Nachstellung): Tatvariante „heimliche digitale Überwachung (GPS-Tracker)“ ergänzen.
  - `NETZ_DG` (NetzDG § 3): Querverweis auf das neue Auskunftsverfahren und Accountsperren ergänzen.
  - `backend/app/services/court_prep_tools.py` / `evals/agent_court_prep.json`: neuen Prozess „gerichtliches Auskunftsverfahren“ (Enttarnung anonymer Täter) als Tool/Case ergänzen, sobald das Gesetz gilt.
- **Quelle:** https://www.lto.de/recht/hintergruende/h/gesetzentwurf-hubig-digitale-gewalt-account-sperren-ip-vorratsdatenspeicherung · https://www.tagesschau.de/inland/innenpolitik/hubig-digitale-gewalt-102.html · https://www.bmjv.de/SharedDocs/Pressemitteilungen/DE/2026/0417_Gesetz_gegen_digitale_Gewalt.html

### EN
- **Headline:** Germany's "Digital Violence" bill advances — new deepfake & GPS-tracker crimes, court identity-disclosure procedure
- **What changed:** The Federal Justice Ministry (Minister Hubig, SPD) finalized the draft "Act to strengthen civil and criminal protection against digital violence" (11 sections). It creates three new criminal offences and a civil-law pillar. Criminal: (1) creating AND sharing pornographic deepfakes expressly criminalized (under § 201a StGB, up to 2 years or a fine); (2) non-sexual deepfakes violating personality rights covered when shared; (3) covert digital surveillance (e.g. GPS trackers on a partner/ex-partner) criminalized (expanding § 238 StGB stalking). Civil: a new court information procedure at the regional court to unmask anonymous perpetrators; courts can order evidence preservation at platforms and, in severe cases, account suspensions (judicial warrant); internet access providers must retain IP addresses for 3 months (reviving data retention). Association standing was dropped.
- **Why:** Closes gaps where AI-generated sexual fakes, doxing and anonymous abuse currently escape prosecution; gives victims a low-cost route to identify anonymous attackers.
- **Effective:** Not yet in force. Draft completed; next: inter-ministerial coordination, then Cabinet, Bundestag, Bundesrat. Realistically 2027 at earliest.
- **Deadline:** None yet — monitor the Bundestag for the government bill's formal introduction.
- **Who's affected:** Victims of deepfakes, doxing, cyberstalking and anonymous online abuse; platforms and access providers.
- **How:** Once enacted, SafeVoice must extend its paragraph register — broaden LAW_201A (§ 201a) to AI-generated intimate images and add a § 184k entry; add covert digital surveillance to LAW_238 (§ 238); cross-reference the new disclosure procedure and account-suspension power in NETZ_DG (NetzDG § 3); and add a "judicial information procedure" tool/case to court_prep_tools.py / evals/agent_court_prep.json.
- **Citizen tip:** If you are targeted by a deepfake or anonymous abuse, document everything now and save URLs — the future law will let a court order the platform to reveal the attacker's identity even behind a fake profile.

---

## Fund 2 — Grüne fordern Neuausrichtung von § 184k StGB (parallele Initiative)

- **Änderung:** Die Fraktion Bündnis 90/Die Grünen brachte am 26.03.2026 einen eigenen Gesetzentwurf (BT-Drs 21/4949) ein, der § 184k StGB neu fassen will zu *„Verletzung der sexuellen Selbstbestimmung durch Bildaufnahmen“*. Damit soll der Schutz über den Intimbereich (z. B. Upskirting) hinaus erweitert werden auf heimliche sexualbezogene Aufnahmen im öffentlichen Raum und KI-manipulierte Bilder. Strafe: bis zu 2 Jahre, in besonders schweren Fällen 3 Monate bis 3 Jahre; Antragsdelikt mit Ausnahme bei besonderem öffentlichem Interesse.
- **Betroffener Paragraph:** § 184k StGB (Schnittstelle zu § 201a).
- **Inkrafttreten:** Noch nicht in Kraft; im Bundestag debattiert (26.03.2026). Die Regierung verweist auf das eigene GgdG.
- **Auswirkung auf SafeVoice Gerichtsvorbereitung:** Paralleler Vorschlag zur GgdG-Reform. SafeVoice sollte § 184k im Paragrafenregister verfolgen (aktuell nur § 201a als `LAW_201A` vorhanden). Bei Übernahme einer der beiden Reformen: `LAW_201A` bzw. einen neuen `LAW_184K`-Eintrag entsprechend anpassen.
- **Quelle:** https://www.bundestag.de/dokumente/textarchiv/2026/kw13-de-strafgesetzbuch-1157670

### EN
- **Headline:** Greens table parallel § 184k StGB reform (image-based sexual violence)
- **What changed:** The Greens introduced their own bill (BT-Drs 21/4949) on 26.03.2026 to rewrite § 184k StGB as "violation of sexual self-determination through image recordings," broadening protection beyond the intimate sphere (e.g. upskirting) to covert sexual recordings in public and AI-manipulated images. Penalty: up to 2 years, 3 months–3 years in aggravated cases; complaint offence with exception for special public interest.
- **Why:** Competing proposal to the government's GgdG; aims to close image-based sexual-violence gaps the existing § 184k does not fully cover.
- **Effective:** Not in force; debated in the Bundestag on 26.03.2026; the government points to its own GgdG instead.
- **Deadline:** None; track which version (GgdG or Greens) is eventually enacted.
- **Who's affected:** Victims of image-based sexual violence; overlaps with the GgdG § 201a reform.
- **How:** SafeVoice should monitor § 184k in its paragraph register (currently only § 201a exists as LAW_201A). On enactment of either reform, align LAW_201A / a new LAW_184K entry accordingly.
- **Citizen tip:** Both drafts target the same harm — save evidence of any non-consensual or faked sexual image now; whichever law passes, a Strafanzeige will be supportable.

---

## Monitoring-Hinweis (NetzDG / BNetzA)
In diesem Lauf wurde **keine spezifische 2026-Textänderung von NetzDG oder BNetzA-Regeln** gefunden. Die plattformbezogenen Elemente des GgdG (Auskunftsverfahren, Accountsperren) sind eigenständige zivilrechtliche Maßnahmen, keine Änderung des NetzDG-Wortlauts. BNetzA (Telekom-Regulierung) ist vom GgdG nicht direkt betroffen; die 3-Monats-IP-Speicherung trifft Internetzugangsanbieter.

### EN
- **Headline:** No 2026 change to NetzDG text or BNetzA rules detected this run
- **What changed:** None. The GgdG's platform-accountability elements are separate civil-law measures, not an amendment to the NetzDG wording; BNetzA telecom regulation is not directly affected (the 3-month IP storage hits internet access providers, not BNetzA rules).
- **Why:** Keeps scope accurate — only flag real changes.
- **Effective:** n/a
- **Deadline:** Continue monitoring.
- **Who's affected:** SafeVoice's NetzDG § 3 mapping unchanged for now.
- **How:** No schema update required for NETZ_DG this run; revisit if GgdG passes.
- **Citizen tip:** Your NetzDG takedown rights (24h/7-day removal) are unchanged.
