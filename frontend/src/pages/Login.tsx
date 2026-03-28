/**
 * Login page — magic link authentication.
 * No passwords. Email only.
 */
import { useState } from 'react'
import { t, type Lang } from '../i18n'

interface Props {
  lang: Lang
  onLogin: (sessionToken: string, user: { id: string; email: string; display_name: string | null }) => void
}

export default function Login({ lang, onLogin }: Props) {
  const [email, setEmail] = useState('')
  const [step, setStep] = useState<'email' | 'check' | 'error'>('email')
  const [magicToken, setMagicToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const isDE = lang === 'de'

  const handleRequestLink = async () => {
    if (!email.trim() || !email.includes('@')) return
    setLoading(true)
    setError('')

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email.trim() }),
      })
      if (!res.ok) throw new Error('Failed')
      const data = await res.json()
      // MVP: token returned directly. Production: sent via email
      setMagicToken(data.magic_link_token)
      setStep('check')
    } catch {
      setError(isDE ? 'Fehler beim Senden. Bitte versuche es erneut.' : 'Failed to send. Please try again.')
      setStep('error')
    } finally {
      setLoading(false)
    }
  }

  const handleVerify = async () => {
    if (!magicToken) return
    setLoading(true)

    try {
      const res = await fetch('/api/auth/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: magicToken }),
      })
      if (!res.ok) throw new Error('Invalid')
      const data = await res.json()
      localStorage.setItem('sv_session', data.session_token)
      onLogin(data.session_token, data.user)
    } catch {
      setError(isDE ? 'Link ungültig oder abgelaufen.' : 'Link invalid or expired.')
      setStep('error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-md mx-auto px-4 py-16">
      <div className="text-center mb-8">
        <div className="w-16 h-16 bg-indigo-600 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <span className="text-white text-2xl font-bold">SV</span>
        </div>
        <h1 className="text-2xl font-bold text-white mb-2">
          {isDE ? 'Anmelden' : 'Sign in'}
        </h1>
        <p className="text-slate-400 text-sm">
          {isDE
            ? 'Kein Passwort nötig. Wir senden dir einen Login-Link per E-Mail.'
            : 'No password needed. We\'ll send you a login link by email.'}
        </p>
      </div>

      {step === 'email' && (
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 space-y-4">
          <div>
            <label className="block text-slate-300 text-sm font-medium mb-1.5">
              {isDE ? 'E-Mail-Adresse' : 'Email address'}
            </label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleRequestLink()}
              placeholder="name@example.com"
              className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2.5 text-slate-200 placeholder-slate-500 text-sm focus:outline-none focus:border-indigo-500"
              autoFocus
            />
          </div>
          <button
            onClick={handleRequestLink}
            disabled={loading || !email.includes('@')}
            className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold py-3 rounded-xl transition-colors"
          >
            {loading
              ? (isDE ? 'Wird gesendet...' : 'Sending...')
              : (isDE ? 'Login-Link senden' : 'Send login link')}
          </button>

          <div className="flex items-center gap-2 pt-2">
            <span className="w-2 h-2 bg-green-400 rounded-full"></span>
            <span className="text-green-300 text-xs">
              {isDE ? 'Anmeldung ist optional. SafeVoice funktioniert auch ohne Konto.' : 'Login is optional. SafeVoice works without an account.'}
            </span>
          </div>
        </div>
      )}

      {step === 'check' && (
        <div className="bg-slate-800 border border-slate-700 rounded-xl p-6 text-center space-y-4">
          <div className="text-4xl mb-2">📧</div>
          <h2 className="text-white font-semibold">
            {isDE ? 'Prüfe dein Postfach' : 'Check your inbox'}
          </h2>
          <p className="text-slate-400 text-sm">
            {isDE
              ? `Wir haben einen Login-Link an ${email} gesendet. Klicke den Link um dich anzumelden.`
              : `We sent a login link to ${email}. Click the link to sign in.`}
          </p>

          {/* MVP: direct verify button since we have the token */}
          <button
            onClick={handleVerify}
            disabled={loading}
            className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold py-3 rounded-xl transition-colors"
          >
            {loading
              ? (isDE ? 'Wird verifiziert...' : 'Verifying...')
              : (isDE ? 'Jetzt anmelden (Demo)' : 'Sign in now (Demo)')}
          </button>

          <button
            onClick={() => { setStep('email'); setMagicToken(null) }}
            className="text-slate-400 hover:text-slate-200 text-sm transition-colors"
          >
            {isDE ? 'Andere E-Mail verwenden' : 'Use a different email'}
          </button>
        </div>
      )}

      {step === 'error' && (
        <div className="bg-slate-800 border border-red-800 rounded-xl p-6 text-center space-y-4">
          <p className="text-red-300 text-sm">{error}</p>
          <button
            onClick={() => setStep('email')}
            className="bg-slate-700 hover:bg-slate-600 text-white font-semibold py-2 px-6 rounded-xl transition-colors"
          >
            {isDE ? 'Erneut versuchen' : 'Try again'}
          </button>
        </div>
      )}
    </div>
  )
}
