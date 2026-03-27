import { Link } from 'react-router-dom'
import { t, type Lang } from '../i18n'

interface Props { lang: Lang }

export default function Home({ lang }: Props) {
  const isDE = lang === 'de'

  return (
    <div className="min-h-screen">
      {/* Hero */}
      <section className="px-4 pt-16 pb-20 text-center max-w-2xl mx-auto">
        <div className="inline-flex items-center gap-2 bg-indigo-900/50 border border-indigo-700 rounded-full px-4 py-1.5 text-indigo-300 text-sm mb-6">
          <span className="w-2 h-2 bg-indigo-400 rounded-full animate-pulse"></span>
          {isDE ? 'Für Deutschland – DSGVO-konform' : 'For Germany – GDPR compliant'}
        </div>

        <h1 className="text-4xl sm:text-5xl font-bold text-white mb-4 leading-tight">
          {t(lang, 'home.hero.title')}
        </h1>

        <p className="text-slate-300 text-lg mb-8 leading-relaxed">
          {t(lang, 'home.hero.subtitle')}
        </p>

        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            to="/analyze"
            className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-8 py-4 rounded-xl transition-colors text-lg"
          >
            {t(lang, 'home.hero.cta')}
          </Link>
          <Link
            to="/cases"
            className="bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold px-8 py-4 rounded-xl transition-colors text-lg border border-slate-700"
          >
            {t(lang, 'home.hero.cases')}
          </Link>
        </div>
      </section>

      {/* Steps */}
      <section className="px-4 pb-16 max-w-3xl mx-auto">
        <h2 className="text-center text-slate-400 text-sm uppercase tracking-wider mb-8">
          {t(lang, 'home.steps.title')}
        </h2>
        <div className="grid sm:grid-cols-3 gap-4">
          {[1, 2, 3].map(step => (
            <div key={step} className="bg-slate-800 border border-slate-700 rounded-xl p-5">
              <div className="w-8 h-8 bg-indigo-900 border border-indigo-700 rounded-lg flex items-center justify-center text-indigo-400 font-bold text-sm mb-3">
                {step}
              </div>
              <h3 className="text-white font-semibold mb-1">
                {t(lang, `home.steps.${step}.title`)}
              </h3>
              <p className="text-slate-400 text-sm">
                {t(lang, `home.steps.${step}.desc`)}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Support banner */}
      <section className="px-4 pb-16 max-w-2xl mx-auto">
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 text-center">
          <p className="text-slate-300 text-sm mb-3">
            {isDE
              ? 'Brauchst du sofortige Unterstützung?'
              : 'Need immediate support?'}
          </p>
          <a
            href="https://hateaid.org"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 text-indigo-400 hover:text-indigo-300 font-semibold transition-colors"
          >
            HateAid – {isDE ? 'Kostenlose Beratung' : 'Free counseling'} →
          </a>
          <p className="text-slate-500 text-xs mt-3">
            {isDE
              ? 'HateAid ist eine gemeinnützige Organisation, die Betroffene digitaler Gewalt unterstützt.'
              : 'HateAid is a non-profit supporting victims of digital violence.'}
          </p>
        </div>
      </section>
    </div>
  )
}
