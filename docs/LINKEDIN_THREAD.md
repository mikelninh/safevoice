# LinkedIn Thread — SafeVoice (5 Posts)

*Zielgruppe: Civic-Tech / NGO / Policy, deutschsprachig. April 2026.*

---

## Post 1 — Hook: Problem + politischer Moment

Ein Deepfake von Ricarda Lang. Massenhafte sexualisierte Bedrohungen gegen Politikerinnen. KI-generierte Beleidigungen, die sich in Stunden viral verbreiten.

Digitale Gewalt skaliert schneller als jede Beratungsstelle der Welt skalieren kann.

Das ist kein technisches Problem. Es ist ein Kapazitätsproblem: Wer ein Opfer wirklich unterstützt, braucht Zeit — für Gespräche, für Einschätzungen, für juristische Begleitung. Diese Zeit geht verloren, bevor ein einziges Dokument entstanden ist.

Die Beweise verfallen. Inhalte werden gelöscht. Plattformen reagieren langsam. Und in der Zwischenzeit sitzt das Opfer allein mit dem Bildschirm.

Der politische Moment, das zu ändern, ist jetzt — nicht in Q3, wenn der nächste Nachrichtenzyklus das Thema wieder verdrängt hat.

Ich baue SafeVoice: ein Tool, das diesen Dokumentationsstau aufbricht. In den nächsten Tagen erkläre ich wie — und vor allem warum ich Feedback von Menschen brauche, die täglich damit arbeiten.

#DigitaleGewalt #CivicTech #SafeVoice

---

## Post 2 — The Gap: Wo die Zeit wirklich verloren geht

Ich habe mit Beratungsstellen gesprochen. Der Prozess sieht oft so aus:

Opfer schickt E-Mail mit 12 Screenshots. Mitarbeiterin öffnet jedes Bild manuell, tippt die Inhalte ab. Dann: welcher Paragraph greift hier — § 185, § 241, NetzDG? Das erfordert juristisches Wissen, das nicht jede Fallbearbeiterin mitbringt. Dann: Beweis sichern. URL archivieren. Datum dokumentieren. PDF erstellen. Das alles für einen einzigen Fall.

Ergebnis: ~90 Minuten operative Arbeit, bevor überhaupt rechtlich beraten wird.

Das Problem liegt nicht in der Beratungskompetenz — die ist unersetzlich. Das Problem liegt in den repetitiven Dokumentationsschritten davor. Schritte, die keine juristische Einschätzung erfordern, aber trotzdem qualifizierte Zeit fressen.

Wenn eine Beratungsstelle 500 Fälle im Jahr bearbeitet, verschwinden schätzungsweise 700 Stunden in genau dieser operativen Schicht. Das entspricht rund 4 Monaten Vollzeit-Praktikum — nur für Tipparbeit.

Diese 700 Stunden könnten in Gespräche investiert werden.

#DigitaleGewalt #Beratungsstellen #NGO

---

## Post 3 — The Tech: Wie SafeVoice das löst

SafeVoice macht drei Dinge, die einzeln nichts Besonderes sind — aber zusammen einen Unterschied machen.

**1. KI-Klassifizierung mit strukturierter Ausgabe.**
Ein LLM (GPT-4o-mini) klassifiziert den eingereichten Text und gibt nicht einfach Freitext zurück, sondern ein strukturiertes Ergebnis: Schweregrad, zutreffende StGB-Paragraphen (12 abgedeckt, von § 185 Beleidigung bis § 241 Bedrohung), Begründung, Schwere auf einer 1-5 Skala. Das ist nicht "KI schreibt einen Absatz" — das ist eine maschinenlesbare Klassifizierung, die direkt ins Dokument fließt.

**2. SHA-256 Hash-Kette.**
Jedes Beweisstück wird beim Einreichen mit einem kryptografischen Hash versehen. Jeder folgende Hash schließt den vorherigen ein. Das Ergebnis: eine manipulationssichere Kette, die nachweist, dass kein Beweis nachträglich verändert wurde. Relevanter als es klingt, wenn Inhalte gelöscht und Screenshots angezweifelt werden.

**3. Archive.org-Backup bei jedem URL-Submit.**
Bevor eine URL von einer Plattform gelöscht wird, sichert SafeVoice sie automatisch via Wayback Machine. Beweis bleibt auch nach Löschung bestehen.

Das Ergebnis: aus 12 eingereichten Screenshots wird in ~3 Minuten ein gerichtsfähiges PDF mit Chain-of-Custody-Anhang.

#StGB #CivicTech #LegalTech

---

## Post 4 — Nutzen: Was das in der Praxis bedeutet

Zahlen zuerst, weil ich Zahlen für ehrlicher halte als Versprechen.

Zeitaufwand ohne SafeVoice: ~90 Min/Fall (manuelle Dokumentation, Paragraphenzuordnung, PDF-Erstellung).
Zeitaufwand mit SafeVoice: ~5 Min/Fall (CSV-Upload oder manueller Input, Klassifizierung läuft, PDF wird generiert).
Ersparnis: ~85 Minuten pro Fall.

Bei 500 Fällen/Jahr: **700 Stunden. Das sind 4 Monate Vollzeit-Arbeitskraft — zurückgegeben an echte Beratungsarbeit.**

Was das nicht ist: SafeVoice ersetzt keine juristische Einschätzung. Jede KI-Klassifizierung wird von Mitarbeitenden reviewt, bevor etwas eingereicht wird. Das Tool entscheidet nicht — es bereitet vor.

Was das ist: eine Infrastruktur, die Beratungsstellen skalierbar macht, ohne dass mehr Stellen finanziert werden müssen. Gerade jetzt, wo digitale Gewalt zunimmt und Budgets nicht mitwachsen, könnte das relevant sein.

Aktueller Stand: 485 Tests, multi-tenant-fähig (mehrere Organisationen auf einer Instanz), Bulk-Import für Massenfälle, DSGVO-Compliance-Draft.

Für 1 NGO oder 10 — die Infrastruktur steht.

#CivicTech #NGO #DigitaleGewalt

---

## Post 5 — Call: Ich suche Feedback, kein Publikum

Ich baue SafeVoice nicht, um ein Startup zu gründen. Ich baue es, weil die Infrastruktur fehlt — und weil ich nach dem Besuch im War Remnants Museum in HCMC verstanden habe, dass Werkzeuge gegen Gewalt gebaut werden müssen, während das Fenster offen ist.

Was ich jetzt brauche, ist kein Applaus. Ich brauche drei Typen von Gesprächspartnerinnen:

**NGOs und Beratungsstellen** — passt der beschriebene Dokumentationsprozess zu eurem Alltag? Was stimmt nicht? Was fehlt?

**Juristinnen (StGB / Strafrecht)** — welche Klassifizierungsfehler wären in der Praxis gefährlich? Wo braucht das Modell Kalibrierung?

**Datenschutzexpertinnen** — AVV-Template und DPIA-Framework sind als Draft fertig. Wäre jemand bereit, kurz drüber zu schauen?

Ich frage nicht nach Zeit, Geld oder Ressourcen. Ich frage nach: "das stimmt nicht, weil..." oder "das brauchst du noch, weil..."

Wer sich angesprochen fühlt: DM oder Kommentar. Alles andere läuft über einen 30-Minuten-Call, den ich terminlich flexibel halten kann.

#DigitaleGewalt #SafeVoice #Feedback

---

*Zeichen pro Post (ohne Hashtags):*
*Post 1: ~1.020 | Post 2: ~1.090 | Post 3: ~1.190 | Post 4: ~1.090 | Post 5: ~1.100*
