/**
 * Simplified API documentation — just the 8 MVP endpoints.
 */
import { useState } from 'react'
import type { Lang } from '../i18n'

interface Props { lang: Lang }

interface Endpoint {
  method: 'GET' | 'POST'
  path: string
  desc_de: string
  desc_en: string
  tryBody?: string
}

const ENDPOINTS: Endpoint[] = [
  {
    method: 'GET',
    path: '/health',
    desc_de: 'Statuscheck — welcher Classifier-Tier ist aktiv?',
    desc_en: 'Health check — which classifier tier is active?',
  },
  {
    method: 'POST',
    path: '/analyze/text',
    desc_de: 'Text klassifizieren — Schweregrad, Kategorien, Gesetze',
    desc_en: 'Classify text — severity, categories, applicable laws',
    tryBody: '{"text": "Women like you should shut up. I know where you live."}',
  },
  {
    method: 'POST',
    path: '/analyze/ingest',
    desc_de: 'Text klassifizieren + als Beweis speichern (mit Hash + Zeitstempel)',
    desc_en: 'Classify + save as evidence (with hash + timestamp)',
    tryBody: '{"text": "I will kill you", "author_username": "threat_user", "url": ""}',
  },
  {
    method: 'POST',
    path: '/analyze/url',
    desc_de: 'Social-Media-URL abrufen + klassifizieren (Instagram, X)',
    desc_en: 'Scrape social media URL + classify (Instagram, X)',
    tryBody: '{"url": "https://www.instagram.com/p/example"}',
  },
  {
    method: 'GET',
    path: '/cases/',
    desc_de: 'Alle Fälle auflisten',
    desc_en: 'List all cases',
  },
  {
    method: 'GET',
    path: '/cases/case-001',
    desc_de: 'Falldetails mit allen Beweisen + Klassifizierungen',
    desc_en: 'Case detail with all evidence + classifications',
  },
  {
    method: 'GET',
    path: '/reports/case-001?report_type=netzdg&lang=de',
    desc_de: 'Textbericht generieren (NetzDG / Strafanzeige / allgemein)',
    desc_en: 'Generate text report (NetzDG / police / general)',
  },
  {
    method: 'GET',
    path: '/reports/case-001/pdf?report_type=general&lang=de',
    desc_de: 'PDF-Bericht herunterladen (gerichtstauglich)',
    desc_en: 'Download PDF report (court-ready)',
  },
]

export default function ApiDocs({ lang }: Props) {
  const isDE = lang === 'de'
  const [results, setResults] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState<Record<string, boolean>>({})

  const tryEndpoint = async (ep: Endpoint) => {
    const key = ep.path
    setLoading(prev => ({ ...prev, [key]: true }))

    try {
      const base = '/api'
      let res: Response

      if (ep.method === 'GET') {
        res = await fetch(`${base}${ep.path}`)
      } else {
        res = await fetch(`${base}${ep.path}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: ep.tryBody || '{}',
        })
      }

      const data = await res.json()
      setResults(prev => ({ ...prev, [key]: JSON.stringify(data, null, 2) }))
    } catch (err) {
      setResults(prev => ({ ...prev, [key]: `Error: ${err}` }))
    } finally {
      setLoading(prev => ({ ...prev, [key]: false }))
    }
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-white mb-2">API</h1>
      <p className="text-slate-400 text-sm mb-6">
        {isDE ? '8 Endpunkte — die Kern-API von SafeVoice' : '8 endpoints — the core SafeVoice API'}
      </p>

      <div className="space-y-3">
        {ENDPOINTS.map(ep => (
          <div key={ep.path} className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
            {/* Header */}
            <div className="flex items-center gap-3 p-4">
              <span className={`text-xs font-bold px-2 py-0.5 rounded ${
                ep.method === 'GET' ? 'bg-emerald-900 text-emerald-300' : 'bg-indigo-900 text-indigo-300'
              }`}>
                {ep.method}
              </span>
              <code className="text-slate-200 text-sm flex-1">{ep.path}</code>
              <button
                onClick={() => tryEndpoint(ep)}
                disabled={loading[ep.path]}
                className="text-xs bg-slate-700 hover:bg-slate-600 text-slate-300 px-3 py-1 rounded-lg transition-colors"
              >
                {loading[ep.path] ? '...' : (isDE ? 'Testen' : 'Try it')}
              </button>
            </div>

            {/* Description */}
            <div className="px-4 pb-3">
              <p className="text-slate-400 text-xs">{isDE ? ep.desc_de : ep.desc_en}</p>
              {ep.tryBody && (
                <pre className="text-slate-500 text-xs mt-2 bg-slate-900 rounded p-2 overflow-x-auto">
                  {ep.tryBody}
                </pre>
              )}
            </div>

            {/* Result */}
            {results[ep.path] && (
              <div className="border-t border-slate-700 p-4">
                <pre className="text-green-300 text-xs bg-slate-900 rounded p-3 overflow-x-auto max-h-64 overflow-y-auto">
                  {results[ep.path]}
                </pre>
              </div>
            )}
          </div>
        ))}
      </div>

      <p className="text-slate-500 text-xs text-center mt-8">
        {isDE
          ? 'Vollständige API-Dokumentation: '
          : 'Full API documentation: '}
        <a href="/api/docs" target="_blank" className="text-indigo-400 hover:underline">/docs</a>
      </p>
    </div>
  )
}
