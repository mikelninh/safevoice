/**
 * Datenschutzerklaerung / Privacy Policy — required by DSGVO (GDPR).
 *
 * Bilingual: renders German or English based on `lang` prop.
 */
import type { Lang } from '../i18n'

interface Props {
  lang: Lang
}

export default function Datenschutz({ lang }: Props) {
  const de = lang === 'de'

  return (
    <div className="max-w-2xl mx-auto px-4 py-10">
      <h1 className="text-2xl font-bold mb-2">
        {de ? 'Datenschutzerklärung' : 'Privacy Policy'}
      </h1>
      <p className="text-slate-400 text-sm mb-8">
        {de ? 'Stand: März 2026' : 'Last updated: March 2026'}
      </p>

      {/* --- 1. Overview --- */}
      <Section title={de ? '1. Überblick' : '1. Overview'}>
        <p>
          {de
            ? 'SafeVoice ist eine Plattform zur Dokumentation digitaler Gewalt. Der Schutz Ihrer persönlichen Daten hat für uns höchste Priorität. Diese Datenschutzerklärung informiert Sie darüber, welche Daten wir erheben, warum wir sie erheben und welche Rechte Sie haben.'
            : 'SafeVoice is a platform for documenting digital harassment. Protecting your personal data is our highest priority. This privacy policy explains what data we collect, why we collect it, and what rights you have.'}
        </p>
      </Section>

      {/* --- 2. No tracking / no cookies --- */}
      <Section
        title={
          de
            ? '2. Kein Tracking, keine Cookies'
            : '2. No Tracking, No Cookies'
        }
      >
        <p>
          {de
            ? 'SafeVoice verwendet keine Tracking-Tools, keine Analyse-Software und keine Cookies. Wir setzen weder Google Analytics, Facebook Pixel noch ähnliche Dienste ein. Es gibt keine Werbung.'
            : 'SafeVoice does not use any tracking tools, analytics software, or cookies. We do not use Google Analytics, Facebook Pixel, or similar services. There is no advertising.'}
        </p>
      </Section>

      {/* --- 3. Data stays on your device --- */}
      <Section
        title={
          de
            ? '3. Daten bleiben auf Ihrem Gerät'
            : '3. Data Stays on Your Device'
        }
      >
        <p>
          {de
            ? 'Fälle und Beweismittel werden primär lokal in Ihrem Browser gespeichert. Nur wenn Sie sich bewusst anmelden und Daten synchronisieren, werden diese verschlüsselt an unseren Server übertragen.'
            : 'Cases and evidence are primarily stored locally in your browser. Only when you explicitly sign in and choose to sync are data transmitted (encrypted) to our server.'}
        </p>
      </Section>

      {/* --- 4. What data we collect --- */}
      <Section
        title={de ? '4. Welche Daten wir erheben' : '4. What Data We Collect'}
      >
        <ul className="list-disc list-inside space-y-1">
          <li>
            {de
              ? 'Analyseanfragen: Der von Ihnen eingegebene Text oder die URL wird zur Klassifikation an unser Backend gesendet und nicht dauerhaft gespeichert.'
              : 'Analysis requests: The text or URL you submit is sent to our backend for classification and is not permanently stored.'}
          </li>
          <li>
            {de
              ? 'Konto-Daten (optional): E-Mail-Adresse, falls Sie sich für ein Konto registrieren.'
              : 'Account data (optional): Email address, if you register for an account.'}
          </li>
          <li>
            {de
              ? 'Server-Logs: IP-Adresse, Zeitstempel und HTTP-Methode werden temporär (max. 7 Tage) für Sicherheitszwecke gespeichert.'
              : 'Server logs: IP address, timestamp, and HTTP method are temporarily stored (max. 7 days) for security purposes.'}
          </li>
        </ul>
      </Section>

      {/* --- 5. Purpose / legal basis --- */}
      <Section
        title={
          de
            ? '5. Zweck und Rechtsgrundlage'
            : '5. Purpose and Legal Basis'
        }
      >
        <p>
          {de
            ? 'Die Datenverarbeitung erfolgt auf Grundlage von Art. 6 Abs. 1 lit. a (Einwilligung) und lit. f (berechtigtes Interesse an der Sicherheit der Plattform) DSGVO.'
            : 'Data processing is based on Art. 6(1)(a) (consent) and Art. 6(1)(f) (legitimate interest in platform security) GDPR.'}
        </p>
      </Section>

      {/* --- 6. Hosting --- */}
      <Section title={de ? '6. Hosting' : '6. Hosting'}>
        <p>
          {de
            ? 'Unsere Server werden bei Hetzner Online GmbH in Deutschland betrieben. Alle Daten verbleiben innerhalb der EU. Hetzner ist nach ISO 27001 zertifiziert.'
            : 'Our servers are hosted by Hetzner Online GmbH in Germany. All data remains within the EU. Hetzner is ISO 27001 certified.'}
        </p>
      </Section>

      {/* --- 7. Data retention --- */}
      <Section
        title={de ? '7. Speicherdauer' : '7. Data Retention'}
      >
        <p>
          {de
            ? 'Analyse-Ergebnisse werden nicht serverseitig gespeichert. Server-Logs werden nach maximal 7 Tagen gelöscht. Kontodaten werden gelöscht, sobald Sie Ihr Konto löschen.'
            : 'Analysis results are not stored server-side. Server logs are deleted after a maximum of 7 days. Account data is deleted as soon as you delete your account.'}
        </p>
      </Section>

      {/* --- 8. Your rights (Art. 15-21 DSGVO) --- */}
      <Section
        title={
          de
            ? '8. Ihre Rechte nach Art. 15–21 DSGVO'
            : '8. Your Rights under Art. 15–21 GDPR'
        }
      >
        <p className="mb-3">
          {de
            ? 'Sie haben folgende Rechte:'
            : 'You have the following rights:'}
        </p>
        <ul className="list-disc list-inside space-y-1">
          <li>
            {de
              ? 'Auskunftsrecht (Art. 15 DSGVO): Sie können Auskunft über Ihre gespeicherten Daten verlangen.'
              : 'Right of access (Art. 15 GDPR): You may request information about your stored data.'}
          </li>
          <li>
            {de
              ? 'Recht auf Berichtigung (Art. 16 DSGVO): Sie können die Berichtigung unrichtiger Daten verlangen.'
              : 'Right to rectification (Art. 16 GDPR): You may request correction of inaccurate data.'}
          </li>
          <li>
            {de
              ? 'Recht auf Löschung (Art. 17 DSGVO): Sie können die Löschung Ihrer Daten verlangen.'
              : 'Right to erasure (Art. 17 GDPR): You may request deletion of your data.'}
          </li>
          <li>
            {de
              ? 'Recht auf Einschränkung der Verarbeitung (Art. 18 DSGVO)'
              : 'Right to restriction of processing (Art. 18 GDPR)'}
          </li>
          <li>
            {de
              ? 'Recht auf Datenübertragbarkeit (Art. 20 DSGVO)'
              : 'Right to data portability (Art. 20 GDPR)'}
          </li>
          <li>
            {de
              ? 'Widerspruchsrecht (Art. 21 DSGVO)'
              : 'Right to object (Art. 21 GDPR)'}
          </li>
        </ul>
      </Section>

      {/* --- 9. Emergency delete / Right to erasure --- */}
      <Section
        title={
          de
            ? '9. Notfall-Löschung'
            : '9. Emergency Delete'
        }
      >
        <p>
          {de
            ? 'SafeVoice bietet eine Notfall-Löschfunktion (Safe Exit), mit der Sie alle lokal gespeicherten Daten sofort und unwiderruflich von Ihrem Gerät löschen können. Diese Funktion ist jederzeit über den "Notausgang"-Button erreichbar. Auf dem Server gespeicherte Daten (falls vorhanden) werden auf Anfrage innerhalb von 24 Stunden gelöscht.'
            : 'SafeVoice provides an emergency delete feature (Safe Exit) that allows you to immediately and irreversibly delete all locally stored data from your device. This feature is accessible at any time via the "Safe Exit" button. Any server-stored data (if applicable) will be deleted within 24 hours upon request.'}
        </p>
      </Section>

      {/* --- 10. Contact --- */}
      <Section
        title={
          de
            ? '10. Verantwortliche Stelle & Kontakt'
            : '10. Data Controller & Contact'
        }
      >
        <p>
          [TODO: Name]<br />
          [TODO: Adresse]<br />
          E-Mail: [TODO: datenschutz@example.com]
        </p>
        <p className="mt-3 text-slate-400 text-sm">
          {de
            ? 'Sie haben das Recht, sich bei einer Datenschutz-Aufsichtsbehörde zu beschweren.'
            : 'You have the right to lodge a complaint with a data protection supervisory authority.'}
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
