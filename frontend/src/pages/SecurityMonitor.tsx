import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import { usePolling } from "../api/usePolling";
import type { GraphData } from "../components/CommGraph";
import { CommGraph } from "../components/CommGraph";
import { IncidentList } from "../components/IncidentList";
import { ReplayControls } from "../components/ReplayControls";
import { RiskDistribution } from "../components/RiskDistribution";
import { SecurityStatus } from "../components/SecurityStatus";
import { SummaryCards } from "../components/SummaryCards";
import { AttackTimeline } from "../components/AttackTimeline";
import { TrafficTable } from "../components/TrafficTable";
import type { IncidentSummary, ReplayFlow, ReplayStatus } from "../api/types";
import { fromReplayFlows } from "../lib/graph";

const POLL_MS = 1500;

export function SecurityMonitor({ onOpenIncident }: { onOpenIncident: (id: number) => void }) {
  const [status, setStatus] = useState<ReplayStatus | null>(null);
  const [flows, setFlows] = useState<ReplayFlow[]>([]);
  const [incidents, setIncidents] = useState<IncidentSummary[]>([]);
  const [speed, setSpeed] = useState(5);
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] });
  const [selection, setSelection] = useState<string | null>(null);
  const [monitorError, setMonitorError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const st = await api.replayStatus();
      setStatus(st);
      const runId = st.run_id ?? undefined;
      const [fl, inc] = await Promise.all([
        api.recentFlows(100, runId),
        api.incidents(runId),
      ]);
      setFlows(fl.flows);
      setIncidents(inc.incidents);
      if (fl.flows.length) setGraphData(fromReplayFlows(fl.flows));
      setMonitorError(null);
    } catch (e) {
      setMonitorError(e instanceof Error ? e.message : String(e));
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);
  usePolling(refresh, POLL_MS, true);

  useEffect(() => {
    if (status?.speed) setSpeed(status.speed);
  }, [status?.speed]);

  const selectionInfo = (() => {
    if (!selection) return null;
    const node = graphData.nodes.find((n) => n.id === selection);
    if (node) {
      const related = flows.filter(
        (f) => f.source === node.label || f.destination === node.label,
      );
      const risk = related.reduce((m, f) => Math.max(m, f.risk_score ?? 0), 0);
      const suspicious = related.filter((f) => f.classification !== "BENIGN").length;
      return {
        title: node.label,
        lines: [
          `${related.length} observed communication${related.length !== 1 ? "s" : ""}`,
          `${suspicious} suspicious flow${suspicious !== 1 ? "s" : ""}`,
          `max risk: ${risk.toFixed(1)}`,
          node.kind === "port" ? "service / port node" : "network host",
        ],
      };
    }
    return null;
  })();

  return (
    <div className="space-y-4">
      {monitorError && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2 text-sm text-red-400">
          Backend unavailable: {monitorError}
        </div>
      )}

      <ReplayControls
        status={status}
        onStarted={(s) => {
          setStatus(s);
          void refresh();
        }}
        speed={speed}
        onSpeed={setSpeed}
      />

      <SecurityStatus status={status} incidents={incidents} />

      <SummaryCards status={status} />

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <AttackTimeline flows={flows} />
        <RiskDistribution flows={flows} />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div>
          <div className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-500">
            Communication Map
          </div>
          <CommGraph data={graphData} height={360} onSelect={(s) => setSelection(s.id)} />
          {selectionInfo && (
            <div className="mt-2 rounded-lg border border-slate-800 bg-slate-900 px-3 py-2">
              <div className="text-sm font-semibold text-slate-200">{selectionInfo.title}</div>
              <ul className="mt-1 space-y-0.5 text-xs text-slate-400">
                {selectionInfo.lines.map((l) => (
                  <li key={l}>{l}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <IncidentList incidents={incidents} onOpen={onOpenIncident} />
      </div>

      <TrafficTable flows={flows} />
    </div>
  );
}
