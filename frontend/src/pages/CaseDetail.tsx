import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { fetchCase } from '../services/api'
import { t, type Lang } from '../i18n'
import type { Case } from '../types'
import SeverityBadge from '../components/SeverityBadge'
import EvidenceCard from '../components/EvidenceCard'
import PatternFlagCard from '../components/PatternFlagCard'
import ReportModal from '../components/ReportModal'

interface Props { lang: Lang }

export default function CaseDetail({ lang }: Props) {
  const { id } = useParams<{ id: string }>()
  const [caseData, setCaseData] = useState<Case | null>(null)
  const [loading, setLoading] = useState(true)
  const [showReport, setShowReport] = useState(false)
  const isDE = lang === 'de'

  useEffect(() => {
    if (!id) return
    fetchCase(id)
      .then(setCaseData)
      .finally(() => setLoading(false))
  }, [id])

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center text-slate-400">
        {isDE ? 'Wird geladen...' : 'Loading...'}
      </div>
    )
  }

  if (!caseData) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <p className="text-slate-400 mb-4">{isDE ? 'Fall nicht gefunden.' : 'Case not found.'}</p>
        <Link to="/cases" className="text-indigo-400 hover:underline">
          {isDE ? '← Zurück zu Fällen' : '← Back to cases'}
        </Link>
      </div>
    )
  }

  const hasCritical = caseData.evidence_items.some(
    e => e.classification?.requires_immediate_action
  )

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      {/* Back nav */}
      <Link to="/cases" className="text-slate-400 hover:text-slate-200 text-sm flex items-center gap-1 mb-6 transition-colors">
        ← {isDE ? 'Alle Fälle' : 'All cases'}
      </Link>

      {/* Header */}
      <div className="mb-6">
        <div className="flex items-start justify-between gap-3 mb-3">
          <h1 className="text-2xl font-bold text-white">{caseData.title}</h1>
          <SeverityBadge severity={caseData.overall_severity} lang={lang} />
        </div>

        {caseData.victim_context && (
          <p className="text-slate-400 text-sm bg-slate-800 border border-slate-700 rounded-lg p-3">
            <span className="text-slate-500 text-xs uppercase tracking-wider block mb-1">
              {isDE ? 'Kontext' : 'Context'}
            </span>
            {caseData.victim_context}
          </p>
        )}
      </div>

      {/* Immediate action banner */}
      {hasCritical && (
        <div className="bg-red-900 border border-red-600 rounded-xl p-4 mb-6">
          <div className="font-bold text-red-200 mb-2">
            ⚠ {isDE ? 'Sofortiger Handlungsbedarf in diesem Fall' : 'Immediate action required in this case'}
          </div>
          <div className="flex flex-col sm:flex-row gap-2">
            <a
              href="https://www.onlinewache.polizei.de"
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 text-center bg-red-700 hover:bg-red-600 text-white text-sm font-semibold py-2.5 rounded-lg transition-colors"
            >
              {t(lang, 'action.polizei')} →
            </a>
            <a
              href="https://hateaid.org"
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 text-center bg-slate-700 hover:bg-slate-600 text-slate-200 text-sm font-semibold py-2.5 rounded-lg transition-colors"
            >
              {t(lang, 'action.hateaid')} →
            </a>
          </div>
        </div>
      )}

      {/* Pattern flags */}
      {caseData.pattern_flags.length > 0 && (
        <div className="mb-6">
          <h2 className="text-slate-400 text-xs uppercase tracking-wider mb-3">
            ⚑ {t(lang, 'cases.patterns')}
          </h2>
          <div className="space-y-2">
            {caseData.pattern_flags.map((flag, i) => (
              <PatternFlagCard key={i} flag={flag} lang={lang} />
            ))}
          </div>
        </div>
      )}

      {/* Evidence */}
      <div className="mb-6">
        <h2 className="text-slate-400 text-xs uppercase tracking-wider mb-3">
          {caseData.evidence_items.length} {t(lang, 'cases.evidence')}
        </h2>
        <div className="space-y-3">
          {caseData.evidence_items.map(ev => (
            <EvidenceCard key={ev.id} evidence={ev} lang={lang} />
          ))}
        </div>
      </div>

      {/* Export report */}
      <button
        onClick={() => setShowReport(true)}
        className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-4 rounded-xl transition-colors text-lg"
      >
        {t(lang, 'cases.report')} →
      </button>

      {showReport && (
        <ReportModal
          caseId={caseData.id}
          lang={lang}
          onClose={() => setShowReport(false)}
        />
      )}
    </div>
  )
}
