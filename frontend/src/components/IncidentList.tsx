import type { IncidentSummary } from "../api/types";
import { ClassificationBadge, RiskBadge, SeverityBar, formatReplayTime } from "./ui";

export function IncidentList({
  incidents,
  onOpen,
}: {
  incidents: IncidentSummary[];
  onOpen: (id: number) => void;
}) {
  return (
    <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900">
      <div className="border-b border-slate-800 px-4 py-3">
        <h2 className="text-sm font-semibold text-slate-200">
          Incidents ({incidents.length})
        </h2>
      </div>
      {incidents.length === 0 ? (
        <div className="px-4 py-8 text-center text-sm text-slate-500">
          No incidents detected
        </div>
      ) : (
        <div className="divide-y divide-slate-800">
          {incidents.map((inc) => (
            <button
              key={inc.id}
              onClick={() => onOpen(inc.id)}
              className="flex w-full items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-slate-800/50"
            >
              <SeverityBar level={inc.risk_level} />
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-semibold text-slate-100">
                    {formatFamily(inc.family, inc.classification)}
                  </span>
                  <RiskBadge level={inc.risk_level} />
                </div>
                <div className="mt-0.5 flex items-center gap-3 text-xs text-slate-400">
                  <span className="font-mono">
                    {inc.source ?? "?"} → {inc.destination ?? "?"}
                    {inc.service_port != null ? `:${inc.service_port}` : ""}
                  </span>
                  <span>{inc.flow_count} related flows</span>
                </div>
                <div className="mt-0.5 flex items-center gap-3 text-xs text-slate-500">
                  <span>
                    {formatReplayTime(inc.started_at)} – {formatReplayTime(inc.ended_at)}
                  </span>
                  <ClassificationBadge value={inc.classification} />
                </div>
              </div>
              <div className="text-right text-xs text-slate-500">
                {inc.risk_score != null ? inc.risk_score.toFixed(1) : ""}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function formatFamily(
  family: string | null,
  classification: string | null,
): string {
  if (family && family !== "BENIGN") {
    return family.replace(/_/g, " ");
  }
  if (classification === "UNKNOWN_SUSPICIOUS") return "Anomalous Behavior";
  return "Security Event";
}
