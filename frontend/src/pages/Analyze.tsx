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
  const [victimContext, setVictimContext] = useState('')
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
  // Three input methods previously stacked with "oder" dividers forced
  // the user to scan all three before starting. Now: text is the default;
  // the other two are quiet tabs above.
  const [inputMethod, setInputMethod] = useState<'text' | 'url' | 'screenshot'>(
    params.get('url') ? 'url' : 'text'
  )
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
        msg || (isDE ? 'Die Analyse antwortet gerade nicht. Bitte nochmal versuchen.' : "The analysis isn't responding right now. Please try again.")
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
        msg || (isDE ? 'Das Bild konnte nicht hochgeladen werden — vielleicht zu groß, oder die OCR antwortet gerade nicht.' : "Couldn't upload the screenshot — file may be too large or OCR is offline.")
      )
    } finally {
      setLoading(false)
      setUploadingScreenshot(false)
      setUploadProgress(null)
    }
  }

  const handleSave = () => {
    if (!result) return
    createCase(result, undefined, victimContext.trim() || undefined)
    setSaved(true)
  }

  const c = result?.classification

  // Tab labels for the three input methods. Persona test showed the
  // previous flat tabs were too subtle — less tech-affine users didn't
  // realise they were clickable. Icons + visible border on the active
  // tab fix the affordance.
  const tabs: Array<{
    key: 'text' | 'url' | 'screenshot'
    label: string
    icon: string
  }> = [
    { key: 'text', label: isDE ? 'Text einfügen' : 'Paste text', icon: '✎' },
    { key: 'url', label: isDE ? 'Link einfügen' : 'Paste link', icon: '↗' },
    { key: 'screenshot', label: isDE ? 'Bild hochladen' : 'Upload image', icon: '⊕' },
  ]

  return (
    <div className="max-w-2xl mx-auto px-4 py-10">
      {/* Title — privacy line removed: it duplicated the mood-bar above. */}
      <h1 className="text-2xl sm:text-3xl font-bold text-white mb-8 tracking-tight">
        {t(lang, 'analyze.title')}
      </h1>

      {/* Form — tabbed input methods. Default is text (the most common
          path: paste something you received). Link + Screenshot are
          quiet alternative tabs above the input. */}
      <div className="bg-slate-800/60 rounded-xl p-5 sm:p-6 mb-6 space-y-5">
        <div className="grid grid-cols-3 gap-2">
          {tabs.map(tab => (
            <button
              key={tab.key}
              type="button"
              onClick={() => setInputMethod(tab.key)}
              className={`flex flex-col items-center justify-center gap-1 py-3 px-2 rounded-lg border text-sm font-medium transition-colors ${
                inputMethod === tab.key
                  ? 'bg-indigo-950/40 border-indigo-700 text-indigo-100'
                  : 'bg-slate-900/40 border-slate-700 text-slate-400 hover:text-slate-200 hover:border-slate-600'
              }`}
            >
              <span className="text-lg leading-none" aria-hidden="true">{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        {inputMethod === 'text' && (
          <div>
            <label className="block text-slate-300 text-sm font-medium mb-0.5">
              {t(lang, 'analyze.text.label')}
            </label>
            <p className="text-slate-500 text-xs mb-1.5">{t(lang, 'analyze.text.hint')}</p>
            <textarea
              value={text}
              onChange={e => setText(e.target.value)}
              placeholder={t(lang, 'analyze.text.placeholder')}
              rows={5}
              className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2.5 text-slate-200 placeholder-slate-500 text-sm focus:outline-none focus:border-indigo-500 resize-none"
            />
          </div>
        )}

        {inputMethod === 'url' && (
          <div>
            <label className="block text-slate-300 text-sm font-medium mb-0.5">
              {t(lang, 'analyze.url.label')}
            </label>
            <p className="text-slate-500 text-xs mb-1.5">{t(lang, 'analyze.url.hint')}</p>
            {/* Honest hint about which URLs actually work. Social media
                blocks server-side scraping; users repeatedly try IG/X
                links and hit a confusing 422. Screenshot is the
                reliable path for those. */}
            <p className="text-amber-300/80 text-xs mb-2 leading-relaxed">
              {isDE
                ? '⚠ Instagram, X/Twitter, TikTok und Facebook blocken den automatischen Abruf fast immer. Für diese bitte Screenshot hochladen. Öffentliche Blogs, News-Artikel und Reddit funktionieren meistens.'
                : '⚠ Instagram, X/Twitter, TikTok and Facebook almost always block automatic fetching. For those, please upload a screenshot. Public blogs, news articles and Reddit usually work.'}
            </p>
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
        )}

        {inputMethod === 'screenshot' && (
          <div>
            <label className="block text-slate-300 text-sm font-medium mb-1.5">
              {isDE ? 'Bild hochladen' : 'Upload image'}
            </label>
            <p className="text-slate-500 text-xs mb-1.5">
              {isDE
                ? 'Funktioniert mit WhatsApp-Verläufen, DM-Screenshots und einzelnen Posts.'
                : 'Works with WhatsApp chats, DM screenshots and single posts.'}
            </p>
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
                    ? (isDE ? `Wird hochgeladen${uploadProgress !== null ? ` · ${uploadProgress}%` : '…'}` : `Uploading${uploadProgress !== null ? ` · ${uploadProgress}%` : '…'}`)
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
        )}

        {/* Optional fields — hidden behind a disclosure so the form
            doesn't ask 4 questions before the first analysis. Only
            shows up when someone wants to add context. */}
        <details className="group">
          <summary className="cursor-pointer inline-flex items-center gap-1.5 text-slate-400 hover:text-slate-200 text-sm">
            <span className="inline-block transition-transform group-open:rotate-90">›</span>
            {isDE ? 'Kontext hinzufügen (optional)' : 'Add context (optional)'}
          </summary>
          <div className="mt-4 space-y-4">
            <div>
              <label className="block text-slate-300 text-sm font-medium mb-0.5">
                {isDE ? 'Was ist passiert?' : 'What happened?'}
              </label>
              <p className="text-slate-500 text-xs mb-1.5">
                {isDE
                  ? 'Was lief vorher? Hilft uns, den Fall besser einzuordnen.'
                  : 'What was happening before? Helps us place the case.'}
              </p>
              <textarea
                value={victimContext}
                onChange={e => setVictimContext(e.target.value)}
                placeholder={isDE
                  ? 'z.B. „Der Account belästigt mich seit 3 Wochen, nachdem ich einen Post über XY geteilt habe …"'
                  : 'e.g. "This account has been harassing me for 3 weeks after I posted about XY..."'}
                rows={3}
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
          </div>
        </details>

        {inputMethod !== 'screenshot' && (
          <button
            onClick={() => handleSubmit()}
            disabled={loading || (!text.trim() && !url.trim())}
            className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold py-3 rounded-xl transition-colors"
          >
            {loading ? t(lang, 'analyze.analyzing') : t(lang, 'analyze.submit')}
          </button>
        )}
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

          {/* Schwerwiegender Inhalt — amber, nicht rot. Kein Alarm-
              Mode, sondern ein ernster Hinweis. Der vorige rote Block
              führte mit "Strafanzeige erstatten →" direkt auf eine
              tote polizei.de-Hubseite, was die Person blockierte.
              Stattdessen: konkreter nächster Schritt im eigenen Flow
              ("Fall speichern → dort wird die Anzeige vorbereitet")
              plus Hilfsangebote als Sekundär-Links. */}
          {c.requires_immediate_action && (
            <div className="bg-amber-950/30 border border-amber-800/50 rounded-xl p-5">
              <div className="flex items-center gap-2 mb-2">
                <span className="text-amber-300 text-lg leading-none">!</span>
                <span className="text-amber-100 font-semibold">
                  {isDE ? 'Schwerwiegender Inhalt' : 'Severe content'}
                </span>
              </div>
              <p className="text-amber-100/80 text-sm leading-relaxed">
                {isDE
                  ? 'Dieser Beleg sollte zeitnah dokumentiert werden. Speichere ihn zuerst — auf der Fall-Seite hilft dir dann der Agent durch die Strafanzeige und NetzDG-Meldung.'
                  : "This piece of evidence should be documented soon. Save it first — on the case page the agent will guide you through the Strafanzeige and NetzDG report."}
              </p>
              <p className="text-amber-100/60 text-xs leading-relaxed mt-3">
                {isDE ? 'Lieber zuerst mit einer Person sprechen? ' : 'Rather talk to a person first? '}
                <a
                  href="https://hateaid.org"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="underline hover:text-amber-50"
                >
                  HateAid
                </a>
                {isDE ? ' berät kostenlos.' : ' offers free counseling.'}
              </p>
            </div>
          )}

          {/* Classification result */}
          <div className="bg-slate-800/60 rounded-xl p-5 sm:p-6 space-y-5">
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

          {/* Save to case — local-only storage, made explicit below the
              button so users don't worry "wohin geht das?" */}
          <div>
            <button
              onClick={handleSave}
              disabled={saved}
              className="w-full bg-slate-700/80 hover:bg-slate-700 disabled:opacity-60 text-slate-100 font-semibold py-3 rounded-xl transition-colors"
            >
              {saved ? `✓ ${t(lang, 'result.saved')}` : t(lang, 'result.save')}
            </button>
            <p className="text-slate-500 text-xs text-center mt-1.5">
              {isDE
                ? 'Speichert nur in diesem Browser. Kein Konto, kein Server.'
                : 'Stores in this browser only. No account, no server.'}
            </p>
          </div>

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
