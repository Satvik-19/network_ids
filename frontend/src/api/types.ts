/** Typed API contracts matching the FastAPI response models (backend/app/schemas). */

export type ReplayState = "IDLE" | "RUNNING" | "PAUSED" | "COMPLETED" | "STOPPED";
export type Classification = "BENIGN" | "KNOWN_ATTACK" | "UNKNOWN_SUSPICIOUS";
export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface ScenarioInfo {
  name: string;
  description: string;
  flows: number;
}

export interface ReplayStatus {
  state: ReplayState;
  scenario: string | null;
  speed: number;
  speeds: number[];
  pace_seconds: number;
  processed: number;
  total: number;
  suspicious: number;
  known_attacks: number;
  unknown_suspicious: number;
  incidents: number;
  errors: number;
  error: string | null;
  progress: number;
  current_sequence: number | null;
  current_replay_time: string | null;
  max_risk_score: number;
  max_risk_level: RiskLevel;
  started_at: string | null;
  run_id: string | null;
}

export interface ReplayFlow {
  id: number;
  flow_id: string | null;
  scenario: string | null;
  seq: number | null;
  source: string | null;
  destination: string | null;
  service_port: number | null;
  label: string | null;
  family: string | null;
  classification: Classification | null;
  confidence: number | null;
  anomaly_score: number | null;
  risk_level: RiskLevel | null;
  risk_score: number | null;
  replay_time: string | null;
}

export interface ReplayFlowsOut {
  total: number;
  flows: ReplayFlow[];
}

export interface IncidentSummary {
  id: number;
  label: string | null;
  family: string | null;
  classification: Classification | null;
  severity: RiskLevel | null;
  risk_level: RiskLevel | null;
  risk_score: number | null;
  source: string | null;
  destination: string | null;
  service_port: number | null;
  flow_count: number;
  started_at: string | null;
  last_activity_at: string | null;
  ended_at: string | null;
}

export interface IncidentList {
  total: number;
  incidents: IncidentSummary[];
}

export interface TopFeature {
  feature: string;
  shap_value: number;
  direction: string;
}

export interface IncidentFlowOut {
  id: number;
  flow_id: string | null;
  prediction_id: number | null;
  label: string | null;
  confidence: number | null;
  classification: Classification | null;
  family: string | null;
  risk_level: RiskLevel | null;
  risk_score: number | null;
  source: string | null;
  destination: string | null;
  service_port: number | null;
  replay_time: string | null;
  anomaly_score: number | null;
  top_features: TopFeature[];
  baseline_features: Record<string, number>;
}

export interface IncidentDetail extends IncidentSummary {
  flows: IncidentFlowOut[];
  confidence: number | null;
  anomaly_score: number | null;
}

export interface BenignBaselineStats {
  median: number;
  mean: number;
  p25: number;
  p75: number;
  std: number;
  n: number;
}

export interface BenignBaselinesOut {
  version: string;
  source: string;
  n_benign_flows: number;
  feature_count: number;
  features: string[];
  baselines: Record<string, BenignBaselineStats>;
  unit_note: string;
}
