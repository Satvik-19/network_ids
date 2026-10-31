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
              className="incident-row"
            >
              <SeverityBar level={inc.risk_level} />
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-sm font-semibold text-slate-100">
                    {formatFamily(inc.family, inc.classification)}
                  </span>
                  <RiskBadge level={inc.risk_level} />
                </div>
                <div className="mt-2 text-sm text-slate-400">
                  <span className="font-mono">
                    {inc.source ?? "?"} → {inc.destination ?? "?"}
                  </span>
                </div>
                <div className="mt-2 flex flex-wrap items-center gap-3 text-sm text-slate-500">
                  <span>{inc.flow_count} related flows</span>
                  {inc.service_port != null && <span>Recorded service :{inc.service_port}</span>}
                  <span className="meta">
                    {formatReplayTime(inc.started_at)} – {formatReplayTime(inc.ended_at)}
                  </span>
                  <ClassificationBadge value={inc.classification} />
                </div>
              </div>
              <div className="shrink-0 text-right"><div className="font-mono text-sm">{inc.risk_score?.toFixed(1) ?? "—"}</div><span className="meta">Inspect →</span></div>
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
