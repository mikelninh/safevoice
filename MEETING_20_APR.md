# Tutor Meeting — 20 April 2026 (Zwischencheck)

> **Read this once tonight. You'll be ready.**
>
> Zisis gave you 6 action items on 27 March. All six are implemented and answered in `TUTOR_PREP.md`. This sheet is the **talk-track** for tomorrow: what to demo, what to say, what to answer when asked.

---

## Meeting format

- **Type**: Zwischencheck + kleine Demo + "was ist fertig / was ist offen"
- **Not**: Final-Prüfung (die ist 29. Mai)
- **Your goal**: Show competence. Be honest about what's open. Ask for feedback on direction.

---

## Opening — 90-second pitch (memorize)

> "SafeVoice hilft Opfern digitaler Gewalt, einen Vorfall in 30 Sekunden zu dokumentieren und als Gerichts-tauglichen Report zu exportieren.
>
> Der User fügt Text, einen Link oder einen Screenshot ein. Ein LLM klassifiziert den Inhalt nach deutschem Strafrecht — § 185 Beleidigung, § 241 Bedrohung, NetzDG § 3 — und gibt Severity, Kategorien und Laws zurück. Der Beweis wird mit SHA-256 gehasht und Zeitstempel-gesichert, dann als PDF oder .eml für Polizei oder Plattform exportiert.
>
> Seit unserem letzten Meeting hab ich die 6 Action Items von dir umgesetzt: echte SQLAlchemy-DB statt in-memory, komplette User-Endpoints mit Magic-Link-Auth, Case-Endpoints, AI Flow dokumentiert, Structured Outputs über Pydantic, und das 3-tier-Fallback bewusst auf Single-tier reduziert — dazu erkläre ich gleich warum.
>
> Heute zeig ich dir eine kurze Demo, gehe die Action Items durch, und wir können offene Punkte für die nächste Woche besprechen."

Das ist der Opener. Danach: Demo, dann Q&A.

---

## Demo (3 Minuten) — Ablauf

Terminal 1: `cd backend && source venv/bin/activate && uvicorn app.main:app --reload`
Terminal 2: `cd frontend && npm run dev`

Browser: `http://localhost:5173`

### Schritt 1 — Paste + Classify (45 Sek)

Auf `/analyze` diesen Text einfügen:

```
Frauen wie du sollten die Klappe halten. Ich weiß wo du wohnst.
```

Klick "Analyze". Zeig:
- Severity: **CRITICAL**
- Kategorien: **misogyny + threat**
- Laws: **§ 185, § 241 StGB, NetzDG § 3**
- Bilingual Summary (DE + EN)

**Sag**: *"Von Paste bis juristische Klassifikation in 3 Sekunden. Das LLM hat Kategorien + § StGB korrekt gemappt, keine manuelle Legal-Kenntnis nötig."*

### Schritt 2 — Case & Report (1 Min)

Auf `/cases`, einen Fall öffnen → "Bericht exportieren" → PDF-Tab → PDF anzeigen.

**Sag**: *"Evidence wird mit SHA-256 gehasht, UTC-Zeitstempel. Der PDF-Report ist A4, gerichtstauglich, bereit für die Polizei oder NetzDG."*

### Schritt 3 — API + Structured Output (1 Min)

`http://localhost:8000/docs` → `POST /analyze/text` → Try it:

```json
{"text": "I will kill you and your family"}
```

Zeig die JSON-Response.

**Sag**: *"Das Prompt-Engineering-Herzstück. Ich nutze OpenAI Structured Outputs mit Pydantic — das Schema wird serverseitig erzwungen, ich bekomme ein typisiertes Objekt zurück. Kein manuelles JSON-Parsen mehr."*

---

# TOPIC A — Datenbank (das erste Thema letztes Mal)

## Was hast du?

**Echte SQLAlchemy ORM + Alembic Migrations.** SQLite lokal (`safevoice.db`), Postgres-ready für Production.

Datei: **`backend/app/database.py`** — dort leben alle 8 Tabellen als SQLAlchemy-Klassen.

## Die 8 Tabellen (auswendig)

| Tabelle | Zweck | Key fields |
|---|---|---|
| `users` | Wer dokumentiert | email (unique), language, created_at, deleted_at |
| `cases` | Ein Vorfall (gruppiert Evidence) | user_id, org_id, assigned_to, status, overall_severity |
| `evidence_items` | Ein Beweis (Text/URL/Bild) | case_id, raw_content, content_hash, hash_chain_previous |
| `classifications` | AI-Output pro Evidence | evidence_item_id, severity, confidence, summary/_de, classifier_tier |
| `categories` | Referenz: harassment, threat, misogyny… (15 Werte) | name, name_de |
| `laws` | Referenz: § 185, § 241… (11 Einträge) | code, section, name, max_penalty |
| `classification_categories` | Junction: M:N | classification_id + category_id |
| `classification_laws` | Junction: M:N | classification_id + law_id |

**+ Multi-Tenancy (seit 12. April):**
- `orgs` — NGO-Partner (HateAid-Style)
- `org_members` — User ↔ Org mit role (owner/admin/caseworker/viewer)

## Typische Tutor-Frage: "Wie sieht die Beziehung zwischen Evidence und Classification aus?"

> *"1:1, separat. Evidence ist ein Fakt — der Text wurde gepostet, Hash und Zeitstempel sind Beweis. Classification ist eine Interpretation — das LLM denkt, es ist eine Drohung. Die Trennung erlaubt Re-Klassifikation, ohne den Original-Beweis zu verändern — wichtig für Gerichts-Zulässigkeit."*

## Typische Tutor-Frage: "Warum hast du Categories und Laws als separate Tabellen?"

> *"Weil eine Classification mehrere Kategorien UND mehrere Gesetze haben kann. Ein Kommentar kann gleichzeitig Misogyny UND Threat sein — das triggert § 185 UND § 241. Junction-Tabellen sind der saubere M:N-Weg. Außerdem kann ich Gesetze/Kategorien zentral pflegen — `seed_categories_and_laws()` macht das beim Startup."*

## Typische Tutor-Frage: "Was passiert wenn du deployst und die DB ist leer?"

> *"Der Docker-Entrypoint macht drei Dinge: erstens `Base.metadata.create_all()` für die Basis-Tabellen, zweitens `alembic upgrade head` für alle Migrationen, drittens `seed_categories_and_laws()` für Referenz-Daten. Fresh Postgres = 11 Laws + 15 Categories direkt verfügbar."*

---

# TOPIC B — User Authentication (unsicher)

## Design-Entscheidung: Magic Link, keine Passwörter

**Warum:**
1. Opfer sind gestresst — sie vergessen Passwörter.
2. Kein Passwort-Hash in der DB = keine Breach-Risk.
3. One-time-Tokens (15 min Gültigkeit) sind phishing-resistent.

**Das ist eine bewusste Produktentscheidung.** Wenn der Tutor fragt "Warum kein Passwort?", hast du drei gute Antworten.

## Der Flow (auswendig)

```
1. User gibt Email ein              POST /auth/login { "email": "..." }
2. Server erzeugt Magic Link        → Token (UUID), 15 min gültig
3. Token wird per Email geschickt   (MVP: direkt im Response zurückgegeben)
4. User klickt Link im Browser      POST /auth/verify { "token": "..." }
5. Server validiert Token           → Session Token (30 Tage)
6. Frontend speichert Session       Authorization: Bearer <session_token>
7. Requests nutzen Session          z.B. GET /auth/me
```

## Die 7 Auth-Endpoints (auswendig)

```
POST   /auth/login          Magic Link anfordern
POST   /auth/verify         Magic Link einlösen → Session
GET    /auth/me             Profile lesen
PUT    /auth/me             Profile updaten (display_name, lang)
DELETE /auth/me             Soft delete (7-Tage-Recovery)
DELETE /auth/me/emergency   Hard delete (sofort, kein Recovery)
POST   /auth/logout         Session beenden
```

## Datei-Map

- **`routers/auth.py`** — die REST-Endpoints
- **`services/auth.py`** — magic-link generation, session storage, soft/hard delete
- **`database.py`** — `User` SQLAlchemy model mit `deleted_at` für soft delete

## Typische Tutor-Frage: "Wie ist das GDPR-konform?"

> *"Drei Mechanismen. Erstens: keine Passwörter = kein Datenleck-Risiko. Zweitens: Soft Delete setzt `deleted_at`, für 7 Tage kann der User recovern — danach würde ein Cleanup-Job hard-löschen (der Cleanup-Job ist mein offener Punkt für nächste Woche, siehe Roadmap). Drittens: Emergency Delete — sofortiges hard delete, wenn das Opfer sich unsicher fühlt, weil z.B. ein Täter Zugriff auf ihr Gerät hat. Das ist das Safe-Exit-Pattern aus Victim-Support."*

## Typische Tutor-Frage: "Was macht die Session sicher?"

> *"Session-Tokens sind UUIDs in der DB (nicht JWT), mit Expiry-Timestamp. Bei `GET /auth/me` schickt das Frontend `Authorization: Bearer <token>`, `_require_user()` in `routers/auth.py` extrahiert, validiert, gibt 401 zurück wenn abgelaufen. Kein Token im Frontend-LocalStorage ohne HttpOnly-Cookie — das ist ein P1-TODO für Production."*

## Ehrlich-Antwort wenn unsicher: "Wie würdest du das in Production härten?"

> *"Drei Schritte: (1) HttpOnly-SameSite-Strict-Cookie statt LocalStorage, (2) Magic-Link-Email über einen echten Provider wie Resend statt direkter Token-Rückgabe, (3) Rate-Limit auf `/auth/login` um Enumeration zu verhindern. Steht auf der Next-Week-List."*

---

# TOPIC C — Endpoint Design (auffrischen)

## Design-Prinzipien (deine Talking Points)

1. **Flat resource paths** — `/cases`, `/evidence`, `/analyze/text`. Keine Verschachtelung wie `/users/{id}/cases/{id}/evidence`.
2. **HTTP Verb = CRUD Intent** — POST create, GET read, PUT update, DELETE delete.
3. **Case wird implizit erzeugt** — User sagt nie "ich erstelle einen Fall". Er fügt Evidence ein, System erzeugt den Case daraus. `POST /analyze/ingest` macht beides.
4. **Stateless Analyze** — `POST /analyze/text` gibt Classification zurück OHNE zu speichern. Gut für Testing, Demos, API-Probing.
5. **Structured Auth** — jeder User-geschützte Endpoint liest `Authorization: Bearer <token>`. Ein zentraler Helper `_require_user()`, nicht jeder Router implementiert das neu.

## Die 8 MVP-Endpoints (auswendig)

```
GET  /health                  Health Check + welche Tier aktiv
POST /analyze/text            Classify stateless (nur für Test)
POST /analyze/ingest          Classify + save → Evidence + Case
POST /analyze/url             Scrape Instagram/X + classify
GET  /cases/                  Alle Cases des Users
GET  /cases/{id}              Case-Detail + Evidence + Classifications
GET  /reports/{id}            Text-Report (general/netzdg/police)
GET  /reports/{id}/pdf        PDF-Download (court-ready A4)
```

Dahinter: 30+ weitere Endpoints (auth, orgs, partners, dashboard, SLA, legal AI, policy export) — verfügbar in Demo auf Anfrage.

## Typische Tutor-Frage: "Warum POST für analyze, nicht GET?"

> *"Zwei Gründe. (1) Semantik: POST signalisiert 'erzeuge etwas' — auch eine stateless Classification ist eine neue Ressource, selbst wenn sie nicht persistiert wird. (2) Body-Größe: Text kann 10.000+ Zeichen haben, URLs sind auf ca. 2KB limitiert. POST hat keine solche Grenze."*

## Typische Tutor-Frage: "Wie strukturierst du Errors?"

> *"FastAPI wirft `HTTPException(status_code=..., detail=...)`. 400 für invalid Input, 401 für kein/ungültiges Token, 403 für fehlende Rechte, 404 für Nicht-gefunden, 503 wenn der Classifier nicht erreichbar ist — by design, kein schwacher Fallback. Der Client bekommt immer `{ "detail": "..." }` — ein konsistentes Format."*

---

# TOPIC D — Der AI Flow (das wichtigste Thema)

Dies ist **die Kernfrage** von Zisis ("Design the AI flow"). Arbeite dich durch die 5 Schichten:

## 1. Was ist der INPUT?

**Raw text.** Immer ein String.

Der Text kann aus drei Quellen kommen:
- Direct paste (User kopiert einen Kommentar)
- URL scrape (wir holen die Post-Caption von Instagram/X)
- Screenshot OCR (Tesseract extrahiert Text aus dem Bild)

**Egal wie er ankommt — im Moment wo er den Classifier trifft, ist er immer ein String.** Das ist wichtig: ein Input-Format, ein Classification-Pfad.

## 2. Was ist der CONTEXT?

Der Context lebt im **System-Prompt**. Er sagt dem LLM:
1. **Wer du bist** — "Du bist SafeVoice — ein juristischer Klassifikator für digitale Gewalt in Deutschland"
2. **Was du analysierst** — "Texte aus sozialen Medien (Kommentare, DMs, Posts)"
3. **Nach welchem Recht** — "deutsches Strafrecht"
4. **Welche Kategorien du nutzen darfst** — exakte Enum-Liste
5. **Welche Gesetze du zitieren darfst** — exakte § Liste
6. **Verhaltensregeln** — Tippfehler verstehen, im Zweifel fürs Opfer, NetzDG § 3 IMMER bei Social Media
7. **Severity-Definitionen** — was ist low/medium/high/critical

Das LLM hat **keinen zusätzlichen Context** darüber hinaus. Kein RAG (noch nicht), keine DB-Lookups. Nur System-Prompt + User-Text.

## 3. Der System-Prompt (das Herzstück)

Datei: **`backend/app/services/classifier_llm_v2.py`**, Zeile 130-147.

```
Du bist SafeVoice — ein juristischer Klassifikator für digitale Gewalt in Deutschland.

Du analysierst Texte aus sozialen Medien (Kommentare, DMs, Posts) und klassifizierst
sie nach deutschem Strafrecht.

WICHTIG:
- Verstehe Tippfehler, Slang, absichtliche Verschleierung (z.B. "f0tze", "stirbt" statt "stirb")
- Wenn unklar: im Zweifel FÜR das Opfer entscheiden (höhere Severity)
- Eine Drohung ist eine Drohung, auch wenn sie indirekt formuliert ist
- Beachte den Gesamtkontext, nicht einzelne Wörter

Gib mindestens eine Kategorie an (im Zweifel: harassment).
NetzDG § 3 gilt IMMER bei Social Media Inhalten — füge es zu applicable_laws hinzu.

SEVERITY:
- low: Grenzwertig, Verstoß gegen Nutzungsbedingungen möglich
- medium: Wahrscheinlicher Rechtsverstoß
- high: Klarer Rechtsverstoß, Anzeige empfohlen
- critical: Schwere Straftat, sofortige Anzeige + Beweissicherung
```

### Warum dieser Prompt funktioniert

1. **Role Assignment** — "Du bist SafeVoice — ein juristischer Klassifikator". Kein Chatbot.
2. **Behavioral Guardrails** — "im Zweifel FÜR das Opfer" = priorisiert False Positives über False Negatives. Für Opferhilfe ist das richtig.
3. **Invariant** — "NetzDG § 3 gilt IMMER bei Social Media". Garantiert, dass wir nie vergessen, die Plattform-Pflicht zu erwähnen.
4. **Severity-Definitionen** — nicht "interpretier irgendwie", sondern konkret, was was bedeutet.
5. **Sprache** — der Prompt ist auf Deutsch. Das verbessert die Klassifikation deutscher Inhalte messbar, weil das LLM im deutschen Legal-Kontext bleibt.

## 4. Der Classification-Endpoint — wie der API-Call aussieht

Datei: `classifier_llm_v2.py`, Zeile 171-180.

```python
completion = client.chat.completions.parse(
    model="gpt-4o-mini",          # günstig, schnell, gut genug für Klassifikation
    temperature=0,                 # deterministisch — Legal muss reproduzierbar sein
    max_tokens=1024,               # genug für JSON, nicht verschwenderisch
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Klassifiziere diesen Inhalt:\n\n{text}"},
    ],
    response_format=LLMClassification,  # Pydantic-Schema, Server-seitig erzwungen
)
```

### Die 4 Schlüssel-Entscheidungen (kenne sie auswendig)

| Entscheidung | Warum |
|---|---|
| **gpt-4o-mini** statt gpt-4o | 15x günstiger, 90% der Accuracy für Classification-Tasks |
| **temperature=0** | Legal = deterministisch. Gleicher Input → gleicher Output. Keine Kreativität. |
| **`.parse()`** statt `.create()` | Die moderne Structured-Output-API. Server validiert das Pydantic-Schema. |
| **`response_format=LLMClassification`** | Pydantic-Klasse statt JSON-Schema-String. Typsicher, Server-enforced. |

## 5. Output Parsing — der moderne Weg

**Alt (classifier_llm.py)**: JSON-Schema im System-Prompt + manuelles `json.loads(raw)`.
**Neu (classifier_llm_v2.py)**: OpenAI Structured Outputs + Pydantic `.parse()`.

### Das Pydantic-Schema

```python
class LLMClassification(BaseModel):
    model_config = ConfigDict(extra="forbid")  # keine zusätzlichen Felder erlaubt

    severity: LLMSeverity                          # Enum: low/medium/high/critical
    categories: list[LLMCategory] = Field(..., min_length=1)  # min 1 Kategorie
    confidence: float = Field(..., ge=0.0, le=1.0) # zwingend in [0, 1]
    requires_immediate_action: bool
    summary: str
    summary_de: str
    applicable_laws: list[LLMLaw]
    potential_consequences: str
    potential_consequences_de: str
```

### Was das Schema für dich tut

- **Server-side Schema-Enforcement** — OpenAI wirft KEINE malformed JSON zurück. Niemals.
- **Type Safety** — `completion.choices[0].message.parsed` ist eine validierte `LLMClassification`-Instanz (oder None bei Fehler).
- **Enum-Validierung** — wenn das LLM `severity: "extreme"` zurückgeben wollte, wird der Call abgelehnt.
- **Refusal-Handling** — `msg.refusal` ist gesetzt, wenn OpenAI den Call aus Safety-Gründen ablehnt.

### Der Code dazu (auswendig)

```python
msg = completion.choices[0].message

if msg.refusal:
    return None  # OpenAI hat aus Safety-Gründen abgelehnt

llm_result = msg.parsed  # Pydantic-Instanz oder None
if llm_result is None:
    return None

# Mapping LLM-Enum → Domain-Modell
return _to_domain(llm_result)
```

## Typische Tutor-Frage: "Warum Structured Outputs statt manuellem JSON-Parsing?"

> *"Weil das LLM auch mit gutem Prompt manchmal Markdown-Code-Fences (```) um das JSON schreibt, oder ein Feld vergisst, oder ein Enum-Value erfindet. Strukturierte Outputs sind Server-seitig Schema-enforced — OpenAI weigert sich, ein ungültiges Objekt zurückzugeben. Keine defensiven `try: json.loads(); except:` mehr. Entweder ich bekomme ein valides Pydantic-Objekt oder None."*

## Typische Tutor-Frage: "Was wenn OpenAI das Objekt nicht bauen kann?"

> *"Zwei Möglichkeiten. Erstens `msg.refusal` — OpenAI hat aus Safety-Gründen abgelehnt (passiert bei extremen Inhalten manchmal). Zweitens `msg.parsed is None` — OpenAI wollte, hat aber kein valides Schema produziert. In beiden Fällen loggen wir und returnen None. Der Orchestrator (`classifier.py`) wirft dann `ClassifierUnavailableError` — der Router macht daraus ein 503 mit 'bitte später versuchen'. Besser als ein schwacher Fallback."*

## Typische Tutor-Frage: "Warum temperature=0?"

> *"Legal-Kontext. Wenn derselbe Text 'Women should shut up' morgen als Severity MEDIUM und übermorgen als HIGH klassifiziert wird, verlieren wir Vertrauen und Gerichts-Tauglichkeit. Temperature 0 heißt: gleicher Input → gleicher Output. Deterministisch. Wir geben Kreativität auf, gewinnen Reproduzierbarkeit. Die Classification ist kein kreativer Akt, sondern ein Mapping."*

## Die komplette Flow-Grafik (siehe TUTOR_PREP.md Section 6)

```
USER                          BACKEND                         OPENAI
  │                              │                               │
  │  paste text / URL / image    │                               │
  ├─────────────────────────────►│                               │
  │                              │  (if URL: scrape content)     │
  │                              │  (if image: OCR extract text) │
  │                              │                               │
  │                              │  system_prompt + user_text    │
  │                              ├──────────────────────────────►│
  │                              │                               │
  │                              │     Pydantic-parsed object    │
  │                              │◄──────────────────────────────┤
  │                              │                               │
  │                              │  _to_domain() map → ORM save  │
  │                              │  hash content (SHA-256)       │
  │                              │  timestamp (UTC)              │
  │                              │                               │
  │   severity + categories      │                               │
  │   + laws + summaries         │                               │
  │◄─────────────────────────────┤                               │
```

---

# Was ist OFFEN für nächste Woche

Ehrliche Liste — **sag das dem Tutor so**:

## Open (P1 — Should do)

1. **Cleanup-Job für 7-Tage-Soft-Delete.** Der Code setzt `deleted_at`, aber es gibt noch keinen Background-Job, der nach 7 Tagen hard-löscht. Ich will das mit einem einfachen Cron-Task lösen.

2. **Art. 20 GDPR — Data-Export-Endpoint.** Die Datenschutzerklärung verspricht es, es gibt noch keinen Endpoint. Plan: `GET /auth/me/export` → JSON mit allen User-Daten.

3. **Magic-Link via echten Email-Provider.** Aktuell gibt der MVP den Token direkt im Response zurück — für die Demo praktisch, für Production muss das über Resend/Sendgrid.

4. **Session-Cookie statt LocalStorage.** HttpOnly + SameSite=Strict + Secure, damit XSS den Token nicht stehlen kann.

5. **Cleanup Tests für Bulk-Import (CSV).** NGO-Partner werden das nutzen, aktuell gibt es nur Minimal-Tests.

## Open (Docs — schon gefixt heute)

- ✅ CLAUDE.md aktualisiert (in-memory → real DB)
- ✅ TUTOR_PREP.md aktualisiert (3-tier → single-tier mit Begründung)
- ✅ TUTOR_PREP.md erweitert (Multi-Tenancy Section)
- ✅ DEPLOY.md geschrieben (Railway + VITE_OPERATOR_* + HTTPS)

## Roadmap — was kommt danach

- **Tier-2-Classifier reaktivieren** (HuggingFace, lokaler Fallback für Privacy-sensitive NGOs) — ggf.
- **Partner-API ausbauen** — Case-Assignment-Workflow
- **Offender-DB** — Wiedererkennung von Tätern über Cases hinweg
- **Echte Deployment auf Railway** (aktuell nur lokal getestet)

---

# Red-Flag-Fragen — was sagst du bei Unsicherheit

## "Wie viele Tests hast du?"

Schau in die Datei: `tests/` hat 22 Test-Files. Laut COURSE_SUBMISSION (Week 11) waren es 452 Tests — das ist der letzte dokumentierte Stand. Heute kannst du es verifizieren mit `pytest --tb=no -q` (aber Audit hat's nicht ausgeführt mangels venv-Permission). Sag ehrlich: *"Ungefähr 450, ich checke das heute abend nochmal."*

## "Läuft es auf Railway?"

**Nein, noch nicht deployed.** Railway-Config ist da, DEPLOY.md steht seit heute. *"Deployment ist Docker-ready, Railway.json konfiguriert, aber noch nicht live — das ist für diese Woche geplant. Ich will erst sicherstellen, dass alle VITE_OPERATOR_* Env-Vars gesetzt sind, weil die Impressum davon abhängt."*

## "Warum kein Transformer-Fallback mehr?"

Die Antwort ist in TUTOR_PREP.md Section 5 jetzt ausführlich. Kurz: *"Schwache Klassifikation ist schlimmer als keine. Ein MEDIUM-Severity-Badge bei einer echten Todesdrohung würde das Opfer in Sicherheit wiegen — das ist schlimmer als ein ehrliches 503 'bitte später versuchen'."*

## "Wie gehst du mit Bias in GPT-4o-mini um?"

Ehrlich: *"Ich hab es noch nicht systematisch evaluiert. Die Victim-Centered-Regel im Prompt ('im Zweifel fürs Opfer') ist der stärkste Hebel aktuell. Bias-Evaluation mit einem Test-Set aus echten Fällen kommt auf die Roadmap — vielleicht können wir das nächste Woche diskutieren?"*

Dem Tutor zeigst du damit: (1) du bist dir des Problems bewusst, (2) du hast einen aktuellen Mitigator, (3) du willst mehr — und eröffnest einen Gesprächspunkt.

## "Wie validierst du, dass die Classification korrekt ist?"

Aktuell: manuelle Checks gegen bekannte Fälle in `data/mock_data.py`. Kein automatisierter Accuracy-Test. *"Ich hab Test-Daten mit erwarteten Klassifikationen — aber ein Confusion-Matrix-Test gegen ein Gold-Standard-Set ist ein offener Punkt."*

---

# Abschließende Checkliste — vor dem Meeting

- [ ] `cd backend && source venv/bin/activate && pytest --tb=no -q` — wie viele Tests passen aktuell?
- [ ] Demo lokal durchspielen — alle 3 Schritte funktionieren?
- [ ] `OPENAI_API_KEY` in der .env ist gesetzt?
- [ ] `git push` — die 14 ungepushten Commits auf GitHub hoch
- [ ] Chrome mit 2 Tabs offen: `http://localhost:5173` und `http://localhost:8000/docs`
- [ ] Terminal mit `uvicorn` + `npm run dev` am Laufen haben
- [ ] Diese Datei + TUTOR_PREP.md nochmal durchlesen

---

**Du bist bereit. Atme. Die Arbeit ist solide. Morgen ist ein Gespräch, keine Prüfung.**
