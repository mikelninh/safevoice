/**
 * Impressum (Legal Notice) — legally required in Germany under § 5 TMG.
 */
import type { Lang } from '../i18n'

interface Props {
  lang: Lang
}

export default function Impressum({ lang }: Props) {
  const isDE = lang === 'de'

  return (
    <div className="max-w-2xl mx-auto px-4 py-10">
      <h1 className="text-2xl font-bold mb-6">Impressum</h1>

      {/* --- Angaben gemaess § 5 TMG --- */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-2">
          {isDE ? 'Angaben gemäß § 5 TMG' : 'Information pursuant to § 5 TMG'}
        </h2>
        <p className="text-slate-300 leading-relaxed">
          [TODO: Firmenname / Name]<br />
          [TODO: Straße und Hausnummer]<br />
          [TODO: PLZ und Ort]<br />
          [TODO: Land]
        </p>
      </section>

      {/* --- Kontakt --- */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-2">
          {isDE ? 'Kontakt' : 'Contact'}
        </h2>
        <p className="text-slate-300 leading-relaxed">
          {isDE ? 'Telefon' : 'Phone'}: [TODO]<br />
          E-Mail: [TODO: email@example.com]
        </p>
      </section>

      {/* --- Vertretungsberechtigte --- */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-2">
          {isDE
            ? 'Vertretungsberechtigte Person'
            : 'Authorized representative'}
        </h2>
        <p className="text-slate-300 leading-relaxed">
          [TODO: Vor- und Nachname]
        </p>
      </section>

      {/* --- Registereintrag --- */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-2">
          {isDE ? 'Registereintrag' : 'Register entry'}
        </h2>
        <p className="text-slate-300 leading-relaxed">
          {isDE ? 'Registergericht' : 'Registration court'}: [TODO]<br />
          {isDE ? 'Registernummer' : 'Registration number'}: [TODO]
        </p>
      </section>

      {/* --- Verantwortlich fuer Inhalte --- */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-2">
          {isDE
            ? 'Verantwortlich für den Inhalt nach § 55 Abs. 2 RStV'
            : 'Responsible for content per § 55 Abs. 2 RStV'}
        </h2>
        <p className="text-slate-300 leading-relaxed">
          [TODO: Vor- und Nachname]<br />
          [TODO: Adresse]
        </p>
      </section>

      {/* --- Haftungsausschluss --- */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-2">
          {isDE ? 'Haftungsausschluss' : 'Disclaimer'}
        </h2>
        <p className="text-slate-400 text-sm leading-relaxed">
          {isDE
            ? 'Trotz sorgfältiger inhaltlicher Kontrolle übernehmen wir keine Haftung für die Inhalte externer Links. Für den Inhalt der verlinkten Seiten sind ausschließlich deren Betreiber verantwortlich.'
            : 'Despite careful content control, we assume no liability for the content of external links. The operators of the linked pages are solely responsible for their content.'}
        </p>
      </section>
    </div>
  )
}
