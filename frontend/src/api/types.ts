/** Typed API contracts matching the FastAPI response models (backend/app/schemas). */

export type ReplayState = "IDLE" | "RUNNING" | "PAUSED" | "COMPLETED" | "STOPPED" | "FAILED";
export interface Health {
  status: string;
  model_loaded: boolean;
  feature_count: number;
  readiness: "ready" | "unavailable";
  message: string | null;
}
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
  anomaly_threshold: number | null;
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
  anomaly_threshold: number | null;
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

export interface EnvironmentProfile {
  environment: "home" | "lab" | "small_organisation" | "web_server";
  scale: "1-10" | "10-50" | "50+";
  exposure: "internal" | "some_public" | "public";
  services: ("web" | "ssh" | "ftp" | "database" | "file_sharing")[];
}

export interface PlaygroundProfile {
  id: number;
  profile: EnvironmentProfile;
  suite: { name: string; reason: string; available: boolean; flow_count: number; purpose: string }[];
  unsupported_services: string[];
  unknown_attack_detection: string;
  notice: string;
}

export interface OutcomeCounts {
  malicious: number; detected: number; missed: number;
  benign: number; false_alerts: number; correct_benign: number;
}

export interface PlaygroundFlow {
  seq: number;
  truth_label: string;
  features: Record<string, number>;
  output: {
    classification: Classification; label: string; family: string; confidence: number;
    anomaly_score: number; anomaly_threshold: number; risk_score: number;
    risk_level: RiskLevel; top_features: TopFeature[];
  };
}

export interface PlaygroundResult {
  run_id: number;
  status: "running" | "completed" | "failed";
  assessment: (OutcomeCounts & {
    status: "complete" | "incomplete" | "not_applicable";
    score: number | null; mean_scenario_recall: number | null; benign_specificity: number | null;
    blind_spots: string[]; strongest: string[];
    weights: { detection_weight: number; false_alert_weight: number };
  }) | null;
  coverage: { selected?: number; executed?: number; unavailable?: string[]; unsupported_services?: string[]; unknown_attack_detection?: string };
  scenarios: { name: string; purpose: string; counts: OutcomeCounts; flows: PlaygroundFlow[]; training_feature_matches: number }[];
  context: { thresholds?: { known_confidence: number; anomaly: number } };
  profile: Partial<EnvironmentProfile>;
  notice: string;
  error: string | null;
}
