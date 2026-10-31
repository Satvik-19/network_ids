import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { ReplayFlow } from "../api/types";
import { EmptyState } from "./ui";

const LEVEL_COLORS: Record<string, string> = {
  LOW: "var(--text3)",
  MEDIUM: "var(--warning)",
  HIGH: "var(--high)",
  CRITICAL: "var(--error)",
};

export function RiskDistribution({ flows }: { flows: Pick<ReplayFlow, "risk_level">[] }) {
  const levels = ["LOW", "MEDIUM", "HIGH", "CRITICAL"] as const;
  const data = levels.map((level) => ({
    level,
    count: flows.filter((f) => f.risk_level === level).length,
    fill: LEVEL_COLORS[level],
  }));

  if (flows.length === 0) {
    return (
      <div className="chart-section">
        <h2 className="text-sm font-semibold text-slate-200">Risk Distribution</h2>
        <EmptyState title="No flows replayed yet" description="Start a scenario to see risk levels" />
      </div>
    );
  }

  return (
    <div className="chart-section">
      <h2 className="text-sm font-semibold text-slate-200">Risk Distribution</h2>
      <p className="text-sm text-slate-500">Actual flow counts per severity level · n = {flows.length}</p>
      <div className="mt-3 h-56">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 4, right: 8, bottom: 0, left: -8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
            <XAxis dataKey="level" tick={{ fontSize: 12, fill: "var(--text3)" }} />
            <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: "var(--text3)" }} />
            <Tooltip
              contentStyle={{ backgroundColor: "var(--surface2)", color: "var(--text1)", border: "1px solid var(--border-visible)", borderRadius: 4, fontSize: 14 }}
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
