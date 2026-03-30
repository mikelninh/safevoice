/**
 * StatsBar — trust signals on home page.
 * Honest stats about what SafeVoice does, not inflated numbers.
 */
import type { Lang } from '../i18n'

interface Props { lang: Lang }

export default function StatsBar({ lang }: Props) {
  const isDE = lang === 'de'

  const stats = [
    {
      value: '8',
      label: isDE ? 'Deutsche Gesetze abgedeckt' : 'German laws covered',
    },
    {
      value: '30s',
      label: isDE ? 'Von Text zur Anzeige' : 'From text to report',
    },
    {
      value: '4',
      label: isDE ? 'Sprachen erkannt' : 'Languages detected',
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
