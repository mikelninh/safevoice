/**
 * LegalChat — ask follow-up questions about a classification result.
 * Uses the /analyze/text endpoint with context from the original classification.
 */
import { useState } from 'react'
import type { Lang } from '../i18n'
import type { ClassificationResult } from '../types'

interface Props {
  lang: Lang
  originalText: string
  classification: ClassificationResult
}

interface Message {
  role: 'user' | 'ai'
  text: string
}

export default function LegalChat({ lang, originalText, classification }: Props) {
  const [open, setOpen] = useState(false)
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const isDE = lang === 'de'

  const handleAsk = async () => {
    if (!question.trim() || loading) return

    const userQ = question.trim()
    setMessages(prev => [...prev, { role: 'user', text: userQ }])
    setQuestion('')
    setLoading(true)

    try {
      // Build context-aware prompt
      const context = [
        `Original content: "${originalText}"`,
        `Classification: severity=${classification.severity}, categories=${classification.categories.join(', ')}`,
        `Laws: ${classification.applicable_laws.map(l => l.paragraph).join(', ')}`,
        `Summary: ${lang === 'de' ? classification.summary_de : classification.summary}`,
        '',
        `User follow-up question: ${userQ}`,
        '',
        'Answer the question about this specific case. Be helpful, victim-centered, and precise about German law. Always mention this is not legal advice.',
      ].join('\n')

      const res = await fetch('/api/analyze/text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: context }),
      })

      if (res.ok) {
        const data = await res.json()
        const answer = lang === 'de' ? data.summary_de : data.summary
        setMessages(prev => [...prev, { role: 'ai', text: answer }])
      } else {
        setMessages(prev => [...prev, { role: 'ai', text: isDE ? 'Fehler bei der Analyse.' : 'Analysis failed.' }])
      }
    } catch {
      setMessages(prev => [...prev, { role: 'ai', text: isDE ? 'Verbindungsfehler.' : 'Connection error.' }])
    } finally {
      setLoading(false)
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="w-full bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 text-sm font-medium py-3 rounded-xl transition-colors"
      >
        {isDE ? 'Rechtliche Rückfragen stellen...' : 'Ask follow-up legal questions...'}
      </button>
    )
  }

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-700">
        <span className="text-white text-sm font-medium">
          {isDE ? 'Rechtliche Rückfragen' : 'Legal follow-up'}
        </span>
        <button onClick={() => setOpen(false)} className="text-slate-400 hover:text-white text-lg">×</button>
      </div>

      {/* Suggestions */}
      {messages.length === 0 && (
        <div className="p-4 space-y-2">
          <p className="text-slate-500 text-xs mb-2">{isDE ? 'Beispielfragen:' : 'Example questions:'}</p>
          {(isDE ? [
            'Was genau bedeutet § 241 StGB für diesen Fall?',
            'Wie erstatte ich Strafanzeige?',
            'Was ist der Unterschied zwischen Beleidigung und Bedrohung?',
            'Wie lange hat Instagram Zeit, den Inhalt zu löschen?',
          ] : [
            'What exactly does § 241 StGB mean for this case?',
            'How do I file a police report?',
            'What is the difference between insult and threat?',
            'How long does Instagram have to remove this content?',
          ]).map((q, i) => (
            <button
              key={i}
              onClick={() => { setQuestion(q); }}
              className="block w-full text-left text-sm text-indigo-300 hover:text-indigo-200 bg-slate-900 rounded-lg px-3 py-2 transition-colors"
            >
              {q}
            </button>
          ))}
        </div>
      )}

      {/* Messages */}
      {messages.length > 0 && (
        <div className="p-4 space-y-3 max-h-64 overflow-y-auto">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                msg.role === 'user'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-slate-900 text-slate-200'
              }`}>
                {msg.text}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-slate-900 rounded-lg px-3 py-2 text-sm text-slate-400">
                {isDE ? 'Analyse läuft...' : 'Analysing...'}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Input */}
      <div className="flex gap-2 p-3 border-t border-slate-700">
        <input
          value={question}
          onChange={e => setQuestion(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && handleAsk()}
          placeholder={isDE ? 'Frage stellen...' : 'Ask a question...'}
          className="flex-1 bg-slate-900 border border-slate-600 rounded-lg px-3 py-2 text-slate-200 placeholder-slate-500 text-sm focus:outline-none focus:border-indigo-500"
        />
        <button
          onClick={handleAsk}
          disabled={loading || !question.trim()}
          className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-sm font-medium px-4 rounded-lg transition-colors"
        >
          {isDE ? 'Fragen' : 'Ask'}
        </button>
      </div>

      {/* Disclaimer */}
      <p className="text-slate-600 text-xs px-4 pb-3">
        {isDE ? 'Dies ist keine Rechtsberatung.' : 'This is not legal advice.'}
      </p>
    </div>
  )
}
