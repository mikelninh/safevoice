/**
 * Datenschutzerklärung / Privacy Policy — required by DSGVO (GDPR).
 *
 * Bilingual: renders German or English based on `lang` prop.
 *
 * Sub-processors disclosed (REQUIRED — we cannot hide these):
 *   - Railway Corp. (US) — hosting (Postgres + FastAPI) — SCC required
 *   - OpenAI Ireland Ltd / OpenAI L.L.C. (US) — AI classification — SCC,
 *     potentially Art. 9 (special category) data when classifying threats
 *     of sexual / discriminatory violence
 *   - Internet Archive (US) — URL archiving via /save endpoint (only when
 *     user submits a URL, not for plain text)
 *
 * Operator contact pulled from same VITE_OPERATOR_* env vars as Impressum.
 */
import type { Lang } from '../i18n'

interface Props {
  lang: Lang
}

const op = {
  name: import.meta.env.VITE_OPERATOR_NAME || '— nicht konfiguriert —',
  email: import.meta.env.VITE_OPERATOR_EMAIL || '— nicht konfiguriert —',
}

export default function Datenschutz({ lang }: Props) {
  const de = lang === 'de'

  return (
    <div className="max-w-2xl mx-auto px-4 py-10">
      <h1 className="text-2xl font-bold mb-2">
        {de ? 'Datenschutzerklärung' : 'Privacy Policy'}
      </h1>
      <p className="text-slate-400 text-sm mb-8">
        {de ? 'Stand: April 2026' : 'Last updated: April 2026'}
      </p>

      <div className="mb-8 rounded border border-amber-500/40 bg-amber-500/10 p-4 text-sm text-amber-200">
        {de
          ? 'Wichtiger Hinweis: Diese Datenschutzerklärung wurde nach bestem Wissen erstellt, aber NICHT anwaltlich geprüft. SafeVoice befindet sich in einer Pilot-/Beta-Phase. Bevor Sie sensible Beweise (insb. Sexualstraftaten oder Bedrohungen besonderer Personengruppen nach Art. 9 DSGVO) hochladen, sollten Sie diese Datenschutzerklärung sorgfältig lesen und bei Zweifeln auf unsere Plattform verzichten.'
          : 'Important: This privacy policy was drafted in good faith but has NOT been reviewed by a lawyer. SafeVoice is in a pilot/beta phase. Before uploading sensitive evidence (especially regarding sexual offenses or threats targeting protected groups under Art. 9 GDPR), please read this policy carefully and refrain from using the platform if in doubt.'}
      </div>

      {/* --- 1. Verantwortlicher --- */}
      <Section title={de ? '1. Verantwortlicher' : '1. Data controller'}>
        <p>
          {de
            ? 'Verantwortlich im Sinne der DSGVO ist:'
            : 'The data controller within the meaning of the GDPR is:'}
          <br />
          {op.name}
          <br />
          E-Mail:{' '}
          <a href={`mailto:${op.email}`} className="text-blue-400 hover:underline">
            {op.email}
          </a>
          <br />
          {de
            ? 'Vollständige Anschrift: siehe '
            : 'Full address: see '}
          <a href="/impressum" className="text-blue-400 hover:underline">
            Impressum
          </a>
          .
        </p>
      </Section>

      {/* --- 2. Was SafeVoice macht --- */}
      <Section title={de ? '2. Was SafeVoice macht' : '2. What SafeVoice does'}>
        <p>
          {de
            ? 'SafeVoice unterstützt Betroffene digitaler Gewalt dabei, Vorfälle zu dokumentieren, sie nach deutschem Strafrecht (StGB, NetzDG) klassifizieren zu lassen und gerichtsfeste Berichte (PDF + .eml) zur Weiterleitung an Polizei, Staatsanwaltschaft, Plattformen oder Beratungsstellen zu erstellen. Dafür verarbeiten wir zwingend bestimmte Daten — die folgenden Abschnitte erklären welche, wo und warum.'
            : 'SafeVoice helps victims of digital harassment document incidents, classify them under German criminal law (StGB, NetzDG), and produce court-ready reports (PDF + .eml) for forwarding to police, prosecutors, platforms, or counseling services. To do this, we must process certain data — the following sections explain which, where, and why.'}
        </p>
      </Section>

      {/* --- 3. No tracking / cookies --- */}
      <Section
        title={de ? '3. Kein Tracking, keine Werbe-Cookies' : '3. No tracking, no advertising cookies'}
      >
        <p>
          {de
            ? 'Wir verwenden weder Google Analytics noch Meta Pixel noch vergleichbare Tracker. Es werden keine Werbe-Cookies gesetzt. Technisch notwendige Cookies (z. B. Session-Cookie nach Magic-Link-Login) werden ohne vorherige Einwilligung gesetzt, da sie für den Betrieb des Dienstes erforderlich sind (§ 25 Abs. 2 Nr. 2 TTDSG).'
            : 'We use neither Google Analytics nor Meta Pixel nor comparable trackers. No advertising cookies are set. Technically necessary cookies (e.g. session cookie after magic-link login) are set without prior consent because they are required for the operation of the service (§ 25 (2) no. 2 TTDSG).'}
        </p>
      </Section>

      {/* --- 4. Welche Daten wir verarbeiten --- */}
      <Section
        title={de ? '4. Welche Daten wir verarbeiten' : '4. What data we process'}
      >
        <p className="mb-3">
          {de ? 'Wir verarbeiten folgende Datenkategorien:' : 'We process the following data categories:'}
        </p>
        <ul className="list-disc list-outside ml-5 space-y-2">
          <li>
            <strong>{de ? 'Beweistext / URLs / Screenshots:' : 'Evidence text / URLs / screenshots:'}</strong>{' '}
            {de
              ? 'Inhalte, die Sie aktiv hochladen — typischerweise belastendes Material gegen Sie. Diese Inhalte können personenbezogene Daten Dritter (Täter:innen, Zeug:innen) enthalten und in Einzelfällen besondere Kategorien nach Art. 9 DSGVO (z. B. sexuelle Orientierung, ethnische Herkunft, politische Überzeugung) berühren. Rechtsgrundlage: Art. 6 Abs. 1 lit. b (Vertragserfüllung), bei Art.-9-Daten zusätzlich Art. 9 Abs. 2 lit. f DSGVO (Geltendmachung von Rechtsansprüchen).'
              : 'Content you actively upload — typically material targeting you. This content may contain personal data of third parties (perpetrators, witnesses) and in some cases special category data under Art. 9 GDPR (e.g. sexual orientation, ethnic origin, political views). Legal basis: Art. 6(1)(b) (contract performance), and for Art. 9 data additionally Art. 9(2)(f) GDPR (establishment of legal claims).'}
          </li>
          <li>
            <strong>{de ? 'Konto-Daten:' : 'Account data:'}</strong>{' '}
            {de
              ? 'E-Mail-Adresse für den passwortlosen Magic-Link-Login. Optional: Name, Adresse, Telefon — nur wenn Sie diese in eine Strafanzeige aufnehmen möchten. Diese werden NICHT dauerhaft im Profil gespeichert, sondern nur für die Dauer der Berichtserstellung gehalten und anschließend in den generierten PDF/.eml-Dateien festgeschrieben.'
              : 'Email address for passwordless magic-link login. Optional: name, address, phone — only if you wish to include them in a criminal complaint. These are NOT permanently stored in your profile but kept only for the duration of report generation and then frozen into the generated PDF/.eml files.'}
          </li>
          <li>
            <strong>{de ? 'Klassifikations-Ergebnisse:' : 'Classification results:'}</strong>{' '}
            {de
              ? 'Schweregrad, Kategorie, einschlägige StGB-Paragraphen und SHA-256-Hashes Ihrer Beweise. Werden in unserer Postgres-Datenbank gespeichert, damit Sie später Berichte erzeugen können.'
              : 'Severity, category, applicable StGB paragraphs, and SHA-256 hashes of your evidence. Stored in our Postgres database so you can generate reports later.'}
          </li>
          <li>
            <strong>Server-Logs:</strong>{' '}
            {de
              ? 'IP-Adresse, Zeitstempel, HTTP-Methode und User-Agent zur Abwehr von Missbrauch. Aufbewahrung max. 14 Tage. Rechtsgrundlage: Art. 6 Abs. 1 lit. f DSGVO (berechtigtes Interesse an Sicherheit).'
              : 'IP address, timestamp, HTTP method, and user agent to defend against abuse. Retention max. 14 days. Legal basis: Art. 6(1)(f) GDPR (legitimate interest in security).'}
          </li>
        </ul>
      </Section>

      {/* --- 5. Auftragsverarbeiter / Sub-processors (CRITICAL) --- */}
      <Section
        title={de ? '5. Auftragsverarbeiter & Drittstaatenübermittlung' : '5. Sub-processors & third-country transfers'}
      >
        <p className="mb-3">
          {de
            ? 'SafeVoice nutzt folgende Auftragsverarbeiter. Übermittlungen in die USA erfolgen auf Grundlage des EU-US Data Privacy Framework und/oder Standardvertragsklauseln (SCC) gemäß Art. 46 Abs. 2 lit. c DSGVO:'
            : 'SafeVoice uses the following sub-processors. Transfers to the US are based on the EU-US Data Privacy Framework and/or Standard Contractual Clauses (SCC) under Art. 46(2)(c) GDPR:'}
        </p>
        <ul className="list-disc list-outside ml-5 space-y-3">
          <li>
            <strong>Railway Corporation</strong> (548 Market St #95945, San Francisco, CA 94104, USA)
            <br />
            <span className="text-slate-400 text-sm">
              {de
                ? 'Hosting der Anwendung und der Postgres-Datenbank. Standort der Server kann in den USA oder einer anderen Region liegen, die Railway als Hosting-Anbieter wählt. Hier liegen ALLE persistierten Daten (Konten, Fälle, Klassifikationen, Beweistexte, Screenshots).'
                : 'Hosts the application and Postgres database. Server region may be the US or any region selected by Railway. ALL persisted data (accounts, cases, classifications, evidence text, screenshots) reside here.'}
            </span>
          </li>
          <li>
            <strong>OpenAI Ireland Ltd / OpenAI L.L.C.</strong> (1 Letterkenny Rd, Letterkenny, Co. Donegal, Ireland; 3180 18th St, San Francisco, CA 94110, USA)
            <br />
            <span className="text-slate-400 text-sm">
              {de
                ? 'KI-gestützte Klassifikation (gpt-4o-mini). Beim Klassifizieren wird der Beweistext zur Analyse an OpenAI gesendet. OpenAI verarbeitet API-Daten gemäß seiner Data Processing Addendum nicht zum Modelltraining. Wichtig: Wenn der Beweistext sensible Daten nach Art. 9 DSGVO enthält (z. B. Beleidigungen mit sexuellem oder ethnischem Bezug), werden auch diese übertragen. Wenn Sie das vermeiden möchten, bietet das Backend einen Regex-/Local-Fallback-Modus — kontaktieren Sie uns für einen privaten Modus ohne LLM.'
                : 'AI-powered classification (gpt-4o-mini). During classification, the evidence text is sent to OpenAI for analysis. Per its Data Processing Addendum, OpenAI does not use API data for model training. Important: if your evidence contains Art. 9 GDPR special-category data (e.g. insults with sexual or ethnic references), this is also transmitted. If you wish to avoid this, the backend offers a regex/local fallback mode — contact us for a private no-LLM mode.'}
            </span>
          </li>
          <li>
            <strong>Internet Archive</strong> (300 Funston Avenue, San Francisco, CA 94118, USA)
            <br />
            <span className="text-slate-400 text-sm">
              {de
                ? 'Wenn Sie eine URL als Beweis hinterlegen, fordern wir eine Archivierung über archive.org/save an, damit der Beweis auch später noch nachweisbar ist. Übermittelt wird nur die URL selbst, nicht Ihre Identität. Bei reinen Text- oder Screenshot-Beweisen findet keine Übermittlung statt.'
                : 'When you submit a URL as evidence, we trigger archival via archive.org/save so the evidence remains verifiable later. Only the URL itself is transmitted, not your identity. For pure text or screenshot evidence, no transmission occurs.'}
            </span>
          </li>
          <li>
            <strong>{de ? 'Empfänger Ihrer Berichte (Strafanzeigen / NetzDG-Meldungen):' : 'Recipients of your reports (criminal complaints / NetzDG notices):'}</strong>{' '}
            <span className="text-slate-400 text-sm">
              {de
                ? 'Wenn Sie über die "Bericht senden"-Funktion eine .eml-Datei generieren und versenden, geht diese direkt von IHREM E-Mail-Programm an die gewählte Empfängerin (Polizei, Staatsanwaltschaft, Plattform). SafeVoice ist an diesem Versand nicht beteiligt — wir sehen weder, ob Sie versendet haben, noch was angekommen ist.'
                : 'When you use the "Send report" function to generate and send a .eml file, it is sent directly from YOUR email client to the chosen recipient (police, prosecutor, platform). SafeVoice is not involved in the actual sending — we neither see whether you sent nor what was received.'}
            </span>
          </li>
        </ul>
      </Section>

      {/* --- 6. Speicherdauer --- */}
      <Section title={de ? '6. Speicherdauer' : '6. Retention'}>
        <ul className="list-disc list-outside ml-5 space-y-1">
          <li>{de ? 'Konto: bis zur Löschung durch Sie.' : 'Account: until you delete it.'}</li>
          <li>
            {de
              ? 'Fälle und Beweise: bis zu Ihrer Löschung. Empfehlung: nach Abschluss des Strafverfahrens löschen oder lokal archivieren und Server-Kopie löschen.'
              : 'Cases and evidence: until you delete them. Recommendation: delete after criminal proceedings conclude, or archive locally and delete the server copy.'}
          </li>
          <li>
            {de
              ? 'Server-Logs: 14 Tage, anschließend automatisierte Löschung.'
              : 'Server logs: 14 days, then automatic deletion.'}
          </li>
          <li>
            {de
              ? 'Bei OpenAI verarbeitete Beweistexte: gemäß OpenAI API-Richtlinien max. 30 Tage zur Missbrauchsprüfung, dann gelöscht (kein Modelltraining).'
              : 'Evidence text processed by OpenAI: per OpenAI API policy, max 30 days for abuse review, then deleted (no model training).'}
          </li>
        </ul>
      </Section>

      {/* --- 7. Hash-Kette / Integrität --- */}
      <Section title={de ? '7. Hash-Kette / Integrität' : '7. Hash chain / integrity'}>
        <p>
          {de
            ? 'Jedes Beweisstück erhält einen SHA-256-Hash, der mit dem Hash des vorherigen Beweisstücks verkettet wird (ähnlich einer Blockchain). Dadurch lässt sich vor Gericht nachweisen, dass Beweise nach dem Hochladen nicht nachträglich verändert wurden. Die Hashes sind keine personenbezogenen Daten, sondern kryptographische Prüfsummen der Inhalte.'
            : 'Each piece of evidence receives a SHA-256 hash that is chained with the hash of the previous piece (similar to a blockchain). This allows you to prove in court that evidence has not been altered after upload. The hashes are not personal data, but cryptographic checksums of content.'}
        </p>
      </Section>

      {/* --- 8. Mehrmandantenfähigkeit --- */}
      <Section title={de ? '8. Organisationen (NGO-Modus)' : '8. Organizations (NGO mode)'}>
        <p>
          {de
            ? 'Falls Sie SafeVoice im Auftrag einer Beratungsstelle oder NGO nutzen, sind Ihre Fälle innerhalb der Organisation für andere autorisierte Mitglieder sichtbar. Fälle sind streng nach org_id voneinander isoliert; eine Organisation hat KEINEN Zugriff auf Fälle einer anderen Organisation. Anonyme (nicht-Org-)Fälle sind ausschließlich für die anlegende Person sichtbar.'
            : 'If you use SafeVoice on behalf of a counseling service or NGO, your cases are visible to other authorized members within your organization. Cases are strictly isolated by org_id; one organization has NO access to cases of another. Anonymous (non-org) cases are visible only to the person who created them.'}
        </p>
      </Section>

      {/* --- 9. Ihre Rechte --- */}
      <Section
        title={de ? '9. Ihre Rechte nach Art. 15–21 DSGVO' : '9. Your rights under Art. 15–21 GDPR'}
      >
        <p className="mb-3">
          {de ? 'Sie haben jederzeit das Recht auf:' : 'At any time you have the right to:'}
        </p>
        <ul className="list-disc list-outside ml-5 space-y-1">
          <li>{de ? 'Auskunft über Ihre gespeicherten Daten (Art. 15 DSGVO)' : 'Access to your stored data (Art. 15 GDPR)'}</li>
          <li>{de ? 'Berichtigung unrichtiger Daten (Art. 16 DSGVO)' : 'Rectification of inaccurate data (Art. 16 GDPR)'}</li>
          <li>{de ? 'Löschung (Art. 17 DSGVO) — auch über den "Notausgang"-Button mit sofortiger Wirkung im Browser' : 'Erasure (Art. 17 GDPR) — also via the "Safe Exit" button for immediate browser-side deletion'}</li>
          <li>{de ? 'Einschränkung der Verarbeitung (Art. 18 DSGVO)' : 'Restriction of processing (Art. 18 GDPR)'}</li>
          <li>{de ? 'Datenübertragbarkeit (Art. 20 DSGVO) — Export als JSON möglich' : 'Data portability (Art. 20 GDPR) — JSON export available'}</li>
          <li>{de ? 'Widerspruch gegen Verarbeitung (Art. 21 DSGVO)' : 'Object to processing (Art. 21 GDPR)'}</li>
          <li>
            {de
              ? 'Beschwerde bei einer Aufsichtsbehörde (Art. 77 DSGVO), z. B. der für unseren Sitz zuständigen Landesdatenschutzbehörde'
              : 'Complaint to a supervisory authority (Art. 77 GDPR), e.g. the state DPA responsible for our seat'}
          </li>
        </ul>
        <p className="mt-3">
          {de
            ? 'Anfragen richten Sie bitte an die im Impressum genannte E-Mail. Wir antworten in der Regel innerhalb von 7 Tagen, spätestens innerhalb der gesetzlichen Frist von einem Monat.'
            : 'Please send requests to the email address listed in the Imprint. We typically respond within 7 days, at the latest within the statutory one-month period.'}
        </p>
      </Section>

      {/* --- 10. Notfall-Löschung --- */}
      <Section title={de ? '10. Notfall-Löschung (Safe Exit)' : '10. Emergency delete (Safe Exit)'}>
        <p>
          {de
            ? 'Über den "Notausgang"-Button löschen Sie alle lokal in Ihrem Browser gespeicherten Daten (LocalStorage, IndexedDB, Service-Worker-Cache) sofort und unwiderruflich. Server-seitige Daten werden auf Anfrage per E-Mail innerhalb von 72 Stunden gelöscht.'
            : 'Via the "Safe Exit" button, all data stored locally in your browser (localStorage, IndexedDB, service worker cache) is deleted immediately and irreversibly. Server-side data is deleted within 72 hours upon email request.'}
        </p>
      </Section>

      {/* --- 11. Sicherheit --- */}
      <Section title={de ? '11. Sicherheit' : '11. Security'}>
        <p>
          {de
            ? 'Die Übertragung erfolgt ausschließlich verschlüsselt via TLS 1.3 (HTTPS). Passwörter werden NICHT gespeichert (passwortloses Magic-Link-Verfahren). Die Datenbank ist nicht öffentlich erreichbar. Wir können trotz aller Maßnahmen keine 100%ige Sicherheit garantieren — kein Internetdienst kann das. Bei einer Datenpanne, die ein Risiko für Sie darstellt, informieren wir Sie und die Aufsichtsbehörde innerhalb von 72 Stunden (Art. 33, 34 DSGVO).'
            : 'Transmission is encrypted exclusively via TLS 1.3 (HTTPS). Passwords are NOT stored (passwordless magic-link flow). The database is not publicly reachable. Despite all measures, we cannot guarantee 100% security — no internet service can. In case of a data breach posing a risk to you, we will notify you and the supervisory authority within 72 hours (Art. 33, 34 GDPR).'}
        </p>
      </Section>

      {/* --- 12. Änderungen --- */}
      <Section title={de ? '12. Änderungen dieser Erklärung' : '12. Changes to this policy'}>
        <p>
          {de
            ? 'Wir behalten uns vor, diese Datenschutzerklärung an geänderte Rechtslage oder Funktionsumfänge anzupassen. Die jeweils aktuelle Version finden Sie stets auf dieser Seite. Bei wesentlichen Änderungen informieren wir aktive Nutzer:innen per E-Mail.'
            : 'We reserve the right to update this privacy policy in response to changes in the law or product. The current version is always available on this page. We will notify active users by email of material changes.'}
        </p>
      </Section>
    </div>
  )
}

/** Reusable section wrapper. */
function Section({
  title,
  children,
}: {
  title: string
  children: React.ReactNode
}) {
  return (
    <section className="mb-8">
      <h2 className="text-lg font-semibold mb-2">{title}</h2>
      <div className="text-slate-300 leading-relaxed">{children}</div>
    </section>
  )
}
