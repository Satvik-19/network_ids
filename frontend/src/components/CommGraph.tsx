import { useEffect, useId, useMemo, useRef, useState } from "react";
import { EmptyState } from "./ui";
import { edgeTone, placeHosts, type HostPositions } from "../lib/graph";

export interface GraphNode { id: string; label: string; kind: "host" }
export interface GraphEdge {
  id: string; source: string; target: string; suspicious: boolean; high_risk: boolean;
  label: string; risk_score: number | null; ports: number[]; flow_count: number;
}
export interface GraphData { nodes: GraphNode[]; edges: GraphEdge[] }
interface Props {
  data: GraphData; height?: number;
  onSelect?: (payload: { kind: "node" | "edge"; id: string }) => void;
}

export function CommGraph({ data, height = 320, onSelect }: Props) {
  const arrowId = useId().replace(/:/g, "");
  const positionsRef = useRef<HostPositions>({});
  const containerRef = useRef<HTMLDivElement>(null);
  const [narrow, setNarrow] = useState(false);
  const hasData = data.nodes.length > 0;
  useEffect(() => {
    if (!containerRef.current) return;
    const observer = new ResizeObserver(([entry]) => setNarrow(entry.contentRect.width < 600));
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, [hasData]);
  const positions = useMemo(() => {
    positionsRef.current = data.nodes.length ? placeHosts(data, positionsRef.current) : {};
    return positionsRef.current;
  }, [data]);
  const [selected, setSelected] = useState<string | null>(null);
  const [suspiciousOnly, setSuspiciousOnly] = useState(false);
  const compact = narrow && !Object.values(positions).some(p => p.x === 360);
  const halfWidth = compact ? 70 : 88;
  const point = (id: string) => ({ ...positions[id], x: compact ? (positions[id].x === 112 ? 88 : 272) : positions[id].x });
  const edges = data.edges.filter(e => !suspiciousOnly || e.suspicious);
  const canvasHeight = Math.max(148, ...data.nodes.map(n => positions[n.id].y + 64));
  function select(kind: "node" | "edge", id: string) { setSelected(id); onSelect?.({ kind, id }); }
  if (!data.nodes.length) return <EmptyState title="No communication evidence" description="Start a replay to load observed host relationships." />;
  return <div className="communication" ref={containerRef}>
    <div className="graph-toolbar"><span className="meta">{data.nodes.length} hosts · {edges.length} directed connection{edges.length === 1 ? "" : "s"}</span><label><input type="checkbox" checked={suspiciousOnly} onChange={e => setSuspiciousOnly(e.target.checked)} /> Suspicious only</label></div>
    <div className="graph-scroll" style={{ maxHeight: height }} tabIndex={0} role="region" aria-label="Host communication diagram; scroll for more hosts">
      <svg viewBox={`0 0 ${compact ? 360 : 720} ${canvasHeight}`} className={`host-diagram ${compact ? "compact" : ""}`} aria-label="Observed directed host relationships">
        <defs>{["neutral", "suspicious", "high"].map(tone => <marker key={tone} id={`${arrowId}-${tone}`} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" className={`arrow-${tone}`} /></marker>)}</defs>
        <text x={compact ? 18 : 24} y="22" className="lane-label">SOURCE HOSTS</text><text x={compact ? 202 : 520} y="22" className="lane-label">DESTINATION HOSTS</text>
        {edges.map(e => {
          const a = point(e.source), b = point(e.target);
          const tone = edgeTone(e);
          const reverse = a.x > b.x;
          const sx = a.x + (reverse ? -halfWidth : halfWidth), tx = b.x + (reverse ? halfWidth + 8 : -halfWidth - 8);
          const offset = edges.some(other => other.source === e.target && other.target === e.source) ? (reverse ? 24 : -24) : 0;
          const path = e.source === e.target
            ? `M ${a.x-30} ${a.y-28} C ${a.x-100} ${a.y-76}, ${a.x+100} ${a.y-76}, ${a.x+30} ${a.y-28}`
            : a.x === b.x ? `M ${a.x+88} ${a.y} C ${a.x+140} ${a.y}, ${b.x+140} ${b.y}, ${b.x+88} ${b.y}`
            : `M ${sx} ${a.y+offset} C ${(sx+tx)/2} ${a.y+offset}, ${(sx+tx)/2} ${b.y+offset}, ${tx} ${b.y+offset}`;
          return <g key={e.id} className={`graph-edge ${tone} ${selected === e.id ? "selected" : ""}`}>
            <path d={path} className="edge-hit" onClick={() => select("edge", e.id)}><title>{e.label}: {e.flow_count} flows; ports {e.ports.join(", ") || "unavailable"}</title></path>
            <path d={path} className="edge-line" markerEnd={`url(#${arrowId}-${tone})`} />
            {data.edges.length === 1 && <text x={compact ? 180 : 360} y={compact ? a.y+58 : a.y-16} textAnchor="middle">{e.flow_count} observed flows</text>}
          </g>;
        })}
        {data.nodes.map(n => {
          const p = point(n.id);
          return <g key={n.id} data-host={n.id} transform={`translate(${p.x},${p.y})`} role="button" tabIndex={0} aria-label={`Select host ${n.label}`} aria-pressed={selected === n.id} className={`graph-host ${selected === n.id ? "selected" : ""}`} onClick={() => select("node", n.id)} onKeyDown={e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); select("node", n.id); } }}>
            <rect x={-halfWidth} y="-28" width={halfWidth*2} height="56" rx="4" /><text textAnchor="middle" y="5">{n.label}</text>
          </g>;
        })}
      </svg>
    </div>
    <div className="graph-legend"><span><i /> Observed</span><span><i className="suspicious" /> Suspicious</span><span><i className="high" /> High / critical</span><span>Arrow = flow direction · scroll diagram on small screens</span></div>
    <div className="table-scroll" tabIndex={0} role="region" aria-label="Observed connection evidence"><table className="connection-table"><thead><tr><th>Connection / select evidence</th><th>Service ports</th><th>Flows</th><th>Max risk / 100</th></tr></thead><tbody>
      {edges.map(e => <tr key={e.id} className={selected === e.id ? "selected" : ""}><td><button aria-pressed={selected === e.id} onClick={() => select("edge", e.id)} className="connection-select">{e.label}</button></td><td className="font-mono">{e.ports.join(", ") || "Unavailable"}</td><td className="font-mono">{e.flow_count}</td><td className="font-mono">{e.risk_score?.toFixed(2) ?? "Unavailable"}</td></tr>)}
    </tbody></table></div>
    {!edges.length && <p className="py-4">No suspicious connections in the loaded records.</p>}
    <p className="meta mt-3">Ports are connection metadata. Protocol is unavailable. Synthetic scenario addresses describe observed flows, not physical network topology.</p>
  </div>;
}
