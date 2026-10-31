import cytoscape, { type CytoscapeOptions, type ElementDefinition } from "cytoscape";
import { useEffect, useRef } from "react";
import { EmptyState } from "./ui";
import { SUSPICIOUS_EDGE_SELECTOR, HIGH_RISK_EDGE_SELECTOR } from "../lib/graph";

export interface GraphNode {
  id: string;
  label: string;
  kind: "host" | "port";
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  suspicious: boolean;
  high_risk: boolean;
  label: string;
  risk_score: number;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

interface Props {
  data: GraphData;
  height?: number;
  onSelect?: (payload: { kind: "node" | "edge"; id: string }) => void;
}

export function CommGraph({ data, height = 320, onSelect }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);

  const elements: ElementDefinition[] = [
    ...data.nodes.map<ElementDefinition>((n) => ({
      data: { id: n.id, label: n.label, kind: n.kind },
    })),
    ...data.edges.map<ElementDefinition>((e) => ({
      data: {
        id: e.id,
        source: e.source,
        target: e.target,
        label: "",
        suspicious: e.suspicious,
        high_risk: e.high_risk,
        risk_score: e.risk_score,
      },
    })),
  ];

  useEffect(() => {
    if (!containerRef.current) return;
    const options: CytoscapeOptions = {
      container: containerRef.current,
      elements,
      style: [
        {
          selector: "node",
          style: {
            "background-color": "#334155",
            label: "data(label)",
            color: "#e2e8f0",
            "font-size": 11,
            "text-valign": "bottom",
            "text-margin-y": 6,
            width: 32,
            height: 32,
            shape: "ellipse",
            "border-width": 1,
            "border-color": "#475569",
          },
        },
        {
          selector: 'node[kind = "port"]',
          style: {
            "background-color": "#1e293b",
            "border-color": "#64748b",
            "border-style": "dashed",
            width: 20,
            height: 20,
            shape: "round-rectangle",
            "font-size": 9,
            color: "#94a3b8",
          },
        },
        {
          selector: "edge",
          style: {
            width: 1.5,
            "line-color": "#475569",
            "target-arrow-color": "#475569",
            "target-arrow-shape": "triangle",
            "curve-style": "bezier",
            "arrow-scale": 0.8,
          },
        },
        {
          selector: SUSPICIOUS_EDGE_SELECTOR,
          style: { "line-color": "#f97316", "target-arrow-color": "#f97316", width: 2 },
        },
        {
          selector: HIGH_RISK_EDGE_SELECTOR,
          style: { "line-color": "#ef4444", "target-arrow-color": "#ef4444", width: 2.5 },
        },
        {
          selector: "node:selected",
          style: { "border-width": 3, "border-color": "#3b82f6" },
        },
        {
          selector: "edge:selected",
          style: { "line-color": "#3b82f6", "target-arrow-color": "#3b82f6" },
        },
      ],
      layout: {
        name: "breadthfirst",
        directed: true,
        padding: 30,
        spacingFactor: 1.4,
        avoidOverlap: true,
      },
      userPanningEnabled: false,
      userZoomingEnabled: false,
      autoungrabify: true,
    };
    cyRef.current = cytoscape(options);

    if (onSelect) {
      cyRef.current.on("tap", "node", (evt) => {
        onSelect({ kind: "node", id: evt.target.id() });
      });
      cyRef.current.on("tap", "edge", (evt) => {
        onSelect({ kind: "edge", id: evt.target.id() });
      });
    }

    return () => {
      cyRef.current?.destroy();
      cyRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!cyRef.current) return;
    // Pick up container size changes (e.g. first paint after mount) so the
    // layout is computed against real dimensions, not a 0-size canvas.
    cyRef.current.resize();
    cyRef.current.elements().remove();
    cyRef.current.add(elements);
    const nodeCount = data.nodes.length;
    cyRef.current.layout({
      name: nodeCount <= 4 ? "cose" : "breadthfirst",
      directed: true,
      padding: 30,
      spacingFactor: nodeCount <= 4 ? 1.8 : 1.4,
      animate: false,
      avoidOverlap: true,
    }).run();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data]);

  return (
    <div
      style={{ height }}
      className="relative rounded-xl border border-slate-800 bg-slate-900"
    >
      {data.nodes.length === 0 && (
        <EmptyState
          title="No communication data"
          description="Start a replay to see network activity"
        />
      )}
      <div ref={containerRef} style={{ height }} className="h-full w-full" />
    </div>
  );
}
