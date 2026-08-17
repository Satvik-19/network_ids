import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { ReplayFlow } from "../api/types";
import { EmptyState } from "./ui";

const CLS_COLORS: Record<string, string> = {
  BENIGN: "#10b981",
  KNOWN_ATTACK: "#ef4444",
  UNKNOWN_SUSPICIOUS: "#8b5cf6",
};

// Benign flows carry risk 0; give them a minimal visible bar so a fully
// benign run (Normal scenario) still communicates "traffic analysed, all
// healthy" instead of an empty chart.
const BENIGN_BASE_HEIGHT = 0.15;

export function AttackTimeline({ flows }: { flows: ReplayFlow[] }) {
  const rows = [...flows]
    .sort((a, b) => (a.seq ?? 0) - (b.seq ?? 0))
    .slice(-200)
    .map((f) => {
      const benign = (f.classification ?? "BENIGN") === "BENIGN";
      return {
        seq: f.seq ?? f.id,
        at: format(f.replay_time),
        score: benign ? BENIGN_BASE_HEIGHT : Math.max(1, f.risk_score ?? 0),
        risk: benign ? 0 : f.risk_score ?? 0,
        cls: f.classification ?? "BENIGN",
        fill: CLS_COLORS[f.classification ?? "BENIGN"] ?? "#64748b",
      };
    });

  if (rows.length === 0) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
        <h2 className="text-sm font-semibold text-slate-200">Replay Activity</h2>
        <EmptyState title="No flows replayed yet" description="Start a scenario to see activity" />
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
      <h2 className="text-sm font-semibold text-slate-200">Replay Activity</h2>
      <p className="text-xs text-slate-500">Risk score per flow · green = benign, red = attack, purple = anomalous</p>
      <div className="mt-3 h-56">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={rows} margin={{ top: 4, right: 8, bottom: 0, left: -8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="seq" tick={{ fontSize: 10, fill: "#64748b" }} tickFormatter={fmtTick} />
            {/* Floor the axis at 1 so benign base-height bars always read as tiny. */}
            <YAxis
              tick={{ fontSize: 10, fill: "#64748b" }}
              domain={[0, (dataMax: number) => Math.max(1, dataMax)]}
            />
            <Tooltip
              contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155", borderRadius: 8, fontSize: 12 }}
              formatter={(_v, _n, item) => {
                const p = item?.payload as (typeof rows)[number] | undefined;
                return [p?.cls === "BENIGN" ? "0 · benign" : `${p?.risk ?? 0}`, "risk score"];
              }}
              labelFormatter={(label, payload) => {
                const p = payload?.[0]?.payload;
                return `flow ${label} · ${p?.at ?? ""} · ${p?.cls ?? ""}`;
              }}
            />
            <Bar dataKey="score" name="Risk" radius={[2, 2, 0, 0]}>
              {rows.map((r, i) => (
                <Cell key={i} fill={r.fill} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function format(iso: string | null): string {
  if (!iso) return "";
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? "" : d.toLocaleTimeString([], { hour12: false });
}

function fmtTick(v: unknown): string {
  return String(v);
}
