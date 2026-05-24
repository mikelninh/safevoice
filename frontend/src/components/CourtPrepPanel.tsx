import { useEffect, useState } from 'react'
import type React from 'react'
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
  { key: 'check_strafantrag_frist', icon: '⏳', label_de: 'Strafantrags-Frist (§ 77b StGB)', label_en: 'Strafantrag deadline (§ 77b StGB)' },
  { key: 'detect_anonymisierung_needed', icon: '🕶', label_de: 'Anonymisierung (§ 68 Abs. 2, 3 StPO)', label_en: 'Anonymity (§ 68 Abs. 2, 3 StPO)' },
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
    // Pace each visible step ~proportional to its real cost: the cheap checks
    // flick by, archiving (idx 3) and PDF gen (idx 6) dwell — so the animation
    // mirrors where the time actually goes.
    const stepDelays = [600, 600, 600, 6000, 700, 700, 11000, 900]
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
        lang,
      })
      setResult(res)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setRunning(false)
    }
  }

  return (
    <section className="rounded-2xl border border-indigo-800/50 bg-gradient-to-br from-indigo-950/40 to-slate-950/60 p-5 sm:p-6 shadow-lg shadow-indigo-950/20">
      <header className="mb-4">
        <div className="flex items-center gap-2 mb-2">
          <h3 className="text-lg font-semibold text-white">
            {isDE ? 'Anzeige-Paket vorbereiten' : 'Prepare report package'}
          </h3>
          <span className="text-[10px] font-bold uppercase tracking-wider text-amber-300 bg-amber-900/40 border border-amber-700/40 rounded px-1.5 py-0.5">
            Beta
          </span>
        </div>
        <p className="text-sm text-slate-300 leading-relaxed">
          {isDE
            ? 'Wir prüfen Fristen, finden die zuständige Staatsanwaltschaft, sichern deine Beweise und bauen die Strafanzeige als PDF. Du sendest am Ende selbst — nichts geht automatisch raus.'
            : "We check deadlines, find the competent prosecutor, secure your evidence, and build the Strafanzeige as a PDF. You send it yourself at the end — nothing leaves automatically."}
        </p>
      </header>

      {!result && !running && (
        <div className="mb-4 space-y-2">
          <p className="text-xs text-slate-400">
            {isDE
              ? 'Deine Daten machen das Anzeige-Paket konkret. Du kannst alles leer lassen — dann bleiben Platzhalter im PDF, die du später im PDF-Reader ergänzt.'
              : "Your details make the package concrete. Leave blank to keep placeholders that you can fill in your PDF reader later."}
          </p>
          <div className="grid sm:grid-cols-2 gap-2">
            <input
              type="text"
              placeholder={isDE ? 'Dein Name' : 'Your name'}
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
                {isDE ? 'Bundesland — für Onlinewache + StA' : 'Federal state'}
              </option>
              {BUNDESLAENDER.map((b) => (
                <option key={b.code} value={b.code}>
                  {b.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}

      <button
        type="button"
        onClick={run}
        disabled={running}
        className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-800 disabled:cursor-wait text-white font-semibold py-3 rounded-xl transition-colors text-base shadow-lg shadow-indigo-900/30"
      >
        {running
          ? isDE
            ? `Wird vorbereitet … ${elapsedSec}s`
            : `Preparing … ${elapsedSec}s`
          : result
          ? isDE
            ? 'Neu vorbereiten'
            : 'Prepare again'
          : isDE
          ? 'Paket vorbereiten'
          : 'Prepare the package'}
      </button>

      {!result && (
        <p className="text-[11px] text-slate-500 mt-3 leading-relaxed">
          {isDE
            ? 'Alle Dokumente kommen als Download — bitte vor dem Versand kurz durchschauen. Für verbindliche Beratung: Anwält:in oder '
            : 'All documents come as downloads — please skim before sending. For binding advice: a lawyer or '}
          <a href="https://hateaid.org" target="_blank" rel="noopener noreferrer" className="text-indigo-300 hover:text-indigo-200 underline">
            HateAid
          </a>
          .
        </p>
      )}

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
          {isDE ? 'Etwas ist schiefgelaufen: ' : 'Something went wrong: '}
          {error}
        </div>
      )}

      {result && <Artefacts result={result} isDE={isDE} />}

      {/* Re-run option — lets the user add or change name/Bundesland
          after the first generation without having to redo the case. */}
      {result && (
        <details className="mt-4 group">
          <summary className="cursor-pointer text-xs text-slate-400 hover:text-slate-200 inline-flex items-center gap-1.5">
            <span className="inline-block transition-transform group-open:rotate-90">›</span>
            {isDE
              ? 'Daten anpassen und Paket neu erstellen'
              : 'Change details and regenerate'}
          </summary>
          <div className="mt-3 space-y-2">
            <div className="grid sm:grid-cols-2 gap-2">
              <input
                type="text"
                placeholder={isDE ? 'Dein Name' : 'Your name'}
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
                  {isDE ? 'Bundesland wählen' : 'Select state'}
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
              className="w-full bg-slate-800 hover:bg-slate-700 border border-slate-600 text-slate-200 text-sm py-2 rounded-lg transition-colors"
            >
              {isDE ? 'Paket neu erstellen' : 'Regenerate package'}
            </button>
          </div>
        </details>
      )}
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
  // Slowest step sets the scale — bars are drawn proportional to real latency,
  // so the expensive steps (PDF gen, archiving) visually dominate.
  const maxLatency = Math.max(1, ...calls.map((c) => c.latency_ms || 0))

  const steps = (
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
            maxLatency={maxLatency}
          />
        )
      })}
    </ol>
  )

  // While running, show the timeline expanded so the user sees progress.
  // Once done, collapse it into a "Was wurde geprüft" disclosure.
  if (running) {
    return (
      <div className="mt-5 rounded-xl border border-slate-700/70 bg-slate-950/50 p-4">
        <div className="flex items-center justify-between mb-3">
          <h4 className="text-xs uppercase tracking-wider text-slate-400 font-medium">
            {isDE ? 'Wird vorbereitet …' : 'Preparing …'}
          </h4>
          <div className="text-xs text-slate-500 font-mono">{elapsedSec}s</div>
        </div>
        {steps}
      </div>
    )
  }

  if (!result) return null

  const rounds = result.rounds ?? []
  const totalTokens =
    (result.total_prompt_tokens ?? 0) + (result.total_completion_tokens ?? 0)

  return (
    <>
      <details className="mt-5 rounded-xl border border-slate-700/70 bg-slate-950/50 group">
        <summary className="cursor-pointer list-none p-3 flex items-center justify-between text-xs text-slate-400 hover:text-slate-200">
          <span className="flex items-center gap-1.5">
            <span className="transition-transform group-open:rotate-90">›</span>
            {isDE ? 'Was geprüft wurde' : 'What was checked'}
          </span>
          <span className="font-mono text-slate-600">
            {result.iterations} {isDE ? 'Schritte' : 'steps'}
          </span>
        </summary>
        <div className="px-4 pb-4">{steps}</div>
      </details>

      {/* Developer telemetry — for the builder, not the victim. Where time +
          tokens + cost actually go, per LLM round. */}
      {rounds.length > 0 && (
        <details className="mt-3 rounded-xl border border-amber-800/40 bg-amber-950/10 group">
          <summary className="cursor-pointer list-none p-3 flex items-center justify-between text-xs text-amber-300/70 hover:text-amber-200">
            <span className="flex items-center gap-1.5">
              <span className="transition-transform group-open:rotate-90">›</span>
              <span className="font-bold uppercase tracking-wider text-[10px] bg-amber-900/40 border border-amber-700/40 rounded px-1.5 py-0.5">
                Dev
              </span>
              {isDE ? 'Telemetrie — Zeit, Tokens, Kosten' : 'Telemetry — time, tokens, cost'}
            </span>
            <span className="font-mono text-amber-600/80">
              ${result.total_cost_usd.toFixed(4)} · {totalTokens.toLocaleString()} tok
            </span>
          </summary>
          <div className="px-4 pb-4">
            <div className="grid grid-cols-4 gap-2 mb-3 text-center">
              <Metric label={isDE ? 'Zeit' : 'Time'} value={`${elapsedSec}s`} />
              <Metric label={isDE ? 'Runden' : 'Rounds'} value={String(result.iterations)} />
              <Metric label="Tokens" value={totalTokens.toLocaleString()} />
              <Metric label="Cost" value={`$${result.total_cost_usd.toFixed(4)}`} />
            </div>
            <table className="w-full text-[11px] font-mono text-slate-400">
              <thead>
                <tr className="text-slate-500 border-b border-slate-800">
                  <th className="text-left py-1 font-normal">#</th>
                  <th className="text-left py-1 font-normal">tool</th>
                  <th className="text-right py-1 font-normal">in</th>
                  <th className="text-right py-1 font-normal">out</th>
                  <th className="text-right py-1 font-normal">$</th>
                </tr>
              </thead>
              <tbody>
                {rounds.map((r) => (
                  <tr key={r.iteration} className="border-b border-slate-900/60">
                    <td className="py-1 text-slate-600">{r.iteration}</td>
                    <td className="py-1 text-slate-300">{r.tools.join(', ') || '—'}</td>
                    <td className="py-1 text-right">{r.prompt_tokens.toLocaleString()}</td>
                    <td className="py-1 text-right">{r.completion_tokens.toLocaleString()}</td>
                    <td className="py-1 text-right text-amber-400/70">${r.cost_usd.toFixed(4)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="mt-2 text-[10px] text-slate-600 leading-relaxed">
              {isDE
                ? 'Tools selbst kosten keine Tokens — der LLM zwischen den Schritten schon. Hohe out-Tokens = teure Runde.'
                : 'Tools cost no tokens — the LLM between steps does. High out-tokens = the expensive round.'}
            </p>
          </div>
        </details>
      )}
    </>
  )
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-slate-900/60 border border-slate-800 py-2">
      <div className="text-sm font-mono text-amber-300/90">{value}</div>
      <div className="text-[9px] uppercase tracking-wider text-slate-500 mt-0.5">{label}</div>
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
  maxLatency = 1,
}: {
  index: number
  icon: string
  label: string
  status: 'done' | 'active' | 'idle' | 'skipped'
  call?: CourtPrepTraceCall
  isDE: boolean
  maxLatency?: number
}) {
  const isLast = index === FLOW_STEPS.length - 1
  // Proportional duration bar: width relative to the slowest step.
  const latency = call?.latency_ms ?? 0
  const widthPct = call ? Math.max(4, Math.round((latency / maxLatency) * 100)) : 0
  const isHeavy = latency >= maxLatency * 0.5 // the slow ones, visually flagged
  const barColor = isHeavy ? 'bg-amber-500/70' : 'bg-emerald-600/50'
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
              {latency >= 1000 ? `${(latency / 1000).toFixed(1)}s` : `${latency}ms`}
              {call.cached && (
                <span className="ml-1 uppercase tracking-wider text-slate-600">cached</span>
              )}
            </span>
          )}
        </div>
        {call && widthPct > 0 && (
          <div className="mt-1 mb-0.5 h-1 rounded-full bg-slate-800/70 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${barColor}`}
              style={{ width: `${widthPct}%` }}
            />
          </div>
        )}
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
            ? '§ 68 Abs. 2, 3 StPO empfohlen'
            : '§ 68 Abs. 2, 3 StPO recommended'
          : isDE
          ? 'kein § 68 StPO nötig'
          : '§ 68 StPO not needed',
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
      {/* Status — calm confirmation, no celebration */}
      <div
        className={`rounded-lg border p-3 ${
          completed
            ? 'border-emerald-800/50 bg-emerald-950/30'
            : 'border-amber-800/50 bg-amber-950/30'
        }`}
      >
        <div className={`text-sm font-medium ${completed ? 'text-emerald-100' : 'text-amber-100'}`}>
          {completed
            ? isDE
              ? 'Dein Paket ist fertig. Bitte schau es kurz durch, bevor du es einreichst.'
              : 'Your package is ready. Please skim it before you submit it.'
            : isDE
            ? `Lief nicht ganz durch (Status: ${result.status}). Du kannst es nochmal versuchen.`
            : `Didn't complete fully (status: ${result.status}). You can try again.`}
        </div>
      </div>

      {/* Combined summary: agent message + jurisdiction + anonymisierung */}
      {(result.final_message || a.jurisdiction || (a.anonymisierung && a.anonymisierung.needed)) && (
        <div className="rounded-lg border border-slate-700 bg-slate-900/60 p-4 space-y-3 text-sm">
          {result.final_message && (
            <p className="text-slate-200 whitespace-pre-line leading-relaxed">
              {result.final_message}
            </p>
          )}

          {a.jurisdiction && (
            <div className="pt-2 border-t border-slate-800">
              <div className="text-[11px] uppercase tracking-wider text-slate-500 mb-1">
                {isDE ? 'Zuständige Staatsanwaltschaft' : 'Competent prosecutor'}
              </div>
              <p className="text-slate-200">{a.jurisdiction.staatsanwaltschaft.name}</p>
              <p className="text-slate-500 text-xs">{a.jurisdiction.staatsanwaltschaft.address}</p>
              <p className="text-slate-500 text-xs font-mono">{a.jurisdiction.staatsanwaltschaft.email}</p>
            </div>
          )}

          {a.anonymisierung && a.anonymisierung.needed && (
            <div className="pt-2 border-t border-slate-800">
              <div className="text-[11px] uppercase tracking-wider text-indigo-300 mb-1">
                {isDE ? 'Anonymisierung empfohlen (§ 68 Abs. 2, 3 StPO)' : 'Anonymity recommended (§ 68 Abs. 2, 3 StPO)'}
              </div>
              <p className="text-slate-300 text-xs leading-relaxed">{a.anonymisierung.begruendung}</p>
            </div>
          )}
        </div>
      )}

      {/* Downloads — primary outcome */}
      {(a.strafanzeige_pdf_base64 || a.netzdg_emls.length > 0) && (
        <div className="rounded-lg border border-slate-700 bg-slate-900/60 p-4">
          <div className="text-xs uppercase tracking-wider text-slate-400 mb-3 font-medium">
            {isDE ? 'Zum Herunterladen' : 'To download'}
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
                className="bg-indigo-600 hover:bg-indigo-500 text-white text-sm px-3 py-2 rounded-lg font-medium"
              >
                📄 Strafanzeige.pdf
              </button>
            )}
            {a.netzdg_emls.map((eml) => (
              <button
                key={eml.platform}
                type="button"
                onClick={() => downloadBase64(eml.eml_base64, eml.filename, 'message/rfc822')}
                className="bg-slate-800 hover:bg-slate-700 border border-slate-600 text-slate-100 text-sm px-3 py-2 rounded-lg"
              >
                📨 NetzDG {eml.platform}
              </button>
            ))}
            {a.hash_chain_csv_base64 && (
              <button
                type="button"
                onClick={() =>
                  downloadBase64(
                    a.hash_chain_csv_base64!,
                    a.hash_chain_csv_filename ?? 'hashes.csv',
                    'text/csv',
                  )
                }
                className="bg-slate-800 hover:bg-slate-700 border border-slate-600 text-slate-100 text-sm px-3 py-2 rounded-lg"
                title={isDE
                  ? 'Beweis-Hashes als Tabelle für unabhängige Verifikation'
                  : 'Evidence hashes as a table for independent verification'}
              >
                📋 {isDE ? 'Hashes.csv' : 'hashes.csv'}
              </button>
            )}
          </div>
        </div>
      )}

      {/* Submission decision helper — answers the questions the persona
          test surfaced: "Muss ich unterschreiben? Ausdrucken? Wohin?" */}
      <SubmissionGuide artefacts={a} isDE={isDE} />

      {a.onlinewache && (
        <OnlinewacheCard onlinewache={a.onlinewache} isDE={isDE} />
      )}

      <div className="text-[10px] text-slate-600 font-mono pt-1">
        run {result.agent_run_id.slice(0, 8)} · prompt {result.prompt_version}
      </div>
    </div>
  )
}

function SubmissionGuide({
  artefacts,
  isDE,
}: {
  artefacts: CourtPrepResponse['artefacts']
  isDE: boolean
}) {
  const hasOnlinewache = Boolean(artefacts.onlinewache)
  const staEmail = artefacts.jurisdiction?.staatsanwaltschaft?.email
  const staName = artefacts.jurisdiction?.staatsanwaltschaft?.name
  const staAddress = artefacts.jurisdiction?.staatsanwaltschaft?.address

  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900/40 p-4">
      <div className="text-xs uppercase tracking-wider text-slate-400 mb-3 font-medium">
        {isDE ? 'Wie sende ich das?' : 'How do I send this?'}
      </div>
      <div className="space-y-3 text-sm">
        {/* ONE recommended path visible by default; everything else folds away. */}
        {hasOnlinewache ? (
          <Path
            badge={isDE ? 'empfohlen · digital' : 'recommended · digital'}
            badgeTone="emerald"
            title={isDE ? 'Direkt online bei der Polizei' : 'File directly online with the police'}
            time={isDE ? '5 Min · keine Unterschrift' : '5 min · no signature'}
            sign={isDE ? 'Du wirst beim Absenden identifiziert' : "You're identified at submit time"}
            body={isDE
              ? `Onlinewache ${artefacts.onlinewache?.bundesland_name ?? ''}: vorbereiteten Text einfügen, Strafanzeige-PDF anhängen, fertig.`
              : `Onlinewache ${artefacts.onlinewache?.bundesland_name ?? ''}: paste the prepared text, attach the PDF, done.`}
          />
        ) : staEmail ? (
          <Path
            badge={isDE ? 'empfohlen · digital' : 'recommended · digital'}
            badgeTone="emerald"
            title={isDE ? 'Email an die Staatsanwaltschaft' : 'Email the Staatsanwaltschaft'}
            time={isDE ? '10 Min · keine Unterschrift' : '10 min · no signature'}
            sign={isDE ? 'Email zählt, wenn dein Name klar ist (§ 158 StPO, 2024)' : 'Email is valid if your name is clear (§ 158 StPO, 2024)'}
            body={
              <>
                <span className="font-mono text-slate-200">{staEmail}</span>
                {isDE ? ' — Strafanzeige-PDF anhängen, kurze Zeile im Body.' : ' — attach the PDF, short body line.'}
              </>
            }
          />
        ) : (
          /* No Bundesland yet → don't dump the user into the letter. Nudge digital. */
          <div className="rounded-lg border border-emerald-800/40 bg-emerald-950/20 p-3">
            <p className="text-slate-200 leading-relaxed">
              {isDE
                ? '📍 Wähle unten dein Bundesland — dann zeigen wir dir den schnellsten digitalen Weg (Onlinewache, ohne Unterschrift).'
                : '📍 Pick your federal state below — then we show the fastest digital route (online police, no signature).'}
            </p>
          </div>
        )}

        {/* Everything else folds away — keeps the page calm. */}
        <details className="group">
          <summary className="cursor-pointer list-none text-xs text-slate-500 hover:text-slate-300 flex items-center gap-1.5">
            <span className="transition-transform group-open:rotate-90">›</span>
            {isDE ? 'Andere Wege' : 'Other ways'}
          </summary>
          <div className="mt-3 space-y-3">
            {hasOnlinewache && staEmail && (
              <Path
                badge={isDE ? 'formell' : 'formal'}
                badgeTone="indigo"
                title={isDE ? 'Email an die Staatsanwaltschaft' : 'Email the Staatsanwaltschaft'}
                time={isDE ? '10 Min' : '10 min'}
                sign={isDE ? 'Keine Unterschrift nötig' : 'No signature needed'}
                body={<><span className="font-mono text-slate-200">{staEmail}</span>{isDE ? ' — PDF anhängen.' : ' — attach the PDF.'}</>}
              />
            )}
            <Path
              badge={isDE ? 'falls du Papier bevorzugst' : 'if you prefer paper'}
              badgeTone="slate"
              title={isDE ? 'Per Brief' : 'By post'}
              time={isDE ? '20 Min + Postweg' : '20 min + postal time'}
              sign={isDE
                ? 'Unterschrift nicht erforderlich (§ 158 StPO, 2024) — dein Name im PDF genügt'
                : 'No signature required (§ 158 StPO, 2024) — your name in the PDF is enough'}
              body={
                <>
                  {isDE ? 'PDF ausdrucken, einkuvertieren. ' : 'Print the PDF, put it in an envelope. '}
                  {staName ? (
                    <span className="text-slate-200">{staName}{staAddress ? `, ${staAddress}` : ''}</span>
                  ) : (
                    <em className="text-slate-500">{isDE ? '(Adresse erscheint nach Bundesland-Wahl.)' : '(address appears after you pick a state.)'}</em>
                  )}
                  {isDE ? ' Eingeschrieben empfohlen.' : ' Registered mail recommended.'}
                </>
              }
            />
          </div>
        </details>

        {artefacts.netzdg_emls.length > 0 && (
          <p className="text-xs text-slate-400 leading-relaxed pt-1 border-t border-slate-700/50 mt-3">
            {isDE
              ? 'Zusätzlich: die NetzDG-Meldungen oben sind separate Mails an die Plattformen — doppelklicken öffnet sie in deinem Mail-Programm. Die Plattform muss innerhalb 24 Stunden bis 7 Tagen den Inhalt prüfen.'
              : "Also: the NetzDG reports above are separate emails to the platforms — double-click opens them in your mail client. Platforms must review the content within 24h to 7 days."}
          </p>
        )}
      </div>
    </div>
  )
}

function Path({
  badge,
  badgeTone,
  title,
  time,
  sign,
  body,
}: {
  badge: string
  badgeTone: 'emerald' | 'indigo' | 'slate'
  title: string
  time: string
  sign: string
  body: React.ReactNode
}) {
  const badgeCls = {
    emerald: 'bg-emerald-900/40 text-emerald-300 border-emerald-800/40',
    indigo: 'bg-indigo-900/40 text-indigo-300 border-indigo-800/40',
    slate: 'bg-slate-800 text-slate-400 border-slate-700',
  }[badgeTone]
  return (
    <div className="rounded-lg bg-slate-950/40 border border-slate-700/60 p-3">
      <div className="flex items-baseline justify-between gap-3 mb-1">
        <h4 className="text-slate-100 font-medium">{title}</h4>
        <span className={`text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded border ${badgeCls}`}>
          {badge}
        </span>
      </div>
      <p className="text-slate-300 leading-relaxed">{body}</p>
      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500">
        <span>⏱ {time}</span>
        <span>✎ {sign}</span>
      </div>
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
            {isDE ? 'Oder: direkt online einreichen' : 'Or: file online directly'}
          </div>
          <p className="text-sm text-slate-200 leading-relaxed">
            {isDE
              ? `Die Onlinewache ${onlinewache.bundesland_name} ist der offizielle Polizei-Kanal, rund um die Uhr erreichbar. Oft schneller als der Brief an die Staatsanwaltschaft.`
              : `The Onlinewache ${onlinewache.bundesland_name} is the official police channel, available 24/7. Often faster than mailing the prosecutor.`}
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
