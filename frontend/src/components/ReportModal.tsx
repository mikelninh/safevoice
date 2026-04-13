import { useState, useEffect } from 'react'
import { fetchReport, downloadPdf, ensureBackendCase, resetServiceWorkerAndCaches } from '../services/api'
import { t, type Lang } from '../i18n'
import { getLocalCase, setBackendId } from '../services/storage'
import SendReport from './SendReport'

interface Props {
  caseId: string  // local case ID (localStorage) OR backend ID
  lang: Lang
  onClose: () => void
}

type ReportType = 'general' | 'netzdg' | 'police'

/**
 * Resolve the frontend case ID to a backend case ID.
 *
 * Cases are created in localStorage first (privacy-first MVP design). The
 * backend's report/PDF endpoints need the case to exist server-side. This
 * does that sync lazily on first report-request.
 */
async function resolveBackendCaseId(caseId: string): Promise<string> {
  const localCase = getLocalCase(caseId)
  if (!localCase) {
    // Might already be a backend ID (e.g. deep link from backend-created case)
    return caseId
  }
  const backendId = await ensureBackendCase(localCase)
  if (backendId !== localCase.backend_id) {
    setBackendId(caseId, backendId)
  }
  return backendId
}

export default function ReportModal({ caseId, lang, onClose }: Props) {
  const [reportType, setReportType] = useState<ReportType>('netzdg')
  const [report, setReport] = useState<Record<string, unknown> | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [downloadError, setDownloadError] = useState<string | null>(null)
  const [backendId, setResolvedBackendId] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const isDE = lang === 'de'

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    setReport(null)

    // Step 1: ensure case exists on backend, then fetch the report.
    resolveBackendCaseId(caseId)
      .then(async (resolvedId) => {
        if (cancelled) return
        setResolvedBackendId(resolvedId)
        const r = await fetchReport(resolvedId, reportType, lang)
        if (!cancelled) setReport(r)
      })
      .catch((e: Error) => {
        if (cancelled) return
        console.error('[ReportModal] fetch failed:', e)
        setError(e?.message ?? 'Unknown error')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [caseId, reportType, lang])

  const handleDownload = async () => {
    setDownloadError(null)
    try {
      const resolved = backendId ?? (await resolveBackendCaseId(caseId))
      if (!backendId) setResolvedBackendId(resolved)
      await downloadPdf(resolved, reportType, lang)
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e)
      console.error('[ReportModal] downloadPdf failed:', e)
      setDownloadError(msg)
    }
  }

  const handleCopy = () => {
    if (!report) return
    const body = (report.body as string) ?? JSON.stringify(report, null, 2)
    navigator.clipboard.writeText(body)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const [mode, setMode] = useState<'preview' | 'send'>('preview')

  const tabs: { key: ReportType; label: string }[] = [
    { key: 'netzdg', label: t(lang, 'report.netzdg') },
    { key: 'police', label: t(lang, 'report.police') },
    { key: 'general', label: t(lang, 'report.general') },
  ]

  return (
    <div className="fixed inset-0 bg-black/80 flex items-end sm:items-center justify-center z-50 p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-700">
          <h2 className="text-white font-bold">
            {mode === 'send'
              ? isDE ? 'Anzeige einreichen' : 'Submit complaint'
              : isDE ? 'Bericht exportieren' : 'Export report'}
          </h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white text-xl leading-none"
          >
            ×
          </button>
        </div>

        {/* Mode switcher: Vorschau vs Senden */}
        <div className="flex border-b border-slate-700 bg-slate-950/50">
          <button
            onClick={() => setMode('preview')}
            className={`flex-1 py-2.5 text-xs font-semibold uppercase tracking-wider transition-colors ${
              mode === 'preview'
                ? 'text-white bg-slate-800'
                : 'text-slate-500 hover:text-slate-300'
            }`}
          >
            {isDE ? 'Vorschau' : 'Preview'}
          </button>
          <button
            onClick={() => setMode('send')}
            disabled={!report}
            className={`flex-1 py-2.5 text-xs font-semibold uppercase tracking-wider transition-colors disabled:opacity-40 ${
              mode === 'send'
                ? 'text-white bg-indigo-600'
                : 'text-slate-500 hover:text-slate-300'
            }`}
          >
            {isDE ? '📧 Senden' : '📧 Send'}
          </button>
        </div>

        {/* Report type tabs — only in preview mode */}
        {mode === 'preview' && (
          <div className="flex border-b border-slate-700">
            {tabs.map(tab => (
              <button
                key={tab.key}
                onClick={() => setReportType(tab.key)}
                className={`flex-1 py-3 text-sm font-medium transition-colors ${
                  reportType === tab.key
                    ? 'text-indigo-400 border-b-2 border-indigo-500'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {mode === 'send' && report && backendId ? (
            <SendReport
              caseId={backendId}
              reportBody={(report.body as string) ?? null}
              reportSubject={(report.subject as string) ?? null}
              lang={lang}
              onDownloadPdf={handleDownload}
            />
          ) : loading ? (
            <div className="text-slate-400 text-center py-12">
              {isDE ? 'Bericht wird generiert...' : 'Generating report...'}
            </div>
          ) : error ? (
            <div className="bg-red-900/40 border border-red-800 text-red-200 rounded-lg p-4 text-sm">
              <div className="font-semibold mb-2">
                {isDE ? 'Bericht konnte nicht geladen werden' : 'Report could not be loaded'}
              </div>
              <div className="text-xs font-mono opacity-80 mb-3 p-2 bg-black/30 rounded break-all">
                {error}
              </div>
              <div className="flex gap-2 flex-wrap">
                <button
                  onClick={async () => {
                    await resetServiceWorkerAndCaches()
                    window.location.reload()
                  }}
                  className="text-xs bg-red-700 hover:bg-red-600 text-white px-3 py-1.5 rounded"
                >
                  {isDE ? 'Service Worker zurücksetzen & neu laden' : 'Reset Service Worker & reload'}
                </button>
                <button
                  onClick={() => window.location.reload()}
                  className="text-xs bg-slate-700 hover:bg-slate-600 text-slate-200 px-3 py-1.5 rounded"
                >
                  {isDE ? 'Seite neu laden' : 'Reload page'}
                </button>
              </div>
              <div className="text-xs mt-3 opacity-60">
                {isDE
                  ? 'Tipp: Wenn Fehler persistiert, öffne DevTools (Cmd+Opt+I), Tab "Application" → "Service Workers" → "Unregister".'
                  : 'Tip: If error persists, open DevTools, Application tab → Service Workers → Unregister.'}
              </div>
            </div>
          ) : report ? (
            <div className="space-y-4">
              {!!report.subject && (
                <div>
                  <div className="text-xs text-slate-500 uppercase tracking-wider mb-1">
                    {isDE ? 'Betreff' : 'Subject'}
                  </div>
                  <div className="text-slate-200 font-medium text-sm">{report.subject as string}</div>
                </div>
              )}

              {!!report.body && (
                <div>
                  <div className="text-xs text-slate-500 uppercase tracking-wider mb-1">
                    {isDE ? 'Inhalt' : 'Content'}
                  </div>
                  <pre className="bg-slate-800 rounded-lg p-4 text-slate-300 text-xs whitespace-pre-wrap font-mono overflow-x-auto">
                    {report.body as string}
                  </pre>
                </div>
              )}

              {!!report.recommended_actions && (
                <div>
                  <div className="text-xs text-slate-500 uppercase tracking-wider mb-2">
                    {isDE ? 'Empfohlene Maßnahmen' : 'Recommended actions'}
                  </div>
                  <ul className="space-y-2">
                    {(report.recommended_actions as string[]).map((action, i) => (
                      <li key={i} className={`flex items-start gap-2 text-sm rounded-lg px-3 py-2 ${
                        action.startsWith('SOFORT') || action.startsWith('IMMEDIATELY')
                          ? 'bg-red-900/40 text-red-200 border border-red-800'
                          : 'bg-slate-800 text-slate-300'
                      }`}>
                        <span className="mt-0.5 shrink-0">→</span>
                        <span>{action}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {!!report.what_to_bring && (
                <div>
                  <div className="text-xs text-slate-500 uppercase tracking-wider mb-2">
                    {isDE ? 'Was Sie mitbringen sollten' : 'What to bring'}
                  </div>
                  <ul className="space-y-1">
                    {(report.what_to_bring as string[]).map((item, i) => (
                      <li key={i} className="text-slate-300 text-sm flex items-start gap-2">
                        <span className="text-indigo-400">✓</span>
                        {item}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/*
                Fallback for report types without body/subject (e.g. "general"
                report has title + evidence[] + recommended_actions but no body).
                Without this, those reports appeared as an empty modal.
              */}
              {!report.subject && !report.body && !report.recommended_actions && (
                <div>
                  <div className="text-xs text-slate-500 uppercase tracking-wider mb-1">
                    {isDE ? 'Bericht-Rohdaten' : 'Report data'}
                  </div>
                  <pre className="bg-slate-800 rounded-lg p-4 text-slate-300 text-xs whitespace-pre-wrap font-mono overflow-x-auto">
                    {JSON.stringify(report, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          ) : null}
          {downloadError && (
            <div className="mt-4 bg-red-900/40 border border-red-800 text-red-200 rounded-lg p-3 text-xs">
              <div className="font-semibold mb-1">
                {isDE ? 'PDF-Download fehlgeschlagen' : 'PDF download failed'}
              </div>
              <div className="font-mono opacity-80">{downloadError}</div>
            </div>
          )}
        </div>

        {/* Footer — hidden in send mode (SendReport has its own buttons) */}
        {mode === 'preview' && (
          <div className="p-4 border-t border-slate-700 flex gap-3">
            <button
              onClick={handleCopy}
              disabled={!report}
              className="flex-1 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold py-3 rounded-xl transition-colors"
            >
              {copied ? t(lang, 'report.copied') : t(lang, 'report.copy')}
            </button>
            <button
              onClick={handleDownload}
              disabled={!report || loading}
              className="flex-1 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-xl transition-colors border border-slate-600"
            >
              {isDE ? '⬇ PDF Export' : '⬇ PDF Export'}
            </button>
            <button
              onClick={onClose}
              className="px-6 py-3 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl transition-colors"
            >
              {isDE ? 'Schließen' : 'Close'}
            </button>
          </div>
        )}
        {mode === 'send' && (
          <div className="p-4 border-t border-slate-700 flex gap-3 justify-end">
            <button
              onClick={onClose}
              className="px-6 py-3 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl transition-colors text-sm"
            >
              {isDE ? 'Schließen' : 'Close'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
