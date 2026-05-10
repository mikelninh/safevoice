/**
 * Client-side SHA-256 verifier — lets a user (or anyone receiving the
 * report) paste the original text and confirm it produces the same hash
 * stored in the evidence record. All in-browser; no network.
 */
import { useState } from 'react'
import type { Lang } from '../i18n'

interface Props {
  expectedHash: string  // "sha256:..." or just hex
  originalText: string  // for the prefill convenience button
  lang: Lang
  onClose: () => void
}

async function sha256Hex(text: string): Promise<string> {
  const enc = new TextEncoder().encode(text)
  const buf = await crypto.subtle.digest('SHA-256', enc)
  return Array.from(new Uint8Array(buf))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('')
}

function normalizeHash(h: string): string {
  return h.replace(/^sha256:/i, '').trim().toLowerCase()
}

export default function HashVerifier({ expectedHash, originalText, lang, onClose }: Props) {
  const isDE = lang === 'de'
  const [text, setText] = useState('')
  const [computed, setComputed] = useState<string | null>(null)
  const [match, setMatch] = useState<boolean | null>(null)
  const [busy, setBusy] = useState(false)

  const expected = normalizeHash(expectedHash)

  const verify = async () => {
    if (!text) return
    setBusy(true)
    const hash = await sha256Hex(text)
    setComputed(hash)
    setMatch(hash === expected)
    setBusy(false)
  }

  return (
    <div className="fixed inset-0 bg-black/80 flex items-end sm:items-center justify-center z-50 p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-2xl w-full max-w-lg flex flex-col max-h-[90vh]">
        <div className="flex items-center justify-between p-4 border-b border-slate-700">
          <h2 className="text-white font-bold">
            {isDE ? 'Prüfsumme verifizieren' : 'Verify checksum'}
          </h2>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white text-xl leading-none"
          >
            ×
          </button>
        </div>

        <div className="p-4 space-y-3 overflow-y-auto">
          <p className="text-slate-400 text-xs leading-relaxed">
            {isDE
              ? 'Füge unten den Originaltext ein. Dein Browser rechnet den SHA-256-Hash und vergleicht ihn mit dem im Bericht. Stimmen beide überein, ist der Inhalt seit der Erfassung nicht verändert worden. Funktioniert offline — der Text verlässt dein Gerät nicht.'
              : 'Paste the original text below. Your browser computes the SHA-256 hash and compares it to the one in the report. If they match, the content has not been altered since capture. Works offline — the text never leaves your device.'}
          </p>

          <div>
            <label className="block text-slate-300 text-xs font-medium mb-1">
              {isDE ? 'Erwartete Prüfsumme' : 'Expected checksum'}
            </label>
            <code className="block text-xs text-slate-300 font-mono bg-slate-800 rounded px-2 py-1.5 break-all">
              {expected}
            </code>
          </div>

          <div>
            <label className="block text-slate-300 text-xs font-medium mb-1">
              {isDE ? 'Originaltext' : 'Original text'}
            </label>
            <textarea
              value={text}
              onChange={e => setText(e.target.value)}
              placeholder={isDE ? 'Originaltext hier einfügen…' : 'Paste original text here…'}
              rows={4}
              className="w-full bg-slate-800 border border-slate-700 rounded px-3 py-2 text-slate-200 placeholder-slate-500 text-sm font-mono"
            />
            {originalText && text !== originalText && (
              <button
                type="button"
                onClick={() => setText(originalText)}
                className="text-indigo-300 hover:text-indigo-200 text-xs mt-1.5"
              >
                {isDE ? '↳ Text aus dem Bericht einsetzen (zum Selbsttest)' : '↳ Insert the text from the report (self-test)'}
              </button>
            )}
          </div>

          <button
            onClick={verify}
            disabled={!text || busy}
            className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 disabled:text-slate-500 text-white font-semibold py-2.5 rounded-lg text-sm"
          >
            {busy ? (isDE ? 'Wird berechnet…' : 'Computing…') : (isDE ? 'Prüfen' : 'Verify')}
          </button>

          {computed !== null && (
            <div
              className={`rounded-lg p-3 text-sm ${
                match ? 'bg-emerald-950/40 border border-emerald-800 text-emerald-100' : 'bg-red-950/40 border border-red-800 text-red-100'
              }`}
            >
              <div className="font-semibold mb-1">
                {match
                  ? (isDE ? '✓ Übereinstimmung — Inhalt unverändert' : '✓ Match — content unaltered')
                  : (isDE ? '✗ Keine Übereinstimmung — Inhalt wurde verändert oder anderer Text eingefügt' : '✗ Mismatch — content was altered or different text was pasted')}
              </div>
              <div className="text-xs font-mono break-all opacity-80">
                {isDE ? 'Berechnet: ' : 'Computed: '}{computed}
              </div>
            </div>
          )}

          <p className="text-slate-500 text-xs leading-relaxed">
            {isDE
              ? 'Du kannst diesen Test auch ohne SafeVoice machen: jedes Linux/macOS-Terminal kann den Hash mit `shasum -a 256 datei.txt` oder `printf "%s" "TEXT" | shasum -a 256` rechnen — gleiches Ergebnis.'
              : 'You can also do this without SafeVoice: any Linux/macOS terminal computes it via `shasum -a 256 file.txt` or `printf "%s" "TEXT" | shasum -a 256` — same result.'}
          </p>
        </div>
      </div>
    </div>
  )
}
