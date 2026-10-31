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
import { RISK_DOMAIN } from "../lib/charts";

const CLS_COLORS: Record<string, string> = {
  BENIGN: "var(--text3)",
  KNOWN_ATTACK: "var(--error)",
  UNKNOWN_SUSPICIOUS: "var(--warning)",
};

export function AttackTimeline({ flows }: { flows: ReplayFlow[] }) {
  const rows = [...flows]
    .sort((a, b) => (a.seq ?? 0) - (b.seq ?? 0))
    .slice(-200)
    .map((f) => {
      return {
        seq: f.seq ?? f.id,
        at: format(f.replay_time),
        score: f.risk_score,
        risk: f.risk_score,
        cls: f.classification ?? "BENIGN",
        fill: CLS_COLORS[f.classification ?? "BENIGN"] ?? "var(--text3)",
      };
    });

  if (rows.length === 0) {
    return (
      <div className="chart-section">
        <h2 className="text-sm font-semibold text-slate-200">Replay Activity</h2>
        <EmptyState title="No flows replayed yet" description="Start a scenario to see activity" />
      </div>
    );
  }

  return (
    <div className="chart-section">
      <h2 className="text-sm font-semibold text-slate-200">Replay Activity</h2>
      <p className="text-sm text-slate-500">Recorded risk / fixed 0–100 · neutral = benign, red = known attack, amber = unknown suspicious</p>
      <div className="mt-3 h-56">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={rows} margin={{ top: 4, right: 8, bottom: 0, left: -8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis dataKey="seq" tick={{ fontSize: 12, fill: "var(--text3)" }} tickFormatter={fmtTick} />
            {/* One risk scale across scenarios; missing scores remain unavailable. */}
            <YAxis
              tick={{ fontSize: 12, fill: "var(--text3)" }}
              domain={RISK_DOMAIN} ticks={[0, 25, 50, 75, 100]}
            />
            <Tooltip
              contentStyle={{ backgroundColor: "var(--surface2)", color: "var(--text1)", border: "1px solid var(--border-visible)", borderRadius: 4, fontSize: 14 }}
              formatter={(_v, _n, item) => {
                const p = item?.payload as (typeof rows)[number] | undefined;
                return [p?.risk == null ? "unavailable" : `${p.risk}`, "risk score"];
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
