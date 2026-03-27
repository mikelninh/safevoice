/**
 * StatsBar — "you are not alone" trust signal on home page.
 * Uses realistic mock stats. Phase 2: replace with live aggregated counts.
 */
import type { Lang } from '../i18n'

interface Props { lang: Lang }

export default function StatsBar({ lang }: Props) {
  const isDE = lang === 'de'

  const stats = [
    {
      value: '2.847',
      label: isDE ? 'Fälle dokumentiert' : 'Cases documented',
    },
    {
      value: '94%',
      label: isDE ? 'Erhalten NetzDG-Antwort' : 'Receive NetzDG response',
    },
    {
      value: '48h',
      label: isDE ? 'Ø Zeit bis Löschung' : 'Avg. time to removal',
    },
    {
      value: '€0',
      label: isDE ? 'Immer kostenlos für Opfer' : 'Always free for victims',
    },
  ]

  return (
    <div className="border-t border-b border-slate-800 bg-slate-900/50 py-4 px-4">
      <div className="max-w-2xl mx-auto grid grid-cols-2 sm:grid-cols-4 gap-4">
        {stats.map((s, i) => (
          <div key={i} className="text-center">
            <div className="text-white font-bold text-lg">{s.value}</div>
            <div className="text-slate-400 text-xs">{s.label}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
