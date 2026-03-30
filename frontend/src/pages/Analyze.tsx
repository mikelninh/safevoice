import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { analyzeText, scrapeUrl, uploadScreenshot } from '../services/api'
import { t, type Lang } from '../i18n'
import type { EvidenceItem } from '../types'
import SeverityBadge from '../components/SeverityBadge'
import CategoryTag from '../components/CategoryTag'
import LawCard from '../components/LawCard'
import AnalysisProgress from '../components/AnalysisProgress'
import HateAidReferral from '../components/HateAidReferral'
import LegalChat from '../components/LegalChat'
import { createCase } from '../services/storage'

interface Props { lang: Lang }

function isSocialUrl(str: string): boolean {
  return /^https?:\/\/(www\.)?(instagram\.com|x\.com|twitter\.com|tiktok\.com|facebook\.com)/i.test(str.trim())
}

function platformLabel(platform: string): string {
  const labels: Record<string, string> = {
    instagram: 'Instagram', x: 'X / Twitter', tiktok: 'TikTok', facebook: 'Facebook', web: 'Web', whatsapp: 'WhatsApp', screenshot: 'Screenshot',
  }
  return labels[platform] || platform
}

export default function Analyze({ lang }: Props) {
  const [params] = useSearchParams()
  const [url, setUrl] = useState(params.get('url') ?? '')
  const [text, setText] = useState(params.get('text') ?? '')
  const [author, setAuthor] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<EvidenceItem | null>(null)
  const [commentResults, setCommentResults] = useState<EvidenceItem[]>([])
  const [scrapedPlatform, setScrapedPlatform] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)
  const [screenshotFile, setScreenshotFile] = useState<File | null>(null)
  const [uploadProgress, setUploadProgress] = useState<number | null>(null)
  const [uploadingScreenshot, setUploadingScreenshot] = useState(false)
  const isDE = lang === 'de'

  // Auto-analyze if coming from share target
  useEffect(() => {
    const sharedUrl = params.get('url')
    const sharedText = params.get('text')
    if (sharedUrl && !result) {
      setUrl(sharedUrl)
      handleSubmit(undefined, sharedUrl)
    } else if (sharedText && !result) {
      setText(sharedText)
      handleSubmit(sharedText)
    }
  }, [])

  const handleSubmit = async (overrideText?: string, overrideUrl?: string) => {
    const inputUrl = overrideUrl ?? url
    const inputText = overrideText ?? text

    if (!inputText.trim() && !inputUrl.trim()) return

    setLoading(true)
    setError(null)
    setResult(null)
    setCommentResults([])
    setScrapedPlatform(null)
    setSaved(false)

    try {
      // If URL looks like a social media link, use the scraper
      if (inputUrl.trim() && isSocialUrl(inputUrl)) {
        const res = await scrapeUrl(inputUrl.trim())
        setResult(res.evidence)
        setCommentResults(res.comments ?? [])
        setScrapedPlatform(res.platform)
      } else {
        // Otherwise use direct text analysis
        const content = inputText || inputUrl
        const res = await analyzeText(content, author || 'unknown', inputUrl)
        setResult(res.evidence)
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : ''
      setError(
        msg || (isDE ? 'Analyse fehlgeschlagen. Bitte versuche es erneut.' : 'Analysis failed. Please try again.')
      )
    } finally {
      setLoading(false)
    }
  }

  const handleScreenshotUpload = async () => {
    if (!screenshotFile) return

    setUploadingScreenshot(true)
    setLoading(true)
    setError(null)
    setResult(null)
    setCommentResults([])
    setScrapedPlatform(null)
    setSaved(false)
    setUploadProgress(0)

    try {
      const res = await uploadScreenshot(screenshotFile, (pct) => {
        setUploadProgress(pct)
      })
      setResult(res.evidence)
      if (res.ocr_metadata.is_whatsapp) {
        setScrapedPlatform('whatsapp')
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : ''
      setError(
        msg || (isDE ? 'Screenshot-Upload fehlgeschlagen.' : 'Screenshot upload failed.')
      )
    } finally {
      setLoading(false)
      setUploadingScreenshot(false)
      setUploadProgress(null)
    }
  }

  const handleSave = () => {
    if (!result) return
    createCase(result)
    setSaved(true)
  }

  const c = result?.classification

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-white mb-2">
        {t(lang, 'analyze.title')}
      </h1>
      <div className="flex items-center gap-2 mb-6">
        <span className="w-2 h-2 bg-green-400 rounded-full"></span>
        <span className="text-green-300 text-sm">{t(lang, 'analyze.privacy')}</span>
      </div>

      {/* Form */}
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 mb-6 space-y-4">
        <div>
          <label className="block text-slate-300 text-sm font-medium mb-1.5">
            {t(lang, 'analyze.url.label')}
          </label>
          <div className="relative">
            <input
              type="url"
              value={url}
              onChange={e => setUrl(e.target.value)}
              placeholder={t(lang, 'analyze.url.placeholder')}
              className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2.5 text-slate-200 placeholder-slate-500 text-sm focus:outline-none focus:border-indigo-500 pr-24"
            />
            {url.trim() && isSocialUrl(url) && (
              <span className="absolute right-3 top-1/2 -translate-y-1/2 bg-indigo-900 border border-indigo-700 text-indigo-300 text-xs px-2 py-0.5 rounded-full">
                {isDE ? 'Auto-Abruf' : 'Auto-fetch'}
              </span>
            )}
          </div>
        </div>

        <div className="relative flex items-center gap-3">
          <div className="flex-1 h-px bg-slate-700"></div>
          <span className="text-slate-500 text-xs">{isDE ? 'oder' : 'or'}</span>
          <div className="flex-1 h-px bg-slate-700"></div>
        </div>

        {/* Screenshot upload */}
        <div>
          <label className="block text-slate-300 text-sm font-medium mb-1.5">
            {isDE ? 'Screenshot hochladen (WhatsApp, DM, ...)' : 'Upload screenshot (WhatsApp, DM, ...)'}
          </label>
          <div className="relative">
            <input
              type="file"
              accept="image/*"
              onChange={e => {
                const f = e.target.files?.[0] ?? null
                setScreenshotFile(f)
              }}
              className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2.5 text-slate-200 text-sm focus:outline-none focus:border-indigo-500 file:mr-3 file:py-1 file:px-3 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-indigo-900 file:text-indigo-300 hover:file:bg-indigo-800"
            />
          </div>
          {screenshotFile && (
            <div className="mt-2 flex items-center gap-2">
              <span className="text-slate-400 text-xs truncate max-w-[200px]">
                {screenshotFile.name}
              </span>
              <span className="text-slate-500 text-xs">
                ({(screenshotFile.size / 1024).toFixed(0)} KB)
              </span>
              <button
                onClick={handleScreenshotUpload}
                disabled={uploadingScreenshot}
                className="ml-auto bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors"
              >
                {uploadingScreenshot
                  ? (isDE ? 'Wird hochgeladen...' : 'Uploading...')
                  : (isDE ? 'Analysieren' : 'Analyze')}
              </button>
            </div>
          )}
          {uploadProgress !== null && (
            <div className="mt-2">
              <div className="w-full bg-slate-700 rounded-full h-1.5">
                <div
                  className="bg-indigo-500 h-1.5 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
              <span className="text-slate-500 text-xs mt-1 block">
                {uploadProgress}%
              </span>
            </div>
          )}
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

      {/* Loading progress */}
      {loading && <AnalysisProgress lang={lang} />}

      {/* Error */}
      {error && (
        <div className="bg-red-900/40 border border-red-700 rounded-xl p-4 text-red-300 text-sm mb-6">
          {error}
        </div>
      )}

      {/* Result */}
      {result && c && (
        <div className="space-y-4">
          {/* Scraped platform badge */}
          {scrapedPlatform && (
            <div className="flex items-center gap-2 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2">
              <span className="w-2 h-2 bg-green-400 rounded-full"></span>
              <span className="text-green-300 text-sm font-medium">
                {isDE ? `Von ${platformLabel(scrapedPlatform)} abgerufen` : `Fetched from ${platformLabel(scrapedPlatform)}`}
              </span>
              <span className="text-slate-500 text-xs ml-auto">
                @{result.author_username}
              </span>
            </div>
          )}

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

          {/* HateAid referral for severe cases */}
          <HateAidReferral lang={lang} severity={c.severity} />

          {/* Legal follow-up chat */}
          <LegalChat lang={lang} originalText={result.content_text} classification={c} />

          {/* Save to case */}
          <button
            onClick={handleSave}
            disabled={saved}
            className="w-full bg-slate-700 hover:bg-slate-600 disabled:opacity-60 text-slate-200 font-semibold py-3 rounded-xl transition-colors border border-slate-600"
          >
            {saved ? `✓ ${t(lang, 'result.saved')}` : t(lang, 'result.save')}
          </button>

          {/* Scraped comments */}
          {commentResults.length > 0 && (
            <div>
              <h3 className="text-slate-400 text-xs uppercase tracking-wider mb-3">
                {commentResults.length} {isDE ? 'Kommentare analysiert' : 'comments analysed'}
              </h3>
              <div className="space-y-2">
                {commentResults.map(comment => (
                  <div
                    key={comment.id}
                    className={`bg-slate-800 border rounded-lg p-3 ${
                      comment.classification?.severity === 'critical' ? 'border-red-700' :
                      comment.classification?.severity === 'high' ? 'border-orange-700' :
                      'border-slate-700'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-slate-400 text-xs">@{comment.author_username}</span>
                      {comment.classification && (
                        <SeverityBadge severity={comment.classification.severity} lang={lang} />
                      )}
                    </div>
                    <p className="text-slate-300 text-sm">{comment.content_text}</p>
                    {comment.classification && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {comment.classification.categories.map(cat => (
                          <CategoryTag key={cat} category={cat} lang={lang} />
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
