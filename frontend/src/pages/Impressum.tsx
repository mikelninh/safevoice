/**
 * Impressum (Legal Notice) — legally required in Germany under § 5 TMG and
 * § 18 Abs. 2 MStV (Medienstaatsvertrag, replaced § 55 Abs. 2 RStV in 2020).
 *
 * Operator details are read from VITE_OPERATOR_* env vars so personal data
 * (name, address, phone) does NOT live in the public git repo. Set them in
 * Railway → Variables (or a local .env.local for dev).
 *
 * Required env vars (set on the FRONTEND service, NOT backend):
 *   VITE_OPERATOR_NAME       e.g. "Mikel Ninh"
 *   VITE_OPERATOR_STREET     e.g. "Beispielstraße 1"
 *   VITE_OPERATOR_CITY       e.g. "10115 Berlin"
 *   VITE_OPERATOR_COUNTRY    e.g. "Deutschland"
 *   VITE_OPERATOR_EMAIL      e.g. "kontakt@safevoice.app"
 *   VITE_OPERATOR_PHONE      optional
 *
 * If any required var is missing, a yellow warning banner is shown so the
 * page never silently looks "complete" while still containing placeholders.
 */
import type { Lang } from '../i18n'

interface Props {
  lang: Lang
}

const PLACEHOLDER = '— nicht konfiguriert —'

const op = {
  name: import.meta.env.VITE_OPERATOR_NAME || PLACEHOLDER,
  street: import.meta.env.VITE_OPERATOR_STREET || '',
  city: import.meta.env.VITE_OPERATOR_CITY || PLACEHOLDER,
  country: import.meta.env.VITE_OPERATOR_COUNTRY || 'Deutschland',
  email: import.meta.env.VITE_OPERATOR_EMAIL || PLACEHOLDER,
  phone: import.meta.env.VITE_OPERATOR_PHONE || '',
}

const hasMinimalImprint =
  op.name !== PLACEHOLDER && op.city !== PLACEHOLDER && op.email !== PLACEHOLDER
const hasStreet = op.street.length > 0
const isConfigured = hasMinimalImprint && hasStreet

export default function Impressum({ lang }: Props) {
  const isDE = lang === 'de'

  return (
    <div className="max-w-2xl mx-auto px-4 py-10">
      <h1 className="text-2xl font-bold mb-6">Impressum</h1>

      {!hasMinimalImprint && (
        <div className="mb-8 rounded border border-yellow-500/40 bg-yellow-500/10 p-4 text-sm text-yellow-200">
          <strong>⚠ Konfiguration unvollständig.</strong>{' '}
          {isDE
            ? 'Die Betreiber-Angaben sind noch nicht gesetzt. Setze VITE_OPERATOR_NAME, VITE_OPERATOR_CITY und VITE_OPERATOR_EMAIL in Vercel, bevor diese Seite öffentlich erreichbar wird.'
            : 'Operator details are not yet configured. Set VITE_OPERATOR_NAME, VITE_OPERATOR_CITY and VITE_OPERATOR_EMAIL in Vercel before this page is publicly reachable.'}
        </div>
      )}

      {hasMinimalImprint && !hasStreet && (
        <div className="mb-8 rounded border border-blue-500/40 bg-blue-500/10 p-4 text-sm text-blue-200">
          {isDE
            ? 'Vorschau / Beta-Phase — diese Instanz wird nicht öffentlich beworben. Eine vollständige Postanschrift gemäß § 5 TMG wird vor dem Live-Gang ergänzt; bis dahin ist die Postanschrift auf Anfrage per E-Mail erhältlich.'
            : 'Preview / beta phase — this instance is not publicly advertised. A full postal address per § 5 TMG will be added before going live; until then the postal address is available on request by email.'}
        </div>
      )}

      {/* --- § 5 TMG --- */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-2">
          {isDE ? 'Angaben gemäß § 5 TMG' : 'Information pursuant to § 5 TMG'}
        </h2>
        <p className="text-slate-300 leading-relaxed">
          {op.name}<br />
          {hasStreet && <>{op.street}<br /></>}
          {op.city}<br />
          {op.country}
          {!hasStreet && (
            <>
              <br />
              <span className="text-slate-400 text-sm">
                {isDE
                  ? 'Postanschrift auf Anfrage per E-Mail.'
                  : 'Postal address available on request by email.'}
              </span>
            </>
          )}
        </p>
      </section>

      {/* --- Kontakt --- */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-2">
          {isDE ? 'Kontakt' : 'Contact'}
        </h2>
        <p className="text-slate-300 leading-relaxed">
          E-Mail: <a href={`mailto:${op.email}`} className="text-blue-400 hover:underline">{op.email}</a>
          {op.phone && (
            <>
              <br />
              {isDE ? 'Telefon' : 'Phone'}: {op.phone}
            </>
          )}
        </p>
      </section>

      {/* --- § 18 Abs. 2 MStV (replaces § 55 Abs. 2 RStV since 2020) --- */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-2">
          {isDE
            ? 'Verantwortlich für den Inhalt nach § 18 Abs. 2 MStV'
            : 'Responsible for content per § 18 (2) MStV'}
        </h2>
        <p className="text-slate-300 leading-relaxed">
          {op.name}<br />
          {hasStreet && <>{op.street}<br /></>}
          {op.city}
        </p>
      </section>

      {/* --- Liability for content (§§ 7-10 TMG) --- */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-2">
          {isDE ? 'Haftung für Inhalte' : 'Liability for content'}
        </h2>
        <p className="text-slate-400 text-sm leading-relaxed">
          {isDE
            ? 'Als Diensteanbieter sind wir gemäß § 7 Abs. 1 TMG für eigene Inhalte auf diesen Seiten nach den allgemeinen Gesetzen verantwortlich. Nach §§ 8 bis 10 TMG sind wir als Diensteanbieter jedoch nicht verpflichtet, übermittelte oder gespeicherte fremde Informationen zu überwachen oder nach Umständen zu forschen, die auf eine rechtswidrige Tätigkeit hinweisen. Verpflichtungen zur Entfernung oder Sperrung der Nutzung von Informationen nach den allgemeinen Gesetzen bleiben hiervon unberührt.'
            : 'As a service provider, we are responsible for our own content on these pages in accordance with § 7 (1) TMG and general laws. Pursuant to §§ 8 to 10 TMG, however, we are not obliged as a service provider to monitor third-party information transmitted or stored on our platform, or to investigate circumstances that indicate illegal activity. Obligations to remove or block the use of information under general laws remain unaffected.'}
        </p>
      </section>

      {/* --- Liability for links --- */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-2">
          {isDE ? 'Haftung für Links' : 'Liability for links'}
        </h2>
        <p className="text-slate-400 text-sm leading-relaxed">
          {isDE
            ? 'Unser Angebot enthält Links zu externen Websites Dritter, auf deren Inhalte wir keinen Einfluss haben. Deshalb können wir für diese fremden Inhalte auch keine Gewähr übernehmen. Für die Inhalte der verlinkten Seiten ist stets der jeweilige Anbieter oder Betreiber der Seiten verantwortlich.'
            : 'Our website contains links to external third-party websites whose content is beyond our control. Therefore, we cannot assume any liability for this third-party content. The respective provider or operator of the linked pages is always responsible for their content.'}
        </p>
      </section>

      {/* --- EU dispute resolution (required by Art. 14 ODR-VO) --- */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-2">
          {isDE ? 'Streitschlichtung' : 'EU dispute resolution'}
        </h2>
        <p className="text-slate-400 text-sm leading-relaxed">
          {isDE
            ? 'Die Europäische Kommission stellt eine Plattform zur Online-Streitbeilegung (OS) bereit: '
            : 'The European Commission provides an Online Dispute Resolution (ODR) platform: '}
          <a
            href="https://ec.europa.eu/consumers/odr"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-400 hover:underline"
          >
            https://ec.europa.eu/consumers/odr
          </a>
          {isDE
            ? '. Wir sind nicht bereit oder verpflichtet, an Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen.'
            : '. We are neither willing nor obliged to participate in dispute resolution proceedings before a consumer arbitration board.'}
        </p>
      </section>

      <p className="text-xs text-slate-500 italic mt-12">
        {isDE
          ? 'Hinweis: Diese Seite wurde nicht von einem Rechtsanwalt geprüft. Vor produktivem Einsatz mit echten Nutzerdaten empfehlen wir eine anwaltliche Prüfung, insbesondere für Vereins-/Unternehmensformen mit Registereintrag.'
          : 'Note: This page has not been reviewed by a lawyer. Before going live with real user data, we recommend a legal review, especially for registered organizations or companies.'}
      </p>
    </div>
  )
}
