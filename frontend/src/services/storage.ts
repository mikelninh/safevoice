/**
 * Local storage service for cases and evidence.
 * Cases persist across browser refreshes.
 * Uses localStorage with JSON serialization.
 */

import type { Case, EvidenceItem, Severity } from '../types'

const CASES_KEY = 'sv_cases'

function readCases(): Case[] {
  try {
    const raw = localStorage.getItem(CASES_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function writeCases(cases: Case[]): void {
  localStorage.setItem(CASES_KEY, JSON.stringify(cases))
}

/** Get all locally stored cases, sorted by most recent first. */
export function getLocalCases(): Case[] {
  return readCases().sort(
    (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
  )
}

/** Get a single case by ID. */
export function getLocalCase(id: string): Case | null {
  return readCases().find(c => c.id === id) ?? null
}

/** Create a new case with an initial evidence item. */
export function createCase(evidence: EvidenceItem, title?: string): Case {
  const now = new Date().toISOString()
  const newCase: Case = {
    id: `case-local-${Date.now()}`,
    created_at: now,
    updated_at: now,
    title: title ?? generateTitle(evidence),
    evidence_items: [evidence],
    pattern_flags: [],
    overall_severity: evidence.classification?.severity ?? 'low',
    status: 'open',
  }

  const cases = readCases()
  cases.push(newCase)
  writeCases(cases)
  return newCase
}

/** Add evidence to an existing case. */
export function addEvidenceToCase(caseId: string, evidence: EvidenceItem): Case | null {
  const cases = readCases()
  const idx = cases.findIndex(c => c.id === caseId)
  if (idx === -1) return null

  cases[idx].evidence_items.push(evidence)
  cases[idx].updated_at = new Date().toISOString()
  cases[idx].overall_severity = computeSeverity(cases[idx].evidence_items)
  writeCases(cases)
  return cases[idx]
}

/** Delete a case. */
export function deleteCase(caseId: string): boolean {
  const cases = readCases()
  const filtered = cases.filter(c => c.id !== caseId)
  if (filtered.length === cases.length) return false
  writeCases(filtered)
  return true
}

/** Delete an evidence item from a case. */
export function deleteEvidence(caseId: string, evidenceId: string): Case | null {
  const cases = readCases()
  const idx = cases.findIndex(c => c.id === caseId)
  if (idx === -1) return null

  cases[idx].evidence_items = cases[idx].evidence_items.filter(e => e.id !== evidenceId)
  cases[idx].updated_at = new Date().toISOString()
  cases[idx].overall_severity = computeSeverity(cases[idx].evidence_items)
  writeCases(cases)
  return cases[idx]
}

/** Migrate legacy sv_evidence array to case structure. */
export function migrateLegacyEvidence(): void {
  try {
    const raw = localStorage.getItem('sv_evidence')
    if (!raw) return

    const items: EvidenceItem[] = JSON.parse(raw)
    if (!Array.isArray(items) || items.length === 0) return

    // Create a case for each legacy evidence item
    for (const item of items) {
      createCase(item)
    }

    // Clear legacy key
    localStorage.removeItem('sv_evidence')
  } catch {
    // Silently fail — don't break the app for migration issues
  }
}

/**
 * Update the stored case with a server-assigned backend_id so subsequent
 * report / PDF / share requests hit the synced case.
 */
export function setBackendId(localCaseId: string, backendId: string): void {
  const cases = readCases()
  const idx = cases.findIndex(c => c.id === localCaseId)
  if (idx === -1) return
  cases[idx].backend_id = backendId
  writeCases(cases)
}

function computeSeverity(items: EvidenceItem[]): Severity {
  const order: Severity[] = ['low', 'medium', 'high', 'critical']
  let max: Severity = 'low'
  for (const item of items) {
    const s = item.classification?.severity ?? 'low'
    if (order.indexOf(s) > order.indexOf(max)) max = s
  }
  return max
}

function generateTitle(evidence: EvidenceItem): string {
  const cats = evidence.classification?.categories ?? []
  if (cats.includes('death_threat')) return 'Death threat case'
  if (cats.includes('threat')) return 'Threat case'
  if (cats.includes('scam') || cats.includes('investment_fraud')) return 'Scam / fraud case'
  if (cats.includes('sexual_harassment')) return 'Sexual harassment case'
  if (cats.includes('misogyny')) return 'Misogyny case'
  if (cats.includes('harassment')) return 'Harassment case'
  return 'New case'
}
