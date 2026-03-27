import type { EvidenceItem } from '../types'
import type { Lang } from '../i18n'
import SeverityBadge from './SeverityBadge'
import CategoryTag from './CategoryTag'
import LawCard from './LawCard'
import { useState } from 'react'

interface Props {
  evidence: EvidenceItem
  lang: Lang
}

export default function EvidenceCard({ evidence, lang }: Props) {
  const [expanded, setExpanded] = useState(false)
  const isDE = lang === 'de'
  const c = evidence.classification

  const date = new Date(evidence.captured_at).toLocaleString(
    isDE ? 'de-DE' : 'en-GB',
    { dateStyle: 'medium', timeStyle: 'short' }
  )

  return (
    <div className={`bg-slate-800 rounded-xl border ${
      c?.requires_immediate_action
        ? 'border-red-600'
        : c?.severity === 'high'
        ? 'border-orange-700'
        : 'border-slate-700'
    }`}>
      {c?.requires_immediate_action && (
        <div className="bg-red-900 border-b border-red-700 px-4 py-2 rounded-t-xl flex items-center gap-2">
          <span className="text-red-300 font-bold text-sm">
            ⚠ {isDE ? 'Sofortiger Handlungsbedarf' : 'Immediate action required'}
          </span>
        </div>
      )}

      <div className="p-4">
        {/* Header */}
        <div className="flex items-start justify-between gap-3 mb-3">
          <div>
            <span className="text-indigo-400 font-mono text-sm">@{evidence.author_username}</span>
            <span className="text-slate-500 text-xs ml-3">{date}</span>
          </div>
          {c && <SeverityBadge severity={c.severity} lang={lang} />}
        </div>

        {/* Content */}
        <blockquote className="bg-slate-900 rounded-lg px-4 py-3 text-slate-300 text-sm italic border-l-4 border-slate-600 mb-3">
          "{evidence.content_text}"
        </blockquote>

        {/* Categories */}
        {c && (
          <div className="flex flex-wrap gap-1.5 mb-3">
            {c.categories.map(cat => (
              <CategoryTag key={cat} category={cat} lang={lang} />
            ))}
          </div>
        )}

        {/* Summary */}
        {c && (
          <p className="text-slate-400 text-sm mb-3">
            {isDE ? c.summary_de : c.summary}
          </p>
        )}

        {/* Expand button */}
        <button
          onClick={() => setExpanded(e => !e)}
          className="text-indigo-400 hover:text-indigo-300 text-xs font-medium transition-colors"
        >
          {expanded
            ? (isDE ? '▲ Weniger anzeigen' : '▲ Show less')
            : (isDE ? '▼ Rechtliche Details anzeigen' : '▼ Show legal details')
          }
        </button>

        {/* Expanded legal details */}
        {expanded && c && (
          <div className="mt-4 space-y-3">
            <div>
              <h4 className="text-slate-400 text-xs uppercase tracking-wider mb-2">
                {isDE ? 'Mögliche Konsequenzen' : 'Potential consequences'}
              </h4>
              <p className="text-slate-300 text-sm">
                {isDE ? c.potential_consequences_de : c.potential_consequences}
              </p>
            </div>
            <div>
              <h4 className="text-slate-400 text-xs uppercase tracking-wider mb-2">
                {isDE ? 'Relevante Gesetze' : 'Applicable laws'}
              </h4>
              <div className="space-y-2">
                {c.applicable_laws.map(law => (
                  <LawCard key={law.paragraph} law={law} lang={lang} />
                ))}
              </div>
            </div>
            <div className="text-xs text-slate-500 font-mono border-t border-slate-700 pt-3">
              <div>Hash: {evidence.content_hash}</div>
              {evidence.archived_url && (
                <div>Archive: <a href={evidence.archived_url} className="text-indigo-400 hover:underline" target="_blank" rel="noopener noreferrer">{evidence.archived_url}</a></div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
