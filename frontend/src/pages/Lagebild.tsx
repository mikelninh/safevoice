import { useEffect, useState } from 'react'
import type { Lang } from '../i18n'
import { getPublicStats, type PublicStats, type StatBucket } from '../services/api'

/**
 * Lagebild digitale Gewalt — the public aggregate page.
 *
 * Privacy by construction: only counts, never content or identities. Makes the
 * invisible (unreported online violence) visible without amplifying any single
 * incident. The data comes from /stats/public (k-anon, aggregates only).
 */

const SEVERITY_COLOR: Record<string, string> = {
  low: '#10b981',
  medium: '#f59e0b',
  high: '#f97316',
  critical: '#ef4444',
}

export default function Lagebild({ lang }: { lang: Lang }) {
  const isDE = lang === 'de'
  const [stats, setStats] = useState<PublicStats | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getPublicStats().then(setStats).catch((e) => setError(String(e)))
  }, [])

  if (error) {
    return (
      <main className="min-h-screen bg-slate-950 text-slate-200 px-6 py-20 text-center">
        <p className="text-slate-400">{isDE ? 'Lagebild nicht erreichbar.' : 'Stats unavailable.'}</p>
      </main>
    )
  }
  if (!stats) {
    return (
      <main className="min-h-screen bg-slate-950 text-slate-500 px-6 py-20 text-center">
        {isDE ? 'Lädt …' : 'Loading …'}
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100">
      <section className="max-w-4xl mx-auto px-6 sm:px-10 py-16 sm:py-24">
        <p className="text-xs font-mono uppercase tracking-[0.25em] text-indigo-400 mb-5">
          {isDE ? 'Lagebild · digitale Gewalt' : 'The picture · online violence'}
        </p>
        <h1 className="font-serif text-4xl sm:text-6xl leading-[1.05] tracking-tight mb-6" style={{ fontFamily: 'Georgia, serif' }}>
          {isDE ? 'Das Unsichtbare, gezählt.' : 'The invisible, counted.'}
        </h1>
        <p className="text-lg text-slate-400 max-w-2xl leading-relaxed">
          {isDE
            ? 'Gemeldeter Schaden ist Daten. Ungemeldeter ist unsichtbar. Das ist, was SafeVoice bisher sieht — nur Zahlen, kein Inhalt, keine Identitäten.'
            : 'Reported harm is data. Unreported harm is invisible. This is what SafeVoice has seen so far — counts only, no content, no identities.'}
        </p>

        {/* Hero number */}
        <div className="mt-14 mb-16">
          <div className="font-serif text-7xl sm:text-8xl font-bold text-white leading-none" style={{ fontFamily: 'Georgia, serif' }}>
            {stats.total_incidents.toLocaleString()}
          </div>
          <div className="mt-3 text-sm font-mono uppercase tracking-[0.2em] text-slate-500">
            {isDE ? 'dokumentierte Vorfälle' : 'documented incidents'}
          </div>
        </div>

        <div className="grid sm:grid-cols-2 gap-x-12 gap-y-12">
          <Block title={isDE ? 'Nach Schwere' : 'By severity'}>
            {stats.by_severity.map((b) => (
              <Bar key={b.label} b={b} total={stats.total_incidents} color={SEVERITY_COLOR[b.label] || '#818cf8'}
                   label={severityLabel(b.label, isDE)} />
            ))}
          </Block>

          <Block title={isDE ? 'Nach Art' : 'By type'}>
            {top(stats.by_category, 6).map((b) => (
              <Bar key={b.label} b={b} total={stats.total_incidents} color="#818cf8" label={b.label} />
            ))}
          </Block>

          <Block title={isDE ? 'Nach Paragraph' : 'By statute'}>
            {top(stats.by_statute, 6).map((b) => (
              <Bar key={b.label} b={b} total={stats.total_incidents} color="#a78bfa" label={b.label} />
            ))}
          </Block>

          <Block title={isDE ? 'Nach Plattform' : 'By platform'}>
            {stats.by_platform.length === 0 ? (
              <p className="text-sm text-slate-600">{isDE ? 'Noch keine Daten.' : 'No data yet.'}</p>
            ) : (
              top(stats.by_platform, 6).map((b) => (
                <Bar key={b.label} b={b} total={stats.total_incidents} color="#64748b" label={b.label} />
              ))
            )}
          </Block>
        </div>

        <p className="mt-16 text-xs text-slate-600 leading-relaxed border-t border-slate-800 pt-6 max-w-2xl">
          {isDE
            ? 'Nur aggregierte Zahlen. Kein Inhalt, keine Identitäten, keine Einzelfälle. Kleine Werte werden unterdrückt. SafeVoice ist anonym — diese Seite kann niemanden identifizieren.'
            : 'Aggregate counts only. No content, no identities, no individual cases. Small values are suppressed. SafeVoice is anonymous — this page cannot identify anyone.'}
        </p>
      </section>
    </main>
  )
}

function Block({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h2 className="text-xs font-mono uppercase tracking-[0.22em] text-slate-500 mb-5">{title}</h2>
      <div className="space-y-3.5">{children}</div>
    </div>
  )
}

function Bar({ b, total, color, label }: { b: StatBucket; total: number; color: string; label: string }) {
  const pct = total > 0 ? Math.round((b.count / total) * 100) : 0
  return (
    <div>
      <div className="flex items-baseline justify-between text-sm mb-1.5">
        <span className="text-slate-300">{label}</span>
        <span className="font-mono text-slate-500 text-xs tabular-nums">{b.count}</span>
      </div>
      <div className="h-1.5 rounded-full bg-slate-800/80 overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${Math.max(pct, 3)}%`, backgroundColor: color }} />
      </div>
    </div>
  )
}

function top(arr: StatBucket[], n: number): StatBucket[] {
  return [...arr].sort((a, b) => b.count - a.count).slice(0, n)
}

function severityLabel(s: string, isDE: boolean): string {
  const de: Record<string, string> = { low: 'niedrig', medium: 'mittel', high: 'hoch', critical: 'kritisch' }
  return isDE ? de[s] || s : s
}
