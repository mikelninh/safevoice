/**
 * Inline edit + add-evidence panel for a case.
 *
 * - "Beweis hinzufügen" tab: append text or a screenshot. Both classify
 *   locally AND push to the backend case so the server-side legal AI +
 *   Strafanzeige template see the new piece.
 * - "Kontext & Titel" tab: change case title + victim_context. PUTs to
 *   the backend so the legal AI sees the updated context.
 *
 * Author handles are edited inline on each EvidenceCard — there is no
 * separate "authors" tab here (it was duplicated work and confused users).
 */
import { useRef, useState } from 'react'
import {
  addEvidenceToBackendCase,
  analyzeText,
  ensureBackendCase,
  updateBackendCase,
  uploadScreenshot,
} from '../services/api'
import {
  addEvidenceToCase,
  updateCaseBackendId,
  updateCaseFields,
} from '../services/storage'
import type { Case } from '../types'
import type { Lang } from '../i18n'

interface Props {
  caseData: Case
  lang: Lang
  onChange: (updated: Case) => void
}

type Tab = 'context' | 'evidence'
type SyncState = 'idle' | 'syncing' | 'synced' | 'failed'

export default function CaseEditor({ caseData, lang, onChange }: Props) {
  const [open, setOpen] = useState(false)
  const [tab, setTab] = useState<Tab>('evidence')
  const isDE = lang === 'de'

  // Context editor state
  const [title, setTitle] = useState(caseData.title)
  const [context, setContext] = useState(caseData.victim_context ?? '')
  const [savingContext, setSavingContext] = useState(false)
  const [contextSync, setContextSync] = useState<SyncState>('idle')

  // Add-evidence state
  const [evidenceText, setEvidenceText] = useState('')
  const [evidenceAuthor, setEvidenceAuthor] = useState('')
  const [evidenceUrl, setEvidenceUrl] = useState('')
  const [addingEvidence, setAddingEvidence] = useState(false)
  const [addError, setAddError] = useState<string | null>(null)
  const [evidenceSync, setEvidenceSync] = useState<SyncState>('idle')
  const screenshotRef = useRef<HTMLInputElement>(null)

  // Resolve the backend ID, syncing the case on first call if needed.
  const getBackendId = async (): Promise<string> => {
    const backendId = await ensureBackendCase(caseData)
    if (backendId !== caseData.backend_id) {
      updateCaseBackendId(caseData.id, backendId)
    }
    return backendId
  }

  const handleSaveContext = async () => {
    setSavingContext(true)
    setContextSync('syncing')
    const updated = updateCaseFields(caseData.id, { title, victim_context: context })
    if (updated) onChange(updated)
    try {
      const backendId = await getBackendId()
      await updateBackendCase(backendId, { title, victim_context: context })
      setContextSync('synced')
      setTimeout(() => setContextSync('idle'), 2200)
    } catch {
      setContextSync('failed')
    } finally {
      setSavingContext(false)
    }
  }

  const handleAddTextEvidence = async () => {
    if (!evidenceText.trim()) return
    setAddingEvidence(true)
    setAddError(null)
    setEvidenceSync('syncing')
    try {
      const res = await analyzeText(
        evidenceText.trim(),
        evidenceAuthor.trim() || 'unknown',
        evidenceUrl.trim() || ''
      )
      const updated = addEvidenceToCase(caseData.id, res.evidence)
      if (updated) onChange(updated)

      // Push to backend so legal AI + Strafanzeige see it.
      const backendId = await getBackendId()
      await addEvidenceToBackendCase(backendId, {
        content_text: res.evidence.content_text,
        url: evidenceUrl.trim() || undefined,
        platform: res.evidence.platform,
        author_username: evidenceAuthor.trim() || 'unknown',
      })
      setEvidenceSync('synced')
      setTimeout(() => setEvidenceSync('idle'), 2200)

      setEvidenceText('')
      setEvidenceAuthor('')
      setEvidenceUrl('')
    } catch (err) {
      setEvidenceSync('failed')
      setAddError(err instanceof Error ? err.message : (isDE ? 'Konnte nicht klassifizieren.' : 'Could not classify.'))
    } finally {
      setAddingEvidence(false)
    }
  }

  const handleAddScreenshot = async (file: File) => {
    setAddingEvidence(true)
    setAddError(null)
    setEvidenceSync('syncing')
    try {
      const res = await uploadScreenshot(file)
      const updated = addEvidenceToCase(caseData.id, res.evidence)
      if (updated) onChange(updated)

      const backendId = await getBackendId()
      await addEvidenceToBackendCase(backendId, {
        content_text: res.evidence.content_text,
        platform: res.evidence.platform,
        screenshot_base64: res.evidence.screenshot_base64,
      })
      setEvidenceSync('synced')
      setTimeout(() => setEvidenceSync('idle'), 2200)
    } catch (err) {
      setEvidenceSync('failed')
      setAddError(err instanceof Error ? err.message : (isDE ? 'Upload fehlgeschlagen.' : 'Upload failed.'))
    } finally {
      setAddingEvidence(false)
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="w-full text-slate-300 hover:text-white text-sm font-medium bg-slate-800/40 hover:bg-slate-800 rounded-xl py-3 transition-colors"
      >
        {isDE ? 'Fall bearbeiten — Beweis hinzufügen, Kontext anpassen' : 'Edit case — add evidence, adjust context'}
      </button>
    )
  }

  const tabBtn = (key: Tab, label: string) => (
    <button
      onClick={() => setTab(key)}
      className={`px-3 py-2 text-xs font-semibold uppercase tracking-wider transition-colors ${
        tab === key ? 'text-white border-b-2 border-indigo-500' : 'text-slate-500 hover:text-slate-300'
      }`}
    >
      {label}
    </button>
  )

  const SyncPill = ({ state }: { state: SyncState }) => {
    if (state === 'idle') return null
    if (state === 'syncing') {
      return (
        <span className="text-slate-400 text-xs">
          {isDE ? 'Wird mit Backend abgeglichen…' : 'Syncing to backend…'}
        </span>
      )
    }
    if (state === 'synced') {
      return (
        <span className="text-emerald-300 text-xs flex items-center gap-1">
          <span className="text-emerald-400">✓</span>
          {isDE ? 'Übernommen — Legal AI & Strafanzeige sehen die Änderung.' : 'Synced — legal AI & criminal complaint see the change.'}
        </span>
      )
    }
    return (
      <span className="text-amber-300 text-xs">
        {isDE ? 'Lokal gespeichert, Backend-Sync fehlgeschlagen.' : 'Saved locally, backend sync failed.'}
      </span>
    )
  }

  return (
    <div className="bg-slate-800/60 rounded-xl overflow-hidden">
      <div className="flex items-center justify-between px-4 pt-2 border-b border-slate-700/60">
        <div className="flex">
          {tabBtn('evidence', isDE ? 'Beweis hinzufügen' : 'Add evidence')}
          {tabBtn('context', isDE ? 'Falldetails' : 'Case details')}
        </div>
        <button
          onClick={() => setOpen(false)}
          className="text-slate-500 hover:text-slate-200 text-lg leading-none"
        >
          ×
        </button>
      </div>

      <div className="p-4">
        {tab === 'evidence' && (
          <div className="space-y-4">
            <div>
              <label className="block text-slate-300 text-xs font-medium mb-1">
                {isDE ? 'Text (z.B. weitere Nachricht)' : 'Text (e.g. another message)'}
              </label>
              <textarea
                value={evidenceText}
                onChange={e => setEvidenceText(e.target.value)}
                placeholder={isDE ? 'Den nächsten Vorfall hier einfügen…' : 'Paste the next incident here…'}
                rows={3}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 placeholder-slate-500 text-sm focus:outline-none focus:border-indigo-500 resize-none"
              />
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-2">
                <input
                  value={evidenceAuthor}
                  onChange={e => setEvidenceAuthor(e.target.value)}
                  placeholder={isDE ? 'Verfasser:in (z.B. @hassuser123)' : 'Author (e.g. @hateuser123)'}
                  className="bg-slate-900 border border-slate-700 rounded px-3 py-2 text-slate-200 placeholder-slate-500 text-sm"
                />
                <input
                  value={evidenceUrl}
                  onChange={e => setEvidenceUrl(e.target.value)}
                  placeholder={isDE ? 'Quelle (URL, optional)' : 'Source URL (optional)'}
                  className="bg-slate-900 border border-slate-700 rounded px-3 py-2 text-slate-200 placeholder-slate-500 text-sm"
                />
              </div>
              <div className="mt-3 flex items-center gap-3 flex-wrap">
                <button
                  onClick={handleAddTextEvidence}
                  disabled={addingEvidence || !evidenceText.trim()}
                  className="bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 disabled:text-slate-500 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
                >
                  {addingEvidence
                    ? (isDE ? 'Wird klassifiziert…' : 'Classifying…')
                    : (isDE ? 'Beweis hinzufügen' : 'Add evidence')}
                </button>
                <SyncPill state={evidenceSync} />
              </div>
            </div>

            <div className="border-t border-slate-700/60 pt-4">
              <label className="block text-slate-300 text-xs font-medium mb-1">
                {isDE ? 'Screenshot (WhatsApp, DM, …)' : 'Screenshot (WhatsApp, DM, …)'}
              </label>
              <input
                ref={screenshotRef}
                type="file"
                accept="image/*"
                onChange={e => {
                  const f = e.target.files?.[0]
                  if (f) handleAddScreenshot(f)
                  e.target.value = ''
                }}
                disabled={addingEvidence}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-sm file:mr-3 file:py-1 file:px-3 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-indigo-900 file:text-indigo-300 hover:file:bg-indigo-800"
              />
              <p className="text-slate-500 text-xs mt-1">
                {isDE
                  ? 'Wird per OCR (Tesseract → OpenAI Vision) ausgelesen und klassifiziert.'
                  : 'Read by OCR (Tesseract → OpenAI Vision) and classified.'}
              </p>
            </div>

            {addError && (
              <p className="text-amber-300 text-xs">{addError}</p>
            )}
          </div>
        )}

        {tab === 'context' && (
          <div className="space-y-3">
            <p className="text-slate-400 text-xs leading-relaxed bg-slate-900/40 border border-slate-700/50 rounded px-3 py-2">
              {isDE
                ? 'Diese Angaben gelten für den ganzen Fall — nicht pro Beweis. Titel und Kontext helfen der juristischen Gesamteinschätzung und der Strafanzeige, den Hintergrund einzuordnen.'
                : 'These fields apply to the whole case — not per piece of evidence. Title and context help the legal assessment and the criminal complaint understand the bigger picture.'}
            </p>
            <div>
              <label className="block text-slate-300 text-xs font-medium mb-1">
                {isDE ? 'Titel des Falls' : 'Case title'}
              </label>
              <input
                value={title}
                onChange={e => setTitle(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-slate-200 text-sm"
              />
              <p className="text-slate-500 text-xs mt-1">
                {isDE
                  ? 'Erscheint in der Fall-Liste und im Bericht. Z.B. „Stalking durch Ex-Partner" oder „Hass-Kampagne nach Tweet".'
                  : 'Shown in the case list and in reports. E.g. "Stalking by ex-partner" or "Hate campaign after tweet".'}
              </p>
            </div>
            <div>
              <label className="block text-slate-300 text-xs font-medium mb-1">
                {isDE ? 'Kontext zum Fall (optional)' : 'Case context (optional)'}
              </label>
              <textarea
                value={context}
                onChange={e => setContext(e.target.value)}
                placeholder={isDE
                  ? 'z.B. „Der Account belästigt mich seit 3 Wochen, nachdem ich einen Post über XY geteilt habe."'
                  : 'e.g. "This account has been harassing me for 3 weeks after I posted about XY."'}
                rows={4}
                className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-slate-200 placeholder-slate-500 text-sm resize-none"
              />
            </div>
            <div className="flex items-center gap-3 flex-wrap">
              <button
                onClick={handleSaveContext}
                disabled={savingContext}
                className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-60 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
              >
                {isDE ? 'Speichern' : 'Save'}
              </button>
              <SyncPill state={contextSync} />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
