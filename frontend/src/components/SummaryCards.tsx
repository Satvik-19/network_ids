import type { ReplayStatus } from "../api/types";
import { RiskBadge } from "./ui";

export function SummaryCards({ status }: { status: ReplayStatus | null }) {
  const s = status;

  const cards = [
    {
      label: "Flows Analysed",
      value: s ? `${s.processed} / ${s.total}` : "—",
      sub: s && s.total > 0 ? `${Math.round(s.progress * 100)}% complete` : "",
    },
    {
      label: "Suspicious Flows",
      value: s ? String(s.suspicious) : "—",
      sub: s && s.suspicious > 0
        ? `${s.known_attacks} known attack${s.known_attacks !== 1 ? "s" : ""} · ${s.unknown_suspicious} anomalous`
        : s?.state === "COMPLETED"
          ? "All flows benign"
          : "",
    },
    {
      label: "Incidents",
      value: s ? String(s.incidents) : "—",
      sub: s && s.incidents > 0 ? "grouped security events" : "",
    },
    {
      label: "Max Risk",
      value: s && s.max_risk_score > 0 ? String(s.max_risk_score.toFixed(1)) : "—",
      sub: s && s.max_risk_level ? <RiskBadge level={s.max_risk_level} /> : "",
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
      {cards.map((c) => (
        <div key={c.label} className="rounded-xl border border-slate-800 bg-slate-900 p-4">
          <div className="text-xs font-medium text-slate-500">{c.label}</div>
          <div className="mt-1 text-2xl font-bold text-white">{c.value}</div>
          <div className="mt-1 text-xs text-slate-500">{c.sub}</div>
        </div>
      ))}
    </div>
  );
}