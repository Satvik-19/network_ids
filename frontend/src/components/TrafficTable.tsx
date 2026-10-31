import type { ReplayFlow } from "../api/types";
import { ClassificationBadge, RiskBadge, EmptyState, formatReplayTime, formatSeq, isAnomalyFlagged } from "./ui";

export function TrafficTable({ flows }: { flows: ReplayFlow[] }) {
  const rows = [...flows].sort((a, b) => (a.seq ?? 0) - (b.seq ?? 0));

  return (
    <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900">
      <div className="border-b border-slate-800 px-4 py-3">
        <h2 className="text-sm font-semibold text-slate-200">Replay Evidence</h2>
        <p className="text-xs text-slate-500">Per-flow telemetry (max 100 rows)</p>
      </div>
      <div className="max-h-96 overflow-auto">
        {rows.length === 0 ? (
          <EmptyState title="No flows replayed yet" description="Start a scenario to see evidence" />
        ) : (
          <table className="min-w-full text-left text-sm">
            <thead className="sticky top-0 bg-slate-900 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-3 py-2 font-medium">#</th>
                <th className="px-3 py-2 font-medium">Time</th>
                <th className="px-3 py-2 font-medium">Source</th>
                <th className="px-3 py-2 font-medium">Destination</th>
                <th className="px-3 py-2 font-medium">Port</th>
                <th className="px-3 py-2 font-medium">Prediction</th>
                <th className="px-3 py-2 font-medium">Decision</th>
                <th className="px-3 py-2 font-medium">Confidence</th>
                <th className="px-3 py-2 font-medium">Anomaly</th>
                <th className="px-3 py-2 font-medium">Risk</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {rows.map((f) => {
                const anomalyFlag = isAnomalyFlagged(f.anomaly_score, f.anomaly_threshold);
                return (
                  <tr key={f.id} className="hover:bg-slate-800/50">
                    <td className="px-3 py-1.5 font-mono text-xs text-slate-400">
                      {formatSeq(f.seq)}
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
                      {f.family ?? "—"}
                    </td>
                    <td className="px-3 py-1.5">
                      <ClassificationBadge value={f.classification} />
                    </td>
                    <td className="px-3 py-1.5 font-mono text-xs text-slate-300">
                      {f.confidence != null ? `${(f.confidence * 100).toFixed(0)}%` : "—"}
                    </td>
                    <td className="px-3 py-1.5">
                      <span
                        className={`inline-block rounded px-1.5 py-0.5 text-xs font-medium ${
                          anomalyFlag == null ? "bg-slate-700 text-slate-300" : anomalyFlag
                            ? "bg-violet-500/20 text-violet-400"
                            : "bg-emerald-500/20 text-emerald-400"
                        }`}
                      >
                        {anomalyFlag == null ? "Threshold unavailable" : anomalyFlag ? "Abnormal" : "Normal"}
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
        )}
      </div>
    </div>
  );
}
