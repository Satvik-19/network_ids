import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { ReplayFlow } from "../api/types";
import { EmptyState } from "./ui";

const LEVEL_COLORS: Record<string, string> = {
  LOW: "#10b981",
  MEDIUM: "#f59e0b",
  HIGH: "#f97316",
  CRITICAL: "#ef4444",
};

export function RiskDistribution({ flows }: { flows: ReplayFlow[] }) {
  const levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"] as const;
  const data = levels.map((level) => ({
    level,
    count: flows.filter((f) => f.risk_level === level).length,
    fill: LEVEL_COLORS[level],
  }));

  if (flows.length === 0) {
    return (
      <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
        <h2 className="text-sm font-semibold text-slate-200">Risk Distribution</h2>
        <EmptyState title="No flows replayed yet" description="Start a scenario to see risk levels" />
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
      <h2 className="text-sm font-semibold text-slate-200">Risk Distribution</h2>
      <p className="text-xs text-slate-500">Flows per severity level</p>
      <div className="mt-3 h-40">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: -8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="level" tick={{ fontSize: 10, fill: "#64748b" }} />
            <YAxis allowDecimals={false} tick={{ fontSize: 10, fill: "#64748b" }} />
            <Tooltip
              contentStyle={{ backgroundColor: "#1e293b", border: "1px solid #334155", borderRadius: 8, fontSize: 12 }}
            />
            <Bar dataKey="count" name="Flows" radius={[2, 2, 0, 0]}>
              {data.map((d, i) => (
                <Cell key={i} fill={d.fill} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
