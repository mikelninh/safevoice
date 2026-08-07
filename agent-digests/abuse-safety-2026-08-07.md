# Abuse-Safety Watch — 2026-08-07

Watchdog-Lauf für SafeVoice: Was ändert sich im deutschen Recht gegen digitale Gewalt — und was heißt das für die Strafanzeige, die SafeVoice erstellt?

**Status: 3 relevante Vorgänge. Noch kein geltendes Recht — alles im Gesetzgebungsverfahren.**

---

## 1. Referentenentwurf „Gesetz gegen digitale Gewalt" (BMJV)

- **Was:** Bundesjustizministerin Hubig hat am 17.04.2026 den Entwurf eines Gesetzes zur Stärkung des zivil- und strafrechtlichen Schutzes vor digitaler Gewalt vorgelegt.
- **Betroffene Paragrafen:**
  - **§ 184k StGB (neu gefasst)** — „Verletzung der Intimsphäre durch Bildaufnahmen": erfasst pornografische Deepfakes, digitalen Voyeurismus, Rache-Pornos — unabhängig davon, ob die Aufnahme echt oder KI-generiert ist und ob sie privat oder öffentlich entstand.
  - **§ 201b StGB (neu)** — „Verletzung von Persönlichkeitsrechten durch täuschende Inhalte": Zugänglichmachen rufschädigender Deepfakes (Satire ausgenommen).
  - **§ 202e StGB (neu)** — „Unbefugte Überwachung mittels Informations- oder Kommunikationstechnik": v. a. Cyberstalking per GPS-Tracker.
  - Zivilrechtlich: **Auskunftsanspruch mit Richtervorbehalt** gegen Plattformen/Zugangsanbieter, **beweissichernde Anordnungen**, **zeitweilige Accountsperre**, **Zustellungsbevollmächtigter** für Nicht-EU-Plattformen.
- **Wirksam ab:** noch nicht. Verbände-/Länderanhörung lief bis 22.05.2026; Regierungsentwurf und Bundestagsverfahren stehen aus.
- **Impact auf SafeVoice Court-Prep:** hoch, sobald verabschiedet.
  - `backend/app/services/law_mapper.py` — `GERMAN_LAW_MAP` kennt bisher nur §§ 185, 186, 241, 126a, 263, 263a, 269. Es fehlen Kategorien/Mappings für bildbasierte sexualisierte Gewalt (§ 184k), Deepfakes (§ 201b) und Stalking-Tracking (§ 202e).
  - `backend/app/data/mock_data.py` — neue `LAW_184K`, `LAW_201B`, `LAW_202E` Objekte nötig (Gesetzestext, Strafrahmen, Antragserfordernis).
  - `backend/app/services/court_prep_tools.py` — Strafantragsfristen-Tabelle (`stgb:185/186/201a/238/241`) muss um die neuen Tatbestände und deren Offizial-/Antragsdelikt-Charakter ergänzt werden.
  - **Noch nichts ändern** — erst bei Verkündung im BGBl.
- **Quellen:**
  - https://www.bmjv.de/SharedDocs/Pressemitteilungen/DE/2026/0417_Gesetz_gegen_digitale_Gewalt.html
  - https://www.bmjv.de/SharedDocs/Gesetzgebungsverfahren/DE/2026_Gesetz_gegen_digitale_Gewalt.html
  - https://www.lto.de/recht/nachrichten/n/entwurf-bmjv-verschaerfungen-stgb-strafrecht-schutz-gegen-digitale-gewalt

## 2. Kritik der Verbände — § 184k-E umstritten, § 241 StGB bleibt unverändert

- **Was:** BRAK (Stellungnahme 30/2026) hält § 184k Abs. 1 StGB-E teils für zu weitgehend und unbestimmt (Wegfall der Beschränkung auf „absichtliche oder wissentliche" Aufnahmen). Deutscher Juristinnenbund (st26-13) und Deutsches Institut für Menschenrechte begrüßen den Entwurf, sehen aber Schutzlücken; eine Anpassung des **§ 241 StGB (Bedrohung)** wird vom Ministerium ausdrücklich nicht für erforderlich gehalten.
- **Betroffene Paragrafen:** § 184k, § 241.
- **Impact auf SafeVoice:** Der § 241-Pfad im Court-Prep (Bedrohung, Offizialdelikt) bleibt stabil — keine Anpassung nötig. Der Wortlaut des künftigen § 184k kann sich im parlamentarischen Verfahren noch deutlich ändern; nicht vorab implementieren.
- **Quellen:**
  - https://www.brak.de/fileadmin/05_zur_rechtspolitik/stellungnahmen-pdf/stellungnahmen-deutschland/2026/stellungnahme-der-brak-2026-30.pdf
  - https://www.djb.de/presse/stellungnahmen/detail/st26-13
  - https://www.institut-fuer-menschenrechte.de/fileadmin/Redaktion/Publikationen/Stellungnahmen/Stellungnahme_BSt_gG_Gesetz_digitale_Gewalt_BMJV_05_2026.pdf

## 3. Bundestag: Kleine Anfrage zur EU-Richtlinien-Umsetzung (hib 581/2026)

- **Was:** Die Fraktion Die Linke fragt am 13.07.2026 (BT-Drs. 21/7054) nach dem Zeitplan für das Gesetz gegen digitale Gewalt und ob die Umsetzungsfrist der EU-Richtlinie zur Bekämpfung von Gewalt gegen Frauen (**14.06.2027**) gehalten wird. Kritik: Cyberbelästigung/**Cyberflashing** und Nudifizierungs-Apps bleiben ungeregelt.
- **Betroffene Paragrafen:** § 184k-E, § 184i, allgemein §§ 185 ff.
- **Wirksam ab:** kein unmittelbarer Rechtsakt; harter Umsetzungstermin 14.06.2027.
- **Impact auf SafeVoice:** Planungssignal — bis spätestens Juni 2027 ist mit neuen Tatbeständen zu rechnen. Court-Prep-Schema sollte so erweiterbar bleiben, dass neue StGB-Keys (`stgb:184k`, `stgb:201b`, `stgb:202e`) ohne Umbau ergänzt werden können.
- **Quellen:**
  - https://www.bundestag.de/presse/hib/kurzmeldungen-1194878
  - https://dserver.bundestag.de/btd/21/070/2107054.pdf

---

## Fazit für Betroffene

Heute gilt weiterhin das alte Recht: Beleidigung (§ 185), üble Nachrede/Verleumdung (§§ 186, 187), Bedrohung (§ 241), Nachstellung (§ 238), Bildaufnahmen (§ 201a). Eine SafeVoice-Strafanzeige ist damit weiterhin korrekt. Neu ist: Deepfake-Pornos und GPS-Stalking sollen bald eigene Straftatbestände bekommen — das Gesetz ist aber noch nicht beschlossen.

**Keine Code-Änderung in diesem Lauf. Nur Beobachtung.**
