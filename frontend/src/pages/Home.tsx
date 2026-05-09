import { Link } from 'react-router-dom'
import { t, type Lang } from '../i18n'
import StatsBar from '../components/StatsBar'

interface Props { lang: Lang }

export default function Home({ lang }: Props) {
  const isDE = lang === 'de'

  return (
    <div className="min-h-screen">
      {/* Hero */}
      <section className="px-4 pt-16 pb-12 text-center max-w-2xl mx-auto">
        <div className="inline-flex items-center gap-2 bg-amber-900/30 border border-amber-800/50 rounded-full px-3 py-1 text-amber-200/90 text-xs mb-8">
          <span className="w-1.5 h-1.5 bg-amber-400 rounded-full animate-pulse"></span>
          {isDE
            ? 'Beta · NGO-Pilot · DSGVO-konform · kostenlos'
            : 'Beta · NGO pilot · GDPR-compliant · free'}
        </div>
        <h1 className="text-4xl sm:text-5xl font-bold text-white mb-5 leading-[1.15] tracking-tight">
          {t(lang, 'home.hero.title')}
        </h1>
        <p className="text-slate-300 text-lg mb-4 leading-relaxed">
          {t(lang, 'home.hero.subtitle')}
        </p>
        <p className="text-indigo-300/90 text-sm mb-10">
          {isDE
            ? 'Was dir passiert ist, ist nicht okay. Du hast das Recht, etwas dagegen zu tun.'
            : 'What happened to you is not okay. You have the right to do something about it.'}
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link to="/analyze" className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-8 py-3.5 rounded-xl transition-colors text-base shadow-lg shadow-indigo-900/30">
            {t(lang, 'home.hero.cta')}
          </Link>
          <Link to="/cases" className="text-slate-300 hover:text-white font-medium px-8 py-3.5 rounded-xl transition-colors text-base">
            {t(lang, 'home.hero.cases')}
          </Link>
        </div>
      </section>

      <StatsBar lang={lang} />

      {/* Steps */}
      <section className="px-4 py-14 max-w-3xl mx-auto">
        <h2 className="text-center text-slate-500 text-xs uppercase tracking-[0.15em] mb-10">
          {t(lang, 'home.steps.title')}
        </h2>
        <div className="grid sm:grid-cols-3 gap-5">
          {[1, 2, 3].map(step => (
            <div key={step} className="bg-slate-800/60 rounded-xl p-5">
              <div className="w-7 h-7 bg-indigo-900/60 rounded-lg flex items-center justify-center text-indigo-300 font-semibold text-sm mb-3">{step}</div>
              <h3 className="text-white font-semibold mb-1.5">{t(lang, `home.steps.${step}.title`)}</h3>
              <p className="text-slate-400 text-sm leading-relaxed">{t(lang, `home.steps.${step}.desc`)}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Beta status — honest about what works and what doesn't yet */}
      <section className="px-4 pb-10 max-w-2xl mx-auto">
        <div className="bg-amber-950/20 border border-amber-900/40 rounded-xl p-5 text-sm">
          <p className="text-amber-200 font-semibold mb-3">
            {isDE ? 'Was „Beta" hier bedeutet' : 'What "beta" means here'}
          </p>
          <ul className="text-amber-100/75 space-y-2 list-disc list-outside ml-5 leading-relaxed">
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
        <div className="bg-slate-800/60 rounded-xl p-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div>
              <p className="text-white font-semibold mb-1">
                {isDE ? 'Brauchst du sofortige menschliche Unterstützung?' : 'Need immediate human support?'}
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
    </div>
  )
}
