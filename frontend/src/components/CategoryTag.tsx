import type { Category } from '../types'
import { t, type Lang } from '../i18n'

const colors: Record<Category, string> = {
  harassment: 'bg-slate-700 text-slate-200',
  threat: 'bg-orange-900 text-orange-200',
  death_threat: 'bg-red-900 text-red-200',
  defamation: 'bg-purple-900 text-purple-200',
  misogyny: 'bg-pink-900 text-pink-200',
  body_shaming: 'bg-rose-900 text-rose-200',
  coordinated_attack: 'bg-yellow-900 text-yellow-200',
  false_facts: 'bg-blue-900 text-blue-200',
  sexual_harassment: 'bg-fuchsia-900 text-fuchsia-200',
  scam: 'bg-amber-900 text-amber-200',
  phishing: 'bg-lime-900 text-lime-200',
  investment_fraud: 'bg-yellow-900 text-yellow-200',
  romance_scam: 'bg-pink-900 text-pink-200',
  impersonation: 'bg-cyan-900 text-cyan-200',
}

interface Props {
  category: Category
  lang: Lang
}

export default function CategoryTag({ category, lang }: Props) {
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${colors[category]}`}>
      {t(lang, `category.${category}`)}
    </span>
  )
}
