export interface User {
  id: string
  email: string
  username: string
  full_name: string
  role: 'admin' | 'manager' | 'engineer' | 'executive' | 'viewer'
  department?: string
  title?: string
  avatar_url?: string
  is_active: boolean
  created_at: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: User
}

export interface Project {
  id: string
  name: string
  key: string
  description?: string
  status: 'active' | 'on_hold' | 'completed' | 'at_risk' | 'cancelled'
  health_score?: 'green' | 'yellow' | 'red'
  health_score_value?: number
  confidence_score?: number
  team_size: number
  start_date?: string
  target_end_date?: string
  jira_project_key?: string
  github_repo?: string
  budget?: number
  budget_spent?: number
  created_at: string
  updated_at: string
}

export interface Sprint {
  id: string
  project_id: string
  name: string
  sprint_number: number
  status: 'active' | 'completed' | 'planned'
  start_date?: string
  end_date?: string
  planned_points: number
  completed_points: number
  carryover_points: number
  velocity?: number
  completion_rate?: number
  success_likelihood?: number
  blocker_count: number
  tickets_total: number
  tickets_done: number
  ai_summary?: string
  created_at: string
}

export interface Risk {
  id: string
  project_id: string
  title: string
  description: string
  category: string
  severity: 'low' | 'medium' | 'high' | 'critical'
  probability: number
  impact: number
  risk_score: number
  status: 'open' | 'mitigated' | 'closed'
  mitigation?: string
  owner?: string
  due_date?: string
  is_ai_generated: boolean
  ai_confidence?: number
  ai_reasoning?: string
  created_at: string
}

export interface Report {
  id: string
  project_id?: string
  title: string
  report_type: string
  audience: string
  period_start?: string
  period_end?: string
  content: string
  summary?: string
  key_metrics?: Record<string, unknown>
  risks_identified?: Risk[]
  action_items?: ActionItem[]
  decisions_required?: Decision[]
  status: string
  is_approved: boolean
  generated_by_agent: string
  model_used?: string
  token_cost?: number
  created_at: string
}

export interface ActionItem {
  title: string
  description: string
  owner_role: string
  priority: 'critical' | 'high' | 'medium' | 'low'
  category: string
  estimated_hours: number
  due_date: string
  reasoning?: string
}

export interface Decision {
  decision: string
  context: string
  urgency: string
}

export interface KnowledgeQueryResult {
  query_id: string
  query: string
  answer: string
  citations: Citation[]
  confidence: number
  response_time_ms: number
  token_count: number
}

export interface Citation {
  source_id: string
  source_type: string
  title: string
  url?: string
  relevance_score: number
  excerpt: string
  author?: string
}

export interface PortfolioSummary {
  total_projects: number
  active_projects: number
  at_risk_projects: number
  on_hold_projects: number
  completed_projects: number
  total_open_risks: number
  critical_risks: number
  avg_health_score: number
  overall_confidence: number
  projects: Project[]
}

export interface Integration {
  id: string
  name: string
  integration_type: string
  is_enabled: boolean
  last_sync_at?: string
  last_sync_status?: string
  last_error?: string
  sync_count: number
  created_at: string
}

export interface AIApproval {
  id: string
  agent_name: string
  action_type: string
  description: string
  proposed_data?: Record<string, unknown>
  ai_reasoning?: string
  confidence_score?: number
  status: 'pending' | 'approved' | 'rejected' | 'expired'
  expires_at?: string
  created_at: string
}
