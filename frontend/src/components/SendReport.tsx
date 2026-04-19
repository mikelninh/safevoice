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

import { useState, useMemo, useEffect } from 'react'
import type { Lang } from '../i18n'
import { downloadEml, fetchReport } from '../services/api'
import {
  POLICE_DIRECTORY,
  plzToBundesland,
  getLandPolice,
  type Bundesland,
} from '../data/police-directory'

interface VictimData {
  name: string
  address: string
  email: string
  phone: string
  plz: string
}

interface Props {
  caseId: string                 // resolved backend case ID
  reportBody: string | null       // pre-generated report body from /reports/{id}
  reportSubject: string | null
  lang: Lang
  onDownloadPdf: () => Promise<void>
}

interface Recipient {
  id: string
  label: string
  email: string
  note: string
  /** If the platform provides a form instead of (or in addition to) email,
      put the URL here — UI will surface a "Formular öffnen" button. */
  formUrl?: string
}

const DEFAULT_RECIPIENTS: Recipient[] = [
  // ── Spezialisierte Cybercrime-Zentralstellen ──
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

  // ── Plattformen (NetzDG-Meldungen / DSA Article 16 Notice) ──
  // Honest stance: most platforms force users to use forms, not email.
  // We surface forms where that's the case, with explicit Form-URL.
  {
    id: 'platform-meta',
    label: 'Meta (Facebook / Instagram) — NetzDG-Formular',
    email: '',
    note: 'Meta akzeptiert NetzDG-Beschwerden ausschließlich über das offizielle Formular.',
    formUrl: 'https://www.facebook.com/help/contact/2402814677039293',
  },
  {
    id: 'platform-x',
    label: 'X (Twitter) — NetzDG-Formular',
    email: '',
    note: 'X verarbeitet NetzDG-Beschwerden über ein eigenes Web-Formular.',
    formUrl: 'https://help.x.com/de/forms/netzdg',
  },
  {
    id: 'platform-tiktok',
    label: 'TikTok — Beschwerdeformular',
    email: '',
    note: 'TikTok verarbeitet rechtswidrige Inhalte über die In-App-/Web-Meldung.',
    formUrl: 'https://www.tiktok.com/legal/report/feedback',
  },
  {
    id: 'platform-youtube',
    label: 'YouTube / Google — NetzDG-Formular',
    email: '',
    note: 'Google bietet ein eigenes NetzDG-Beschwerdeformular für YouTube.',
    formUrl: 'https://support.google.com/youtube/contact/netzdg',
  },
  {
    id: 'platform-reddit',
    label: 'Reddit — Legal/Abuse-Formular',
    email: '',
    note: 'Reddit verarbeitet rechtliche Beschwerden über das Legal-Formular.',
    formUrl: 'https://www.reddit.com/report',
  },

  // ── Beratung / Beistand ──
  {
    id: 'hateaid',
    label: 'HateAid (Beratung)',
    email: 'beratung@hateaid.org',
    note: 'Persönliche Beratung + Prozesskostenhilfe',
  },

  // ── Generischer Fallback ──
  {
    id: 'local',
    label: 'Lokale Polizei (Onlinewache, generisch)',
    email: '',
    note: 'Generische Onlinewache-Übersicht. Wenn möglich PLZ oben eingeben für Bundesland-spezifischen Link.',
  },
  {
    id: 'custom',
    label: 'Andere E-Mail-Adresse',
    email: '',
    note: 'Eigene Adresse eintragen (z.B. Anwalt)',
  },
]

export default function SendReport({ caseId, reportBody, reportSubject, lang, onDownloadPdf }: Props) {
  const isDE = lang === 'de'
  const [victim, setVictim] = useState<VictimData>({ name: '', address: '', email: '', phone: '', plz: '' })
  const [recipientId, setRecipientId] = useState<string>('zac-nrw')
  const [detectedBL, setDetectedBL] = useState<Bundesland | null>(null)
  const [plzSuggestionAccepted, setPlzSuggestionAccepted] = useState(false)

  // Detect Bundesland from PLZ as user types (debounced-lite: only on 5 digits)
  useEffect(() => {
    if (/^\d{5}$/.test(victim.plz.trim())) {
      const bl = plzToBundesland(victim.plz.trim())
      setDetectedBL(bl)
      if (bl && !plzSuggestionAccepted) {
        // Don't auto-overwrite if user has actively chosen something else
        setRecipientId(`landespolizei-${bl}`)
      }
    } else {
      setDetectedBL(null)
    }
  }, [victim.plz, plzSuggestionAccepted])
  const [customEmail, setCustomEmail] = useState<string>('')
  const [sent, setSent] = useState(false)
  const [emlLoading, setEmlLoading] = useState(false)
  const [emlError, setEmlError] = useState<string | null>(null)
  const [emlDone, setEmlDone] = useState(false)

  // Resolve the selected recipient. Three sources:
  //   1. One of the hand-picked DEFAULT_RECIPIENTS (ZACs, HateAid, custom)
  //   2. A Bundesland landespolizei entry (id = "landespolizei-<CODE>")
  //   3. A Bundesland onlinewache entry (id = "onlinewache-<CODE>")
  const landespolizeiMatch = recipientId.match(/^landespolizei-([A-Z]{2})$/)
  const onlinewacheMatch = recipientId.match(/^onlinewache-([A-Z]{2})$/)

  const selectedRecipient: { label: string; email: string; note: string; onlinewacheUrl?: string } =
    landespolizeiMatch
      ? (() => {
          const p = getLandPolice(landespolizeiMatch[1] as Bundesland)!
          return {
            label: `Landespolizei ${p.name}`,
            email: p.centralEmail,
            note: `Zentrale Poststelle der Landespolizei ${p.name}. Bitte vor Senden verifizieren.`,
            onlinewacheUrl: p.onlinewacheUrl,
          }
        })()
      : onlinewacheMatch
        ? (() => {
            const p = getLandPolice(onlinewacheMatch[1] as Bundesland)!
            return {
              label: `Onlinewache ${p.name}`,
              email: '',
              note: `Online-Formular statt E-Mail. Text kopieren, im Formular einfügen.`,
              onlinewacheUrl: p.onlinewacheUrl,
            }
          })()
        : DEFAULT_RECIPIENTS.find(r => r.id === recipientId) ?? DEFAULT_RECIPIENTS[0]!

  const actualEmail = recipientId === 'custom'
    ? customEmail
    : selectedRecipient?.email ?? ''

  // Form-based recipients (Onlinewache OR platform NetzDG forms) have no
  // single email — they all need the same UX: copy text → open form →
  // paste. Group them under one mode flag.
  const isFormMode =
    recipientId === 'local' ||
    !!onlinewacheMatch ||
    recipientId.startsWith('platform-')

  /**
   * Derive the right report template from the chosen recipient.
   * Polizei/ZACs/Onlinewache → Strafanzeige (police body — "Ich erstatte Strafanzeige…")
   * Platforms (future) → NetzDG-Meldung (netzdg body — "auf Ihrer Plattform…")
   * HateAid / custom → police (best default — beratung@hateaid.org helps with filing)
   *
   * This fixes the bug where someone selecting Landespolizei was sending
   * the NetzDG platform-takedown text. Wrong recipient, wrong template.
   */
  const intendedReportType = useMemo<'police' | 'netzdg' | 'general'>(() => {
    if (recipientId.startsWith('platform-')) return 'netzdg'
    // Default everything else to police — that's what victims actually file
    return 'police'
  }, [recipientId])

  const TEMPLATE_LABELS_DE: Record<'police' | 'netzdg' | 'general', string> = {
    police: 'Strafanzeige (für Polizei)',
    netzdg: 'NetzDG-Meldung (für Plattform)',
    general: 'Allgemeiner Bericht',
  }
  const TEMPLATE_LABELS_EN: Record<'police' | 'netzdg' | 'general', string> = {
    police: 'Criminal complaint (for police)',
    netzdg: 'NetzDG takedown notice (for platform)',
    general: 'General report',
  }
  const intendedTemplateLabel = isDE
    ? TEMPLATE_LABELS_DE[intendedReportType]
    : TEMPLATE_LABELS_EN[intendedReportType]

  // Fetch the right template body whenever recipient (and thus intendedReportType) changes.
  // Cached per type so flipping back-and-forth doesn't re-fetch.
  const [bodyByType, setBodyByType] = useState<Record<string, string>>({})
  const [bodyLoading, setBodyLoading] = useState(false)
  const [bodyError, setBodyError] = useState<string | null>(null)

  useEffect(() => {
    if (bodyByType[intendedReportType]) return  // already cached
    setBodyLoading(true)
    setBodyError(null)
    fetchReport(caseId, intendedReportType, lang)
      .then(r => {
        setBodyByType(prev => ({ ...prev, [intendedReportType]: (r.body as string) ?? '' }))
      })
      .catch((e: Error) => setBodyError(e.message))
      .finally(() => setBodyLoading(false))
  }, [caseId, intendedReportType, lang, bodyByType])

  // Use template-specific body (overrides what was passed via prop, which
  // was tied to the Vorschau tab and could be the wrong template).
  const effectiveReportBody = bodyByType[intendedReportType] ?? reportBody ?? ''

  // Personalize the (template-correct) report body with victim data
  const personalizedBody = useMemo(() => {
    if (!effectiveReportBody) return ''
    const addressBlock = [victim.address, victim.plz].filter(Boolean).join(', ')
    const nameLine = victim.name
      ? `${victim.name}${addressBlock ? '\n' + addressBlock : ''}${victim.phone ? '\nTel: ' + victim.phone : ''}${victim.email ? '\nE-Mail: ' + victim.email : ''}`
      : '[NAME DES OPFERS]'
    return effectiveReportBody
      .replace('[NAME DES OPFERS]', nameLine)
      .replace('[VICTIM NAME]', nameLine)
      .replace('[UNTERSCHRIFT]', victim.name || '[UNTERSCHRIFT]')
      .replace('[SIGNATURE]', victim.name || '[SIGNATURE]')
  }, [effectiveReportBody, victim])

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

  const canSend = !!actualEmail.trim() && !!effectiveReportBody && !bodyLoading
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
        victim_address: [victim.address, victim.plz].filter(Boolean).join(', ') || undefined,
        victim_phone: victim.phone || undefined,
        // Send the personalized body for the template that matches the
        // recipient (police vs netzdg). This was the bug: previously we
        // sent whatever Vorschau showed, which was often the wrong template.
        body: personalizedBody || undefined,
        report_type: intendedReportType,
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
          {isDE ? '1. Absenderdaten' : '1. Sender details'}
        </h3>
        <p className="text-xs text-slate-400 mb-3">
          {isDE
            ? 'Wird in die Strafanzeige eingefügt. Bleibt nur im Browser — nichts wird ohne Klick versendet.'
            : 'Inserted into the complaint. Stays in the browser — nothing sent without a click.'}
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
            placeholder={isDE ? 'Straße und Hausnummer' : 'Street and number'}
            value={victim.address}
            onChange={(e) => setVictim(v => ({ ...v, address: e.target.value }))}
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 sm:col-span-2"
          />
          <input
            type="text"
            inputMode="numeric"
            maxLength={5}
            placeholder={isDE ? 'PLZ (5-stellig)' : 'Postal code (5 digits)'}
            value={victim.plz}
            onChange={(e) => { setVictim(v => ({ ...v, plz: e.target.value.replace(/\D/g, '') })); setPlzSuggestionAccepted(false) }}
            className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500"
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

        {/* PLZ-based detection hint */}
        {detectedBL && (
          <div className="mb-2 bg-indigo-950/30 border border-indigo-800/50 rounded-lg px-3 py-2 text-xs text-indigo-200">
            <span className="font-medium">📍 {getLandPolice(detectedBL)?.name}</span>
            {' '}
            <span className="text-indigo-300/80">
              {isDE
                ? `— basierend auf deiner PLZ. Landespolizei ${getLandPolice(detectedBL)?.name} ist vorausgewählt.`
                : `— based on your postal code. Landespolizei ${getLandPolice(detectedBL)?.name} pre-selected.`}
            </span>
          </div>
        )}

        <select
          value={recipientId}
          onChange={(e) => { setRecipientId(e.target.value); setPlzSuggestionAccepted(true) }}
          className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100"
        >
          <optgroup label={isDE ? 'Spezialisierte Zentralstellen (empfohlen für Online-Hass)' : 'Specialised units (recommended for online hate)'}>
            {DEFAULT_RECIPIENTS.filter(r => r.id.startsWith('zac-') || r.id.startsWith('zcb-') || r.id.startsWith('zit-')).map(r => (
              <option key={r.id} value={r.id}>{r.label}</option>
            ))}
          </optgroup>
          <optgroup label={isDE ? 'Landespolizei (alle 16 Bundesländer)' : 'State police (all 16 Bundesländer)'}>
            {POLICE_DIRECTORY.map(p => (
              <option key={`landespolizei-${p.code}`} value={`landespolizei-${p.code}`}>
                Landespolizei {p.name}{detectedBL === p.code ? ' ⭐' : ''}
              </option>
            ))}
          </optgroup>
          <optgroup label={isDE ? 'Onlinewache (Formular statt E-Mail)' : 'Online portal (form instead of email)'}>
            {POLICE_DIRECTORY.map(p => (
              <option key={`onlinewache-${p.code}`} value={`onlinewache-${p.code}`}>
                Onlinewache {p.name}{detectedBL === p.code ? ' ⭐' : ''}
              </option>
            ))}
          </optgroup>
          <optgroup label={isDE ? 'Plattformen (NetzDG-Beschwerde)' : 'Platforms (NetzDG takedown)'}>
            {DEFAULT_RECIPIENTS.filter(r => r.id.startsWith('platform-')).map(r => (
              <option key={r.id} value={r.id}>{r.label}</option>
            ))}
          </optgroup>
          <optgroup label={isDE ? 'Beratung & Andere' : 'Counseling & Other'}>
            <option value="hateaid">HateAid (Beratung)</option>
            <option value="local">Onlinewache (bundesweit generisch)</option>
            <option value="custom">Andere E-Mail-Adresse</option>
          </optgroup>
        </select>

        <p className="text-xs text-slate-400 mt-1">{selectedRecipient?.note}</p>

        {/* Show the email we'll use so user can verify */}
        {actualEmail && (
          <p className="text-[11px] text-slate-500 mt-1 font-mono">
            → {actualEmail}
          </p>
        )}

        {/* Show which template will be sent — fixes the bug where users
            sent the NetzDG platform-takedown text to the police. */}
        <div className="mt-3 bg-slate-800/50 border border-slate-700 rounded-lg px-3 py-2 text-xs flex items-center gap-2">
          <span>📄</span>
          <div className="flex-1">
            <span className="text-slate-400">{isDE ? 'Vorlage:' : 'Template:'}</span>{' '}
            <span className="text-slate-100 font-medium">{intendedTemplateLabel}</span>
            {bodyLoading && (
              <span className="text-slate-500 ml-2">{isDE ? '(Vorlage wird vom Server geladen…)' : '(fetching template…)'}</span>
            )}
            {bodyError && (
              <span className="text-red-400 ml-2">{bodyError.slice(0, 60)}</span>
            )}
          </div>
        </div>

        {recipientId === 'custom' && (
          <input
            type="email"
            placeholder="E-Mail-Adresse eingeben"
            value={customEmail}
            onChange={(e) => setCustomEmail(e.target.value)}
            className="mt-2 w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500"
          />
        )}

        {/* Verification hint for Landespolizei emails */}
        {recipientId.startsWith('landespolizei-') && (
          <p className="text-[11px] text-amber-400/80 mt-2 leading-relaxed">
            {isDE
              ? '⚠ Zentrale Poststelle der Landespolizei. Diese Adressen wurden recherchiert, bitte vor Senden kurz verifizieren. Spezialisierte Cybercrime-Stellen (wenn oben gelistet) sind für Online-Hass meist die bessere Wahl.'
              : '⚠ Central police office email. These were researched but please verify before sending. Specialised cybercrime units (if listed above) are usually a better choice for online hate.'}
          </p>
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

      {/* PRIMARY ACTIONS — different flow for form-based recipients (Onlinewache, Plattformen) vs email */}
      {isFormMode ? (() => {
        const isPlatform = recipientId.startsWith('platform-')
        const formUrl =
          (selectedRecipient as Recipient).formUrl
          || (selectedRecipient as { onlinewacheUrl?: string }).onlinewacheUrl
          || 'https://www.onlinewache.polizei.de'
        return (
          <div className="space-y-2 pt-2">
            <div className="bg-indigo-950/30 border border-indigo-800/50 rounded-xl p-3 space-y-3">
              <div className="flex items-start gap-2">
                <span className="text-xl">{isPlatform ? '🛡️' : '🌐'}</span>
                <div className="flex-1">
                  <div className="text-sm font-semibold text-indigo-200">
                    {isPlatform
                      ? isDE ? 'Plattform-Beschwerde: 2-Schritt-Ablauf' : 'Platform takedown: 2-step flow'
                      : isDE ? 'Onlinewache: 2-Schritt-Ablauf' : 'Onlinewache: 2-step flow'}
                  </div>
                  <div className="text-xs text-indigo-300/80 mt-0.5">
                    {isPlatform
                      ? isDE
                        ? 'Diese Plattform akzeptiert keine NetzDG-E-Mails — nur das offizielle Formular. Text kopieren, Formular öffnen, einfügen.'
                        : 'This platform does not accept NetzDG complaints by email — only via their official form. Copy, open form, paste.'
                      : isDE
                        ? 'Die Onlinewache jedes Bundeslands hat ein eigenes Formular — keine einheitliche E-Mail-Adresse. Text kopieren, Formular öffnen, einfügen.'
                        : 'Every Bundesland\'s online police portal has its own form — no unified email. Copy, open form, paste.'}
                  </div>
                </div>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                <button
                  onClick={async () => { await copyFullReport(); setEmlDone(true) }}
                  disabled={!effectiveReportBody}
                  className="bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 disabled:opacity-50 text-white font-semibold py-3 rounded-xl transition-colors text-sm"
                >
                  {emlDone
                    ? isDE ? '✓ Text kopiert' : '✓ Text copied'
                    : isDE ? '1. Text kopieren' : '1. Copy text'}
                </button>
                <a
                  href={formUrl}
                  target="_blank"
                  rel="noreferrer"
                  onClick={async () => { await onDownloadPdf() }}
                  className="bg-slate-700 hover:bg-slate-600 text-white font-semibold py-3 rounded-xl transition-colors text-sm text-center inline-flex items-center justify-center gap-1"
                >
                  {isPlatform
                    ? isDE ? '2. Plattform-Formular öffnen' : '2. Open platform form'
                    : isDE ? '2. Onlinewache öffnen' : '2. Open portal'}
                </a>
              </div>
              <div className="text-[11px] text-indigo-300/70">
                {isPlatform
                  ? isDE
                    ? 'Der zweite Klick lädt zusätzlich das PDF herunter — viele Plattform-Formulare erlauben PDF-Upload als Beweis.'
                    : 'The second click also downloads the PDF — many platform forms accept PDF as evidence upload.'
                  : isDE
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
                      <li>{isPlatform ? 'Plattform-Formular öffnen (Button oben)' : 'Onlinewache öffnen (Button oben)'}</li>
                      {isPlatform
                        ? <li>Im Beschwerde-Formular „Sonstiges" / „Begründung" wählen</li>
                        : <li>Bundesland wählen</li>}
                      <li>Text einfügen (Cmd+V)</li>
                      <li>{isPlatform
                        ? 'PDF als Anhang hochladen (falls möglich) und absenden.'
                        : 'Formular abschicken. PDF später anhängen, wenn du angeschrieben wirst.'}</li>
                    </ol>
                  </>
                ) : (
                  <>
                    <div className="font-semibold mb-1">Text in clipboard. Next:</div>
                    <ol className="list-decimal list-inside space-y-0.5 text-emerald-100/80">
                      <li>{isPlatform ? 'Open the platform form (button above)' : 'Open Onlinewache (button above)'}</li>
                      <li>{isPlatform ? 'Select "Other" / "Reason" in the form' : 'Select the Bundesland'}</li>
                      <li>Paste text (Cmd+V)</li>
                      <li>{isPlatform
                        ? 'Upload PDF as attachment (if supported) and submit.'
                        : 'Submit. Attach PDF later when police reply.'}</li>
                    </ol>
                  </>
                )}
              </div>
            )}
          </div>
        )
      })() : (
        <div className="space-y-2 pt-2">
          <div className="bg-indigo-950/30 border border-indigo-800/50 rounded-xl p-3 space-y-3">
            <div className="flex items-start gap-2">
              <div className="flex-1">
                <div className="text-sm font-semibold text-indigo-200">
                  {isDE ? 'Empfohlen: Fertige E-Mail (.eml)' : 'Recommended: Ready-to-send email (.eml)'}
                </div>
                <div className="text-xs text-indigo-300/80 mt-0.5">
                  {isDE
                    ? 'Doppelklick auf die Datei öffnet deine Mail-App mit Empfänger, Betreff, Text und Anhängen — du musst noch senden.'
                    : 'Double-click the file to open your mail app with recipient, subject, body, and attachments all pre-filled — then send.'}
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
                ? isDE ? '.eml wird vom Server gebaut…' : 'Building .eml on server…'
                : emlDone
                  ? isDE ? '✓ .eml heruntergeladen — Doppelklick öffnet Mail' : '✓ .eml downloaded — double-click to open'
                  : isDE ? 'E-Mail-Datei (.eml) herunterladen' : 'Download email file (.eml)'}
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
                    : isDE ? 'mailto: öffnen + PDF herunterladen' : 'Open mailto: + download PDF'}
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
                {isDE ? 'Volltext kopieren (z.B. für Onlinewache)' : 'Copy full text (for online police forms)'}
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
