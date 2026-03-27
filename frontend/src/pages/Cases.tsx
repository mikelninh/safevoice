import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchCases } from '../services/api'
import { t, type Lang } from '../i18n'
import type { Case } from '../types'
import SeverityBadge from '../components/SeverityBadge'
import { getLocalCases, migrateLegacyEvidence } from '../services/storage'

interface Props { lang: Lang }

export default function Cases({ lang }: Props) {
  const [cases, setCases] = useState<Case[]>([])
  const [loading, setLoading] = useState(true)
  const isDE = lang === 'de'

  useEffect(() => {
    // Migrate any legacy evidence items from old format
    migrateLegacyEvidence()

    // Load local cases + demo cases from API
    const localCases = getLocalCases()
    fetchCases()
      .then(apiCases => {
        // Merge: local cases first, then demo cases (avoid ID collisions)
        const localIds = new Set(localCases.map(c => c.id))
        const demoCases = apiCases.filter(c => !localIds.has(c.id))
        setCases([...localCases, ...demoCases])
      })
      .catch(() => {
        // API down — show local cases only
        setCases(localCases)
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center text-slate-400">
        {isDE ? 'Wird geladen...' : 'Loading...'}
      </div>
    )
  }

  if (cases.length === 0) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <p className="text-slate-400 mb-4">{t(lang, 'cases.empty')}</p>
        <Link
          to="/analyze"
          className="inline-block bg-indigo-600 hover:bg-indigo-500 text-white font-semibold px-6 py-3 rounded-xl transition-colors"
        >
          {t(lang, 'cases.empty.cta')}
        </Link>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">{t(lang, 'cases.title')}</h1>
        <Link
          to="/analyze"
          className="bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
        >
          + {isDE ? 'Neuer Fall' : 'New case'}
        </Link>
      </div>

      <div className="space-y-3">
        {cases.map(c => (
          <Link key={c.id} to={`/cases/${c.id}`} className="block">
            <div className="bg-slate-800 border border-slate-700 hover:border-slate-500 rounded-xl p-4 transition-colors">
              <div className="flex items-start justify-between gap-3 mb-2">
                <h2 className="text-white font-semibold text-sm">{c.title}</h2>
                <SeverityBadge severity={c.overall_severity} lang={lang} />
              </div>

              <div className="flex items-center gap-4 text-xs text-slate-500">
                <span>
                  {c.evidence_items.length} {t(lang, 'cases.evidence')}
                </span>
                {c.pattern_flags.length > 0 && (
                  <span className="text-yellow-400">
                    ⚑ {c.pattern_flags.length} {t(lang, 'cases.patterns')}
                  </span>
                )}
                <span className="ml-auto">
                  {new Date(c.updated_at).toLocaleDateString(isDE ? 'de-DE' : 'en-GB')}
                </span>
              </div>

              {c.victim_context && (
                <p className="text-slate-400 text-xs mt-2 line-clamp-2">
                  {c.victim_context}
                </p>
              )}
            </div>
          </Link>
        ))}
      </div>
    </div>
  )
}
