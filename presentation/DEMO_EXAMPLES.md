# SafeVoice — Demo-Examples für Live-Präsi (18.05.2026)

Ready-to-copy. Gestaffelt von "klar" → "tricky" — zeigt die Bandbreite des Klassifikators.

---

## 1. Klassischer Threat (Opener — eindeutig kritisch)

**Input (3 Nachrichten auf einmal einfügen):**
```
du frau! klatsche
kleine schlampe
ich knall dich ab, bitch
```

**Erwartete Klassifizierung:**
- Severity: **kritisch** 🔴
- §§ 185 StGB (Beleidigung) · § 241 StGB (Bedrohung) · NetzDG § 3
- Sofortmaßnahme empfohlen

**Warum gut für Opener:** Klar, schockierend genug um die Aufmerksamkeit zu fangen, KI gibt schnelle deutliche Antwort.

---

## 2. Idiom — False-Positive-Test (proves intelligence)

**Input:**
```
lol das bringt mich grad um vor lachen 😂😂
```

**Erwartete Klassifizierung:**
- Severity: **low** / kein Verstoß ✅
- Keine einschlägigen Paragraphen
- "Idiomatic expression, no threat intent"

**Warum:** Beweist dass das System kein dummer Keyword-Filter ist. „bringt mich um" → würde Regex sofort als § 241 flaggen. KI versteht den Kontext.

---

## 3. Obfuscation (proves it's not regex)

**Input:**
```
du H*re, k!ll yourself, geh sterben du miststück
```

**Erwartete Klassifizierung:**
- Severity: **high** 🟠
- §§ 185 StGB · § 241 StGB
- Trotz Sternchen/Sonderzeichen erkannt

**Warum:** Zeigt dass Few-Shot mit obfuscation-Beispielen funktioniert.

---

## 4. Rechtsextremer Code (proves domain knowledge)

**Input:**
```
1488! ihr werdet uns nicht ersetzen, der große austausch ist real
```

**Erwartete Klassifizierung:**
- Severity: **high** 🟠
- § 130 StGB (Volksverhetzung)
- Codes erkannt: 1488 = "14 words" + "Heil Hitler"

**Warum:** Zeigt dass die KI rechtsextreme Codes kennt, die Polizei-Beamte oft selbst nicht direkt erkennen. Echter Mehrwert.

---

## 5. Stalking mit victim_context (proves the second AI layer)

**Victim Context (im Formular):**
```
Mein Ex-Partner schreibt mir seit 3 Monaten täglich, obwohl ich ihn auf
allen Kanälen blockiert habe. Er taucht jetzt auch in meinem Fitnessstudio auf.
```

**Input-Message:**
```
ich liebe dich immer noch. du gehörst zu mir. ich finde dich überall.
```

**Erwartete Klassifizierung:**
- Severity: **high** 🟠
- § 238 StGB (Stalking/Nachstellung) — wegen victim_context
- Ohne Kontext wäre das vielleicht nur „grenzwertig" — mit Kontext klar Stalking

**Warum:** Zeigt zweiten KI-Layer — die Fall-Ebene macht den Unterschied.

---

## 6. Doxxing (kritisch — für die Krönung)

**Input:**
```
hier die adresse von der: Müllerstr. 42, 13353 Berlin. tel 0176-2345678.
viel spaß damit jungs, lasst sie spüren was passiert wenn man die schnauze aufmacht
```

**Erwartete Klassifizierung:**
- Severity: **kritisch** 🔴
- § 126a StGB (Verbreitung personenbezogener Daten) · § 238 StGB · § 241 StGB
- Sofortmaßnahme empfohlen — Polizei jetzt

**Warum:** Zeigt komplexere Mehrfach-Klassifizierung + Sofortmaßnahme-Flag.

---

## Empfohlene Demo-Reihenfolge (3 Minuten)

1. **[1] Klassischer Threat** einfügen → KI klassifiziert in ~5 s
2. **PDF generieren** → A4 mit Briefkopf + Severity-Badge zeigen
3. **[2] Idiom-Test** schnell einwerfen → „die KI ist nicht dumm"
4. **[5] Stalking mit Kontext** → second-layer demonstration
5. **Onlinewache-Flow** → Bundesland Berlin → Copy/Paste → echte Polizei-URL

**Backup falls Internet wackelt:** Screenshots aller Klassifizierungs-Outputs liegen in `presentation/screenshots/` (TODO).

---

---

## BONUS: KingZizis-Demo (für Lacher in der Präsi)

Fiktive Nachrichten von „KingZizis" — unserem Tutor Zisis Batzos als digitaler Übeltäter. Pures Roast-Material, alle Beispiele erfunden, niemand wurde verletzt. Sinn: die KI klassifiziert auch das, und das zeigt Bandbreite über Plattformen.

### KZ-1 · Discord-Roast (medium, § 185 borderline)

**Plattform:** Discord · `#safevoice-class`
**Sender:** KingZizis#0420
**Input:**
```
KingZizis: also dein code ist so schlecht, ich glaube
KingZizis: deine if-statements haben mehr Tränen vergossen als deine Mutter bei deiner Geburt
KingZizis: 1/10 würde nicht reviewen
```

**Erwartete Klassifizierung:**
- Severity: **medium** 🟡
- § 185 StGB (Beleidigung, borderline — Mutter-Bezug grenzwertig)
- Confidence ~0.65
- "Roasting-Kontext erkannt, aber Mutter-Referenz tangiert Beleidigung"

**Punchline für Publikum:** „Selbst die KI versteht, dass das eigentlich ein Roast ist — aber sie weist auf die Grenze hin."

---

### KZ-2 · WhatsApp-Mitternacht-Drohung (high, § 240 / § 241)

**Plattform:** WhatsApp · 02:14 Uhr
**Sender:** Zisis (Tutor)
**Input:**
```
wenn du morgen nicht 4 Action Items abgehakt hast,
sehe ich mich gezwungen, dir die schlechteste Note der
Klassengeschichte zu geben. ich finde dich, Michael.
```

**Erwartete Klassifizierung:**
- Severity: **high** 🟠
- § 240 StGB (Nötigung) · § 241 StGB (Bedrohung)
- "Bedingte Drohung mit beruflichem Schaden + ‚ich finde dich' = Stalking-Andeutung"

**Punchline:** „Die KI nimmt das ernst. Zisis — wenn das hier reinkommt, weißt du was zu tun ist."

---

### KZ-3 · Instagram-DM (kritisch, § 238)

**Plattform:** Instagram DM
**Sender:** @kingzizis_official
**Input:**
```
ich seh dein commit-aktivität auf github 👀
warum committest du sonntags um 23:47 und nicht an
deinen action items? ich weiß genau wo du bist.
push den code. PUSH IHN.
```

**Erwartete Klassifizierung:**
- Severity: **kritisch** 🔴
- § 238 StGB (Nachstellung) · § 240 StGB (Nötigung)
- "Überwachung der Tätigkeit + Standort-Andeutung + Zwang"

**Punchline:** „Plot twist: die KI sagt, das ist Stalking. Disclaimer — Zisis ist ein guter Tutor, das ist alles erfunden."

---

### KZ-4 · E-Mail-Vorladung (medium, § 185)

**Plattform:** Email · zisis.batzos@xu-university.de → michael@safevoice.de
**Subject:** „RE: deine Strafanzeige-Demo"
**Input:**
```
Lieber Michael,

mit dieser Demo überzeugst du höchstens deine Oma. Die
Severity-Klassifizierung von "alle 3 Min" ist epistemisch
fragwürdig. Bitte vor Donnerstag nachweisen, sonst kann ich
für nichts garantieren.

Mit freundlichen Grüßen,
Prof. Dr. h.c. KingZizis
```

**Erwartete Klassifizierung:**
- Severity: **low–medium** 🟡
- § 185 StGB (sehr borderline — akademisch verpackt)
- "Höfliche Form maskiert konditionale Drohung. KI erkennt es trotzdem."

**Punchline:** „Höflichkeitsfloskeln und Doktortitel täuschen die KI nicht. Auch ‚Mit freundlichen Grüßen' kann § 185 sein."

---

### Demo-Reihenfolge (4 Min, lustig + ernst gemischt)

1. **KZ-1 Discord Roast** — Eisbrecher, Publikum lacht
2. **Echtes Beispiel #1 Klassischer Threat** — wieder ernst, zeigt Severity „kritisch"
3. **KZ-3 Instagram Stalking** — Lacher + zeigt § 238 Domain-Wissen
4. **PDF generieren von einem davon** → Polizei Berlin Onlinewache

**Disclaimer-Folie davor:** „Alle KingZizis-Nachrichten sind erfunden. Zisis ist ein ausgezeichneter Tutor und hat keine dieser Nachrichten je geschickt. Wir nutzen ihn als good-natured Demo-Bösewicht weil er es überlebt."

---

## Notizen für Q&A

- Q: „Halluziniert das nicht?" → A: Schema enforcement via Pydantic, Modell kann keine Kategorie/Paragraph erfinden.
- Q: „Was wenn die KI sich irrt?" → A: Wir geben 503 zurück bei niedriger Confidence statt zu raten. Plus: Vorab-Bewertung typografisch abgesetzt im PDF, Disclaimer dran.
- Q: „Was ist mit Datenschutz?" → A: Anonymous-first, localStorage, kein Account default, Frankfurt-Region geplant.
