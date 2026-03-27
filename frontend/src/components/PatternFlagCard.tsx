import type { PatternFlag } from '../types'
import type { Lang } from '../i18n'
import { t } from '../i18n'
import SeverityBadge from './SeverityBadge'

interface Props {
  flag: PatternFlag
  lang: Lang
}

const patternIcons: Record<string, string> = {
  coordinated_attack: '🔗',
  escalation: '📈',
  repeat_offender: '🔁',
  serial_harasser: '⚡',
}

export default function PatternFlagCard({ flag, lang }: Props) {
  const isDE = lang === 'de'
  return (
    <div className="bg-slate-800 border border-yellow-700 rounded-lg p-4">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-lg">{patternIcons[flag.type] ?? '⚑'}</span>
        <span className="font-semibold text-yellow-300 text-sm">
          {t(lang, `pattern.${flag.type}`)}
        </span>
        <SeverityBadge severity={flag.severity} lang={lang} />
        <span className="ml-auto text-xs text-slate-400">
          {flag.evidence_count} {isDE ? 'Belege' : 'items'}
        </span>
      </div>
      <p className="text-slate-300 text-sm">
        {isDE ? flag.description_de : flag.description}
      </p>
    </div>
  )
}
