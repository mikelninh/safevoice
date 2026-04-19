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
  const isDE = lang === 'de'

  const selectedLand = BUNDESLAENDER.find(b => b.name === selected)

  const handleCopy = () => {
    navigator.clipboard.writeText(reportText)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="bg-slate-800 border border-slate-700 rounded-xl p-5 space-y-4">
      <div>
        <h3 className="text-white font-semibold mb-1">
          {isDE ? 'Online-Strafanzeige erstatten' : 'File police report online'}
        </h3>
        <p className="text-slate-400 text-sm">
          {isDE
            ? 'Bundesland wählen, vorbereiteten Text kopieren, in das Onlinewache-Formular einfügen.'
            : 'Select the state, copy the prepared text, paste it into the Onlinewache form.'}
        </p>
      </div>

      {/* Bundesland selector */}
      <select
        value={selected}
        onChange={e => setSelected(e.target.value)}
        className="w-full bg-slate-900 border border-slate-600 rounded-lg px-3 py-2.5 text-slate-200 text-sm focus:outline-none focus:border-indigo-500"
      >
        <option value="">
          {isDE ? '— Bundesland wählen —' : '— Select state —'}
        </option>
        {BUNDESLAENDER.map(b => (
          <option key={b.name} value={b.name}>{b.name}</option>
        ))}
      </select>

      {/* Actions */}
      {selected && (
        <div className="space-y-3">
          <div className="flex flex-col sm:flex-row gap-2">
            <button
              onClick={handleCopy}
              className="flex-1 bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold py-2.5 rounded-lg transition-colors"
            >
              {copied
                ? (isDE ? '✓ Text kopiert' : '✓ Text copied')
                : (isDE ? '1. Text kopieren' : '1. Copy report text')}
            </button>
            {selectedLand && (
              <a
                href={selectedLand.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 text-center bg-slate-700 hover:bg-slate-600 text-white text-sm font-semibold py-2.5 rounded-lg transition-colors border border-slate-600"
              >
                {isDE ? '2. Onlinewache öffnen' : '2. Open Onlinewache'} →
              </a>
            )}
          </div>

          <p className="text-slate-500 text-xs">
            {isDE
              ? 'Tipp: Füge den kopierten Text im Freitext-Feld der Onlinewache ein. Die meisten Onlinewachen akzeptieren Anzeigen rund um die Uhr.'
              : 'Tip: Paste the copied text in the free-text field of the Onlinewache. Most accept reports 24/7.'}
          </p>
        </div>
      )}
    </div>
  )
}
