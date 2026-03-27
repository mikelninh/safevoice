import type { Severity } from '../types'
import { t, type Lang } from '../i18n'

const colors: Record<Severity, string> = {
  low: 'bg-slate-700 text-slate-200',
  medium: 'bg-yellow-900 text-yellow-200 border border-yellow-600',
  high: 'bg-orange-900 text-orange-200 border border-orange-500',
  critical: 'bg-red-900 text-red-200 border border-red-500 animate-pulse',
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
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-semibold ${colors[severity]}`}>
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
