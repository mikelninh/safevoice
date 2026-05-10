/**
 * Inline edit + add-evidence panel for a case.
 *
 * - Edit title / victim_context inline
 * - Edit author_username on existing evidence items
 * - Add new evidence (text or screenshot) to the case
 *
 * All operations write to localStorage first, then sync to backend via
 * the existing /api/cases/{id}/evidence endpoint when applicable.
 */
import { useRef, useState } from 'react'
import { analyzeText, ensureBackendCase, uploadScreenshot } from '../services/api'
import {
  addEvidenceToCase,
  updateCaseFields,
  updateEvidenceAuthor,
} from '../services/storage'
import type { Case, EvidenceItem } from '../types'
import type { Lang } from '../i18n'

interface Props {
  caseData: Case
  lang: Lang
  onChange: (updated: Case) => void
}

type Tab = 'context' | 'evidence' | 'authors'

export default function CaseEditor({ caseData, lang, onChange }: Props) {
  const [open, setOpen] = useState(false)
  const [tab, setTab] = useState<Tab>('evidence')
  const isDE = lang === 'de'

  // Context editor state
  const [title, setTitle] = useState(caseData.title)
  const [context, setContext] = useState(caseData.victim_context ?? '')
  const [savingContext, setSavingContext] = useState(false)
  const [contextSaved, setContextSaved] = useState(false)

  // Add-evidence state
  const [evidenceText, setEvidenceText] = useState('')
  const [evidenceAuthor, setEvidenceAuthor] = useState('')
  const [evidenceUrl, setEvidenceUrl] = useState('')
  const [addingEvidence, setAddingEvidence] = useState(false)
  const [addError, setAddError] = useState<string | null>(null)
  const screenshotRef = useRef<HTMLInputElement>(null)

  const handleSaveContext = () => {
    setSavingContext(true)
    const updated = updateCaseFields(caseData.id, { title, victim_context: context })
    if (updated) {
      onChange(updated)
      setContextSaved(true)
      setTimeout(() => setContextSaved(false), 1800)
    }
    setSavingContext(false)
  }

  const handleAddTextEvidence = async () => {
    if (!evidenceText.trim()) return
    setAddingEvidence(true)
    setAddError(null)
    try {
      const res = await analyzeText(
        evidenceText.trim(),
        evidenceAuthor.trim() || 'unknown',
        evidenceUrl.trim() || ''
      )
      const updated = addEvidenceToCase(caseData.id, res.evidence)
      if (updated) onChange(updated)
      // Sync to backend in the background — no need to block UI
      ensureBackendCase(updated ?? caseData).catch(() => {})
      setEvidenceText('')
      setEvidenceAuthor('')
      setEvidenceUrl('')
    } catch (err) {
      setAddError(err instanceof Error ? err.message : (isDE ? 'Konnte nicht klassifizieren.' : 'Could not classify.'))
    } finally {
      setAddingEvidence(false)
    }
  }

  const handleAddScreenshot = async (file: File) => {
    setAddingEvidence(true)
    setAddError(null)
    try {
      const res = await uploadScreenshot(file)
      const updated = addEvidenceToCase(caseData.id, res.evidence)
      if (updated) onChange(updated)
      ensureBackendCase(updated ?? caseData).catch(() => {})
    } catch (err) {
      setAddError(err instanceof Error ? err.message : (isDE ? 'Upload fehlgeschlagen.' : 'Upload failed.'))
    } finally {
      setAddingEvidence(false)
    }
  }

  const updateAuthor = (evidenceId: string, value: string) => {
    const updated = updateEvidenceAuthor(caseData.id, evidenceId, value || 'unknown')
    if (updated) onChange(updated)
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="w-full text-slate-300 hover:text-white text-sm font-medium bg-slate-800/40 hover:bg-slate-800 rounded-xl py-3 transition-colors"
      >
        {isDE ? 'Fall bearbeiten — Kontext, Beweise, Verfasser:innen' : 'Edit case — context, evidence, authors'}
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

  return (
    <div className="bg-slate-800/60 rounded-xl overflow-hidden">
      <div className="flex items-center justify-between px-4 pt-2 border-b border-slate-700/60">
        <div className="flex">
          {tabBtn('evidence', isDE ? 'Beweis hinzufügen' : 'Add evidence')}
          {tabBtn('context', isDE ? 'Kontext & Titel' : 'Context & title')}
          {tabBtn('authors', isDE ? 'Verfasser:innen' : 'Authors')}
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
              <button
                onClick={handleAddTextEvidence}
                disabled={addingEvidence || !evidenceText.trim()}
                className="mt-3 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 disabled:text-slate-500 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
              >
                {addingEvidence
                  ? (isDE ? 'Wird klassifiziert…' : 'Classifying…')
                  : (isDE ? 'Beweis hinzufügen' : 'Add evidence')}
              </button>
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
            <div>
              <label className="block text-slate-300 text-xs font-medium mb-1">
                {isDE ? 'Titel' : 'Title'}
              </label>
              <input
                value={title}
                onChange={e => setTitle(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-slate-200 text-sm"
              />
            </div>
            <div>
              <label className="block text-slate-300 text-xs font-medium mb-1">
                {isDE ? 'Was ist passiert? (Kontext)' : 'What happened? (context)'}
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
            <div className="flex items-center gap-3">
              <button
                onClick={handleSaveContext}
                disabled={savingContext}
                className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-60 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
              >
                {isDE ? 'Speichern' : 'Save'}
              </button>
              {contextSaved && (
                <span className="text-emerald-300 text-xs flex items-center gap-1">
                  <span className="text-emerald-400">✓</span>
                  {isDE ? 'Gespeichert' : 'Saved'}
                </span>
              )}
            </div>
          </div>
        )}

        {tab === 'authors' && (
          <div className="space-y-2">
            <p className="text-slate-500 text-xs mb-2">
              {isDE
                ? 'Verfasser:in pro Beweis ändern. Hilft, wenn der ursprüngliche Account anonym war oder du den richtigen Handle nachträglich kennst.'
                : 'Change the author for each piece of evidence. Useful if the account was anonymous or you learned the correct handle later.'}
            </p>
            {caseData.evidence_items.map((ev: EvidenceItem) => (
              <div key={ev.id} className="bg-slate-900/60 rounded-lg p-3">
                <p className="text-slate-400 text-xs line-clamp-2 mb-2">"{ev.content_text.slice(0, 120)}"</p>
                <div className="flex items-center gap-2">
                  <span className="text-slate-500 text-xs">@</span>
                  <input
                    defaultValue={ev.author_username}
                    onBlur={e => updateAuthor(ev.id, e.target.value.replace(/^@/, ''))}
                    placeholder="username"
                    className="flex-1 bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-slate-200 placeholder-slate-500 text-sm"
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
