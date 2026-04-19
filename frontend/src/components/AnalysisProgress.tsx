/**
 * AnalysisProgress — ambient "working" indicator during classification.
 *
 * The analyze endpoint (POST /analyze/text) is synchronous: the backend
 * returns a single response when the classifier is done. We do not have
 * per-step progress events, so we do not fake them. This component shows
 * the one honest signal we have — elapsed wall-clock time — plus a muted
 * pulse. No progress bar, no percentage, no staged checklist.
 *
 * If/when the backend emits SSE or polling events for (hash → scrape →
 * classify → persist), restore the step list and drive it from real state.
 */
import { useEffect, useState } from 'react'
import type { Lang } from '../i18n'

interface Props {
  lang: Lang
  totalComments?: number
}

export default function AnalysisProgress({ lang, totalComments }: Props) {
  const [seconds, setSeconds] = useState(0)
  const isDE = lang === 'de'

  useEffect(() => {
    const start = Date.now()
    const interval = setInterval(() => {
      setSeconds(Math.floor((Date.now() - start) / 1000))
    }, 250)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 mb-6">
      <div className="flex items-center gap-3">
        <span className="w-2 h-2 bg-indigo-400 rounded-full animate-pulse shrink-0" aria-hidden="true" />
        <span className="text-indigo-200 text-sm font-medium">
          {isDE ? 'Klassifikator läuft' : 'Classifier running'}
        </span>
        <span className="text-slate-500 text-sm tabular-nums ml-auto">
          {seconds}s
        </span>
      </div>

      {totalComments && totalComments > 0 && (
        <p className="text-slate-500 text-xs mt-4 pt-3 border-t border-slate-700">
          {isDE
            ? `${totalComments} Kommentare werden ebenfalls analysiert.`
            : `${totalComments} comments are also being analysed.`}
        </p>
      )}

      <p className="text-slate-600 text-xs mt-3">
        {isDE
          ? 'Inhalte verlassen dieses Gerät nur verschlüsselt.'
          : 'Content leaves this device only in encrypted form.'}
      </p>
    </div>
  )
}
