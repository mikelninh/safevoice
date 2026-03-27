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
        <div className="inline-flex items-center gap-2 bg-indigo-900/50 border border-indigo-700 rounded-full px-4 py-1.5 text-indigo-300 text-sm mb-6">
          <span className="w-2 h-2 bg-indigo-400 rounded-full animate-pulse"></span>
          {isDE ? 'Für Deutschland – DSGVO-konform – kostenlos' : 'For Germany – GDPR compliant – free'}
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

      {/* Coverage grid */}
      <section className="px-4 pb-12 max-w-2xl mx-auto">
        <h2 className="text-center text-slate-400 text-sm uppercase tracking-wider mb-6">
          {isDE ? 'Was wir abdecken' : 'What we cover'}
        </h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {[
            { icon: '🚨', de: 'Drohungen & Todesdrohungen', en: 'Threats & death threats' },
            { icon: '♀️', de: 'Frauenfeindlichkeit', en: 'Misogyny & gender hate' },
            { icon: '💬', de: 'Belästigung & Beleidigung', en: 'Harassment & insults' },
            { icon: '📸', de: 'Sexuelle Belästigung', en: 'Sexual harassment' },
            { icon: '💸', de: 'Betrug & Scams', en: 'Fraud & scams' },
            { icon: '🎭', de: 'Identitätsmissbrauch', en: 'Impersonation' },
          ].map((item, i) => (
            <div key={i} className="bg-slate-800 border border-slate-700 rounded-lg p-3 text-center">
              <div className="text-2xl mb-1">{item.icon}</div>
              <p className="text-slate-300 text-xs">{isDE ? item.de : item.en}</p>
            </div>
          ))}
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
