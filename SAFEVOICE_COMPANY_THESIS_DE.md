# SafeVoice Company Thesis

## One-line thesis

SafeVoice wird die agentische Vertrauens- und Beweisoberflaeche fuer digitale Gewalt, ueber die Betroffene, NGOs, Schulen, Kanzleien und Meldestellen Vorfaelle strukturiert sichern, bewerten, eskalieren und exportieren koennen.

## The problem

Digitale Gewalt wird heute systematisch unterschaetzt, zu spaet dokumentiert und schlecht weiterverarbeitet.

Die typischen Brueche:

- Vorfaelle kommen ueber Screenshots, Chats, Links, Videos, Fotos, Sprachmemos.
- Betroffene wissen nicht, was rechtlich relevant ist.
- Beweise gehen verloren oder sind nicht belastbar dokumentiert.
- NGOs, Beratungsstellen und Anwaelt:innen muessen dieselben Informationen mehrfach neu strukturieren.
- Meldungen an Plattformen, Polizei oder Jugendamt sind zeitaufwendig und uneinheitlich.

Das Kernproblem ist nicht nur:

`Harassment detection`

Sondern:

`Der Weg von rohem Vorfall -> belastbarer Fallakte -> richtige Eskalation ist kaputt.`

## The wedge

SafeVoice beginnt nicht als "Safety chatbot".

Der Wedge ist:

`Evidence-to-action workflow for digital harm cases.`

Das ist stark fuer:

- NGO-/Beratungsstellen
- Opferhilfe
- Schul- und Kinderschutzkontexte
- Anwaelt:innen im Bereich digitaler Gewalt
- Meldestellen / Plattform-Trust-and-Safety-nahe Partner

Warum dieser Einstieg funktioniert:

- Die Not ist real und hoch.
- Die Dateneingaenge sind chaotisch.
- Zeitkritik und Beweisverlust machen den Workflow extrem wertvoll.
- Menschliche Review ist selbstverstaendlich, also passt agentische KI sehr gut.

## Product thesis

SafeVoice ist nicht "ein Modell, das Hass erkennt".

SafeVoice ist:

`A supervised multi-agent evidence and escalation system for digital harm.`

Die Agentenlogik:

- Intake Agent
  - nimmt Text, Screenshots, Links, Uploads, Metadaten auf
  - erkennt Quelle, Sprache, Prioritaet, Fallzuordnung
- Evidence Agent
  - erzeugt Hash-Kette
  - extrahiert Text
  - sichert Timeline und Referenzen
- Classification Agent
  - bewertet Art, Schwere, Wahrscheinlichkeiten, relevante Kategorien
- Legal / Policy Agent
  - ordnet moegliche Rechtsgrundlagen, NetzDG-/Policy-Relevanz und Eskalationspfade zu
- Report Agent
  - erzeugt strukturierte Exporte fuer Plattform, Polizei, interne Falldoku, Jugendamt oder Anwalt
- Triage Agent
  - priorisiert kritische Faelle und empfiehlt naechste Schritte
- Memory Agent
  - lernt aus freigegebenen Faellen, Eskalationsmustern und Partnerkontexten

Wichtig:

`SafeVoice entscheidet nicht final ueber Wahrheit oder Schuld. Es strukturiert, sichert und beschleunigt menschliche Fallarbeit.`

## Why now

- Digitale Gewalt nimmt zu und verteilt sich auf mehr Kanaele.
- Institutionen und Beratungsstellen sind personell ueberlastet.
- Plattform- und Rechtsprozesse sind zu langsam fuer die manuelle Aufbereitung.
- AI kann genau bei Klassifikation, Strukturierung und Reporting einen grossen Unterschied machen.
- Vertrauen entsteht hier nicht durch rohe Modellleistung, sondern durch Nachvollziehbarkeit.

## Ideal customer

### ICP 1: NGOs and victim-support organizations

- kleine bis mittlere Teams
- hohe Falllast
- wenig strukturierte Software
- Bedarf an schneller, sauberer Falldokumentation

### ICP 2: Child-safety / school / family-protection contexts

- besonders hoher Dokumentations- und Eskalationsdruck
- Jugendamt-/Schul-/Eltern-Schnittstellen

### ICP 3: Legal and partner workflows

- spezialisierte Kanzleien
- journalistische / watchdog-Partner
- Trust-and-Safety-nahe Teams

## Core value proposition

SafeVoice verkauft 4 Dinge:

1. `Evidence integrity`
- aus verstreuten Vorfaellen wird eine belastbare, zeitlich nachvollziehbare Akte

2. `Faster triage`
- Teams erkennen schneller, was akut ist und was als naechstes passieren muss

3. `Safer escalation`
- Exporte und Handlungspfade sind sauberer, konsistenter und schneller

4. `Institutional leverage`
- eine Fachkraft kann mehr Faelle vorbereiten, ohne in Chaos und Copy/Paste unterzugehen

## Moat thesis

Der Moat ist nicht das nackte Klassifikationsmodell.

Der Moat ist die Verbindung aus:

1. `Evidence moat`
- Hash-Kette, Timeline, Exportierbarkeit, strukturierte Beweissicherung

2. `Workflow moat`
- Intake -> Evidence -> Triage -> Report -> Follow-up

3. `Trust moat`
- nachvollziehbare Agentenarbeit, menschliche Review, Datenschutz, Rollen

4. `Partner moat`
- sobald NGOs / Kanzleien / Schutzstellen ihre Prozesse darauf aufbauen, wird es klebrig

5. `Case memory moat`
- Muster wiederkehrender Vorfaelle, Eskalationen und hilfreicher Report-Strukturen

## Why SafeVoice can become agentic

Digitale Gewalt ist kein einzelner API-Call.

Es ist ein wiederkehrender Agenten-Workflow:

- Vorfall kommt rein
- Material wird gesichert
- Bedeutung wird bewertet
- Dringlichkeit wird erkannt
- richtiger Export / Eskalationspfad wird vorbereitet
- Fall wird intern weiterverarbeitet

Genau diese Verkettung macht SafeVoice agentisch stark.

## Non-goals

SafeVoice soll anfangs nicht sein:

- allgemeines Moderationstool fuer jede Plattform
- autonomes strafrechtliches Bewertungssystem
- endlos breite Consumer-Safety-App fuer alle Risikoarten
- Social-network-wide trust layer ohne klaren B2B/B2NGO-Einstieg

## Company thesis in one paragraph

SafeVoice baut die agentische Fall- und Beweisoberflaeche fuer digitale Gewalt. Statt nur Content zu klassifizieren, fuehrt das Produkt von chaotischem Eingang ueber Beweissicherung, Schweregradbewertung und Rechts-/Policy-Einordnung bis zu strukturierten Exporten fuer reale Eskalationspfade. Der Moat liegt in Evidence Integrity, Workflow-Tiefe, Partner-Einbettung und Vertrauen. Die erste starke Wedge ist nicht "AI gegen Hass", sondern `evidence-to-action operations for digital harm cases`.
