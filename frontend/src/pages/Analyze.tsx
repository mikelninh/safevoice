import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { analyzeText } from '../services/api'
import { t, type Lang } from '../i18n'
import type { EvidenceItem } from '../types'
import SeverityBadge from '../components/SeverityBadge'
import CategoryTag from '../components/CategoryTag'
import LawCard from '../components/LawCard'

interface Props { lang: Lang }

export default function Analyze({ lang }: Props) {
  const [params] = useSearchParams()
  const [url, setUrl] = useState(params.get('url') ?? '')
  const [text, setText] = useState(params.get('text') ?? '')
  const [author, setAuthor] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<EvidenceItem | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)
  const isDE = lang === 'de'

  // Auto-analyze if coming from share target
  useEffect(() => {
    const sharedText = params.get('text') ?? params.get('url')
    if (sharedText && !result) {
      handleSubmit(sharedText)
    }
  }, [])

  const handleSubmit = async (overrideText?: string) => {
    const content = overrideText ?? text ?? url
    if (!content.trim()) return

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const res = await analyzeText(content, author || 'unknown', url)
      setResult(res.evidence)
    } catch {
      setError(isDE ? 'Analyse fehlgeschlagen. Bitte versuche es erneut.' : 'Analysis failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = () => {
    // MVP: save to localStorage
    if (!result) return
    const existing = JSON.parse(localStorage.getItem('sv_evidence') ?? '[]')
    existing.push(result)
    localStorage.setItem('sv_evidence', JSON.stringify(existing))
    setSaved(true)
  }

  const c = result?.classification

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-white mb-6">
        {t(lang, 'analyze.title')}
      </h1>

      {/* Form */}
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 mb-6 space-y-4">
        <div>
          <label className="block text-slate-300 text-sm font-medium mb-1.5">
            {t(lang, 'analyze.url.label')}
          </label>
          <input
            type="url"
            value={url}
            onChange={e => setUrl(e.target.value)}
            placeholder={t(lang, 'analyze.url.placeholder')}
            className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2.5 text-slate-200 placeholder-slate-500 text-sm focus:outline-none focus:border-indigo-500"
          />
        </div>

        <div className="relative flex items-center gap-3">
          <div className="flex-1 h-px bg-slate-700"></div>
          <span className="text-slate-500 text-xs">{isDE ? 'oder' : 'or'}</span>
          <div className="flex-1 h-px bg-slate-700"></div>
        </div>

        <div>
          <label className="block text-slate-300 text-sm font-medium mb-1.5">
            {t(lang, 'analyze.text.label')}
          </label>
          <textarea
            value={text}
            onChange={e => setText(e.target.value)}
            placeholder={t(lang, 'analyze.text.placeholder')}
            rows={4}
            className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2.5 text-slate-200 placeholder-slate-500 text-sm focus:outline-none focus:border-indigo-500 resize-none"
          />
        </div>

        <div>
          <label className="block text-slate-300 text-sm font-medium mb-1.5">
            {t(lang, 'analyze.author.label')}
          </label>
          <input
            type="text"
            value={author}
            onChange={e => setAuthor(e.target.value)}
            placeholder={t(lang, 'analyze.author.placeholder')}
            className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2.5 text-slate-200 placeholder-slate-500 text-sm focus:outline-none focus:border-indigo-500"
          />
        </div>

        <button
          onClick={() => handleSubmit()}
          disabled={loading || (!text.trim() && !url.trim())}
          className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold py-3 rounded-xl transition-colors"
        >
          {loading ? t(lang, 'analyze.analyzing') : t(lang, 'analyze.submit')}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-900/40 border border-red-700 rounded-xl p-4 text-red-300 text-sm mb-6">
          {error}
        </div>
      )}

      {/* Result */}
      {result && c && (
        <div className="space-y-4">
          {/* Immediate action alert */}
          {c.requires_immediate_action && (
            <div className="bg-red-900 border border-red-600 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-xl">⚠</span>
                <span className="text-red-200 font-bold">
                  {t(lang, 'result.immediate_action')}
                </span>
              </div>
              <p className="text-red-300 text-sm">
                {t(lang, 'result.immediate_action.desc')}
              </p>
              <div className="mt-3 flex flex-col sm:flex-row gap-2">
                <a
                  href="https://www.onlinewache.polizei.de"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-1 text-center bg-red-700 hover:bg-red-600 text-white text-sm font-semibold py-2.5 rounded-lg transition-colors"
                >
                  {t(lang, 'action.polizei')} →
                </a>
                <a
                  href="https://hateaid.org"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-1 text-center bg-slate-700 hover:bg-slate-600 text-slate-200 text-sm font-semibold py-2.5 rounded-lg transition-colors"
                >
                  {t(lang, 'action.hateaid')} →
                </a>
              </div>
            </div>
          )}

          {/* Classification result */}
          <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <SeverityBadge severity={c.severity} lang={lang} showDesc />
              <span className="text-slate-500 text-xs">
                {t(lang, 'result.confidence')}: {Math.round(c.confidence * 100)}%
              </span>
            </div>

            <div className="flex flex-wrap gap-1.5">
              {c.categories.map(cat => (
                <CategoryTag key={cat} category={cat} lang={lang} />
              ))}
            </div>

            <p className="text-slate-300 text-sm">
              {isDE ? c.summary_de : c.summary}
            </p>

            <div>
              <h3 className="text-slate-400 text-xs uppercase tracking-wider mb-2">
                {t(lang, 'result.consequences')}
              </h3>
              <p className="text-slate-300 text-sm">
                {isDE ? c.potential_consequences_de : c.potential_consequences}
              </p>
            </div>

            <div>
              <h3 className="text-slate-400 text-xs uppercase tracking-wider mb-3">
                {t(lang, 'result.laws')}
              </h3>
              <div className="space-y-2">
                {c.applicable_laws.map(law => (
                  <LawCard key={law.paragraph} law={law} lang={lang} />
                ))}
              </div>
            </div>
          </div>

          {/* Save to case */}
          <button
            onClick={handleSave}
            disabled={saved}
            className="w-full bg-slate-700 hover:bg-slate-600 disabled:opacity-60 text-slate-200 font-semibold py-3 rounded-xl transition-colors border border-slate-600"
          >
            {saved ? `✓ ${t(lang, 'result.saved')}` : t(lang, 'result.save')}
          </button>
        </div>
      )}
    </div>
  )
}
