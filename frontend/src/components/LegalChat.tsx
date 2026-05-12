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

/**
 * Build follow-up questions tied to *this* classification — paragraph names,
 * categories, and platform from the evidence — so users don't have to ask
 * generic questions against a specific case.
 */
function buildSuggestions(c: ClassificationResult, isDE: boolean): string[] {
  const paragraphs = c.applicable_laws.map(l => l.paragraph).filter(p => p && p !== 'NetzDG § 3')
  const primaryParagraph = paragraphs[0] ?? '§ 185 StGB'
  const secondaryParagraph = paragraphs.length > 1 ? paragraphs[1] : null
  const sev = c.severity
  const cats = c.categories
  const out: string[] = []

  if (isDE) {
    out.push(`Was bedeutet ${primaryParagraph} konkret für meinen Fall — wie wahrscheinlich ist eine Verurteilung?`)
    if (sev === 'critical' || sev === 'high') {
      out.push('Sollte ich sofort zur Polizei gehen oder reicht eine Online-Strafanzeige?')
    } else {
      out.push('Lohnt sich eine Strafanzeige bei dieser Schwere oder bringt eine NetzDG-Meldung mehr?')
    }
    if (cats.includes('death_threat') || cats.includes('threat')) {
      out.push('Welche Schutzmaßnahmen kann ich beantragen, wenn die Drohung ernst gemeint sein könnte?')
    } else if (cats.includes('volksverhetzung')) {
      out.push('Wer ist bei § 130 StGB ermittlungspflichtig und wann wird die Staatsanwaltschaft aktiv?')
    } else if (cats.includes('intimate_images') || cats.includes('sexual_harassment')) {
      out.push('Welche Sofortmaßnahmen gibt es gegen die Verbreitung intimer Inhalte?')
    } else if (cats.includes('doxxing')) {
      out.push('Welche meiner Daten kann ich nach DSGVO sofort löschen lassen?')
    } else {
      out.push('Wie unterscheidet sich Beleidigung (§ 185) von übler Nachrede (§ 186) in meinem Fall?')
    }
    out.push('Welche Beweise brauche ich zusätzlich, damit die Anzeige Aussicht auf Erfolg hat?')
    if (secondaryParagraph) {
      out.push(`Greift hier zusätzlich ${secondaryParagraph} und was ändert das an der Strafhöhe?`)
    } else {
      out.push('Wie lange habe ich Zeit, Strafanzeige zu erstatten — gibt es Verjährungsfristen?')
    }
  } else {
    out.push(`What does ${primaryParagraph} actually mean for my case — how likely is a conviction?`)
    if (sev === 'critical' || sev === 'high') {
      out.push('Should I go to the police immediately, or is an online complaint enough?')
    } else {
      out.push('At this severity, is a criminal complaint worth filing or is a NetzDG report more effective?')
    }
    if (cats.includes('death_threat') || cats.includes('threat')) {
      out.push('What protective measures can I apply for if the threat might be real?')
    } else if (cats.includes('volksverhetzung')) {
      out.push('Who is required to investigate § 130 hate speech and when does the prosecutor get involved?')
    } else if (cats.includes('intimate_images') || cats.includes('sexual_harassment')) {
      out.push('What immediate steps stop intimate content from spreading further?')
    } else if (cats.includes('doxxing')) {
      out.push('Which of my personal data can I get removed under GDPR right now?')
    } else {
      out.push('How does insult (§ 185) differ from defamation (§ 186) in my case?')
    }
    out.push('What additional evidence makes the complaint more likely to succeed?')
    if (secondaryParagraph) {
      out.push(`Does ${secondaryParagraph} also apply, and how does that affect potential penalties?`)
    } else {
      out.push('How long do I have to file — are there limitation periods?')
    }
  }

  return out.slice(0, 4)
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

      const res = await fetch('/api/analyze/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: userQ, context, lang }),
      })

      if (res.ok) {
        const data = await res.json()
        setMessages(prev => [...prev, { role: 'ai', text: data.answer }])
      } else {
        setMessages(prev => [...prev, { role: 'ai', text: isDE ? `Classifier antwortete ${res.status}. Bitte Frage erneut stellen.` : `Classifier returned ${res.status}. Please ask again.` }])
      }
    } catch {
      setMessages(prev => [...prev, { role: 'ai', text: isDE ? 'Classifier nicht erreichbar. Netzwerk prüfen.' : 'Classifier unreachable. Check network.' }])
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

      {/* Suggestions — case-aware: built from the actual classification */}
      {messages.length === 0 && (
        <div className="p-4 space-y-2">
          <p className="text-slate-500 text-xs mb-2">
            {isDE ? 'Beispielfragen zu deinem Fall:' : 'Example questions about your case:'}
          </p>
          {buildSuggestions(classification, isDE).map((q, i) => (
            <button
              key={i}
              onClick={() => { setQuestion(q) }}
              className="block w-full text-left text-sm text-indigo-300 hover:text-indigo-200 bg-slate-900 rounded-lg px-3 py-2 transition-colors leading-relaxed"
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
                {isDE ? 'Classifier läuft…' : 'Classifier running…'}
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
