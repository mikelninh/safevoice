import type { Case, ClassificationResult, EvidenceItem, LegalAnalysisResponse } from '../types'

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

/**
 * Push a single new evidence item to an existing backend case so the
 * server-side classifier + legal AI see it. Used by the "add evidence"
 * flow on a case that's already been synced once.
 */
export async function addEvidenceToBackendCase(
  backendCaseId: string,
  evidence: {
    content_text: string
    url?: string
    platform?: string
    author_username?: string
    screenshot_base64?: string
  }
): Promise<void> {
  const res = await fetch(`${BASE}/cases/${backendCaseId}/evidence`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      content_type: evidence.screenshot_base64 ? 'screenshot' : 'text',
      text: evidence.content_text,
      source_url: evidence.url || undefined,
      author_username: evidence.author_username ?? 'unknown',
      platform: evidence.platform ?? undefined,
      screenshot_base64: evidence.screenshot_base64,
    }),
  })
  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new Error(`Evidence sync failed (${res.status}): ${body.slice(0, 200)}`)
  }
}

/**
 * PUT updates to a backend case (title, victim_context). Without this the
 * server-side legal AI and Strafanzeige use stale context.
 */
export async function updateBackendCase(
  backendCaseId: string,
  patch: { title?: string; victim_context?: string }
): Promise<void> {
  const res = await fetch(`${BASE}/cases/${backendCaseId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(patch),
  })
  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new Error(`Case update failed (${res.status}): ${body.slice(0, 200)}`)
  }
}

export async function fetchLegalAnalysis(caseId: string): Promise<LegalAnalysisResponse> {
  const res = await fetch(`${BASE}/legal/${caseId}`, { cache: 'no-store' })
  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new Error(`Legal analysis unavailable (${res.status}): ${body.slice(0, 200)}`)
  }
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

export interface VictimInfo {
  name?: string
  address?: string
  phone?: string
  email?: string
  /** Optional postal code — used by SendReport to pre-select Bundesland police. */
  plz?: string
}

function _victimQuery(v?: VictimInfo): string {
  if (!v) return ''
  const params: string[] = []
  if (v.name) params.push(`victim_name=${encodeURIComponent(v.name)}`)
  if (v.address) params.push(`victim_address=${encodeURIComponent(v.address)}`)
  if (v.phone) params.push(`victim_phone=${encodeURIComponent(v.phone)}`)
  if (v.email) params.push(`victim_email=${encodeURIComponent(v.email)}`)
  return params.length ? '&' + params.join('&') : ''
}

export async function fetchReport(
  caseId: string,
  reportType: 'general' | 'netzdg' | 'police',
  lang: 'de' | 'en',
  victim?: VictimInfo
): Promise<Record<string, unknown>> {
  const url = `${BASE}/reports/${caseId}?report_type=${reportType}&lang=${lang}${_victimQuery(victim)}`
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
      content_hash?: string
      url?: string
      platform?: string
      author_username?: string
      screenshot_base64?: string
    }>
  }
): Promise<string> {
  /** Push a single evidence item; logs+swallows errors so partial sync is OK. */
  const pushEvidence = async (
    backendId: string,
    ev: typeof localCase.evidence_items[number],
  ) => {
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
      console.warn('[ensureBackendCase] evidence sync failed:', evRes.status, body.slice(0, 200))
    }
  }

  // Fast path: already synced — reconcile evidence on every call so newly
  // added local pieces always reach the backend before reports are fetched.
  if (localCase.backend_id) {
    const check = await fetch(`${BASE}/cases/${localCase.backend_id}`, { cache: 'no-store' })
    if (check.ok) {
      try {
        const remote = await check.json()
        const remoteHashes = new Set<string>(
          (remote.evidence_items ?? []).map((e: { content_hash?: string }) => e.content_hash)
        )
        const missing = localCase.evidence_items.filter(
          ev => ev.content_hash && !remoteHashes.has(ev.content_hash)
        )
        for (const ev of missing) {
          await pushEvidence(localCase.backend_id, ev)
        }
      } catch (err) {
        console.warn('[ensureBackendCase] reconcile failed:', err)
      }
      return localCase.backend_id
    }
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
    await pushEvidence(backendId, ev)
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
  lang: 'de' | 'en',
  victim?: VictimInfo
): Promise<void> {
  const res = await fetch(
    `${BASE}/reports/${caseId}/pdf?report_type=${reportType}&lang=${lang}${_victimQuery(victim)}`
  )
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
