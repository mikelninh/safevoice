import type { GermanLaw } from '../types'
import type { Lang } from '../i18n'

interface Props {
  law: GermanLaw
  lang: Lang
}

export default function LawCard({ law, lang }: Props) {
  const isDE = lang === 'de'
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg p-4">
      <div className="flex items-start justify-between gap-2 mb-2">
        <span className="font-mono text-indigo-400 font-bold text-sm">{law.paragraph}</span>
        <span className="text-xs text-slate-400 bg-slate-700 px-2 py-0.5 rounded">
          {law.max_penalty}
        </span>
      </div>
      <p className="font-semibold text-slate-100 text-sm mb-1">
        {isDE ? law.title_de : law.title}
      </p>
      <p className="text-slate-400 text-xs mb-2">
        {isDE ? law.description_de : law.description}
      </p>
      <div className="border-t border-slate-700 pt-2">
        <p className="text-xs text-slate-300">
          <span className="text-indigo-400 font-medium">
            {isDE ? 'Warum relevant: ' : 'Why applicable: '}
          </span>
          {isDE ? law.applies_because_de : law.applies_because}
        </p>
      </div>
    </div>
  )
}
