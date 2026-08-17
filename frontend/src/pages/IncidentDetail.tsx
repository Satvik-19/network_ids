import { useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import type { BenignBaselinesOut, IncidentDetail as IncidentDetailType } from "../api/types";
import { CommGraph } from "../components/CommGraph";
import {
  ClassificationBadge,
  RiskBadge,
  formatPercent,
  formatReplayTime,
  formatScore,
  isAnomalyFlagged,
} from "../components/ui";
import { fromIncidentFlows } from "../lib/graph";

interface Props {
  incidentId: number;
  onBack: () => void;
}

export function IncidentDetail({ incidentId, onBack }: Props) {
  const [detail, setDetail] = useState<IncidentDetailType | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api
      .incidentDetail(incidentId)
      .then((d) => {
        setDetail(d);
        setError(null);
      })
      .catch((e) => setError(e instanceof Error ? e.message : String(e)))
      .finally(() => setLoading(false));
  }, [incidentId]);

  return (
    <div className="space-y-4">
      <button onClick={onBack} className="text-sm text-slate-400 hover:text-white transition-colors">
        ← Back to incidents
      </button>

      {loading && !detail && <div className="text-sm text-slate-500">Loading incident…</div>}

      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2 text-sm text-red-400">
          {error} {error.includes("404") && "— incident not found."}
        </div>
      )}

      {!loading && !error && !detail && (
        <div className="rounded-xl border border-slate-800 bg-slate-900 px-4 py-8 text-center text-sm text-slate-500">
          Incident not found.
        </div>
      )}

      {detail && (
        <>
          <HeroBlock detail={detail} />
          <IncidentGraphBlock detail={detail} />
          <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
            <ShapBlock detail={detail} />
            <BaselineBlock detail={detail} />
          </div>
          <HybridDecisionBlock detail={detail} />
          <EvidenceBlock detail={detail} />
        </>
      )}
    </div>
  );
}

function HeroBlock({ detail }: { detail: IncidentDetailType }) {
  const isUnknown = detail.classification === "UNKNOWN_SUSPICIOUS";
  const isAttack = detail.classification === "KNOWN_ATTACK";
  const family = detail.family ?? "";
  const title = isUnknown && (family === "BENIGN" || !family)
    ? "Unrecognized Suspicious Behavior"
    : family.replace(/_/g, " ") || "Security Event";

  return (
    <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900">
      <div className="flex flex-wrap items-center gap-4 px-6 py-5">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-xl font-bold tracking-tight text-white">{title}</h1>
            <RiskBadge level={detail.risk_level} />
          </div>
          <div className="mt-1 font-mono text-sm text-slate-400">
            {detail.source ?? "?"} → {detail.destination ?? "?"}
            {detail.service_port != null ? `:${detail.service_port}` : ""}
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-slate-400">
            <span>{detail.flow_count} related suspicious flows</span>
            <span>
              {formatReplayTime(detail.started_at)} – {formatReplayTime(detail.ended_at)}
            </span>
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-500">
            <ClassificationBadge value={detail.classification} />
            {detail.label && <span>· {detail.label}</span>}
            {detail.risk_score != null && <span>· risk score {detail.risk_score.toFixed(1)}</span>}
          </div>
        </div>
      </div>
      {isUnknown && (
        <div className="border-t border-slate-800 px-6 py-3 text-sm text-violet-300">
          The supervised classifier predicted benign traffic, but the anomaly detector found this
          flow outside the learned normal pattern. The hybrid IDS escalated it as suspicious.
        </div>
      )}
      {isAttack && (
        <div className="border-t border-slate-800 px-6 py-3 text-sm text-red-300">
          The supervised model recognised this traffic as a known attack with high confidence.
          Risk reflects the estimated severity of the behaviour.
        </div>
      )}
    </div>
  );
}

function IncidentGraphBlock({ detail }: { detail: IncidentDetailType }) {
  const graph = useMemo(() => fromIncidentFlows(detail.flows), [detail.flows]);
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
      <h2 className="text-sm font-semibold text-slate-200">Observed Communications</h2>
      <p className="text-xs text-slate-500">
        Evidence flows for this incident (observed communication, not reconstructed topology)
      </p>
      <div className="mt-2">
        <CommGraph data={graph} height={280} />
      </div>
    </div>
  );
}

function ShapBlock({ detail }: { detail: IncidentDetailType }) {
  const dominant = useMemo(() => {
    if (!detail.flows.length) return null;
    return [...detail.flows].sort((a, b) => (b.risk_score ?? 0) - (a.risk_score ?? 0))[0];
  }, [detail.flows]);
  const features = dominant?.top_features ?? [];

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
      <h2 className="text-sm font-semibold text-slate-200">What Influenced the Model Prediction?</h2>
      <p className="text-xs text-slate-500">
        Feature contributions of the supervised model for the dominant flow
        {dominant ? ` (${dominant.label ?? dominant.family ?? "flow"} #${parseSeq(dominant.flow_id)})` : ""}.
        These are model contributions — not causal explanations.
      </p>
      {features.length === 0 ? (
        <div className="mt-3 text-sm text-slate-500">No feature contributions persisted for this flow.</div>
      ) : (
        <div className="mt-3 space-y-2">
          {features.map((tf) => {
            const magnitude = Math.abs(tf.shap_value);
            const positive = tf.shap_value > 0 || tf.direction === "pushes_towards";
            return (
              <div key={tf.feature} className="flex items-center gap-2">
                <span className="w-44 truncate text-xs text-slate-400" title={tf.feature}>
                  {formatFeatureName(tf.feature)}
                </span>
                <div className="h-3 flex-1 overflow-hidden rounded bg-slate-800">
                  <div
                    className={`h-3 ${positive ? "bg-orange-500" : "bg-blue-500"}`}
                    style={{ width: `${Math.min(100, magnitude * 40)}%` }}
                  />
                </div>
                <span className="w-20 text-right font-mono text-xs text-slate-400">
                  {positive ? "+" : ""}
                  {tf.shap_value.toFixed(3)}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function BaselineBlock({ detail }: { detail: IncidentDetailType }) {
  const [baselines, setBaselines] = useState<BenignBaselinesOut | null>(null);
  useEffect(() => {
    api.baselines().then(setBaselines).catch(() => setBaselines(null));
  }, []);

  const dominant = useMemo(() => {
    if (!detail.flows.length) return null;
    return [...detail.flows].sort((a, b) => (b.risk_score ?? 0) - (a.risk_score ?? 0))[0];
  }, [detail.flows]);

  if (!baselines || !dominant || !Object.keys(dominant.baseline_features).length) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
        <h2 className="text-sm font-semibold text-slate-200">Behaviour vs Normal Baseline</h2>
        <p className="mt-1 text-xs text-slate-500">
          Baseline comparison data unavailable for this incident.
        </p>
      </div>
    );
  }

  const featureNames = Object.keys(dominant.baseline_features).slice(0, 4);
  const rows = featureNames
    .map((name) => {
      const current = dominant.baseline_features[name];
      const base = baselines.baselines[name];
      if (base === undefined) return null;
      const median = base.median ?? 0;
      const ratio = median > 0 ? current / median : 0;
      // Within/outside judgement uses the benign p25–p75 band, not a guess.
      const within = current >= base.p25 && current <= base.p75;
      const below = current < base.p25;
      return { name, current, median, ratio, within, below };
    })
    .filter(Boolean) as {
    name: string;
    current: number;
    median: number;
    ratio: number;
    within: boolean;
    below: boolean;
  }[];

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
      <h2 className="text-sm font-semibold text-slate-200">Behaviour vs Normal Baseline</h2>
      <p className="text-xs text-slate-500">
        Dominant evidence flow compared to typical benign traffic patterns
        {baselines.unit_note ? ` · ${baselines.unit_note}` : ""}
      </p>
      <div className="mt-3 space-y-3">
        {rows.map((r) => (
          <div key={r.name} className="flex items-center gap-4">
            <div className="w-40 shrink-0">
              <div className="text-xs font-medium text-slate-300">{formatFeatureName(r.name)}</div>
            </div>
            <div className="flex-1">
              <div className="flex items-baseline gap-2">
                <span className="font-mono text-sm text-white">{formatNumber(r.current)}</span>
                <span className="text-xs text-slate-500">vs normal</span>
                <span className="font-mono text-xs text-slate-400">{formatNumber(r.median)}</span>
              </div>
              <div
                className={`mt-0.5 text-xs ${
                  r.within
                    ? "text-emerald-400"
                    : r.below
                      ? "font-medium text-blue-400"
                      : "font-medium text-orange-400"
                }`}
              >
                {r.within
                  ? "within normal range"
                  : r.below
                    ? `≈${r.ratio > 0 ? r.ratio.toFixed(1) : "0"}× of normal · below normal range`
                    : `≈${r.ratio.toFixed(1)}× of normal · above normal range`}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function HybridDecisionBlock({ detail }: { detail: IncidentDetailType }) {
  if (detail.classification !== "UNKNOWN_SUSPICIOUS") return null;
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
      <h2 className="text-sm font-semibold text-slate-200">Why Was It Flagged as Suspicious?</h2>
      <p className="mt-1 text-sm leading-relaxed text-slate-400">
        The supervised classifier predicted this traffic was benign (confidence{" "}
        {formatPercent(detail.confidence)}). However, the anomaly detector flagged it as outside
        the learned normal pattern (anomaly score {formatScore(detail.anomaly_score, 4)}). The
        hybrid IDS treats disagreement from the anomaly detector as a signal: the flow is
        escalated to{" "}
        <span className="font-medium text-violet-400">unknown suspicious</span> with elevated risk.
      </p>
    </div>
  );
}

function EvidenceBlock({ detail }: { detail: IncidentDetailType }) {
  const rows = [...detail.flows].sort(
    (a, b) => (a.replay_time ?? "") < (b.replay_time ?? "") ? -1 : 1,
  );

  return (
    <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900">
      <div className="border-b border-slate-800 px-4 py-3">
        <h2 className="text-sm font-semibold text-slate-200">Evidence Flows</h2>
        <p className="text-xs text-slate-500">{rows.length} flows in this incident</p>
      </div>
      <div className="max-h-96 overflow-auto">
        <table className="min-w-full text-left text-sm">
          <thead className="sticky top-0 bg-slate-900 text-xs uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-3 py-2 font-medium">#</th>
              <th className="px-3 py-2 font-medium">Time</th>
              <th className="px-3 py-2 font-medium">Source</th>
              <th className="px-3 py-2 font-medium">Destination</th>
              <th className="px-3 py-2 font-medium">Port</th>
              <th className="px-3 py-2 font-medium">Prediction</th>
              <th className="px-3 py-2 font-medium">Confidence</th>
              <th className="px-3 py-2 font-medium">Anomaly</th>
              <th className="px-3 py-2 font-medium">Risk</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {rows.map((f) => {
              const anomalyFlag = isAnomalyFlagged(f.anomaly_score);
              return (
                <tr key={f.id} className="hover:bg-slate-800/50">
                  <td className="px-3 py-1.5 font-mono text-xs text-slate-400">
                    {parseSeq(f.flow_id)}
                  </td>
                  <td className="px-3 py-1.5 font-mono text-xs text-slate-400">
                    {formatReplayTime(f.replay_time)}
                  </td>
                  <td className="px-3 py-1.5 font-mono text-xs text-slate-300">
                    {f.source ?? "—"}
                  </td>
                  <td className="px-3 py-1.5 font-mono text-xs text-slate-300">
                    {f.destination ?? "—"}
                  </td>
                  <td className="px-3 py-1.5 font-mono text-xs text-slate-400">
                    {f.service_port != null ? `:${f.service_port}` : "—"}
                  </td>
                  <td className="px-3 py-1.5 text-xs text-slate-400">
                    {f.label ?? f.family ?? "—"}
                  </td>
                  <td className="px-3 py-1.5 font-mono text-xs text-slate-300">
                    {formatPercent(f.confidence)}
                  </td>
                  <td className="px-3 py-1.5">
                    <span
                      className={`inline-block rounded px-1.5 py-0.5 text-xs font-medium ${
                        anomalyFlag
                          ? "bg-violet-500/20 text-violet-400"
                          : "bg-emerald-500/20 text-emerald-400"
                      }`}
                    >
                      {anomalyFlag ? "Abnormal" : "Normal"}
                    </span>
                  </td>
                  <td className="px-3 py-1.5">
                    <RiskBadge level={f.risk_level} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function formatFeatureName(name: string): string {
  return name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatNumber(v: number): string {
  if (Math.abs(v) >= 1000) return v.toLocaleString(undefined, { maximumFractionDigits: 0 });
  return v.toFixed(1);
}

function parseSeq(flowId: string | null): number | null {
  if (!flowId) return null;
  const m = flowId.match(/-f(\d+)$/);
  return m ? Number(m[1]) : null;
}