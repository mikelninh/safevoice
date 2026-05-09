/**
 * AcknowledgementBanner — trauma-informed opening statement.
 * Shows on home and analyze pages. Dismissible per session.
 */
import { useState } from 'react'
import type { Lang } from '../i18n'

interface Props { lang: Lang }

export default function AcknowledgementBanner({ lang }: Props) {
  const [dismissed, setDismissed] = useState(
    () => sessionStorage.getItem('sv_banner_dismissed') === 'true'
  )

  if (dismissed) return null

  const dismiss = () => {
    sessionStorage.setItem('sv_banner_dismissed', 'true')
    setDismissed(true)
  }

  return (
    <div className="bg-indigo-950/70 border-b border-indigo-900/60 px-4 py-3">
      <div className="max-w-2xl mx-auto flex items-start justify-between gap-4">
        <p className="text-indigo-200 text-sm leading-relaxed">
          {lang === 'de'
            ? '💙 Was dir passiert ist, ist nicht okay. Du musst das nicht hinnehmen — und du musst es auch nicht alleine durchstehen. Alles hier ist anonym und sicher.'
            : '💙 What happened to you is not okay. You don\'t have to put up with it — and you don\'t have to deal with it alone. Everything here is anonymous and safe.'}
        </p>
        <button
          onClick={dismiss}
          className="text-indigo-400 hover:text-indigo-200 text-lg leading-none shrink-0 mt-0.5"
          aria-label="Dismiss"
        >
          ×
        </button>
      </div>
    </div>
  )
}
