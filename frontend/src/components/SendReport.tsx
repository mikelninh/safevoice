/**
 * SendReport — Opferdaten-Form + Ein-Klick-Versand.
 *
 * Flow:
 *   1. User füllt Absenderdaten aus (Name, Anschrift, E-Mail)
 *   2. User wählt Empfänger (Staatsanwaltschaft / Plattform / eigene E-Mail)
 *   3. Klick auf "Per E-Mail senden":
 *      - PDF wird heruntergeladen (enthält vollen Text + Hash-Chain)
 *      - mailto: wird geöffnet mit pre-filled Subject + Summary
 *   4. User hängt PDF manuell an die offene E-Mail
 *
 * Limitation: Browser lassen keine Anhänge via mailto: zu. Das PDF muss
 * manuell angehängt werden. Deswegen der Toast nach Klick.
 */

import { useState, useMemo } from 'react'
import type { Lang } from '../i18n'

interface VictimData {
  name: string
  address: string
  email: string
  phone: string
}

interface Props {
  caseId: string                 // resolved backend case ID
  reportBody: string | null       // pre-generated report body from /reports/{id}
  reportSubject: string | null
  lang: Lang
  onDownloadPdf: () => Promise<void>
}

const DEFAULT_RECIPIENTS = [
  {
    id: 'zac-nrw',
    label: 'ZAC NRW (Staatsanwaltschaft Köln)',
    email: 'poststelle@sta-koeln.nrw.de',
    note: 'Zentralstelle Hasskriminalität NRW — Zuständig bei hohen Fallzahlen in NRW',
  },
  {
    id: 'zcb-bayern',
    label: 'ZCB Bayern (GenStA Bamberg)',
    email: 'poststelle@generalstaatsanwaltschaft-bamberg.bayern.de',
    note: 'Zentralstelle Cybercrime Bayern',
  },
  {
    id: 'zit-hessen',
    label: 'ZIT Hessen (GenStA Frankfurt)',
    email: 'poststelle@gsta-frankfurt.justiz.hessen.de',
    note: 'Zentralstelle Internet- und Computerkriminalität',
  },
  {
    id: 'local',
    label: 'Lokale Polizei (Onlinewache)',
    email: '',
    note: 'Nutze die Onlinewache deines Bundeslands — onlinewache.polizei.de',
  },
  {
    id: 'hateaid',
    label: 'HateAid (Beratung)',
    email: 'beratung@hateaid.org',
    note: 'Persönliche Beratung + Prozesskostenhilfe',
  },
  {
    id: 'custom',
    label: 'Andere E-Mail-Adresse',
    email: '',
    note: 'Eigene Adresse eintragen (z.B. Anwalt)',
  },
]

const PLATFORM_ABUSE_EMAILS: Record<string, string> = {
  instagram: 'support@meta.com',
  facebook: 'support@meta.com',
  x: 'support@x.com',
  twitter: 'support@x.com',
  tiktok: 'legal@tiktok.com',
}

export default function SendReport({ caseId, reportBody, reportSubject, lang, onDownloadPdf }: Props) {
  const isDE = lang === 'de'
  const [victim, setVictim] = useState<VictimData>({ name: '', address: '', email: '', phone: '' })
  const [recipientId, setRecipientId] = useState<string>('zac-nrw')
  const [customEmail, setCustomEmail] = useState<string>('')
  const [sent, setSent] = useState(false)

  const selectedRecipient = DEFAULT_RECIPIENTS.find(r => r.id === recipientId) ?? DEFAULT_RECIPIENTS[0]
  const actualEmail = recipientId === 'custom'
    ? customEmail
    : selectedRecipient?.email ?? ''

  // Personalize the report body with victim data
  const personalizedBody = useMemo(() => {
    if (!reportBody) return ''
    const nameLine = victim.name
      ? `${victim.name}${victim.address ? '\n' + victim.address : ''}${victim.phone ? '\nTel: ' + victim.phone : ''}${victim.email ? '\nE-Mail: ' + victim.email : ''}`
      : '[NAME DES OPFERS]'
    return reportBody
      .replace('[NAME DES OPFERS]', nameLine)
      .replace('[VICTIM NAME]', nameLine)
      .replace('[UNTERSCHRIFT]', victim.name || '[UNTERSCHRIFT]')
      .replace('[SIGNATURE]', victim.name || '[SIGNATURE]')
  }, [reportBody, victim])

  // mailto body: browsers limit URL to ~2000 chars. We truncate body and
  // tell the user the full content is in the attached PDF.
  const mailBody = useMemo(() => {
    const summary = personalizedBody.length > 1200
      ? personalizedBody.slice(0, 1200) + '\n\n[...] \n\n— Vollständiger Bericht + Hash-Chain-Beweis siehe beigefügtes PDF.'
      : personalizedBody
    return summary + (isDE
      ? '\n\n---\nErstellt mit SafeVoice. PDF mit Beweiskette ist manuell beigefügt.'
      : '\n\n---\nCreated with SafeVoice. PDF with chain-of-custody is attached manually.')
  }, [personalizedBody, isDE])

  const subject = reportSubject || 'Strafanzeige'
  const mailtoUrl = `mailto:${encodeURIComponent(actualEmail)}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(mailBody)}`

  const canSend = !!actualEmail.trim() && !!reportBody
  const missingName = !victim.name.trim()

  const handleSend = async () => {
    // Start PDF download first so it's ready in Downloads when mailto opens
    try {
      await onDownloadPdf()
    } catch (e) {
      console.error('[SendReport] PDF download failed:', e)
    }
    // Open mailto — delay slightly so download trigger settles
    setTimeout(() => {
      window.location.href = mailtoUrl
    }, 200)
    setSent(true)
  }

  const copyFullReport = async () => {
    if (!personalizedBody) return
    await navigator.clipboard.writeText(personalizedBody)
  }

  return (
    <div className="space-y-4">
      {/* Step 1: Opferdaten */}
      <section>
        <h3 className="text-sm font-semibold text-slate-200 mb-2">
          {isDE ? '1. Ihre Absenderdaten' : '1. Your sender details'}
        </h3>
        <p className="text-xs text-slate-400 mb-3">
          {isDE
            ? 'Wird in die Strafanzeige eingefügt. Bleibt nur in deinem Browser — nichts wird ohne dein Klick versendet.'
            : 'Inserted into the complaint. Stays in your browser — nothing sent without your click.'}
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          <input
            type="text"
            placeholder={isDE ? 'Vollständiger Name' : 'Full name'}
            value={victim.name}
            onChange={(e) => setVictim(v => ({ ...v, name: e.target.value }))}
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500"
          />
          <input
            type="email"
            placeholder="E-Mail"
            value={victim.email}
            onChange={(e) => setVictim(v => ({ ...v, email: e.target.value }))}
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500"
          />
          <input
            type="text"
            placeholder={isDE ? 'Anschrift (Straße, PLZ, Ort)' : 'Address'}
            value={victim.address}
            onChange={(e) => setVictim(v => ({ ...v, address: e.target.value }))}
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 sm:col-span-2"
          />
          <input
            type="tel"
            placeholder={isDE ? 'Telefon (optional)' : 'Phone (optional)'}
            value={victim.phone}
            onChange={(e) => setVictim(v => ({ ...v, phone: e.target.value }))}
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500"
          />
        </div>
      </section>

      {/* Step 2: Recipient */}
      <section>
        <h3 className="text-sm font-semibold text-slate-200 mb-2">
          {isDE ? '2. Empfänger' : '2. Recipient'}
        </h3>
        <select
          value={recipientId}
          onChange={(e) => setRecipientId(e.target.value)}
          className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100"
        >
          {DEFAULT_RECIPIENTS.map(r => (
            <option key={r.id} value={r.id}>{r.label}</option>
          ))}
        </select>
        <p className="text-xs text-slate-400 mt-1">{selectedRecipient?.note}</p>
        {recipientId === 'custom' && (
          <input
            type="email"
            placeholder="E-Mail-Adresse eingeben"
            value={customEmail}
            onChange={(e) => setCustomEmail(e.target.value)}
            className="mt-2 w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500"
          />
        )}
        {recipientId === 'local' && (
          <a
            href="https://www.onlinewache.polizei.de"
            target="_blank"
            rel="noreferrer"
            className="mt-2 inline-block text-xs text-indigo-400 hover:text-indigo-300 underline"
          >
            {isDE ? '→ Onlinewache öffnen (bundesweit)' : '→ Open online police portal'}
          </a>
        )}
      </section>

      {/* Step 3: Attachment checklist */}
      <section>
        <h3 className="text-sm font-semibold text-slate-200 mb-2">
          {isDE ? '3. Anhänge-Checkliste' : '3. Attachment checklist'}
        </h3>
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-3 text-xs text-slate-300 space-y-2">
          <div className="flex items-start gap-2">
            <span className="text-emerald-400 mt-0.5">✓</span>
            <div>
              <div className="font-medium text-slate-200">{isDE ? 'PDF-Bericht (automatisch)' : 'PDF report (automatic)'}</div>
              <div className="text-slate-500">
                {isDE ? 'Wird heruntergeladen beim Klick. Enthält Hash-Chain + alle Beweise.' : 'Downloads on click. Contains hash chain + all evidence.'}
              </div>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-amber-400 mt-0.5">⚠</span>
            <div>
              <div className="font-medium text-slate-200">
                {isDE ? 'PDF manuell an E-Mail anhängen' : 'Manually attach PDF to email'}
              </div>
              <div className="text-slate-500">
                {isDE
                  ? 'Browser lassen keine automatischen Anhänge zu. Bitte per Drag&Drop einfügen.'
                  : 'Browsers don\'t allow automatic attachments. Drag & drop into the email.'}
              </div>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-slate-500 mt-0.5">◌</span>
            <div>
              <div className="font-medium text-slate-400">
                {isDE ? 'Lichtbildausweis (falls gefordert)' : 'Photo ID (if requested)'}
              </div>
              <div className="text-slate-500">
                {isDE
                  ? 'Manuell anhängen — sensible Daten laufen nicht über SafeVoice.'
                  : 'Attach manually — SafeVoice does not transmit ID documents.'}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Warnings */}
      {missingName && (
        <div className="bg-amber-900/30 border border-amber-800 text-amber-200 rounded-lg p-3 text-xs">
          {isDE
            ? '⚠ Ohne Namen wird der Platzhalter "[NAME DES OPFERS]" im Bericht stehen bleiben.'
            : '⚠ Without a name, the placeholder "[VICTIM NAME]" will remain in the report.'}
        </div>
      )}

      {/* Action */}
      <div className="flex flex-col sm:flex-row gap-2 pt-2">
        <button
          onClick={handleSend}
          disabled={!canSend}
          className="flex-1 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-xl transition-colors"
        >
          {sent
            ? isDE ? 'E-Mail geöffnet — PDF anhängen' : 'Email opened — attach PDF'
            : isDE ? '📧 E-Mail öffnen + PDF herunterladen' : '📧 Open email + download PDF'}
        </button>
        <button
          onClick={copyFullReport}
          className="bg-slate-700 hover:bg-slate-600 text-slate-200 font-medium py-3 px-4 rounded-xl transition-colors text-sm"
          title={isDE ? 'Volltext kopieren — für Onlinewache-Formular' : 'Copy full text — for online police forms'}
        >
          {isDE ? 'Text kopieren' : 'Copy text'}
        </button>
      </div>

      {sent && (
        <div className="bg-emerald-900/30 border border-emerald-800 text-emerald-200 rounded-lg p-3 text-xs">
          {isDE ? (
            <>
              <div className="font-semibold mb-1">Nächste Schritte:</div>
              <ol className="list-decimal list-inside space-y-0.5 text-emerald-100/80">
                <li>PDF aus Downloads öffnen und prüfen</li>
                <li>In die geöffnete E-Mail per Drag &amp; Drop anhängen</li>
                <li>Bei Bedarf: Lichtbildausweis anhängen</li>
                <li>Senden</li>
              </ol>
            </>
          ) : (
            <>
              <div className="font-semibold mb-1">Next steps:</div>
              <ol className="list-decimal list-inside space-y-0.5 text-emerald-100/80">
                <li>Open PDF from Downloads and review</li>
                <li>Drag &amp; drop it into the email</li>
                <li>Attach photo ID if needed</li>
                <li>Send</li>
              </ol>
            </>
          )}
        </div>
      )}

      {/* Subtle watermark */}
      <p className="text-[10px] text-slate-600 text-center pt-2">
        {isDE
          ? `Fall-ID: ${caseId.slice(0, 8)}... · SafeVoice generiert · Keine Rechtsberatung`
          : `Case ID: ${caseId.slice(0, 8)}... · Generated by SafeVoice · Not legal advice`}
      </p>
    </div>
  )
}
