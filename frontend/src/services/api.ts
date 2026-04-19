import type { Case, ClassificationResult, EvidenceItem } from '../types'

const BASE = '/api'

export async function fetchCases(): Promise<Case[]> {
  const res = await fetch(`${BASE}/cases/`)
  if (!res.ok) throw new Error(`Fall-Liste nicht erreichbar (${res.status} ${res.statusText})`)
  const data = await res.json()
  // API returns CaseListOut (no evidence_items) — fill defaults for frontend compatibility
  return data.map((c: Record<string, unknown>) => ({
    evidence_items: [],
    pattern_flags: [],
    victim_context: '',
    ...c,
  }))
}

export async function fetchCase(id: string): Promise<Case> {
  const res = await fetch(`${BASE}/cases/${id}`)
  if (!res.ok) throw new Error('Case not found')
  return res.json()
}

export async function analyzeText(
  text: string,
  author_username: string,
  url: string
): Promise<{ evidence: EvidenceItem; classification: ClassificationResult }> {
  const res = await fetch(`${BASE}/analyze/ingest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, author_username, url }),
  })
  if (!res.ok) throw new Error(`Classifier antwortete ${res.status} ${res.statusText}`)
  return res.json()
}

export async function scrapeUrl(url: string): Promise<{
  evidence: EvidenceItem
  comments: EvidenceItem[]
  classification: ClassificationResult
  platform: string
  scraped: {
    author_username: string
    author_display_name: string | null
    posted_at: string | null
    comment_count: number
    media_count: number
  }
}> {
  const res = await fetch(`${BASE}/analyze/url`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: `Scraper antwortete ${res.status} (URL möglicherweise privat, gelöscht oder rate-limited)` }))
    throw new Error(err.detail || `Scraper antwortete ${res.status}`)
  }
  return res.json()
}

export async function fetchReport(
  caseId: string,
  reportType: 'general' | 'netzdg' | 'police',
  lang: 'de' | 'en'
): Promise<Record<string, unknown>> {
  const url = `${BASE}/reports/${caseId}?report_type=${reportType}&lang=${lang}`
  const res = await fetch(url, { cache: 'no-store' })
  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new Error(`${res.status} ${res.statusText} — ${body.slice(0, 300) || 'no body'}`)
  }
  return res.json()
}

/**
 * Ensure a case exists on the backend. If the caseId is a local-only ID
 * (e.g. "case-local-1234"), push the case + all its evidence to the backend
 * and return the backend's server-generated ID. If the case already has a
 * `backend_id`, that's returned immediately.
 *
 * This bridges the frontend's localStorage-first model with the backend's
 * DB-backed report/PDF/org features.
 */
export async function ensureBackendCase(
  localCase: {
    id: string
    backend_id?: string
    title: string
    victim_context?: string
    evidence_items: Array<{
      content_text: string
      url?: string
      platform?: string
      author_username?: string
      screenshot_base64?: string
    }>
  }
): Promise<string> {
  // Fast path: already synced
  if (localCase.backend_id) {
    // Verify it still exists server-side
    const check = await fetch(`${BASE}/cases/${localCase.backend_id}`, { cache: 'no-store' })
    if (check.ok) return localCase.backend_id
    // Fall through to re-create if server-side case was deleted
  }

  // Create case on backend
  const createRes = await fetch(`${BASE}/cases/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      title: localCase.title,
      victim_context: localCase.victim_context,
    }),
  })
  if (!createRes.ok) {
    const body = await createRes.text().catch(() => '')
    throw new Error(`Case-Sync: POST /cases failed (${createRes.status}): ${body.slice(0, 200)}`)
  }
  const created = await createRes.json()
  const backendId: string = created.id

  // Push each evidence item (re-classify server-side for fresh hash chain)
  for (const ev of localCase.evidence_items) {
    const evRes = await fetch(`${BASE}/cases/${backendId}/evidence`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        content_type: ev.screenshot_base64 ? 'screenshot' : 'text',
        text: ev.content_text,
        source_url: ev.url || undefined,
        author_username: ev.author_username ?? 'unknown',
        platform: ev.platform ?? undefined,
        screenshot_base64: ev.screenshot_base64,
      }),
    })
    if (!evRes.ok) {
      const body = await evRes.text().catch(() => '')
      // Continue — partial sync is better than no sync.
      console.warn('[ensureBackendCase] evidence sync failed:', evRes.status, body.slice(0, 200))
    }
  }

  return backendId
}

/** Unregister any Service Worker + clear Cache API — use when users hit stale cache. */
export async function resetServiceWorkerAndCaches(): Promise<void> {
  try {
    if ('serviceWorker' in navigator) {
      const regs = await navigator.serviceWorker.getRegistrations()
      await Promise.all(regs.map(r => r.unregister()))
    }
    if ('caches' in window) {
      const names = await caches.keys()
      await Promise.all(names.map(n => caches.delete(n)))
    }
  } catch (e) {
    console.error('[SW reset] failed:', e)
  }
}

/**
 * Read a File as a data URL ("data:image/png;base64,...") — resolves entirely
 * client-side so we keep the bytes available for later PDF embedding without
 * a second round-trip.
 */
function fileToDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = () => reject(new Error('Could not read file'))
    reader.readAsDataURL(file)
  })
}

export async function uploadScreenshot(
  file: File,
  onProgress?: (pct: number) => void
): Promise<{
  evidence: EvidenceItem
  classification: ClassificationResult
  ocr_metadata: {
    text_extracted: boolean
    is_whatsapp: boolean
    timestamps_found: string[]
    has_read_receipts: boolean
    whatsapp_indicators: string[]
  }
}> {
  // Capture the base64 bytes client-side in parallel with the upload so we can
  // attach them to the evidence record for PDF embedding later. No second
  // round-trip needed — the bytes never leave the browser unencrypted.
  const dataUrlPromise = fileToDataUrl(file)

  const response = await new Promise<{
    evidence: EvidenceItem
    classification: ClassificationResult
    ocr_metadata: {
      text_extracted: boolean
      is_whatsapp: boolean
      timestamps_found: string[]
      has_read_receipts: boolean
      whatsapp_indicators: string[]
    }
  }>((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('POST', `${BASE}/upload/screenshot`)

    xhr.upload.addEventListener('progress', (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress(Math.round((e.loaded / e.total) * 100))
      }
    })

    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText))
      } else {
        const err = JSON.parse(xhr.responseText).detail ?? `Upload-Server antwortete ${xhr.status}`
        reject(new Error(err))
      }
    })

    xhr.addEventListener('error', () => reject(new Error('Upload-Server nicht erreichbar (Netzwerkfehler)')))
    xhr.addEventListener('abort', () => reject(new Error('Upload vom Browser abgebrochen')))

    const formData = new FormData()
    formData.append('file', file)
    xhr.send(formData)
  })

  // Attach the data URL so downstream code (localStorage persistence,
  // ensureBackendCase sync, PDF embedding) can carry the screenshot bytes.
  const screenshotDataUrl = await dataUrlPromise
  response.evidence.screenshot_base64 = screenshotDataUrl

  return response
}

export async function downloadPdf(
  caseId: string,
  reportType: 'general' | 'netzdg' | 'police',
  lang: 'de' | 'en'
): Promise<void> {
  const res = await fetch(`${BASE}/reports/${caseId}/pdf?report_type=${reportType}&lang=${lang}`)
  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new Error(`PDF generation failed (${res.status}): ${body.slice(0, 200)}`)
  }
  const blob = await res.blob()
  triggerDownload(blob, `safevoice_${caseId}_${reportType}_${lang}.pdf`)
}

/** Download the NGO-grade legal PDF (org letterhead + chain-of-custody appendix). */
export async function downloadLegalPdf(caseId: string): Promise<void> {
  const res = await fetch(`${BASE}/reports/${caseId}/legal-pdf`)
  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new Error(`Legal PDF generation failed (${res.status}): ${body.slice(0, 200)}`)
  }
  const blob = await res.blob()
  triggerDownload(blob, `safevoice_legal_${caseId}.pdf`)
}

export interface EmlVictimData {
  recipient_email: string
  victim_name?: string
  victim_email?: string
  victim_address?: string
  victim_phone?: string
  /** Which template to use — controls "Strafanzeige" (police) vs "NetzDG-Meldung" (platform). */
  report_type?: 'general' | 'netzdg' | 'police'
  subject?: string
  body?: string
}

/**
 * Build a downloadable .eml file for this case. Double-clicking the file
 * opens Apple Mail / Outlook / Thunderbird with recipient, subject, body,
 * and attachments (PDF + hash-chain CSV) all pre-filled — user just hits
 * Send. More complete than mailto:, lighter than server-side SMTP.
 */
export async function downloadEml(caseId: string, data: EmlVictimData): Promise<void> {
  const res = await fetch(`${BASE}/reports/${caseId}/eml`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
    cache: 'no-store',
  })
  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new Error(`${res.status} ${res.statusText} — ${body.slice(0, 300) || 'no body'}`)
  }
  const blob = await res.blob()
  triggerDownload(blob, `safevoice-strafanzeige-${caseId.slice(0, 8)}.eml`)
}

/**
 * Trigger a file download from a Blob in a way that works across browsers.
 *
 * The previous implementation clicked an unattached <a> element, which works
 * in Chrome/Firefox but silently fails in Safari + mobile browsers — the
 * anchor must be in the DOM for .click() to dispatch a download.
 */
function triggerDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.rel = 'noopener'
  a.style.display = 'none'
  document.body.appendChild(a)
  a.click()
  // defer cleanup so Safari actually processes the click
  setTimeout(() => {
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }, 100)
}
