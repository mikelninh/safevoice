/**
 * AnalysisProgress — visual step-by-step progress during classification.
 * Shows exactly where we are in the pipeline.
 */
import { useState, useEffect } from 'react'
import type { Lang } from '../i18n'

interface Props {
  lang: Lang
  totalComments?: number
}

const STEPS_DE = [
  { label: 'Inhalt erfassen', desc: 'Text wird gesichert und gehasht' },
  { label: 'KI-Analyse', desc: 'Inhalt wird durch den Classifier geschickt' },
  { label: 'Rechtliche Einordnung', desc: 'Zuordnung zu deutschen Gesetzen' },
  { label: 'Bericht vorbereiten', desc: 'Ergebnis wird aufbereitet' },
]

const STEPS_EN = [
  { label: 'Capture content', desc: 'Text is being secured and hashed' },
  { label: 'AI analysis', desc: 'Content is being classified' },
  { label: 'Legal mapping', desc: 'Mapping to applicable German laws' },
  { label: 'Prepare report', desc: 'Building your results' },
]

export default function AnalysisProgress({ lang, totalComments }: Props) {
  const [step, setStep] = useState(0)
  const steps = lang === 'de' ? STEPS_DE : STEPS_EN
  const isDE = lang === 'de'

  useEffect(() => {
    const interval = setInterval(() => {
      setStep(s => s < steps.length - 1 ? s + 1 : s)
    }, 800)
    return () => clearInterval(interval)
  }, [steps.length])

  const pct = Math.round(((step + 1) / steps.length) * 100)

  return (
    <div className="bg-slate-800 border border-indigo-800 rounded-xl p-6 mb-6">
      {/* Header with percentage */}
      <div className="flex items-center justify-between mb-4">
        <span className="text-indigo-300 text-sm font-medium">
          {isDE ? 'Analyse läuft...' : 'Analysing...'}
        </span>
        <span className="text-indigo-400 text-sm font-bold">{pct}%</span>
      </div>

      {/* Progress bar */}
      <div className="h-2 bg-slate-700 rounded-full overflow-hidden mb-5">
        <div
          className="h-full bg-indigo-500 rounded-full transition-all duration-700 ease-out"
          style={{ width: `${pct}%` }}
        />
      </div>

      {/* Step list */}
      <div className="space-y-3">
        {steps.map((s, i) => (
          <div key={i} className="flex items-start gap-3">
            {/* Step indicator */}
            <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0 mt-0.5 transition-all duration-300 ${
              i < step ? 'bg-indigo-600 text-white' :
              i === step ? 'bg-indigo-500 text-white ring-2 ring-indigo-400 ring-offset-2 ring-offset-slate-800' :
              'bg-slate-700 text-slate-500'
            }`}>
              {i < step ? '\u2713' : i + 1}
            </div>

            {/* Step text */}
            <div>
              <p className={`text-sm font-medium transition-colors duration-300 ${
                i <= step ? 'text-white' : 'text-slate-500'
              }`}>
                {s.label}
              </p>
              {i === step && (
                <p className="text-xs text-indigo-300 mt-0.5">{s.desc}</p>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Comment count info */}
      {totalComments && totalComments > 0 && (
        <p className="text-slate-500 text-xs mt-4 pt-3 border-t border-slate-700">
          {isDE
            ? `${totalComments} Kommentare werden ebenfalls analysiert...`
            : `${totalComments} comments are also being analysed...`}
        </p>
      )}

      {/* Privacy note */}
      <p className="text-slate-600 text-xs mt-3">
        {isDE
          ? 'Dein Inhalt verlässt niemals dieses Gerät unverschlüsselt.'
          : 'Your content never leaves this device unencrypted.'}
      </p>
    </div>
  )
}
