import type { GraphData } from "../components/CommGraph";
import type { IncidentFlowOut, ReplayFlow } from "../api/types";

interface SrcFlow {
  source: string | null;
  destination: string | null;
  service_port: number | null;
  classification: string | null;
  risk_level: string | null;
  risk_score: number | null;
}

/**
 * Build a communication-graph model from observed flows (PRD §15). Nodes are
 * the source/destination hosts; a service/port node is added per destination
 * when flows carry a service_port. Edges are observed communications with
 * the max risk across their flows. Real flow data only — never topology.
 */
export function buildGraphData(flows: SrcFlow[]): GraphData {
  const nodes = new Map<string, { id: string; label: string; kind: "host" | "port" }>();
  const edges = new Map<
    string,
    { id: string; source: string; target: string; suspicious: boolean; high_risk: boolean; label: string; risk_score: number }
  >();

  const hostId = (addr: string) => addr;

  for (const f of flows) {
    if (!f.source || !f.destination) continue;
    const src = hostId(f.source);
    const dst = hostId(f.destination);

    if (!nodes.has(src)) nodes.set(src, { id: src, label: f.source, kind: "host" });
    if (!nodes.has(dst)) nodes.set(dst, { id: dst, label: f.destination, kind: "host" });

    let target = dst;
    if (f.service_port != null) {
      const portId = `${dst}:${f.service_port}`;
      if (!nodes.has(portId)) {
        nodes.set(portId, { id: portId, label: `:${f.service_port}`, kind: "port" });
      }
      target = portId;
    }

    const edgeId = `${src}->${target}`;
    const suspicious = f.classification !== "BENIGN";
    const highRisk = f.risk_level === "HIGH" || f.risk_level === "CRITICAL";
    const score = f.risk_score ?? 0;
    const existing = edges.get(edgeId);
    if (existing) {
      existing.suspicious = existing.suspicious || suspicious;
      existing.high_risk = existing.high_risk || highRisk;
      existing.risk_score = Math.max(existing.risk_score, score);
    } else {
      edges.set(edgeId, {
        id: edgeId,
        source: src,
        target,
        suspicious,
        high_risk: highRisk,
        risk_score: score,
        label: f.service_port != null ? `${f.source} → :${f.service_port}` : f.source ?? "",
      });
    }
  }

  return {
    nodes: [...nodes.values()],
    edges: [...edges.values()],
  };
}

/** Convenience wrappers for the two typed flow shapes. */
export const fromReplayFlows = (flows: ReplayFlow[]) => buildGraphData(flows);
export const fromIncidentFlows = (flows: IncidentFlowOut[]) => buildGraphData(flows);
