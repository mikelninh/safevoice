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
}
