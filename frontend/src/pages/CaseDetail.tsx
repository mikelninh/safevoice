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
import CaseEditor from '../components/CaseEditor'
import CourtPrepPanel from '../components/CourtPrepPanel'

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
      <Link to="/cases" className="text-slate-500 hover:text-slate-300 text-sm inline-flex items-center gap-1 mb-6 transition-colors">
        ← {isDE ? 'Alle Fälle' : 'All cases'}
      </Link>

      {/* Header */}
      <header className="mb-10">
        <div className="flex items-start justify-between gap-3 mb-3">
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight leading-tight">{caseData.title}</h1>
          <SeverityBadge severity={caseData.overall_severity} lang={lang} />
        </div>

        {caseData.victim_context && (
          <p className="text-slate-400 text-sm leading-relaxed">
            {caseData.victim_context}
          </p>
        )}
      </header>

      {/* Schwerwiegender-Inhalt Banner — amber statt rot. Der vorige
          rote Block + "Polizei-Onlinewache →"-Button führte direkt
          auf eine tote polizei.de-Hubseite, die der Person nicht
          weiterhilft. Stattdessen: kein externer Link, sondern ein
          Hinweis nach unten zur Court-Prep-Karte (die jetzt der
          einzig richtige nächste Schritt ist) plus HateAid für
          menschliche Hilfe. */}
      {hasCritical && (
        <div className="bg-amber-950/30 border border-amber-800/50 rounded-xl p-5 mb-10">
          <div className="font-semibold text-amber-100 mb-2 flex items-center gap-2">
            <span className="text-amber-300 text-lg leading-none">!</span>
            {isDE ? 'Bitte zügig handeln' : 'Please act soon'}
          </div>
          <p className="text-amber-100/80 text-sm leading-relaxed">
            {isDE
              ? 'Ein Beleg in diesem Fall enthält eine konkrete Bedrohung. Unten findest du den Knopf "Anzeige-Paket vorbereiten" — das ist der schnellste Weg jetzt.'
              : 'One piece of evidence in this case contains a concrete threat. The "Prepare report package" button below is your fastest path now.'}
          </p>
          <p className="text-amber-100/60 text-xs leading-relaxed mt-3">
            {isDE ? 'Lieber zuerst mit jemandem sprechen? ' : 'Rather talk to someone first? '}
            <a
              href="https://hateaid.org"
              target="_blank"
              rel="noopener noreferrer"
              className="underline hover:text-amber-50"
            >
              HateAid
            </a>
            {isDE ? ' berät kostenlos.' : ' offers free counseling.'}
          </p>
        </div>
      )}

      {/* ── Act 1: Understanding ─────────────────────────────────────── */}
      <section className="mb-10">
        <h2 className="text-slate-300 text-sm font-medium mb-1">
          {isDE ? 'Was wir bisher sehen' : 'What we see so far'}
        </h2>
        <p className="text-slate-500 text-xs mb-4">
          {isDE
            ? 'Aktualisiert sich automatisch, wenn du Beweise hinzufügst.'
            : 'Updates automatically when you add evidence.'}
        </p>

        {/* Pattern flags as inline chips above the legal text */}
        {caseData.pattern_flags.length > 0 && (
          <div className="mb-4 space-y-2">
            {caseData.pattern_flags.map((flag, i) => (
              <PatternFlagCard key={i} flag={flag} lang={lang} />
            ))}
          </div>
        )}

        <div className="bg-slate-800/50 rounded-xl p-5 sm:p-6">
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
              <p className="text-slate-100 leading-relaxed">
                {isDE ? legalAnalysis.legal_assessment_de : legalAnalysis.legal_assessment_en}
              </p>

              <div className="grid sm:grid-cols-2 gap-3 pt-1">
                <div className="bg-slate-900/60 rounded-lg p-3">
                  <div className="text-slate-500 text-[11px] uppercase tracking-wider mb-1.5">
                    {isDE ? 'Eskalationsrisiko' : 'Escalation risk'}
                  </div>
                  <div className="text-slate-100 font-semibold text-sm mb-1">
                    {String(legalAnalysis.risk_assessment.escalation_risk).toUpperCase()}
                  </div>
                  <p className="text-slate-400 text-xs leading-relaxed">
                    {isDE ? legalAnalysis.risk_assessment.reason_de : legalAnalysis.risk_assessment.reason_en}
                  </p>
                </div>

                <div className="bg-slate-900/60 rounded-lg p-3">
                  <div className="text-slate-500 text-[11px] uppercase tracking-wider mb-1.5">
                    {isDE ? 'Stärkste Vorwürfe' : 'Strongest charges'}
                  </div>
                  <ul className="space-y-1">
                    {legalAnalysis.strongest_charges.slice(0, 3).map((charge, i) => (
                      <li key={i} className="text-xs text-slate-200">
                        <span className="font-semibold">{charge.paragraph}</span>{' '}
                        <span className="text-slate-500">({charge.strength})</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <details className="group">
                <summary className="cursor-pointer text-slate-400 text-xs hover:text-slate-200 list-none flex items-center gap-1.5">
                  <span className="transition-transform group-open:rotate-90">›</span>
                  {isDE ? 'Empfohlene Schritte anzeigen' : 'Show recommended steps'}
                </summary>
                <ul className="space-y-2 mt-3 pl-4 border-l border-slate-700">
                  {legalAnalysis.recommended_actions.slice(0, 4).map((action, i) => (
                    <li key={i} className="text-sm text-slate-200">
                      <span className="font-semibold text-slate-300">
                        {action.priority}
                        {action.deadline !== 'none' ? ` · ${action.deadline}` : ''}
                      </span>
                      <div className="text-slate-400 mt-0.5">
                        {isDE ? action.action_de : action.action_en}
                      </div>
                    </li>
                  ))}
                </ul>
              </details>

              {legalUpdatedAt && !legalLoading && (
                <p className="text-slate-600 text-[11px] pt-1">
                  {isDE ? 'Stand ' : 'As of '}
                  {legalUpdatedAt.toLocaleTimeString(isDE ? 'de-DE' : 'en-GB', { hour: '2-digit', minute: '2-digit' })}
                  {' · '}
                  <button
                    type="button"
                    onClick={() => caseData && refetchLegal(caseData)}
                    className="text-indigo-400 hover:text-indigo-300 underline-offset-2 hover:underline"
                  >
                    {isDE ? 'aktualisieren' : 'refresh'}
                  </button>
                </p>
              )}
            </div>
          )}
        </div>
      </section>

      {/* ── Act 2: Evidence ──────────────────────────────────────────── */}
      <section className="mb-10">
        <h2 className="text-slate-300 text-sm font-medium mb-1">
          {isDE
            ? `Deine Beweise (${caseData.evidence_items.length})`
            : `Your evidence (${caseData.evidence_items.length})`}
        </h2>
        <p className="text-slate-500 text-xs mb-4">
          {isDE
            ? 'Je mehr Belege du speicherst, desto stärker die Anzeige.'
            : 'The more evidence you save, the stronger the case.'}
        </p>

        <div className="space-y-3 mb-4">
          {caseData.evidence_items.map(ev => (
            <EvidenceCard key={ev.id} evidence={ev} caseId={caseData.id} lang={lang} />
          ))}
        </div>

        <CaseEditor caseData={caseData} lang={lang} onChange={setCaseData} />
      </section>

      {/* ── Act 3: Next step ─────────────────────────────────────────── */}
      <section className="mb-10">
        <h2 className="text-slate-300 text-sm font-medium mb-1">
          {isDE ? 'Dein nächster Schritt' : 'Your next step'}
        </h2>
        <p className="text-slate-500 text-xs mb-4">
          {isDE
            ? 'Wenn du bereit bist, bereiten wir alles für die Anzeige vor.'
            : "When you're ready, we'll prepare everything for the report."}
        </p>

        <CourtPrepPanel caseId={caseData.id} caseData={caseData} lang={lang} />

        {/* Quieter alternatives */}
        <div className="mt-4 space-y-3">
          <HateAidReferral
            lang={lang}
            severity={caseData.overall_severity}
            caseContext={caseData.victim_context}
          />

          <button
            onClick={() => setShowReport(true)}
            className="w-full text-xs text-slate-500 hover:text-slate-300 underline-offset-4 hover:underline py-2"
          >
            {isDE
              ? 'Lieber selbst zusammenstellen (ohne Agent)'
              : 'Prefer to assemble it yourself (without the agent)'}
          </button>
        </div>
      </section>

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
