import type { Case, ClassificationResult, EvidenceItem } from '../types'

const BASE = '/api'

export async function fetchCases(): Promise<Case[]> {
  const res = await fetch(`${BASE}/cases/`)
  if (!res.ok) throw new Error('Failed to fetch cases')
  return res.json()
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

export async function fetchReport(
  caseId: string,
  reportType: 'general' | 'netzdg' | 'police',
  lang: 'de' | 'en'
): Promise<Record<string, unknown>> {
  const res = await fetch(`${BASE}/reports/${caseId}?report_type=${reportType}&lang=${lang}`)
  if (!res.ok) throw new Error('Failed to generate report')
  return res.json()
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
