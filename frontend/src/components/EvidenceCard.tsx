import type { EvidenceItem } from '../types'
import type { Lang } from '../i18n'
import SeverityBadge from './SeverityBadge'
import CategoryTag from './CategoryTag'
import LawCard from './LawCard'
import { useState } from 'react'
import { updateEvidenceAuthor } from '../services/storage'
import HashVerifier from './HashVerifier'

interface Props {
  evidence: EvidenceItem
  /** Optional case ID — when present, the @author handle becomes inline-editable. */
  caseId?: string
  lang: Lang
}

export default function EvidenceCard({ evidence, caseId, lang }: Props) {
  const [expanded, setExpanded] = useState(false)
  const [editingAuthor, setEditingAuthor] = useState(false)
  const [authorDraft, setAuthorDraft] = useState(evidence.author_username)
  const [showVerifier, setShowVerifier] = useState(false)
  const isDE = lang === 'de'
  const c = evidence.classification

  const date = new Date(evidence.captured_at).toLocaleString(
    isDE ? 'de-DE' : 'en-GB',
    { dateStyle: 'medium', timeStyle: 'short' }
  )

  const commitAuthor = () => {
    if (!caseId) return
    const cleaned = authorDraft.trim().replace(/^@/, '') || 'unknown'
    if (cleaned !== evidence.author_username) {
      updateEvidenceAuthor(caseId, evidence.id, cleaned)
      evidence.author_username = cleaned
    }
    setEditingAuthor(false)
  }

  return (
    <div className={`bg-slate-800/60 rounded-xl ${
      c?.requires_immediate_action ? 'ring-1 ring-red-700/60' : ''
    }`}>
      {c?.requires_immediate_action && (
        <div className="bg-red-950/70 px-4 py-2 rounded-t-xl flex items-center gap-2">
          <span className="text-red-400 leading-none">⚠</span>
          <span className="text-red-100 font-semibold text-xs">
            {isDE ? 'Sofortiger Handlungsbedarf' : 'Immediate action required'}
          </span>
        </div>
      )}

      <div className="p-4 sm:p-5">
        {/* Header */}
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="min-w-0 flex items-center gap-3 flex-wrap">
            {editingAuthor && caseId ? (
              <input
                value={authorDraft}
                onChange={e => setAuthorDraft(e.target.value)}
                onBlur={commitAuthor}
                onKeyDown={e => {
                  if (e.key === 'Enter') (e.target as HTMLInputElement).blur()
                  if (e.key === 'Escape') {
                    setAuthorDraft(evidence.author_username)
                    setEditingAuthor(false)
                  }
                }}
                autoFocus
                placeholder="username"
                className="bg-slate-900 border border-slate-600 rounded px-2 py-0.5 text-slate-200 placeholder-slate-500 text-sm font-mono w-40"
              />
            ) : (
              <button
                onClick={() => caseId && setEditingAuthor(true)}
                disabled={!caseId}
                title={caseId ? (isDE ? 'Verfasser:in bearbeiten' : 'Edit author') : undefined}
                className={`text-indigo-300 font-mono text-sm ${caseId ? 'hover:text-indigo-200 cursor-pointer' : 'cursor-default'}`}
              >
                @{evidence.author_username}
                {caseId && <span className="text-slate-500 ml-1 text-xs">✎</span>}
              </button>
            )}
            <span className="text-slate-500 text-xs">{date}</span>
          </div>
          {c && <SeverityBadge severity={c.severity} lang={lang} />}
        </div>

        {/* Content */}
        <blockquote className="bg-slate-900/70 rounded-lg px-4 py-3 text-slate-300 text-sm italic border-l-2 border-slate-600 mb-4 leading-relaxed">
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
          <p className="text-slate-300 text-sm mb-3 leading-relaxed">
            {isDE ? c.summary_de : c.summary}
          </p>
        )}

        {/* Expand button */}
        <button
          onClick={() => setExpanded(e => !e)}
          className="text-indigo-300 hover:text-indigo-200 text-xs font-medium transition-colors"
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
            <div className="border-t border-slate-700/60 pt-3 space-y-2">
              <div>
                <div className="text-slate-400 text-xs uppercase tracking-wider mb-1">
                  {isDE ? 'Prüfsumme (SHA-256)' : 'Checksum (SHA-256)'}
                </div>
                <div className="text-xs text-slate-500 font-mono break-all">{evidence.content_hash}</div>
                <p className="text-slate-500 text-xs mt-1.5 leading-relaxed font-sans">
                  {isDE
                    ? 'Eindeutiger Fingerabdruck des Inhalts zum Erfassungszeitpunkt. Polizei, Gericht, Anwält:in oder NGO können damit prüfen, dass der Text nachträglich nicht verändert wurde — den selben Hash über den Originalinhalt rechnen und vergleichen. Du musst damit nichts tun; er liegt deinem Bericht bei.'
                    : 'Unique fingerprint of the content at capture time. Police, court, lawyer or NGO can verify the text wasn\'t altered later — they recompute the same hash on the original and compare. You don\'t need to do anything with it; it\'s included in your report.'}
                </p>
                <button
                  type="button"
                  onClick={() => setShowVerifier(true)}
                  className="text-indigo-300 hover:text-indigo-200 text-xs mt-2 underline-offset-2 hover:underline font-sans"
                >
                  {isDE ? '↗ Hash jetzt im Browser prüfen' : '↗ Verify hash in browser'}
                </button>
              </div>
              {evidence.archived_url && (
                <div>
                  <div className="text-slate-400 text-xs uppercase tracking-wider mb-1">
                    {isDE ? 'Archiv-Link' : 'Archive link'}
                  </div>
                  <a href={evidence.archived_url} className="text-indigo-400 hover:underline text-xs font-mono break-all" target="_blank" rel="noopener noreferrer">{evidence.archived_url}</a>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {showVerifier && (
        <HashVerifier
          expectedHash={evidence.content_hash}
          originalText={evidence.content_text}
          lang={lang}
          onClose={() => setShowVerifier(false)}
        />
      )}
    </div>
  )
}
