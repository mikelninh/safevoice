/**
 * OnlinewachePanel — pre-fill and link to state-specific online police report.
 * Each of Germany's 16 Bundesländer has its own Onlinewache URL.
 */
import { useState } from 'react'
import type { Lang } from '../i18n'

interface Props {
  lang: Lang
  reportText: string
}

const BUNDESLAENDER: { name: string; url: string }[] = [
  { name: 'Baden-Württemberg', url: 'https://www.polizei-bw.de/onlinewache' },
  { name: 'Bayern', url: 'https://www.polizei.bayern.de/onlinewache' },
  { name: 'Berlin', url: 'https://www.internetwache-polizei-berlin.de' },
  { name: 'Brandenburg', url: 'https://polizei.brandenburg.de/onlineanzeige' },
  { name: 'Bremen', url: 'https://www.polizei.bremen.de/onlinewache' },
  { name: 'Hamburg', url: 'https://www.polizei.hamburg/onlinewache' },
  { name: 'Hessen', url: 'https://onlinewache.polizei.hessen.de' },
  { name: 'Mecklenburg-Vorpommern', url: 'https://www.polizei.mvnet.de/Onlineanzeige' },
  { name: 'Niedersachsen', url: 'https://www.onlinewache.polizei.niedersachsen.de' },
  { name: 'Nordrhein-Westfalen', url: 'https://polizei.nrw/internetwache' },
  { name: 'Rheinland-Pfalz', url: 'https://www.polizei.rlp.de/onlinewache' },
  { name: 'Saarland', url: 'https://www.polizei.saarland.de/onlinewache' },
  { name: 'Sachsen', url: 'https://www.polizei.sachsen.de/onlinewache' },
  { name: 'Sachsen-Anhalt', url: 'https://www.polizei.sachsen-anhalt.de/onlinewache' },
  { name: 'Schleswig-Holstein', url: 'https://www.schleswig-holstein.de/onlinewache' },
  { name: 'Thüringen', url: 'https://www.thueringen.de/th3/polizei/onlinewache' },
]

export default function OnlinewachePanel({ lang, reportText }: Props) {
  const [selected, setSelected] = useState<string>('')
  const [copied, setCopied] = useState(false)
  const [showPreview, setShowPreview] = useState(false)
  const isDE = lang === 'de'

  const selectedLand = BUNDESLAENDER.find(b => b.name === selected)

  const handleCopy = () => {
    navigator.clipboard.writeText(reportText)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="bg-slate-800/60 rounded-xl p-5 space-y-4">
      <div>
        <h3 className="text-white font-semibold mb-1">
          {isDE ? 'Online-Strafanzeige erstatten' : 'File police report online'}
        </h3>
        <p className="text-slate-400 text-sm leading-relaxed">
          {isDE
            ? 'Jedes Bundesland hat ein eigenes Online-Formular (keine einheitliche E-Mail). SafeVoice hat den passenden Strafanzeige-Text für deinen Fall vorbereitet — du kopierst ihn und fügst ihn unten im Formular ins „Sachverhalt"-Feld ein.'
            : 'Every Bundesland has its own online form (no unified email). SafeVoice has prepared the matching criminal complaint text for your case — copy it and paste it into the form\'s "Sachverhalt" / details field below.'}
        </p>
      </div>

      {/* Bundesland selector */}
      <div>
        <label className="block text-slate-300 text-xs font-medium mb-1.5 uppercase tracking-wider">
          {isDE ? '1. Bundesland wählen' : '1. Select Bundesland'}
        </label>
        <select
          value={selected}
          onChange={e => setSelected(e.target.value)}
          className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2.5 text-slate-200 text-sm focus:outline-none focus:border-indigo-500"
        >
          <option value="">
            {isDE ? '— Bundesland wählen —' : '— Select Bundesland —'}
          </option>
          {BUNDESLAENDER.map(b => (
            <option key={b.name} value={b.name}>{b.name}</option>
          ))}
        </select>
      </div>

      {/* Actions */}
      {selected && (
        <div className="space-y-3">
          {/* Step 2: copy — with explainer + optional preview */}
          <div>
            <label className="block text-slate-300 text-xs font-medium mb-1.5 uppercase tracking-wider">
              {isDE ? '2. Strafanzeige-Text kopieren' : '2. Copy criminal complaint text'}
            </label>
            <p className="text-slate-500 text-xs mb-2 leading-relaxed">
              {isDE
                ? 'Kopiert den vorbereiteten Strafanzeige-Text in deine Zwischenablage — Sachverhalt, alle dokumentierten Vorfälle und rechtliche Einordnung. Im nächsten Schritt fügst du ihn in das Formular ein.'
                : 'Copies the prepared criminal complaint text to your clipboard — facts, all documented incidents, legal classification. You\'ll paste it into the form in the next step.'}
            </p>
            <div className="flex items-center gap-2 flex-wrap">
              <button
                onClick={handleCopy}
                className="bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
              >
                {copied
                  ? (isDE ? '✓ Text in Zwischenablage' : '✓ Text in clipboard')
                  : (isDE ? 'Text kopieren' : 'Copy text')}
              </button>
              <button
                onClick={() => setShowPreview(s => !s)}
                className="text-slate-400 hover:text-slate-200 text-xs"
              >
                {showPreview
                  ? (isDE ? '▲ Vorschau ausblenden' : '▲ Hide preview')
                  : (isDE ? '▼ Vorschau anzeigen' : '▼ Show preview')}
              </button>
            </div>
            {showPreview && (
              <pre className="mt-3 bg-slate-900 rounded-lg p-3 text-slate-300 text-xs font-mono whitespace-pre-wrap max-h-48 overflow-y-auto border border-slate-700">
                {reportText.slice(0, 800)}
                {reportText.length > 800 ? '…' : ''}
              </pre>
            )}
          </div>

          {/* Step 3: open the form */}
          {selectedLand && (
            <div>
              <label className="block text-slate-300 text-xs font-medium mb-1.5 uppercase tracking-wider">
                {isDE ? '3. Onlinewache öffnen und Text einfügen' : '3. Open Onlinewache and paste'}
              </label>
              <a
                href={selectedLand.url}
                target="_blank"
                rel="noopener noreferrer"
                className={`inline-flex items-center justify-center gap-1 px-4 py-2 rounded-lg transition-colors text-sm font-semibold ${
                  copied
                    ? 'bg-emerald-600 hover:bg-emerald-500 text-white'
                    : 'bg-slate-700 hover:bg-slate-600 text-white border border-slate-600'
                }`}
              >
                {isDE ? `Onlinewache ${selectedLand.name} öffnen` : `Open Onlinewache ${selectedLand.name}`} →
              </a>
              <p className="text-slate-500 text-xs mt-2 leading-relaxed">
                {isDE
                  ? 'Im Formular: Anzeigeerstatter:in-Daten ausfüllen, dann den Text aus der Zwischenablage in das „Sachverhalt"-Feld einfügen (Cmd/Ctrl + V). Onlinewachen sind 24/7 erreichbar.'
                  : 'In the form: fill in your complainant details, then paste the clipboard text into the "Sachverhalt" / details field (Cmd/Ctrl + V). Onlinewachen are open 24/7.'}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
