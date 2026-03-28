/**
 * Dashboard page — aggregate statistics for institutional users.
 * Shows anonymized case data, category breakdown, platform stats.
 */
import { useEffect, useState } from 'react'
import { t, type Lang } from '../i18n'

interface Props { lang: Lang }

interface DashboardData {
  total_cases: number
  total_evidence_items: number
  severity_distribution: Record<string, number>
  category_distribution: Record<string, number>
  platform_distribution: Record<string, number>
  requires_immediate_action_count: number
  avg_evidence_per_case: number
  top_categories: { category: string; count: number }[]
}

const SEVERITY_COLORS: Record<string, string> = {
  critical: 'bg-red-500',
  high: 'bg-orange-500',
  medium: 'bg-yellow-500',
  low: 'bg-slate-500',
}

const SEVERITY_LABELS_DE: Record<string, string> = {
  critical: 'Kritisch',
  high: 'Hoch',
  medium: 'Mittel',
  low: 'Niedrig',
}

export default function Dashboard({ lang }: Props) {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const isDE = lang === 'de'

  useEffect(() => {
    fetch('/api/dashboard/stats')
      .then(r => r.json())
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-16 text-center text-slate-400">
        {isDE ? 'Dashboard wird geladen...' : 'Loading dashboard...'}
      </div>
    )
  }

  if (!data) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-16 text-center text-slate-400">
        {isDE ? 'Dashboard nicht verfügbar.' : 'Dashboard unavailable.'}
      </div>
    )
  }

  const totalSeverity = Object.values(data.severity_distribution).reduce((a, b) => a + b, 0) || 1

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-white mb-2">
        {isDE ? 'Dashboard' : 'Dashboard'}
      </h1>
      <p className="text-slate-400 text-sm mb-8">
        {isDE ? 'Anonymisierte Gesamtstatistik aller dokumentierten Fälle.' : 'Anonymized aggregate statistics across all documented cases.'}
      </p>

      {/* Key metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
        {[
          { value: data.total_cases, label: isDE ? 'Fälle' : 'Cases' },
          { value: data.total_evidence_items, label: isDE ? 'Beweismittel' : 'Evidence items' },
          { value: data.requires_immediate_action_count, label: isDE ? 'Sofortmaßnahmen' : 'Urgent actions' },
          { value: data.avg_evidence_per_case, label: isDE ? 'Ø pro Fall' : 'Avg per case' },
        ].map((m, i) => (
          <div key={i} className="bg-slate-800 border border-slate-700 rounded-xl p-4 text-center">
            <div className="text-2xl font-bold text-white">{m.value}</div>
            <div className="text-slate-400 text-xs mt-1">{m.label}</div>
          </div>
        ))}
      </div>

      {/* Severity distribution */}
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 mb-6">
        <h2 className="text-slate-400 text-xs uppercase tracking-wider mb-4">
          {isDE ? 'Schweregrade' : 'Severity distribution'}
        </h2>
        <div className="space-y-3">
          {['critical', 'high', 'medium', 'low'].map(sev => {
            const count = data.severity_distribution[sev] || 0
            const pct = Math.round((count / totalSeverity) * 100)
            return (
              <div key={sev} className="flex items-center gap-3">
                <span className="text-slate-300 text-sm w-20">
                  {isDE ? SEVERITY_LABELS_DE[sev] : sev.charAt(0).toUpperCase() + sev.slice(1)}
                </span>
                <div className="flex-1 h-3 bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${SEVERITY_COLORS[sev]}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
                <span className="text-slate-500 text-xs w-12 text-right">{count} ({pct}%)</span>
              </div>
            )
          })}
        </div>
      </div>

      {/* Top categories */}
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 mb-6">
        <h2 className="text-slate-400 text-xs uppercase tracking-wider mb-4">
          {isDE ? 'Häufigste Kategorien' : 'Top categories'}
        </h2>
        <div className="space-y-2">
          {data.top_categories.map((cat, i) => (
            <div key={cat.category} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-slate-500 text-xs w-5">{i + 1}.</span>
                <span className="text-slate-200 text-sm">
                  {t(lang, `category.${cat.category}`)}
                </span>
              </div>
              <span className="text-indigo-400 text-sm font-medium">{cat.count}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Platform breakdown */}
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 mb-6">
        <h2 className="text-slate-400 text-xs uppercase tracking-wider mb-4">
          {isDE ? 'Plattformen' : 'Platforms'}
        </h2>
        <div className="grid grid-cols-2 gap-3">
          {Object.entries(data.platform_distribution).map(([platform, count]) => (
            <div key={platform} className="flex items-center justify-between bg-slate-900 rounded-lg px-3 py-2">
              <span className="text-slate-300 text-sm capitalize">{platform}</span>
              <span className="text-indigo-400 text-sm font-medium">{count}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Anonymization notice */}
      <div className="text-center text-slate-500 text-xs">
        {isDE
          ? 'Alle Daten sind vollständig anonymisiert. Keine personenbezogenen Daten werden angezeigt.'
          : 'All data is fully anonymized. No personal data is displayed.'}
      </div>
    </div>
  )
}
