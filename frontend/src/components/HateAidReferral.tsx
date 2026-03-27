/**
 * HateAidReferral — warm handoff to HateAid counseling.
 * Shows when case severity is HIGH or CRITICAL.
 * Provides context-aware link with pre-filled information.
 */
import type { Lang } from '../i18n'
import type { Severity } from '../types'

interface Props {
  lang: Lang
  severity: Severity
  caseContext?: string
}

export default function HateAidReferral({ lang, severity, caseContext }: Props) {
  if (severity !== 'high' && severity !== 'critical') return null

  const isDE = lang === 'de'

  return (
    <div className="bg-indigo-950 border border-indigo-800 rounded-xl p-5">
      <div className="flex items-start gap-3">
        <div className="w-10 h-10 bg-indigo-800 rounded-lg flex items-center justify-center shrink-0 text-lg">
          <span role="img" aria-label="support">💙</span>
        </div>
        <div className="flex-1">
          <h3 className="text-white font-semibold mb-1">
            {isDE
              ? 'Du musst das nicht alleine durchstehen'
              : 'You don\'t have to go through this alone'}
          </h3>
          <p className="text-indigo-200 text-sm mb-3 leading-relaxed">
            {isDE
              ? 'HateAid bietet kostenlose Beratung und rechtliche Unterstützung für Betroffene digitaler Gewalt. Sie können dir helfen, die nächsten Schritte zu gehen.'
              : 'HateAid provides free counseling and legal support for victims of digital violence. They can help you take the next steps.'}
          </p>

          <div className="flex flex-col sm:flex-row gap-2">
            <a
              href="https://hateaid.org/betroffene/"
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 text-center bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold py-2.5 rounded-lg transition-colors"
            >
              {isDE ? 'HateAid kontaktieren' : 'Contact HateAid'} →
            </a>
            <a
              href="tel:+493025295321"
              className="flex-1 text-center bg-slate-700 hover:bg-slate-600 text-slate-200 text-sm font-semibold py-2.5 rounded-lg transition-colors"
            >
              {isDE ? 'Hotline: 030 252 953 21' : 'Hotline: +49 30 252 953 21'}
            </a>
          </div>

          <p className="text-indigo-400 text-xs mt-3">
            {isDE
              ? 'Kostenlos · Vertraulich · Mo-Fr 10-18 Uhr'
              : 'Free · Confidential · Mon-Fri 10am-6pm CET'}
          </p>
        </div>
      </div>
    </div>
  )
}
