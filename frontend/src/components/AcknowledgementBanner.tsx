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
    <div className="bg-indigo-950 border-b border-indigo-800 px-4 py-3">
      <div className="max-w-2xl mx-auto flex items-start justify-between gap-4">
        <p className="text-indigo-200 text-sm leading-relaxed">
          {lang === 'de'
            ? '💙 Was dir passiert ist, ist nicht okay. Du hast das Recht, dich zu wehren — und wir helfen dir dabei. Alles hier ist anonym und sicher.'
            : '💙 What happened to you is not okay. You have the right to fight back — and we are here to help. Everything here is anonymous and safe.'}
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
