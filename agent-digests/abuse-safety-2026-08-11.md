# Abuse-Safety Digest — 2026-08-11

**Watch topic:** German harassment / cybercrime law (StGB §§, NetzDG, BNetzA) affecting SafeVoice's 12 tracked paragraphs and the court-prep agent.
**Repo:** safevoice · **Branch:** agent/abuse-safety-2026-08-11

---

## Summary

One **material legal development** detected. It is a **draft (not yet in force)** but it directly targets SafeVoice's domain (digital violence, deepfakes, cyberstalking) and will change the law catalog once passed. No in-force 2026 StGB change touches any of the 12 currently-tracked paragraphs.

| # | Change | Paragraph(s) affected | Effective date | Status | Impact on SafeVoice |
|---|--------|----------------------|----------------|--------|---------------------|
| 1 | **Gesetz gegen digitale Gewalt (GgdG)** — BMJV Referentenentwurf, creates 3 new StGB offenses for digital violence | New: **§ 184k StGB** (sexualisierte Deepfakes / digitaler Voyeurismus / Rachepornos, real & KI-generiert), **§ 201b StGB** (Identitäts-Deepfakes, die das Ansehen schädigen), **§ 202e StGB** (Cyberstalking via GPS-Tracker). Plus platform duties incl. **§ 5 NetzDG** (Zustellungsbevollmächtigter). | **Not yet in force.** Draft published 17 Apr 2026; stakeholder comments closed 22 May 2026. As of Aug 2026: in legislative process, not yet passed by Bundestag/Bundesrat. | Draft (Referentenentwurf) | SafeVoice law catalog does **not** yet contain §§ 184k/201b/202e. Will need updating when enacted. |

### What is NOT affected (verified)
In-force 2026 StGB amendments (BGBl. 2026 I Nr. 46, 95, 9, 3) changed §§ 44, 69b, 5, 76a, 87a, 89a–c, 91, 99, 129a, 138, 310, 127, 6, 126, 308, 313, 314, 314a, 321 (terrorism, driving bans, explosives, geoschutz). **None of these are in SafeVoice's 12 tracked paragraphs** (§§ 185, 186, 187, 241, 126a, 238, 263, 263a, 269, 130, 201a StGB + NetzDG § 3). No schema update required for them.

---

## Detail — Change #1: Gesetz gegen digitale Gewalt (GgdG)

**Source:** BMJV Pressemitteilung Nr. 28/2026 (17 Apr 2026) + Gesetzgebungsverfahren page (Stand 08 May 2026).
**URLs:**
- https://www.bmjv.de/SharedDocs/Pressemitteilungen/DE/2026/0417_Gesetz_gegen_digitale_Gewalt.html
- https://www.bmjv.de/SharedDocs/Gesetzgebungsverfahren/DE/2026_Gesetz_gegen_digitale_Gewalt.html
- Bundestag Aktuelle Stunde (25 Mar 2026): https://www.bundestag.de/dokumente/textarchiv/2026/kw13-de-aktuelle-stunde-gewalt-1157648

**New criminal offenses:**
- **§ 184k StGB — Verletzung der Intimsphäre durch Bildaufnahmen:** criminalises making/distributing intimate image material regardless of how produced (real or AI-generated) and regardless of location (closes the "digital voyeurism" gap). Covers pornographic deepfakes, revenge porn, rape videos. *Overlaps with and largely supersedes § 201a StGB for AI/intimate-image cases.*
- **§ 201b StGB — Verletzung von Persönlichkeitsrechten durch täuschende Inhalte:** criminalises *making accessible* (not producing) non-sexual deepfakes that seriously damage a person's reputation (e.g. fake footage of someone committing a crime). Satire exempt.
- **§ 202e StGB — Unbefugte Überwachung mittels Informations- oder Kommunikationstechnik:** captures cyberstalking via GPS trackers etc.

**Platform / enforcement duties (relevant to NetzDG pipeline):**
- New Auskunftsanspruch (identity disclosure from platforms/access providers, with judicial oversight).
- Gerichtliche Beweissicherungsanordnungen (preserve perpetrator data).
- Zeitweilige Accountsperre (temporary account block for serious, repeat violations).
- **§ 5 NetzDG amendment** — obligation for non-EU platforms to name an in-country Zustellungsbevollmächtigter.

---

## Impact on SafeVoice court-prep & schema

**Once the GgdG is enacted**, SafeVoice should update (do NOT change now — pending law):

1. **`backend/app/data/mock_data.py`** — add constants `LAW_184K`, `LAW_201B`, `LAW_202E` (parallel to existing `LAW_201A`, `LAW_238`).
2. **`backend/app/services/law_mapper.py`** — extend `GERMAN_LAW_MAP`:
   - `Category.SEXUAL_HARASSMENT` → add `LAW_184K` (alongside `LAW_185`); for deepfake/intimate-image cases § 184k becomes the primary citation over § 201a.
   - `Category.IMPERSATION` / `Category.DEFAMATION` (identity deepfakes) → add `LAW_201B`.
   - `Category.THREAT`/`DEATH_THREAT`/stalking (GPS tracker) → add `LAW_202E` alongside `LAW_238`/`LAW_241`.
3. **`schema.dbml`** — `laws` table already supports arbitrary `code`/`section`, so new rows need no structural change.
4. **`backend/app/services/court_prep_tools.py`** — the Antragsdelikte list (currently "§§ 185, 186, 201a StGB") should add **§ 184k** once in force, because § 184k is also an Antragsdelikt (private-prosecution offense) — this affects the `check_strafantrag_frist` tool's frist_months mapping. The NetzDG-Meldekontakte logic should also reflect the new § 5 Zustellungsbevollmächtigter duty.

**Citizen bottom line:** If you are preparing a Strafanzeige for a deepfake, revenge-porn, or GPS-stalking case *today*, SafeVoice currently cites § 201a / § 238. After the GgdG passes, those cases should additionally/primarily cite the new §§ 184k / 201b / 202e for maximum legal accuracy. No action needed until the law is enacted — this digest is an early-warning for maintainers.

---

## Sources
- BMJV Pressemitteilung 28/2026: https://www.bmjv.de/SharedDocs/Pressemitteilungen/DE/2026/0417_Gesetz_gegen_digitale_Gewalt.html
- BMJV Gesetzgebungsverfahren GgdG: https://www.bmjv.de/SharedDocs/Gesetzgebungsverfahren/DE/2026_Gesetz_gegen_digitale_Gewalt.html
- Bundestag Aktuelle Stunde "Gewalt gegen Frauen" (25.03.2026): https://www.bundestag.de/dokumente/textarchiv/2026/kw13-de-aktuelle-stunde-gewalt-1157648
- Bundestag Plenardebatte § 184k (Grüne BT-Drs. 21/4949, 26.03.2026): https://www.bundestag.de/dokumente/textarchiv/2026/kw13-de-strafgesetzbuch-1157670
- Buzer.de StGB Änderungshistorie (verifies no 2026 in-force change to tracked paragraphs): https://www.buzer.de/gesetz/6165/l.htm
