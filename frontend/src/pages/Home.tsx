import { Link } from 'react-router-dom'
import { t, type Lang } from '../i18n'
import StatsBar from '../components/StatsBar'

interface Props { lang: Lang }

export default function Home({ lang }: Props) {
  const isDE = lang === 'de'

  return (
    <div className="min-h-screen">
      {/* Hero */}
      <section className="px-4 pt-12 pb-10 text-center max-w-2xl mx-auto">
        <div className="inline-flex items-center gap-2 bg-amber-900/40 border border-amber-700/60 rounded-full px-4 py-1.5 text-amber-200 text-sm mb-3">
          <span className="w-2 h-2 bg-amber-400 rounded-full animate-pulse"></span>
          {isDE
            ? 'Beta · Pilot mit NGO-Partnern · kein Produktivbetrieb'
            : 'Beta · NGO partner pilot · not yet production-ready'}
        </div>
        <div className="inline-flex items-center gap-2 bg-indigo-900/50 border border-indigo-700 rounded-full px-4 py-1.5 text-indigo-300 text-sm mb-6 ml-2">
          <span className="w-2 h-2 bg-indigo-400 rounded-full"></span>
          {isDE ? 'Für Deutschland · DSGVO-Ansatz · kostenlos' : 'For Germany · GDPR-by-design · free'}
        </div>
        <h1 className="text-4xl sm:text-5xl font-bold text-white mb-4 leading-tight">
          {t(lang, 'home.hero.title')}
        </h1>
        <p className="text-slate-300 text-lg mb-3 leading-relaxed">
          {t(lang, 'home.hero.subtitle')}
        </p>
        <p className="text-indigo-300 text-sm mb-8 italic">
          {isDE
            ? 'Was dir passiert ist, ist nicht okay. Du hast das Recht auf Gerechtigkeit.'
            : 'What happened to you is not okay. You have the right to justice.'}
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link to="/analyze" className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-8 py-4 rounded-xl transition-colors text-lg">
            {t(lang, 'home.hero.cta')}
          </Link>
          <Link to="/cases" className="bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold px-8 py-4 rounded-xl transition-colors text-lg border border-slate-700">
            {t(lang, 'home.hero.cases')}
          </Link>
        </div>
      </section>

      <StatsBar lang={lang} />

      {/* Steps */}
      <section className="px-4 py-12 max-w-3xl mx-auto">
        <h2 className="text-center text-slate-400 text-sm uppercase tracking-wider mb-8">
          {t(lang, 'home.steps.title')}
        </h2>
        <div className="grid sm:grid-cols-3 gap-4">
          {[1, 2, 3].map(step => (
            <div key={step} className="bg-slate-800 border border-slate-700 rounded-xl p-5">
              <div className="w-8 h-8 bg-indigo-900 border border-indigo-700 rounded-lg flex items-center justify-center text-indigo-400 font-bold text-sm mb-3">{step}</div>
              <h3 className="text-white font-semibold mb-1">{t(lang, `home.steps.${step}.title`)}</h3>
              <p className="text-slate-400 text-sm">{t(lang, `home.steps.${step}.desc`)}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Beta status — honest about what works and what doesn't yet */}
      <section className="px-4 pb-8 max-w-2xl mx-auto">
        <div className="bg-amber-950/30 border border-amber-800/50 rounded-xl p-5 text-sm">
          <p className="text-amber-200 font-semibold mb-2">
            {isDE ? '🧪 Was "Beta" hier bedeutet' : '🧪 What "beta" means here'}
          </p>
          <ul className="text-amber-100/80 space-y-1.5 list-disc list-outside ml-5">
            <li>
              {isDE
                ? 'Der Klassifikator arbeitet zuverlässig (47 reale Test-Cases bestanden), aber falsch-positive Ergebnisse sind möglich — bitte vor Versand selbst prüfen.'
                : 'The classifier is reliable (47 real-world tests passed), but false positives are possible — please review before sending.'}
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
                className="underline hover:text-amber-50"
              >
                GitHub
              </a>
              {isDE ? '. Feedback willkommen.' : '. Feedback welcome.'}
            </li>
          </ul>
        </div>
      </section>

      {/* Support banner */}
      <section className="px-4 pb-20 max-w-2xl mx-auto">
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <p className="text-white font-semibold mb-1">
                {isDE ? 'Brauchst du sofortige menschliche Unterstützung?' : 'Need immediate human support?'}
              </p>
              <p className="text-slate-400 text-sm">
                {isDE ? 'HateAid bietet kostenlose Beratung für Betroffene digitaler Gewalt.' : 'HateAid offers free counseling for victims of digital violence.'}
              </p>
            </div>
            <a href="https://hateaid.org" target="_blank" rel="noopener noreferrer"
              className="shrink-0 bg-indigo-700 hover:bg-indigo-600 text-white text-sm font-semibold px-5 py-2.5 rounded-lg transition-colors">
              HateAid →
            </a>
          </div>
        </div>
      </section>
    </div>
  )
}
