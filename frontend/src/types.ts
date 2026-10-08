export type AgentStatus = 'ACTIVE' | 'RESTRICTED' | 'SUSPENDED' | 'DECOMMISSIONED';

export interface HumanOwner {
  owner_id: string;
  name: string;
  email: string;
  department: string;
  manager_role: string;
}

export interface Agent {
  agent_id: string;
  name: string;
  display_name: string;
  model_architecture: string;
  role: string;
  department: string;
  status: AgentStatus;
  trust_score: number;
  human_owner_id?: string;
  client_id: string;
  permitted_actions: string[];
  forbidden_actions: string[];
  hitl_actions: string[];
  created_at: string;
  last_active_at: string;
  provisioned_by: string;
  owner?: HumanOwner;
}

export interface TrustScoreBreakdown {
  base_score: number;
  success_contribution: number;
  success_count: number;
  violation_penalty: number;
  violation_count: number;
  rejection_penalty: number;
  rejection_count: number;
  temporal_decay_adjustment: number;
  total: number;
}

export interface HITLBriefing {
  agent_id: string;
  agent_name: string;
  trust_score?: number;
  action: string;
  tool_name?: string;
  arguments?: Record<string, any>;
  customer_id?: string;
  customer_name?: string;
  customer_tier?: string;
  amount?: number;
  currency?: string;
  policy_triggered: string;
  reason: string;
  reversible: boolean;
  approver_role: string;
  timeout_at?: number;
}

export interface HITLItem {
  hitl_id: string;
  agent_id: string;
  action: string;
  resource_id: string;
  approver_role: string;
  status: string;
  decision?: string;
  rationale?: string;
  briefing: HITLBriefing;
  requested_at: string;
  timeout_at: number;
}

export interface AuditEntry {
  entry_id: string;
  sequence_num: number;
  agent_id: string;
  action: string;
  resource_id: string;
  resource_type: string;
  policy_id?: string;
  decision: string;
  tier: number;
  context_snapshot: Record<string, any>;
  cedar_detail: Record<string, any>;
  entry_hash: string;
  prev_entry_hash: string;
  created_at: string;
}

export interface Violation {
  violation_id: string;
  agent_id: string;
  entry_id?: string;
  violation_type: string;
  severity: number;
  attempted_action: string;
  policy_blocked?: string;
  detected_at: string;
}

export interface Alert {
  id: string;
  level: 'info' | 'warning' | 'critical';
  agent_id?: string;
  agent_name?: string;
  title: string;
  message: string;
  recommendation?: string;
  created_at: string;
}

export interface SentinelEvent {
  type: string;
  payload: Record<string, any>;
  ts: number;
  id: string;
}
