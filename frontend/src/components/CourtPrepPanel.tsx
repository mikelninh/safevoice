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
 * CourtPrepPanel — single entry point for the SafeVoice Court-Prep Agent.
 *
 * Owns the full Strafanzeige journey: the agent prepares the package,
 * we render an animated timeline of every tool call with grounded output
 * chips, then offer downloads + the Onlinewache fast-path. There is no
 * separate Onlinewache panel anymore — the agent's `build_onlinewache_text`
 * tool merged that flow in, removing the previous redundant UI.
 *
 * Nothing is auto-sent. Every artefact is a download or a paste-ready text;
 * the user takes the final step.
 */

interface Props {
  caseId: string
  caseData: Case
  lang: Lang
}

// Expected agent flow — shown as a step skeleton during the run, then
// replaced by the actual tool_trace once the response arrives.
const FLOW_STEPS: Array<{ key: string; icon: string; label_de: string; label_en: string }> = [
  { key: 'read_case', icon: '📂', label_de: 'Fall + Beweise lesen', label_en: 'Read case + evidence' },
  { key: 'check_strafantrag_frist', icon: '⏳', label_de: 'Strafantrags-Frist (§ 77 StGB)', label_en: 'Strafantrag deadline (§ 77 StGB)' },
  { key: 'detect_anonymisierung_needed', icon: '🕶', label_de: 'Anonymisierung (§ 200a StPO)', label_en: 'Anonymity (§ 200a StPO)' },
  { key: 're_archive_urls', icon: '📌', label_de: 'Beweise archivieren', label_en: 'Archive evidence' },
  { key: 'draft_netzdg_email', icon: '📨', label_de: 'NetzDG-Meldungen', label_en: 'NetzDG reports' },
  { key: 'determine_jurisdiction', icon: '⚖️', label_de: 'Zuständige Staatsanwaltschaft', label_en: 'Competent prosecutor' },
  { key: 'generate_strafanzeige_pdf', icon: '📄', label_de: 'Strafanzeige-PDF', label_en: 'Strafanzeige PDF' },
  { key: 'build_onlinewache_text', icon: '🚓', label_de: 'Onlinewache-Text', label_en: 'Onlinewache text' },
]

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

export default function CourtPrepPanel({ caseId, caseData, lang }: Props) {
  const isDE = lang === 'de'
  const [name, setName] = useState('')
  const [bundesland, setBundesland] = useState('')
  const [running, setRunning] = useState(false)
  const [progressIdx, setProgressIdx] = useState(0)
  const [elapsedSec, setElapsedSec] = useState(0)
  const [result, setResult] = useState<CourtPrepResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!running) return
    const start = Date.now()
    const elapsedTimer = setInterval(() => {
      setElapsedSec(Math.floor((Date.now() - start) / 1000))
    }, 200)
    // Pace each "visible" step. PDF gen is the slow one (~11s), front-load
    // the cheap steps so the UI feels alive immediately.
    const stepDelays = [400, 800, 1200, 1800, 2400, 2800, 3400, 4200]
    let cancelled = false
    let i = 0
    const tick = () => {
      if (cancelled || i >= stepDelays.length) return
      setProgressIdx(i)
      const wait = stepDelays[i]
      i += 1
      setTimeout(tick, wait)
    }
    tick()
    return () => {
      cancelled = true
      clearInterval(elapsedTimer)
    }
  }, [running])

  const run = async () => {
    setRunning(true)
    setError(null)
    setResult(null)
    setProgressIdx(0)
    setElapsedSec(0)
    try {
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

  return (
    <section className="mb-6 rounded-2xl border border-indigo-800/50 bg-gradient-to-br from-indigo-950/40 to-slate-950/60 p-5 shadow-lg shadow-indigo-950/20">
      <header className="mb-4">
        <h2 className="text-lg font-semibold text-white flex items-center gap-2 mb-1">
          <span>{isDE ? 'Strafanzeige vorbereiten' : 'Prepare Strafanzeige'}</span>
          <span className="text-[10px] font-bold uppercase tracking-wider text-amber-300 bg-amber-900/40 border border-amber-700/40 rounded px-1.5 py-0.5">
            Beta
          </span>
        </h2>
        <p className="text-sm text-slate-300">
          {isDE
            ? 'Ein KI-Agent prüft Fristen, findet die zuständige Staatsanwaltschaft, sichert Beweise auf archive.org, baut NetzDG-Meldungen pro Plattform und liefert PDF + Onlinewache-Text. Du sendest nichts automatisch — alles als Download oder zum Reinkopieren.'
            : 'An AI agent checks deadlines, finds the competent prosecutor, secures evidence on archive.org, builds per-platform NetzDG reports, and delivers PDF + Onlinewache text. Nothing is sent automatically — all downloads or paste-ready text.'}
        </p>
      </header>

      <div className="grid sm:grid-cols-2 gap-3 mb-3">
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
            {isDE ? 'Bundesland (optional, für StA + Onlinewache)' : 'Federal state (optional)'}
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

      <p className="text-xs text-slate-400 mt-3 leading-relaxed">
        {isDE
          ? 'Hinweis: Agent in Beta. Alle Dokumente als Download — vor dem Versand prüfen. Für verbindliche Beratung Anwält:in oder '
          : 'Note: agent in beta. All documents as downloads — review before sending. For binding advice, contact a lawyer or '}
        <a href="https://hateaid.org" target="_blank" rel="noopener noreferrer" className="text-indigo-300 hover:text-indigo-200 underline">
          HateAid
        </a>
        .
      </p>

      {(running || result) && (
        <FlowTimeline
          isDE={isDE}
          running={running}
          progressIdx={progressIdx}
          elapsedSec={elapsedSec}
          result={result}
        />
      )}

      {error && (
        <div className="mt-4 rounded-lg border border-red-800/50 bg-red-950/40 p-3 text-sm text-red-200">
          {isDE ? 'Fehler: ' : 'Error: '}
          {error}
        </div>
      )}

      {result && <Artefacts result={result} isDE={isDE} />}
    </section>
  )
}

// ── Animated timeline of the agent flow ─────────────────────────────────

function FlowTimeline({
  isDE,
  running,
  progressIdx,
  elapsedSec,
  result,
}: {
  isDE: boolean
  running: boolean
  progressIdx: number
  elapsedSec: number
  result: CourtPrepResponse | null
}) {
  // While running, drive the timeline with the fake progress cursor.
  // After completion, drive it from the real tool_trace.
  const calls = result?.tool_trace ?? []
  const callByTool = new Map<string, CourtPrepTraceCall>()
  calls.forEach((c) => callByTool.set(c.tool, c))

  return (
    <div className="mt-5 rounded-xl border border-slate-700/70 bg-slate-950/50 p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs uppercase tracking-wider text-slate-400 font-medium">
          {isDE ? 'Agent-Flow' : 'Agent flow'}
        </h3>
        <div className="text-xs text-slate-500 font-mono">
          {running
            ? `${elapsedSec}s`
            : result
            ? `${result.iterations} ${isDE ? 'Schritte' : 'iterations'} · $${result.total_cost_usd.toFixed(4)}`
            : ''}
        </div>
      </div>

      <ol className="space-y-2">
        {FLOW_STEPS.map((step, i) => {
          const call = callByTool.get(step.key)
          const status: 'done' | 'active' | 'idle' | 'skipped' = result
            ? call
              ? 'done'
              : 'skipped'
            : i < progressIdx
            ? 'done'
            : i === progressIdx
            ? 'active'
            : 'idle'
          return (
            <FlowStep
              key={step.key}
              index={i}
              icon={step.icon}
              label={isDE ? step.label_de : step.label_en}
              status={status}
              call={call}
              isDE={isDE}
            />
          )
        })}
      </ol>
    </div>
  )
}

function FlowStep({
  index,
  icon,
  label,
  status,
  call,
  isDE,
}: {
  index: number
  icon: string
  label: string
  status: 'done' | 'active' | 'idle' | 'skipped'
  call?: CourtPrepTraceCall
  isDE: boolean
}) {
  const isLast = index === FLOW_STEPS.length - 1
  const ringColor =
    status === 'done'
      ? 'border-emerald-500 bg-emerald-950/70 text-emerald-300'
      : status === 'active'
      ? 'border-indigo-400 bg-indigo-950/80 text-indigo-200'
      : status === 'skipped'
      ? 'border-slate-700 bg-slate-900 text-slate-600'
      : 'border-slate-700 bg-slate-900 text-slate-500'
  const labelColor =
    status === 'done'
      ? 'text-slate-200'
      : status === 'active'
      ? 'text-indigo-100 font-medium'
      : status === 'skipped'
      ? 'text-slate-600'
      : 'text-slate-500'

  return (
    <li className="flex items-start gap-3">
      <div className="relative flex flex-col items-center">
        <div
          className={`w-8 h-8 rounded-full border-2 flex items-center justify-center text-sm shrink-0 transition-colors ${ringColor}`}
        >
          {status === 'active' ? <Spinner /> : icon}
        </div>
        {!isLast && (
          <div
            className={`w-0.5 flex-1 mt-0.5 mb-0.5 ${
              status === 'done' ? 'bg-emerald-700/40' : 'bg-slate-800'
            }`}
            style={{ minHeight: 18 }}
          />
        )}
      </div>
      <div className="flex-1 pb-2">
        <div className="flex items-baseline justify-between gap-3">
          <span className={`text-sm ${labelColor}`}>{label}</span>
          {call?.latency_ms !== undefined && (
            <span className="text-[10px] text-slate-500 font-mono shrink-0">
              {call.latency_ms}ms
              {call.cached && (
                <span className="ml-1 uppercase tracking-wider text-slate-600">cached</span>
              )}
            </span>
          )}
        </div>
        {call && <OutputChip call={call} isDE={isDE} />}
        {status === 'skipped' && !call && (
          <span className="text-[10px] text-slate-600 italic">
            {isDE ? 'übersprungen — nicht nötig' : 'skipped — not needed'}
          </span>
        )}
      </div>
    </li>
  )
}

// Pulls a single-line, grounded summary from the tool output so the user
// sees WHAT the agent actually found, not just that the step happened.
function OutputChip({ call, isDE }: { call: CourtPrepTraceCall; isDE: boolean }) {
  if (call.error) {
    return (
      <span className="inline-block mt-0.5 text-[11px] text-red-300 bg-red-950/50 border border-red-800/40 rounded px-1.5 py-0.5">
        ✗ {call.error}
      </span>
    )
  }
  const out = call.output as Record<string, unknown> | null
  if (!out || typeof out !== 'object') return null

  let chip: { text: string; tone: 'good' | 'warn' | 'info' } | null = null

  switch (call.tool) {
    case 'read_case': {
      const count = (out.evidence_count as number | undefined) ?? 0
      chip = { text: `${count} ${isDE ? 'Beweise geladen' : 'evidence items'}`, tone: 'info' }
      break
    }
    case 'check_strafantrag_frist': {
      const lvl = out.warning_level as string | undefined
      const summary = out.summary as string | undefined
      const tone = lvl === 'expired' ? 'warn' : lvl === 'urgent' ? 'warn' : 'good'
      chip = { text: summary || `${lvl ?? '–'}`, tone }
      break
    }
    case 'detect_anonymisierung_needed': {
      const needed = Boolean(out.needed)
      chip = {
        text: needed
          ? isDE
            ? '§ 200a StPO empfohlen'
            : '§ 200a StPO recommended'
          : isDE
          ? 'kein § 200a nötig'
          : '§ 200a not needed',
        tone: needed ? 'info' : 'good',
      }
      break
    }
    case 're_archive_urls': {
      const att = (out.attempted as number | undefined) ?? 0
      const ok = (out.succeeded as number | undefined) ?? 0
      chip = {
        text: `${ok}/${att} ${isDE ? 'URLs archiviert' : 'URLs archived'}`,
        tone: ok > 0 ? 'good' : 'info',
      }
      break
    }
    case 'draft_netzdg_email': {
      const ok = Boolean(out.ok)
      const platform = out.platform as string | undefined
      chip = ok
        ? { text: `eml: ${platform ?? '?'}`, tone: 'good' }
        : { text: String(out.error ?? '–'), tone: 'info' }
      break
    }
    case 'determine_jurisdiction': {
      const sta = (out.staatsanwaltschaft as { name?: string } | undefined)?.name
      if (sta) chip = { text: sta, tone: 'good' }
      break
    }
    case 'generate_strafanzeige_pdf': {
      const len = (out.pdf_bytes_len as number | undefined) ?? 0
      if (len > 0) chip = { text: `PDF ${Math.round(len / 1024)} KB`, tone: 'good' }
      break
    }
    case 'build_onlinewache_text': {
      const ok = Boolean(out.ok)
      const land = out.bundesland_name as string | undefined
      chip = ok
        ? { text: `Onlinewache ${land ?? ''}`, tone: 'good' }
        : { text: String(out.error ?? '–'), tone: 'info' }
      break
    }
  }

  if (!chip) return null

  const cls =
    chip.tone === 'good'
      ? 'text-emerald-300 bg-emerald-950/40 border-emerald-800/40'
      : chip.tone === 'warn'
      ? 'text-amber-200 bg-amber-950/40 border-amber-800/40'
      : 'text-indigo-200 bg-indigo-950/40 border-indigo-800/40'

  return (
    <span
      className={`inline-block mt-1 text-[11px] border rounded px-1.5 py-0.5 ${cls}`}
    >
      {chip.text}
    </span>
  )
}

function Spinner() {
  return (
    <span
      className="inline-block w-3.5 h-3.5 rounded-full border-2 border-indigo-300 border-t-transparent animate-spin"
      aria-hidden="true"
    />
  )
}

// ── Artefact downloads + Onlinewache fast-path ──────────────────────────

function Artefacts({ result, isDE }: { result: CourtPrepResponse; isDE: boolean }) {
  const a = result.artefacts
  const completed = result.status === 'completed'

  return (
    <div className="mt-5 space-y-4">
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
              ? 'Paket bereit — bitte vor Versand prüfen.'
              : 'Package ready — review before sending.'
            : isDE
            ? `Status: ${result.status}`
            : `Status: ${result.status}`}
        </div>
        <div className="text-[11px] opacity-70 mt-1 font-mono">
          run {result.agent_run_id.slice(0, 8)} · prompt {result.prompt_version}
        </div>
      </div>

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

      {a.jurisdiction && (
        <div className="rounded-lg border border-slate-700 bg-slate-900/60 p-3 text-sm">
          <div className="text-xs uppercase tracking-wider text-slate-500 mb-1">
            {isDE ? 'Zuständige Staatsanwaltschaft' : 'Competent prosecutor'} (§ 7 StPO)
          </div>
          <p className="text-slate-200 font-medium">{a.jurisdiction.staatsanwaltschaft.name}</p>
          <p className="text-slate-400 text-xs">{a.jurisdiction.staatsanwaltschaft.address}</p>
          <p className="text-slate-400 text-xs font-mono mt-1">
            {a.jurisdiction.staatsanwaltschaft.email}
          </p>
        </div>
      )}

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
        <div className="text-xs uppercase tracking-wider text-slate-500 mb-2">Downloads</div>
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
              onClick={() => downloadBase64(eml.eml_base64, eml.filename, 'message/rfc822')}
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

      {a.onlinewache && (
        <OnlinewacheCard onlinewache={a.onlinewache} isDE={isDE} />
      )}
    </div>
  )
}

function OnlinewacheCard({
  onlinewache,
  isDE,
}: {
  onlinewache: NonNullable<CourtPrepResponse['artefacts']['onlinewache']>
  isDE: boolean
}) {
  const [copied, setCopied] = useState(false)
  const [showPreview, setShowPreview] = useState(false)

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(onlinewache.text_for_paste)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // older browsers — silently skip
    }
  }

  return (
    <div className="rounded-lg border border-blue-800/50 bg-blue-950/30 p-3">
      <div className="flex items-start justify-between gap-2 mb-2">
        <div>
          <div className="text-xs uppercase tracking-wider text-blue-300 mb-0.5">
            {isDE ? 'Direkt online einreichen' : 'File online directly'}
          </div>
          <p className="text-sm text-slate-200">
            {isDE
              ? `Onlinewache ${onlinewache.bundesland_name} — offizieller 24/7-Polizei-Kanal. Schneller als Brief an die Staatsanwaltschaft.`
              : `Onlinewache ${onlinewache.bundesland_name} — official 24/7 police channel.`}
          </p>
        </div>
      </div>

      <ol className="text-xs text-slate-300 space-y-1 mb-3 list-decimal list-inside">
        <li>{isDE ? 'Text kopieren (Button rechts).' : 'Copy the text (button right).'}</li>
        <li>{isDE ? 'Onlinewache öffnen.' : 'Open the Onlinewache.'}</li>
        <li>
          {isDE
            ? 'Im Formular eigene Daten ausfüllen, dann den Text ins "Sachverhalt"-Feld einfügen.'
            : 'Fill in your own data, then paste the text into the "Sachverhalt" field.'}
        </li>
      </ol>

      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          onClick={copy}
          className="bg-slate-800 hover:bg-slate-700 border border-slate-600 text-slate-100 text-sm px-3 py-1.5 rounded-lg"
        >
          {copied
            ? isDE
              ? '✓ Kopiert'
              : '✓ Copied'
            : isDE
            ? '📋 Text kopieren'
            : '📋 Copy text'}
        </button>
        <a
          href={onlinewache.onlinewache_url}
          target="_blank"
          rel="noopener noreferrer"
          className="bg-blue-600 hover:bg-blue-500 text-white text-sm px-3 py-1.5 rounded-lg font-medium"
        >
          {isDE
            ? `Onlinewache ${onlinewache.bundesland_name} öffnen →`
            : `Open Onlinewache ${onlinewache.bundesland_name} →`}
        </a>
        <button
          type="button"
          onClick={() => setShowPreview((v) => !v)}
          className="text-xs text-slate-400 hover:text-slate-200 underline ml-auto"
        >
          {showPreview
            ? isDE
              ? 'Vorschau ausblenden'
              : 'Hide preview'
            : isDE
            ? 'Vorschau anzeigen'
            : 'Show preview'}
        </button>
      </div>

      {showPreview && (
        <pre className="mt-3 max-h-64 overflow-auto text-[11px] font-mono text-slate-300 bg-slate-950/70 border border-slate-800 rounded p-3 whitespace-pre-wrap">
          {onlinewache.text_for_paste}
        </pre>
      )}
    </div>
  )
}
