import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api } from "../api/client";
import { usePolling } from "../api/usePolling";
import { CommGraph } from "../components/CommGraph";
import { IncidentList } from "../components/IncidentList";
import { ReplayControls } from "../components/ReplayControls";
import { RiskDistribution } from "../components/RiskDistribution";
import { SecurityStatus } from "../components/SecurityStatus";
import { SummaryCards } from "../components/SummaryCards";
import { AttackTimeline } from "../components/AttackTimeline";
import { TrafficTable } from "../components/TrafficTable";
import type { IncidentSummary, ReplayFlow, ReplayStatus } from "../api/types";
import { fromReplayFlows, relatedFlows } from "../lib/graph";

const POLL_MS = 1500;

export function SecurityMonitor({ ready, onOpenIncident }: { ready: boolean; onOpenIncident: (id: number) => void }) {
  const [snapshot, setSnapshot] = useState<{
    status: ReplayStatus | null; flows: ReplayFlow[]; incidents: IncidentSummary[];
  }>({ status: null, flows: [], incidents: [] });
  const { status, flows, incidents } = snapshot;
  const request = useRef(0);
  const currentRun = useRef<string | null>(null);
  const [speed, setSpeed] = useState(5);
  const graphData = useMemo(() => fromReplayFlows(flows), [flows]);
  const [selection, setSelection] = useState<string | null>(null);
  const [monitorError, setMonitorError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const version = ++request.current;
    try {
      const st = await api.replayStatus();
      if (version !== request.current) return;
      if (currentRun.current !== st.run_id || !st.run_id) {
        currentRun.current = st.run_id;
        setSelection(null);
        setSnapshot({ status: st, flows: [], incidents: [] });
      }
      if (!st.run_id) {
        setMonitorError(null);
        return;
      }
      const [fl, inc] = await Promise.all([
        api.recentFlows(100, st.run_id),
        api.incidents(st.run_id),
      ]);
      if (version !== request.current) return;
      setSnapshot({ status: st, flows: fl.flows, incidents: inc.incidents });
      setMonitorError(null);
    } catch (e) {
      if (version === request.current) setMonitorError(e instanceof Error ? e.message : String(e));
    }
  }, []);

  useEffect(() => {
    void refresh();
    return () => { request.current += 1; };
  }, [refresh]);
  usePolling(refresh, POLL_MS, true);

  useEffect(() => {
    if (status?.speed) setSpeed(status.speed);
  }, [status?.speed]);

  const selectionInfo = (() => {
    if (!selection) return null;
    const node = graphData.nodes.find((n) => n.id === selection);
    const edge = graphData.edges.find((e) => e.id === selection);
    if (node || edge) {
      const related = relatedFlows(flows, selection);
      const scores = related.flatMap(f => f.risk_score == null ? [] : [f.risk_score]);
      const risk = scores.length ? Math.max(...scores) : null;
      const suspicious = related.filter((f) => f.classification != null && f.classification !== "BENIGN").length;
      return {
        title: node?.label ?? edge!.label,
        lines: [
          `${related.length} observed communication${related.length !== 1 ? "s" : ""}`,
          `${suspicious} suspicious flow${suspicious !== 1 ? "s" : ""}`,
          `max risk: ${risk == null ? "unavailable" : risk.toFixed(1)}`,
          node ? "network host" : `service ports: ${edge!.ports.join(", ") || "unavailable"}`,
        ],
      };
    }
    return null;
  })();

  return (
    <div className="space-y-4">
      {monitorError && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2 text-sm text-red-400">
          Monitoring unavailable: {monitorError}
        </div>
      )}

      <ReplayControls
        ready={ready}
        status={status}
        onStarted={(s) => {
          request.current += 1;
          if (currentRun.current !== s.run_id) {
            currentRun.current = s.run_id;
            setSelection(null);
            setSnapshot({ status: s, flows: [], incidents: [] });
          } else {
            setSnapshot((previous) => ({ ...previous, status: s }));
          }
          void refresh();
        }}
        speed={speed}
        onSpeed={setSpeed}
      />

      <SummaryCards status={status} />
      <SecurityStatus status={status} incidents={incidents} />
      <div className="investigation-grid">
        <section className="communication-section">
          <h2>Observed communications</h2>
          <p className="meta">Current run · latest 100 flow records · select a host or connection</p>
          <CommGraph key={status?.run_id ?? "idle"} data={graphData} height={360} onSelect={(s) => setSelection(s.id)} />
          {selectionInfo && (
            <div className="mt-2 rounded-lg border border-slate-800 bg-slate-900 px-3 py-2">
              <div className="text-sm font-semibold text-slate-200">{selectionInfo.title}</div>
              <ul className="mt-1 space-y-0.5 text-sm text-slate-400">
                {selectionInfo.lines.map((l) => (
                  <li key={l}>{l}</li>
                ))}
              </ul>
            </div>
          )}
        </section>

        <IncidentList incidents={incidents} onOpen={onOpenIncident} />
      </div>
      <div className="chart-grid">
        <AttackTimeline flows={flows} />
        <RiskDistribution flows={flows} />
      </div>
      <TrafficTable flows={flows} />
    </div>
  );
}
