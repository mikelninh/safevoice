export type Severity = 'low' | 'medium' | 'high' | 'critical'

export type Category =
  | 'harassment'
  | 'threat'
  | 'death_threat'
  | 'defamation'
  | 'misogyny'
  | 'body_shaming'
  | 'coordinated_attack'
  | 'false_facts'
  | 'sexual_harassment'
  | 'scam'
  | 'phishing'
  | 'investment_fraud'
  | 'romance_scam'
  | 'impersonation'

export interface GermanLaw {
  paragraph: string
  title: string
  title_de: string
  description: string
  description_de: string
  max_penalty: string
  applies_because: string
  applies_because_de: string
}

export interface ClassificationResult {
  severity: Severity
  categories: Category[]
  confidence: number
  requires_immediate_action: boolean
  summary: string
  summary_de: string
  applicable_laws: GermanLaw[]
  potential_consequences: string
  potential_consequences_de: string
}

export interface EvidenceItem {
  id: string
  url: string
  platform: string
  captured_at: string
  author_username: string
  author_display_name?: string
  content_text: string
  content_type: string
  archived_url?: string
  content_hash: string
  classification?: ClassificationResult
  /** Screenshot as data URL (e.g. "data:image/png;base64,...") — embedded in legal PDFs. */
  screenshot_base64?: string
}

export interface PatternFlag {
  type: string
  description: string
  description_de: string
  evidence_count: number
  severity: Severity
}

export interface Case {
  id: string
  created_at: string
  updated_at: string
  victim_context?: string
  evidence_items: EvidenceItem[]
  pattern_flags: PatternFlag[]
  overall_severity: Severity
  status: string
  title: string
  /** Backend (server-side) case ID, populated after sync. */
  backend_id?: string
}

export interface LegalAction {
  priority: 'immediate' | 'soon' | 'when_ready'
  action_de: string
  action_en: string
  deadline: '24h' | '7d' | 'none'
}

export interface LegalRiskAssessment {
  escalation_risk: 'low' | 'medium' | 'high'
  reason_de: string
  reason_en: string
}

export interface LegalAnalysisPayload {
  legal_assessment_de: string
  legal_assessment_en: string
  strongest_charges: Array<{
    paragraph: string
    strength: 'strong' | 'medium' | 'weak'
    reason_de: string
    reason_en: string
  }>
  recommended_actions: LegalAction[]
  risk_assessment: LegalRiskAssessment
  evidence_gaps: Array<{
    gap_de: string
    gap_en: string
    how_to_fill_de: string
    how_to_fill_en: string
  }>
  cross_references: string
  disclaimer_de: string
  disclaimer_en: string
}

export interface LegalAnalysisResponse {
  case_id: string
  ai_available: boolean
  analysis: LegalAnalysisPayload
}
