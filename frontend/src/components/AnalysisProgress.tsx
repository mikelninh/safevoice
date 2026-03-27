/**
 * AnalysisProgress — animated multi-step progress shown during classification.
 * Makes the 1-2 second wait feel meaningful and trustworthy.
 */
import { useState, useEffect } from 'react'
import type { Lang } from '../i18n'

interface Props { lang: Lang }

const STEPS_DE = [
  'Inhalt wird erfasst und gesichert...',
  'Text wird analysiert...',
  'Rechtliche Einordnung wird vorgenommen...',
  'Bericht wird vorbereitet...',
]

const STEPS_EN = [
  'Capturing and preserving content...',
  'Analysing text...',
  'Mapping to applicable laws...',
  'Preparing your report...',
]

export default function AnalysisProgress({ lang }: Props) {
  const [step, setStep] = useState(0)
  const steps = lang === 'de' ? STEPS_DE : STEPS_EN

  useEffect(() => {
    const interval = setInterval(() => {
      setStep(s => (s + 1) % steps.length)
    }, 600)
    return () => clearInterval(interval)
  }, [steps.length])

  return (
    <div className="bg-slate-800 border border-indigo-800 rounded-xl p-6 text-center">
      {/* Animated dots */}
      <div className="flex justify-center gap-2 mb-4">
        {steps.map((_, i) => (
          <div
            key={i}
            className={`w-2 h-2 rounded-full transition-all duration-300 ${
              i === step ? 'bg-indigo-400 scale-125' :
              i < step ? 'bg-indigo-700' : 'bg-slate-600'
            }`}
          />
        ))}
      </div>

      {/* Step text */}
      <p className="text-indigo-300 text-sm font-medium min-h-[1.5rem]">
        {steps[step]}
      </p>

      {/* Progress bar */}
      <div className="mt-4 h-1 bg-slate-700 rounded-full overflow-hidden">
        <div
          className="h-full bg-indigo-500 rounded-full transition-all duration-500"
          style={{ width: `${((step + 1) / steps.length) * 100}%` }}
        />
      </div>

      <p className="text-slate-500 text-xs mt-3">
        {lang === 'de'
          ? 'Dein Inhalt verlässt niemals dieses Gerät unverschlüsselt.'
          : 'Your content never leaves this device unencrypted.'}
      </p>
    </div>
  )
}
