import type { Case, ClassificationResult, EvidenceItem } from '../types'

const BASE = '/api'

export async function fetchCases(): Promise<Case[]> {
  const res = await fetch(`${BASE}/cases/`)
  if (!res.ok) throw new Error('Failed to fetch cases')
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
  if (!res.ok) throw new Error('Analysis failed')
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
    const err = await res.json().catch(() => ({ detail: 'Scraping failed' }))
    throw new Error(err.detail || 'Scraping failed')
  }
  return res.json()
}

export async function fetchReport(
  caseId: string,
  reportType: 'general' | 'netzdg' | 'police',
  lang: 'de' | 'en'
): Promise<Record<string, unknown>> {
  const res = await fetch(`${BASE}/reports/${caseId}?report_type=${reportType}&lang=${lang}`)
  if (!res.ok) throw new Error('Failed to generate report')
  return res.json()
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
  return new Promise((resolve, reject) => {
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
        const err = JSON.parse(xhr.responseText).detail ?? 'Upload failed'
        reject(new Error(err))
      }
    })

    xhr.addEventListener('error', () => reject(new Error('Upload failed')))
    xhr.addEventListener('abort', () => reject(new Error('Upload cancelled')))

    const formData = new FormData()
    formData.append('file', file)
    xhr.send(formData)
  })
}

export async function downloadPdf(
  caseId: string,
  reportType: 'general' | 'netzdg' | 'police',
  lang: 'de' | 'en'
): Promise<void> {
  const res = await fetch(`${BASE}/reports/${caseId}/pdf?report_type=${reportType}&lang=${lang}`)
  if (!res.ok) throw new Error('Failed to generate PDF')
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `safevoice_${caseId}_${reportType}_${lang}.pdf`
  a.click()
  URL.revokeObjectURL(url)
}
