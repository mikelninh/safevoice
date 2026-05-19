import { useEffect, useState } from 'react'
import type { Lang } from '../i18n'
import type { Case } from '../types'
import {
  downloadBase64,
  ensureBackendCase,
  runCourtPrepAgent,
  type CourtPrepResponse,
  type CourtPrepTraceCall,
} from '../services/api'
import { updateCaseBackendId } from '../services/storage'

/**
 * CourtPrepPanel — Beta entry point for the SafeVoice Court-Prep Agent.
 *
 * Single button on the CaseDetail page. Triggers POST /agent/court-prep/{id},
 * shows a live-ish trace of the 6-7 tool calls, and renders download buttons
 * for the artefacts: Strafanzeige PDF, NetzDG eml per platform, the jurisdiction
 * info, the Frist warning, the § 200a StPO recommendation.
 *
 * No mail is sent. The user reviews + sends manually — human-in-loop is
 * non-negotiable for legal-tech.
 */

interface Props {
  caseId: string
  caseData: Case
  lang: Lang
}

// The agent calls tools in roughly this order. We surface this list as a
// progress checklist while the request is in flight so the user has something
// to watch. The endpoint is synchronous, so we can't truly stream — but a
// time-based "current step" indicator is honest enough at MVP. Real streaming
// (SSE, or polling /agent/runs/{id}) is a later improvement.
const EXPECTED_STEPS_DE = [
  'Fall + Beweise lesen',
  'Strafantrags-Frist berechnen (§ 77 StGB)',
  'Anonymisierungs-Bedarf prüfen (§ 200a StPO)',
  'Beweise sichern (archive.org)',
  'NetzDG-Meldungen pro Plattform draften',
  'Zuständige Staatsanwaltschaft (§ 7 StPO)',
  'Strafanzeige-PDF generieren',
] as const
const EXPECTED_STEPS_EN = [
  'Read case + evidence',
  'Compute Strafantrag deadline (§ 77 StGB)',
  'Check anonymity need (§ 200a StPO)',
  'Re-archive evidence (archive.org)',
  'Draft NetzDG reports per platform',
  'Competent prosecutor (§ 7 StPO)',
  'Generate Strafanzeige PDF',
] as const

const BUNDESLAENDER: Array<{ code: string; name: string }> = [
  { code: 'BE', name: 'Berlin' },
  { code: 'BW', name: 'Baden-Württemberg' },
  { code: 'BY', name: 'Bayern' },
  { code: 'BB', name: 'Brandenburg' },
  { code: 'HB', name: 'Bremen' },
  { code: 'HH', name: 'Hamburg' },
  { code: 'HE', name: 'Hessen' },
  { code: 'MV', name: 'Mecklenburg-Vorpommern' },
  { code: 'NI', name: 'Niedersachsen' },
  { code: 'NW', name: 'Nordrhein-Westfalen' },
  { code: 'RP', name: 'Rheinland-Pfalz' },
  { code: 'SL', name: 'Saarland' },
  { code: 'SN', name: 'Sachsen' },
  { code: 'ST', name: 'Sachsen-Anhalt' },
  { code: 'SH', name: 'Schleswig-Holstein' },
  { code: 'TH', name: 'Thüringen' },
]

const TOOL_LABEL_DE: Record<string, string> = {
  read_case: 'Fall + Beweise lesen',
  check_strafantrag_frist: 'Strafantrags-Frist prüfen (§ 77 StGB)',
  determine_jurisdiction: 'Zuständige Staatsanwaltschaft (§ 7 StPO)',
  detect_anonymisierung_needed: 'Anonymisierungs-Antrag prüfen (§ 200a StPO)',
  re_archive_urls: 'URLs archivieren (archive.org)',
  draft_netzdg_email: 'NetzDG-Meldung pro Plattform draften',
  generate_strafanzeige_pdf: 'Strafanzeige-PDF generieren',
}
const TOOL_LABEL_EN: Record<string, string> = {
  read_case: 'Read case + evidence',
  check_strafantrag_frist: 'Check Strafantrag deadline (§ 77 StGB)',
  determine_jurisdiction: 'Competent prosecutor (§ 7 StPO)',
  detect_anonymisierung_needed: 'Anonymity request needed (§ 200a StPO)',
  re_archive_urls: 'Re-archive URLs (archive.org)',
  draft_netzdg_email: 'Draft NetzDG email per platform',
  generate_strafanzeige_pdf: 'Generate Strafanzeige PDF',
}

export default function CourtPrepPanel({ caseId, caseData, lang }: Props) {
  const isDE = lang === 'de'
  const expectedSteps = isDE ? EXPECTED_STEPS_DE : EXPECTED_STEPS_EN
  const [name, setName] = useState('')
  const [bundesland, setBundesland] = useState('')
  const [running, setRunning] = useState(false)
  const [progressStep, setProgressStep] = useState(0)
  const [progressLabel, setProgressLabel] = useState<string>('')
  const [elapsedSec, setElapsedSec] = useState(0)
  const [result, setResult] = useState<CourtPrepResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  // Tick a "expected step" cursor + elapsed counter while running, so the
  // user has visible progress during the ~10-30s synchronous call.
  useEffect(() => {
    if (!running) return
    const start = Date.now()
    const elapsedTimer = setInterval(() => {
      setElapsedSec(Math.floor((Date.now() - start) / 1000))
    }, 200)
    // Step pacing: most steps run 1-4s, generate_strafanzeige_pdf is ~11s.
    // Front-load early steps quickly, slow at the end where PDF gen lives.
    const stepDelaysMs = [400, 800, 1200, 1800, 2400, 3000, 4000]
    let cancelled = false
    let step = 0
    const advance = () => {
      if (cancelled || step >= stepDelaysMs.length) return
      setProgressStep(step)
      setProgressLabel(expectedSteps[step] ?? '')
      const delay = stepDelaysMs[step]
      step += 1
      setTimeout(advance, delay)
    }
    advance()
    return () => {
      cancelled = true
      clearInterval(elapsedTimer)
    }
  }, [running, expectedSteps])

  const run = async () => {
    setRunning(true)
    setError(null)
    setResult(null)
    setProgressStep(0)
    setProgressLabel('')
    setElapsedSec(0)
    try {
      // Local-only cases (id starts with "case-local-") have no backend row,
      // so the agent's read_case tool would 404. Push the local case + all
      // its evidence to the backend first, then run the agent against the
      // resolved backend id. Same pattern as fetchLegalAnalysis.
      let resolvedCaseId = caseId
      if (caseId.startsWith('case-local-')) {
        resolvedCaseId = await ensureBackendCase(caseData)
        if (resolvedCaseId !== caseData.backend_id) {
          updateCaseBackendId(caseId, resolvedCaseId)
        }
      }
      const res = await runCourtPrepAgent(resolvedCaseId, {
        victim_name: name || undefined,
        bundesland_code: bundesland || undefined,
      })
      setResult(res)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setRunning(false)
    }
  }

  const toolLabel = (name: string): string => {
    const map = isDE ? TOOL_LABEL_DE : TOOL_LABEL_EN
    return map[name] ?? name
  }

  return (
    <section className="mb-6 rounded-2xl border border-indigo-800/50 bg-indigo-950/30 p-5">
      <header className="flex items-start justify-between gap-3 mb-4">
        <div>
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <span>{isDE ? 'Strafanzeige vorbereiten' : 'Prepare Strafanzeige'}</span>
            <span className="text-[10px] font-bold uppercase tracking-wider text-amber-300 bg-amber-900/40 border border-amber-700/40 rounded px-1.5 py-0.5">
              Beta
            </span>
          </h2>
          <p className="text-sm text-slate-300 mt-1">
            {isDE
              ? 'Ein KI-Agent prüft Fristen, findet die zuständige Staatsanwaltschaft, baut NetzDG-Meldungen und die fertige Strafanzeige — alles als Download. Es wird nichts automatisch versendet.'
              : 'An AI agent checks deadlines, finds the competent prosecutor, builds NetzDG reports and the final Strafanzeige — all as downloads. Nothing is sent automatically.'}
          </p>
        </div>
      </header>

      <div className="grid sm:grid-cols-2 gap-3 mb-4">
        <input
          type="text"
          placeholder={isDE ? 'Dein Name (optional)' : 'Your name (optional)'}
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="bg-slate-900 border border-slate-700 text-slate-100 rounded-lg px-3 py-2 text-sm placeholder-slate-500"
        />
        <select
          value={bundesland}
          onChange={(e) => setBundesland(e.target.value)}
          className="bg-slate-900 border border-slate-700 text-slate-100 rounded-lg px-3 py-2 text-sm"
        >
          <option value="">
            {isDE
              ? 'Bundesland für Staatsanwaltschaft (optional)'
              : 'Federal state for prosecutor (optional)'}
          </option>
          {BUNDESLAENDER.map((b) => (
            <option key={b.code} value={b.code}>
              {b.name}
            </option>
          ))}
        </select>
      </div>

      <button
        type="button"
        onClick={run}
        disabled={running}
        className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-800 disabled:cursor-wait text-white font-semibold py-3 rounded-xl transition-colors text-base shadow-lg shadow-indigo-900/30"
      >
        {running
          ? isDE
            ? `Agent läuft … ${elapsedSec}s`
            : `Agent running … ${elapsedSec}s`
          : isDE
          ? '⚖️  Paket vorbereiten lassen'
          : '⚖️  Prepare the package'}
      </button>

      {running && (
        <ProgressList
          steps={expectedSteps}
          currentStep={progressStep}
          currentLabel={progressLabel}
          elapsedSec={elapsedSec}
          isDE={isDE}
        />
      )}

      <p className="text-xs text-slate-400 mt-3 leading-relaxed">
        {isDE
          ? 'Hinweis: dieser Agent ist in Beta. Du bekommst alle Dokumente als Downloads — bitte vor dem Versand durchlesen. Für verbindliche juristische Beratung kontaktiere eine Anwält:in oder '
          : 'Note: this agent is in beta. You receive every document as a download — please review before sending. For legally binding advice, contact a lawyer or '}
        <a
          href="https://hateaid.org"
          target="_blank"
          rel="noopener noreferrer"
          className="text-indigo-300 hover:text-indigo-200 underline"
        >
          HateAid
        </a>
        .
      </p>

      {error && (
        <div className="mt-4 rounded-lg border border-red-800/50 bg-red-950/40 p-3 text-sm text-red-200">
          {isDE ? 'Fehler: ' : 'Error: '}
          {error}
        </div>
      )}

      {result && <ResultBlock result={result} isDE={isDE} toolLabel={toolLabel} />}
    </section>
  )
}

function ProgressList({
  steps,
  currentStep,
  currentLabel,
  elapsedSec,
  isDE,
}: {
  steps: readonly string[]
  currentStep: number
  currentLabel: string
  elapsedSec: number
  isDE: boolean
}) {
  return (
    <div className="mt-4 rounded-lg border border-slate-700 bg-slate-900/60 p-3">
      <div className="flex items-center justify-between text-xs uppercase tracking-wider text-slate-500 mb-2">
        <span>
          {isDE ? 'Agent läuft' : 'Agent running'} —{' '}
          <span className="font-mono normal-case text-slate-400">{currentLabel}</span>
        </span>
        <span className="font-mono normal-case text-slate-400">{elapsedSec}s</span>
      </div>
      <ol className="space-y-1 text-xs">
        {steps.map((s, i) => {
          const done = i < currentStep
          const active = i === currentStep
          return (
            <li
              key={s}
              className={`flex items-center gap-2 ${
                done
                  ? 'text-emerald-300'
                  : active
                  ? 'text-indigo-200 font-medium'
                  : 'text-slate-500'
              }`}
            >
              <span className="w-4 inline-flex justify-center shrink-0">
                {done ? '✓' : active ? <Spinner /> : '○'}
              </span>
              <span>{s}</span>
            </li>
          )
        })}
      </ol>
      <p className="text-[10px] text-slate-500 mt-2 italic">
        {isDE
          ? 'Geschätzte Reihenfolge — der Agent entscheidet selbst und überspringt Schritte wenn nicht nötig.'
          : 'Expected order — the agent picks its own and skips steps when not needed.'}
      </p>
    </div>
  )
}

function Spinner() {
  return (
    <span
      className="inline-block w-3 h-3 rounded-full border-2 border-indigo-400 border-t-transparent animate-spin"
      aria-hidden="true"
    />
  )
}

function ResultBlock({
  result,
  isDE,
  toolLabel,
}: {
  result: CourtPrepResponse
  isDE: boolean
  toolLabel: (n: string) => string
}) {
  const a = result.artefacts
  const completed = result.status === 'completed'

  return (
    <div className="mt-5 space-y-4">
      {/* Status banner */}
      <div
        className={`rounded-lg border p-3 text-sm ${
          completed
            ? 'border-emerald-800/50 bg-emerald-950/30 text-emerald-200'
            : 'border-amber-800/50 bg-amber-950/30 text-amber-200'
        }`}
      >
        <div className="font-medium">
          {completed
            ? isDE
              ? 'Paket bereit — bitte alle Dokumente vor dem Versand prüfen.'
              : 'Package ready — please review all documents before sending.'
            : isDE
            ? `Status: ${result.status} (${result.error ?? '—'})`
            : `Status: ${result.status} (${result.error ?? '—'})`}
        </div>
        <div className="text-xs opacity-75 mt-1">
          {result.iterations} {isDE ? 'Schritte' : 'iterations'} · $
          {result.total_cost_usd.toFixed(4)} · run {result.agent_run_id.slice(0, 8)}
        </div>
      </div>

      {/* Final agent message */}
      {result.final_message && (
        <div className="rounded-lg border border-slate-700 bg-slate-900/60 p-3">
          <div className="text-xs uppercase tracking-wider text-slate-500 mb-1">
            {isDE ? 'Agent-Zusammenfassung' : 'Agent summary'}
          </div>
          <p className="text-sm text-slate-200 whitespace-pre-line">
            {result.final_message}
          </p>
        </div>
      )}

      {/* Frist warning */}
      {a.frist && a.frist.applicable_antragsdelikte.length > 0 && (
        <div
          className={`rounded-lg border p-3 text-sm ${
            a.frist.warning_level === 'expired'
              ? 'border-red-800/50 bg-red-950/40 text-red-200'
              : a.frist.warning_level === 'urgent'
              ? 'border-amber-800/50 bg-amber-950/40 text-amber-200'
              : 'border-slate-700 bg-slate-900/60 text-slate-200'
          }`}
        >
          <div className="font-medium mb-1">
            {isDE ? 'Strafantrags-Frist' : 'Strafantrag deadline'} (§ 77 StGB)
          </div>
          <p className="text-xs opacity-90 mb-2">{a.frist.summary}</p>
          <ul className="text-xs space-y-0.5">
            {a.frist.applicable_antragsdelikte.map((f) => (
              <li key={f.law}>
                <span className="font-mono">{f.law}</span> — {f.days_left}{' '}
                {isDE ? 'Tage verbleibend' : 'days left'} ·{' '}
                {f.deadline_utc.slice(0, 10)}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Jurisdiction */}
      {a.jurisdiction && (
        <div className="rounded-lg border border-slate-700 bg-slate-900/60 p-3 text-sm">
          <div className="text-xs uppercase tracking-wider text-slate-500 mb-1">
            {isDE ? 'Zuständige Staatsanwaltschaft' : 'Competent prosecutor'} (§ 7 StPO)
          </div>
          <p className="text-slate-200 font-medium">
            {a.jurisdiction.staatsanwaltschaft.name}
          </p>
          <p className="text-slate-400 text-xs">
            {a.jurisdiction.staatsanwaltschaft.address}
          </p>
          <p className="text-slate-400 text-xs font-mono mt-1">
            {a.jurisdiction.staatsanwaltschaft.email}
          </p>
        </div>
      )}

      {/* § 200a recommendation */}
      {a.anonymisierung && a.anonymisierung.needed && (
        <div className="rounded-lg border border-indigo-800/50 bg-indigo-950/40 p-3 text-sm">
          <div className="text-xs uppercase tracking-wider text-indigo-300 mb-1">
            {isDE ? 'Anonymisierung empfohlen' : 'Anonymity recommended'} (§ 200a StPO)
          </div>
          <p className="text-slate-200">{a.anonymisierung.begruendung}</p>
        </div>
      )}

      {/* Downloads */}
      <div className="rounded-lg border border-slate-700 bg-slate-900/60 p-3">
        <div className="text-xs uppercase tracking-wider text-slate-500 mb-2">
          {isDE ? 'Downloads' : 'Downloads'}
        </div>
        <div className="flex flex-wrap gap-2">
          {a.strafanzeige_pdf_base64 && (
            <button
              type="button"
              onClick={() =>
                downloadBase64(
                  a.strafanzeige_pdf_base64!,
                  a.strafanzeige_filename ?? 'strafanzeige.pdf',
                  'application/pdf',
                )
              }
              className="bg-slate-800 hover:bg-slate-700 border border-slate-600 text-slate-100 text-sm px-3 py-1.5 rounded-lg"
            >
              📄 Strafanzeige.pdf
            </button>
          )}
          {a.netzdg_emls.map((eml) => (
            <button
              key={eml.platform}
              type="button"
              onClick={() =>
                downloadBase64(eml.eml_base64, eml.filename, 'message/rfc822')
              }
              className="bg-slate-800 hover:bg-slate-700 border border-slate-600 text-slate-100 text-sm px-3 py-1.5 rounded-lg"
            >
              📨 NetzDG {eml.platform}
            </button>
          ))}
          {!a.strafanzeige_pdf_base64 && a.netzdg_emls.length === 0 && (
            <p className="text-xs text-slate-500">
              {isDE ? 'Keine Artefakte verfügbar.' : 'No artefacts available.'}
            </p>
          )}
        </div>
      </div>

      {/* Tool trace */}
      <details className="rounded-lg border border-slate-700 bg-slate-900/40 p-3">
        <summary className="cursor-pointer text-xs uppercase tracking-wider text-slate-500">
          {isDE ? 'Agent-Trace anzeigen' : 'Show agent trace'} (
          {result.tool_trace.length})
        </summary>
        <ol className="mt-3 space-y-1.5 text-xs">
          {result.tool_trace.map((c, i) => (
            <ToolCallLine key={i} call={c} toolLabel={toolLabel} />
          ))}
        </ol>
      </details>
    </div>
  )
}

function ToolCallLine({
  call,
  toolLabel,
}: {
  call: CourtPrepTraceCall
  toolLabel: (n: string) => string
}) {
  const ok = !call.error
  return (
    <li
      className={`flex items-start gap-2 ${
        ok ? 'text-slate-300' : 'text-red-300'
      }`}
    >
      <span className="font-mono text-slate-500 w-12 text-right shrink-0">
        {call.latency_ms}ms
      </span>
      <span>
        {ok ? '✓' : '✗'} {toolLabel(call.tool)}
        {call.cached && (
          <span className="ml-2 text-[10px] uppercase tracking-wider text-slate-500">
            cached
          </span>
        )}
        {call.error && <span className="ml-2 opacity-80">— {call.error}</span>}
      </span>
    </li>
  )
}
