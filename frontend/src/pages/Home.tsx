import { Link } from 'react-router-dom'
import { t, type Lang } from '../i18n'
import StatsBar from '../components/StatsBar'

interface Props { lang: Lang }

export default function Home({ lang }: Props) {
  const isDE = lang === 'de'

  return (
    <div className="min-h-screen">
      {/* Hero — single focus: headline + subline + one primary CTA.
          The warm "Was dir passiert ist…" line was previously echoed
          here too; it already lives in the top mood-bar so we removed
          the duplicate so the page can breathe. */}
      <section className="px-4 pt-16 pb-12 text-center max-w-2xl mx-auto">
        <div className="inline-flex items-center gap-2 bg-amber-900/30 border border-amber-800/50 rounded-full px-3 py-1 text-amber-200/90 text-xs mb-8">
          <span className="w-1.5 h-1.5 bg-amber-400 rounded-full animate-pulse"></span>
          {isDE ? 'Beta · kostenlos · anonym' : 'Beta · free · anonymous'}
        </div>
        <h1 className="text-4xl sm:text-5xl font-bold text-white mb-5 leading-[1.15] tracking-tight">
          {t(lang, 'home.hero.title')}
        </h1>
        <p className="text-slate-300 text-lg mb-10 leading-relaxed">
          {t(lang, 'home.hero.subtitle')}
        </p>
        <div className="flex flex-col items-center gap-3">
          <Link to="/analyze" className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-8 py-3.5 rounded-xl transition-colors text-base shadow-lg shadow-indigo-900/30">
            {t(lang, 'home.hero.cta')}
          </Link>
          {/* Quieter secondary — a thin breadcrumb instead of the
              previous 3-card-step section, and a link to existing cases. */}
          <p className="text-slate-500 text-xs">
            {isDE
              ? 'Text einfügen · prüfen · speichern'
              : 'Paste text · review · save'}
          </p>
          <Link to="/cases" className="text-slate-400 hover:text-slate-200 text-sm underline-offset-4 hover:underline">
            {t(lang, 'home.hero.cases')}
          </Link>
        </div>
      </section>

      <StatsBar lang={lang} />

      {/* Support card — kept as the final block because human support
          is the safety net the user must always be able to reach. */}
      <section className="px-4 pt-14 pb-10 max-w-2xl mx-auto">
        <div className="bg-slate-800/60 rounded-xl p-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <p className="text-white font-semibold mb-1">
                {isDE ? 'Lieber mit einem Menschen sprechen?' : 'Prefer to talk to a person?'}
              </p>
              <p className="text-slate-400 text-sm leading-relaxed">
                {isDE ? 'HateAid bietet kostenlose Beratung für Betroffene digitaler Gewalt.' : 'HateAid offers free counseling for victims of digital violence.'}
              </p>
            </div>
            <a href="https://hateaid.org" target="_blank" rel="noopener noreferrer"
              className="shrink-0 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold px-5 py-2.5 rounded-lg transition-colors">
              HateAid →
            </a>
          </div>
        </div>
      </section>

      {/* Beta details — collapsible. The previous prominent amber box
          was splitting attention with the HateAid card; the info still
          matters but only when someone actively wants it. */}
      <section className="px-4 pb-20 max-w-2xl mx-auto">
        <details className="group text-sm">
          <summary className="cursor-pointer inline-flex items-center gap-1.5 text-slate-400 hover:text-slate-200">
            <span className="inline-block transition-transform group-open:rotate-90">›</span>
            {isDE ? 'Was „Beta" hier bedeutet' : 'What "beta" means here'}
          </summary>
          <ul className="mt-3 text-slate-400 space-y-2 list-disc list-outside ml-7 leading-relaxed">
            <li>
              {isDE
                ? 'Die Analyse ist getestet, kann aber daneben liegen — bitte vor dem Versand kurz selbst prüfen.'
                : 'The analysis is tested but can be off — please review briefly before sending.'}
            </li>
            <li>
              {isDE
                ? 'Datenschutzerklärung und Impressum sind Vorabversionen, noch nicht anwaltlich geprüft.'
                : 'Privacy policy and imprint are drafts, not yet reviewed by a lawyer.'}
            </li>
            <li>
              {isDE
                ? 'Wir suchen NGO-Partner (z. B. HateAid) für die produktive Trägerschaft. Bis dahin bitte keine sensiblen Massendaten hochladen.'
                : 'We are looking for an NGO partner (e.g. HateAid) to formally host the service. Until then please do not upload sensitive data at scale.'}
            </li>
            <li>
              {isDE
                ? 'Open Source — Quellcode auf '
                : 'Open source — source code on '}
              <a
                href="https://github.com/mikelninh/safevoice"
                target="_blank"
                rel="noopener noreferrer"
                className="underline hover:text-slate-200"
              >
                GitHub
              </a>
              {isDE ? '. Feedback willkommen.' : '. Feedback welcome.'}
            </li>
          </ul>
        </details>
      </section>
    </div>
  )
}
