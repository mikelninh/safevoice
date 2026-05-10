import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ensureBackendCase, fetchCase, fetchLegalAnalysis } from '../services/api'
import { t, type Lang } from '../i18n'
import type { Case, LegalAnalysisPayload } from '../types'
import SeverityBadge from '../components/SeverityBadge'
import EvidenceCard from '../components/EvidenceCard'
import PatternFlagCard from '../components/PatternFlagCard'
import ReportModal from '../components/ReportModal'
import { getLocalCase, updateCaseBackendId } from '../services/storage'
import HateAidReferral from '../components/HateAidReferral'
import OnlinewachePanel from '../components/OnlinewachePanel'
import CaseEditor from '../components/CaseEditor'

interface Props { lang: Lang }

export default function CaseDetail({ lang }: Props) {
  const { id } = useParams<{ id: string }>()
  const [caseData, setCaseData] = useState<Case | null>(null)
  const [legalAnalysis, setLegalAnalysis] = useState<LegalAnalysisPayload | null>(null)
  const [legalLoading, setLegalLoading] = useState(false)
  const [legalError, setLegalError] = useState<string | null>(null)
  const [legalUpdatedAt, setLegalUpdatedAt] = useState<Date | null>(null)
  const [loading, setLoading] = useState(true)
  const [showReport, setShowReport] = useState(false)
  const isDE = lang === 'de'

  useEffect(() => {
    if (!id) return
    // Try local storage first, then API
    const local = getLocalCase(id)
    if (local) {
      setCaseData(local)
      setLoading(false)
      return
    }
    fetchCase(id)
      .then(setCaseData)
      .finally(() => setLoading(false))
  }, [id])

  // Extracted so the manual "Aktualisieren" button can call the same code path.
  const refetchLegal = (current: Case) => {
    setLegalLoading(true)
    setLegalError(null)

    const isLocal = current.id.startsWith('case-local-')

    const getBackendId = isLocal
      ? ensureBackendCase(current).then(backendId => {
          updateCaseBackendId(current.id, backendId)
          return backendId
        })
      : Promise.resolve(current.backend_id ?? current.id)

    // Retry once on 404: a stale local backend_id (e.g. from a prior deploy
    // whose DB is gone) can resolve to a phantom case. Force re-sync.
    const fetchWithRetry = (backendId: string) =>
      fetchLegalAnalysis(backendId).catch(async err => {
        const msg = err instanceof Error ? err.message : String(err)
        if (!msg.includes('404')) throw err
        const fresh = await ensureBackendCase({ ...current, backend_id: undefined })
        updateCaseBackendId(current.id, fresh)
        return fetchLegalAnalysis(fresh)
      })

    getBackendId
      .then(fetchWithRetry)
      .then(res => {
        setLegalAnalysis(res.analysis)
        setLegalUpdatedAt(new Date())
      })
      .catch(err => setLegalError(err instanceof Error ? err.message : 'Legal analysis unavailable'))
      .finally(() => setLegalLoading(false))
  }

  useEffect(() => {
    if (!caseData) return
    refetchLegal(caseData)
    // Re-run when evidence count or context changes — exactly the inputs
    // the server-side legal AI builds its assessment from.
  }, [caseData?.id, caseData?.evidence_items.length, caseData?.victim_context])

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center text-slate-400">
        {isDE ? 'Fall wird geladen…' : 'Loading case…'}
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
    <div className="max-w-2xl mx-auto px-4 py-10">
      {/* Back nav */}
      <Link to="/cases" className="text-slate-400 hover:text-slate-200 text-sm inline-flex items-center gap-1 mb-8 transition-colors">
        ← {isDE ? 'Alle Fälle' : 'All cases'}
      </Link>

      {/* Header */}
      <div className="mb-8">
        <div className="flex items-start justify-between gap-3 mb-4">
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight leading-tight">{caseData.title}</h1>
          <SeverityBadge severity={caseData.overall_severity} lang={lang} />
        </div>

        {caseData.victim_context && (
          <div className="bg-slate-800/60 rounded-lg p-4">
            <span className="text-slate-500 text-xs uppercase tracking-wider block mb-1.5">
              {isDE ? 'Kontext' : 'Context'}
            </span>
            <p className="text-slate-300 text-sm leading-relaxed">{caseData.victim_context}</p>
          </div>
        )}
      </div>

      {/* Immediate action banner */}
      {hasCritical && (
        <div className="bg-red-950/60 border border-red-800 rounded-xl p-5 mb-6">
          <div className="font-semibold text-red-100 mb-3 flex items-center gap-2">
            <span className="text-red-400 text-lg leading-none">⚠</span>
            {isDE ? 'Sofortiger Handlungsbedarf in diesem Fall' : 'Immediate action required in this case'}
          </div>
          <div className="flex flex-col sm:flex-row gap-2">
            <a
              href="https://www.polizei.de/Polizei/DE/Einrichtungen/onlinewache_node.html"
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

      {/* Legal AI summary */}
      <div className="mb-6 bg-slate-800/60 rounded-xl p-5 sm:p-6">
        <div className="flex items-start justify-between gap-3 mb-4 flex-wrap">
          <div className="flex-1 min-w-0">
            <h2 className="text-slate-400 text-xs uppercase tracking-wider mb-1.5">
              {isDE ? 'Juristische Gesamteinschätzung' : 'Legal case assessment'}
            </h2>
            <p className="text-slate-500 text-sm leading-relaxed">
              {isDE
                ? 'Alle Belege + Kontext werden zu einer Fallanalyse mit Risiken und nächsten Schritten zusammengeführt. Aktualisiert sich automatisch, wenn du Beweise hinzufügst oder den Kontext änderst.'
                : 'All evidence + context is consolidated into one case-level assessment with risks and next steps. Auto-refreshes when you add evidence or edit the context.'}
            </p>
            {legalUpdatedAt && !legalLoading && (
              <p className="text-slate-600 text-xs mt-2">
                {isDE ? 'Stand: ' : 'Last updated: '}
                {legalUpdatedAt.toLocaleTimeString(isDE ? 'de-DE' : 'en-GB', { hour: '2-digit', minute: '2-digit' })}
                {' · '}
                <button
                  type="button"
                  onClick={() => caseData && refetchLegal(caseData)}
                  className="text-indigo-300 hover:text-indigo-200 underline-offset-2 hover:underline"
                >
                  {isDE ? '↻ Jetzt aktualisieren' : '↻ Refresh now'}
                </button>
              </p>
            )}
          </div>
        </div>

        {legalLoading && (
          <p className="text-slate-400 text-sm">
            {legalAnalysis
              ? (isDE ? 'Wird mit neuen Belegen aktualisiert…' : 'Refreshing with new evidence…')
              : (isDE ? 'Analyse wird geladen…' : 'Loading legal analysis…')}
          </p>
        )}

        {!legalLoading && legalError && (
          <p className="text-amber-300 text-sm">{legalError}</p>
        )}

        {!legalLoading && legalAnalysis && (
          <div className="space-y-4">
            <div className="text-slate-100 leading-relaxed">
              {isDE ? legalAnalysis.legal_assessment_de : legalAnalysis.legal_assessment_en}
            </div>

            <div className="grid sm:grid-cols-2 gap-3">
              <div className="bg-slate-900/70 rounded-lg p-4">
                <div className="text-slate-400 text-xs uppercase tracking-wider mb-2">
                  {isDE ? 'Eskalationsrisiko' : 'Escalation risk'}
                </div>
                <div className="text-white font-semibold mb-1">
                  {String(legalAnalysis.risk_assessment.escalation_risk).toUpperCase()}
                </div>
                <div className="text-slate-300 text-sm">
                  {isDE ? legalAnalysis.risk_assessment.reason_de : legalAnalysis.risk_assessment.reason_en}
                </div>
              </div>

              <div className="bg-slate-900/70 rounded-lg p-4">
                <div className="text-slate-400 text-xs uppercase tracking-wider mb-2">
                  {isDE ? 'Stärkste Vorwürfe' : 'Strongest charges'}
                </div>
                <ul className="space-y-2">
                  {legalAnalysis.strongest_charges.slice(0, 3).map((charge, i) => (
                    <li key={i} className="text-sm text-slate-200">
                      <span className="font-semibold">{charge.paragraph}</span>{' '}
                      <span className="text-slate-400">({charge.strength})</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            <div className="bg-slate-800 rounded-lg p-3 border border-slate-700">
              <div className="text-slate-400 text-xs uppercase tracking-wider mb-2">
                {isDE ? 'Empfohlene nächste Schritte' : 'Recommended next steps'}
              </div>
              <ul className="space-y-2">
                {legalAnalysis.recommended_actions.slice(0, 4).map((action, i) => (
                  <li key={i} className="text-sm text-slate-200">
                    <span className="font-semibold">
                      {action.priority}
                      {action.deadline !== 'none' ? ` · ${action.deadline}` : ''}
                    </span>
                    <div className="text-slate-300 mt-0.5">
                      {isDE ? action.action_de : action.action_en}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>

      {/* Evidence */}
      <div className="mb-6">
        <h2 className="text-slate-400 text-xs uppercase tracking-wider mb-3">
          {caseData.evidence_items.length} {t(lang, 'cases.evidence')}
        </h2>
        <div className="space-y-3">
          {caseData.evidence_items.map(ev => (
            <EvidenceCard key={ev.id} evidence={ev} caseId={caseData.id} lang={lang} />
          ))}
        </div>
      </div>

      {/* Edit / add evidence */}
      <div className="mb-6">
        <CaseEditor caseData={caseData} lang={lang} onChange={setCaseData} />
      </div>

      {/* HateAid referral */}
      <div className="mb-6">
        <HateAidReferral
          lang={lang}
          severity={caseData.overall_severity}
          caseContext={caseData.victim_context}
        />
      </div>

      {/* Onlinewache */}
      <div className="mb-6">
        <OnlinewachePanel
          lang={lang}
          reportText={_buildPoliceText(caseData, isDE)}
        />
      </div>

      {/* Export report */}
      <button
        onClick={() => setShowReport(true)}
        className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-4 rounded-xl transition-colors text-base shadow-lg shadow-indigo-900/30"
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

function _buildPoliceText(caseData: Case, isDE: boolean): string {
  const lines: string[] = []

  if (isDE) {
    lines.push('STRAFANZEIGE — Digitale Belästigung / Bedrohung')
    lines.push('')
    lines.push(`Fall-ID: ${caseData.id}`)
    lines.push(`Schweregrad: ${caseData.overall_severity.toUpperCase()}`)
    lines.push(`Belege: ${caseData.evidence_items.length}`)
    lines.push('')
    if (caseData.victim_context) {
      lines.push(`Kontext: ${caseData.victim_context}`)
      lines.push('')
    }
    lines.push('--- Vorfälle ---')
    for (const ev of caseData.evidence_items) {
      lines.push('')
      lines.push(`Datum: ${new Date(ev.captured_at).toLocaleString('de-DE')}`)
      lines.push(`Plattform: ${ev.platform}`)
      lines.push(`Verfasser:in: @${ev.author_username}`)
      lines.push(`Inhalt: "${ev.content_text}"`)
      lines.push(`URL: ${ev.url}`)
      lines.push(`Prüfsumme: ${ev.content_hash}`)
      if (ev.classification) {
        lines.push(`Einordnung: ${ev.classification.severity} — ${ev.classification.categories.join(', ')}`)
        lines.push(`Gesetze: ${ev.classification.applicable_laws.map(l => l.paragraph).join(', ')}`)
      }
    }
    lines.push('')
    lines.push('--- Generiert von SafeVoice (safevoice.org) ---')
  } else {
    lines.push('CRIMINAL COMPLAINT — Digital Harassment / Threats')
    lines.push('')
    lines.push(`Case ID: ${caseData.id}`)
    lines.push(`Severity: ${caseData.overall_severity.toUpperCase()}`)
    lines.push(`Evidence items: ${caseData.evidence_items.length}`)
    lines.push('')
    if (caseData.victim_context) {
      lines.push(`Context: ${caseData.victim_context}`)
      lines.push('')
    }
    lines.push('--- Incidents ---')
    for (const ev of caseData.evidence_items) {
      lines.push('')
      lines.push(`Date: ${new Date(ev.captured_at).toLocaleString('en-GB')}`)
      lines.push(`Platform: ${ev.platform}`)
      lines.push(`Author: @${ev.author_username}`)
      lines.push(`Content: "${ev.content_text}"`)
      lines.push(`URL: ${ev.url}`)
      lines.push(`Hash: ${ev.content_hash}`)
      if (ev.classification) {
        lines.push(`Classification: ${ev.classification.severity} — ${ev.classification.categories.join(', ')}`)
        lines.push(`Laws: ${ev.classification.applicable_laws.map(l => l.paragraph).join(', ')}`)
      }
    }
    lines.push('')
    lines.push('--- Generated by SafeVoice (safevoice.org) ---')
  }

  return lines.join('\n')
}
