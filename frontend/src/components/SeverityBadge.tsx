import type { Severity } from '../types'
import { t, type Lang } from '../i18n'

const colors: Record<Severity, string> = {
  low: 'bg-slate-700/70 text-slate-200',
  medium: 'bg-yellow-950/80 text-yellow-200 ring-1 ring-yellow-700/60',
  high: 'bg-orange-950/80 text-orange-200 ring-1 ring-orange-600/70',
  critical: 'bg-red-950/80 text-red-200 ring-1 ring-red-500/70',
}

const icons: Record<Severity, string> = {
  low: '○',
  medium: '◐',
  high: '●',
  critical: '⚠',
}

interface Props {
  severity: Severity
  lang: Lang
  showDesc?: boolean
}

export default function SeverityBadge({ severity, lang, showDesc }: Props) {
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold ${colors[severity]}`}>
      <span>{icons[severity]}</span>
      {t(lang, `severity.${severity}`)}
      {showDesc && (
        <span className="ml-1 font-normal opacity-80 text-xs hidden sm:inline">
          — {t(lang, `severity.${severity}.desc`)}
        </span>
      )}
    </span>
  )
}
