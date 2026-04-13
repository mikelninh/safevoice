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
import { downloadEml } from '../services/api'

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
  const [emlLoading, setEmlLoading] = useState(false)
  const [emlError, setEmlError] = useState<string | null>(null)
  const [emlDone, setEmlDone] = useState(false)

  const selectedRecipient = DEFAULT_RECIPIENTS.find(r => r.id === recipientId) ?? DEFAULT_RECIPIENTS[0]
  const actualEmail = recipientId === 'custom'
    ? customEmail
    : selectedRecipient?.email ?? ''

  // "Lokale Polizei / Onlinewache" has no single email address (each
  // Bundesland runs its own portal), so we show an alternative flow instead
  // of disabled email buttons: open the portal + copy-paste text.
  const isOnlineWacheMode = recipientId === 'local'

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

  const handleEmlDownload = async () => {
    setEmlError(null)
    setEmlLoading(true)
    setEmlDone(false)
    try {
      await downloadEml(caseId, {
        recipient_email: actualEmail,
        victim_name: victim.name || undefined,
        victim_email: victim.email || undefined,
        victim_address: victim.address || undefined,
        victim_phone: victim.phone || undefined,
        // Pass the pre-computed body if the user stayed on the police tab;
        // otherwise backend will build its own from the police template.
        body: personalizedBody || undefined,
      })
      setEmlDone(true)
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e)
      console.error('[SendReport] EML download failed:', e)
      setEmlError(msg)
    } finally {
      setEmlLoading(false)
    }
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

      {/* PRIMARY ACTIONS — different flow for Onlinewache vs email recipients */}
      {isOnlineWacheMode ? (
        <div className="space-y-2 pt-2">
          <div className="bg-indigo-950/30 border border-indigo-800/50 rounded-xl p-3 space-y-3">
            <div className="flex items-start gap-2">
              <span className="text-xl">🌐</span>
              <div className="flex-1">
                <div className="text-sm font-semibold text-indigo-200">
                  {isDE ? 'Onlinewache: 2-Schritt-Ablauf' : 'Onlinewache: 2-step flow'}
                </div>
                <div className="text-xs text-indigo-300/80 mt-0.5">
                  {isDE
                    ? 'Die Onlinewache jedes Bundeslands hat ein eigenes Formular — keine einheitliche E-Mail-Adresse. Deshalb: Text kopieren, Formular öffnen, einfügen.'
                    : 'Every Bundesland\'s online police portal has its own form — no unified email. So: copy text, open portal, paste.'}
                </div>
              </div>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              <button
                onClick={async () => { await copyFullReport(); setEmlDone(true) }}
                disabled={!reportBody}
                className="bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 disabled:opacity-50 text-white font-semibold py-3 rounded-xl transition-colors text-sm"
              >
                {emlDone
                  ? isDE ? '✓ Text kopiert' : '✓ Text copied'
                  : isDE ? '1. 📋 Text kopieren' : '1. 📋 Copy text'}
              </button>
              <a
                href="https://www.onlinewache.polizei.de"
                target="_blank"
                rel="noreferrer"
                onClick={async () => { await onDownloadPdf() }}
                className="bg-slate-700 hover:bg-slate-600 text-white font-semibold py-3 rounded-xl transition-colors text-sm text-center inline-flex items-center justify-center gap-1"
              >
                {isDE ? '2. 🌐 Onlinewache öffnen' : '2. 🌐 Open portal'}
              </a>
            </div>
            <div className="text-[11px] text-indigo-300/70">
              {isDE
                ? 'Der zweite Klick lädt zusätzlich das PDF herunter — zum späteren Anhängen an die Antwort-Mail der Polizei.'
                : 'The second click also downloads the PDF — to attach later to the police response.'}
            </div>
          </div>
          {emlDone && (
            <div className="bg-emerald-900/30 border border-emerald-800 text-emerald-200 rounded-lg p-3 text-xs">
              {isDE ? (
                <>
                  <div className="font-semibold mb-1">Text in Zwischenablage. Weiter so:</div>
                  <ol className="list-decimal list-inside space-y-0.5 text-emerald-100/80">
                    <li>Onlinewache öffnen (Button oben)</li>
                    <li>Bundesland wählen</li>
                    <li>Im Formular-Freitext-Feld einfügen (Cmd+V)</li>
                    <li>Formular abschicken. PDF später anhängen, wenn du angeschrieben wirst.</li>
                  </ol>
                </>
              ) : (
                <>
                  <div className="font-semibold mb-1">Text in clipboard. Next:</div>
                  <ol className="list-decimal list-inside space-y-0.5 text-emerald-100/80">
                    <li>Open Onlinewache (button above)</li>
                    <li>Select your Bundesland</li>
                    <li>Paste (Cmd+V) into the free-text field</li>
                    <li>Submit. Attach PDF later when police reply.</li>
                  </ol>
                </>
              )}
            </div>
          )}
        </div>
      ) : (
        <div className="space-y-2 pt-2">
          <div className="bg-indigo-950/30 border border-indigo-800/50 rounded-xl p-3 space-y-3">
            <div className="flex items-start gap-2">
              <span className="text-xl">✨</span>
              <div className="flex-1">
                <div className="text-sm font-semibold text-indigo-200">
                  {isDE ? 'Empfohlen: Fertige E-Mail (.eml)' : 'Recommended: Ready-to-send email (.eml)'}
                </div>
                <div className="text-xs text-indigo-300/80 mt-0.5">
                  {isDE
                    ? 'Doppelklick auf die Datei öffnet deine Mail-App mit Empfänger, Betreff, Text und Anhängen — du musst nur noch senden.'
                    : 'Double-click the file to open your mail app with recipient, subject, body, and attachments all ready — just hit send.'}
                </div>
              </div>
            </div>
            {!actualEmail.trim() && recipientId === 'custom' && (
              <div className="bg-amber-900/30 border border-amber-800 text-amber-200 rounded px-3 py-2 text-xs">
                {isDE ? 'Bitte E-Mail-Adresse oben eingeben.' : 'Please enter an email address above.'}
              </div>
            )}
            <button
              onClick={handleEmlDownload}
              disabled={!canSend || emlLoading}
              className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-xl transition-colors flex items-center justify-center gap-2"
            >
              {emlLoading
                ? isDE ? 'Wird erstellt…' : 'Building…'
                : emlDone
                  ? isDE ? '✓ .eml heruntergeladen — Doppelklick öffnet Mail' : '✓ .eml downloaded — double-click to open'
                  : isDE ? '📨 E-Mail-Datei (.eml) herunterladen' : '📨 Download email file (.eml)'}
            </button>
            {emlError && (
              <div className="text-xs text-red-300 bg-red-950/40 border border-red-900 rounded px-3 py-2 break-all font-mono">
                {emlError}
              </div>
            )}
            <div className="text-[11px] text-indigo-400/70">
              {isDE
                ? 'Funktioniert mit: Apple Mail, Outlook, Thunderbird. Gmail-Web: bitte untere Option nutzen.'
                : 'Works with: Apple Mail, Outlook, Thunderbird. For Gmail web: use the option below.'}
            </div>
          </div>

          {/* Secondary fallback: mailto + copy */}
          <details className="text-xs text-slate-400">
            <summary className="cursor-pointer py-2 select-none hover:text-slate-300">
              {isDE ? 'Andere Optionen (Gmail, Text kopieren)' : 'Other options (Gmail, copy text)'}
            </summary>
            <div className="mt-2 pl-3 space-y-2 border-l border-slate-700">
              <div>
                <button
                  onClick={handleSend}
                  disabled={!canSend}
                  className="w-full bg-slate-700 hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed text-slate-200 font-medium py-2.5 rounded-lg text-sm"
                >
                  {sent
                    ? isDE ? 'E-Mail geöffnet — PDF manuell anhängen' : 'Email opened — attach PDF manually'
                    : isDE ? '📧 mailto: öffnen + PDF herunterladen' : '📧 Open mailto: + download PDF'}
                </button>
                <p className="text-[11px] text-slate-500 mt-1">
                  {isDE
                    ? 'Öffnet die Mail-App mit Text. Anhänge musst du selbst per Drag & Drop einfügen.'
                    : 'Opens mail app with body. You must drag & drop attachments yourself.'}
                </p>
              </div>
              <button
                onClick={copyFullReport}
                className="w-full bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium py-2.5 rounded-lg text-sm border border-slate-700"
              >
                {isDE ? '📋 Volltext kopieren (z.B. für Onlinewache)' : '📋 Copy full text (for online police forms)'}
              </button>
            </div>
          </details>
        </div>
      )}

      {emlDone && (
        <div className="bg-emerald-900/30 border border-emerald-800 text-emerald-200 rounded-lg p-3 text-xs">
          {isDE ? (
            <>
              <div className="font-semibold mb-1">Nächste Schritte:</div>
              <ol className="list-decimal list-inside space-y-0.5 text-emerald-100/80">
                <li>Finder / Explorer öffnen, zu Downloads gehen</li>
                <li>Doppelklick auf die <code className="bg-black/40 px-1 rounded">.eml</code> Datei</li>
                <li>Mail-App öffnet sich — PDF und Hash-Chain-CSV sind bereits angehängt</li>
                <li>Prüfen, ggf. Lichtbildausweis hinzufügen, dann senden</li>
              </ol>
            </>
          ) : (
            <>
              <div className="font-semibold mb-1">Next steps:</div>
              <ol className="list-decimal list-inside space-y-0.5 text-emerald-100/80">
                <li>Open Finder / Explorer, go to Downloads</li>
                <li>Double-click the <code className="bg-black/40 px-1 rounded">.eml</code> file</li>
                <li>Mail app opens — PDF and hash-chain CSV already attached</li>
                <li>Review, optionally attach photo ID, hit Send</li>
              </ol>
            </>
          )}
        </div>
      )}
      {sent && !emlDone && (
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
