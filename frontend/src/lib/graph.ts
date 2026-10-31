import type { GraphData, GraphEdge, GraphNode } from "../components/CommGraph";
import type { IncidentFlowOut, ReplayFlow } from "../api/types";

interface SrcFlow {
  source: string | null; destination: string | null; service_port: number | null;
  classification: string | null; risk_level: string | null; risk_score: number | null;
}
export function edgeTone(edge: GraphEdge) {
  return edge.high_risk ? "high" : edge.suspicious ? "suspicious" : "neutral";
}

export function relatedFlows<T extends SrcFlow>(flows: T[], id: string): T[] {
  return flows.filter((f) => {
    const service = f.service_port == null ? f.destination : `${f.destination}:${f.service_port}`;
    return f.source === id || f.destination === id || `${f.source}->${f.destination}` === id ||
      service === id || `${f.source}->${service}` === id;
  });
}

/** Hosts and directed relationships observed in the loaded flow records only. */
export function buildGraphData(flows: SrcFlow[]): GraphData {
  const nodes = new Map<string, GraphNode>();
  const edges = new Map<string, GraphEdge>();
  for (const f of flows) {
    if (!f.source || !f.destination) continue;
    for (const id of [f.source, f.destination]) nodes.set(id, { id, label: id, kind: "host" });
    const id = `${f.source}->${f.destination}`;
    const edge = edges.get(id) ?? {
      id, source: f.source, target: f.destination, label: `${f.source} → ${f.destination}`,
      suspicious: false, high_risk: false, risk_score: null, ports: [], flow_count: 0,
    };
    edge.flow_count += 1;
    edge.suspicious ||= f.classification != null && f.classification !== "BENIGN";
    edge.high_risk ||= f.risk_level === "HIGH" || f.risk_level === "CRITICAL";
    if (f.risk_score != null) edge.risk_score = Math.max(edge.risk_score ?? f.risk_score, f.risk_score);
    if (f.service_port != null && !edge.ports.includes(f.service_port)) edge.ports.push(f.service_port);
    edge.ports.sort((a, b) => a - b);
    edges.set(id, edge);
  }
  return { nodes: [...nodes.values()].sort((a, b) => a.id.localeCompare(b.id)),
    edges: [...edges.values()].sort((a, b) => a.id.localeCompare(b.id)) };
}

export type HostPositions = Record<string, { x: number; y: number }>;
export function placeHosts(data: GraphData, previous: HostPositions): HostPositions {
  // Keep occupied slots even if the rolling evidence window drops a host.
  const positions = { ...previous };
  for (const node of data.nodes) {
    if (positions[node.id]) continue;
    const outgoing = data.edges.some(e => e.source === node.id);
    const incoming = data.edges.some(e => e.target === node.id);
    const x = outgoing && incoming ? 360 : outgoing ? 112 : 608;
    const occupied = Object.values(positions).filter(p => p.x === x).map(p => p.y);
    positions[node.id] = { x, y: occupied.length ? Math.max(...occupied) + 88 : 76 };
  }
  return positions;
}
export const fromReplayFlows = (flows: ReplayFlow[]) => buildGraphData(flows);
export const fromIncidentFlows = (flows: IncidentFlowOut[]) => buildGraphData(flows);
