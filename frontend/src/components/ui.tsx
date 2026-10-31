import type { Classification, RiskLevel } from "../api/types";
import { isAnomalyFlagged } from "../lib/detection";
export { isAnomalyFlagged } from "../lib/detection";

export function formatReplayTime(iso: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleTimeString([], { hour12: false });
}

export function formatSeq(seq: number | null): string {
  return seq === null ? "—" : String(seq);
}

export function formatScore(v: number | null | undefined, digits = 2): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return v.toFixed(digits);
}

export function formatPercent(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return `${(v * 100).toFixed(0)}%`;
}

export function formatAnomaly(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return v.toFixed(4);
}

export function formatAnomalyFlag(v: number | null | undefined, threshold: number | null | undefined): { label: string; flagged: boolean | null } {
  const flagged = isAnomalyFlagged(v, threshold);
  return { label: flagged == null ? "Unavailable" : flagged ? "Abnormal" : "Normal", flagged };
}

export function RiskBadge({ level }: { level: RiskLevel | null | undefined }) {
  if (!level) return <span className="text-slate-400">—</span>;
  const cls = level.toLowerCase();
  return (
    <span className={`risk-tag ${cls}`}>
      {level}
    </span>
  );
}

const CLASS_DISPLAY: Record<string, string> = {
  BENIGN: "Benign",
  KNOWN_ATTACK: "Known Attack",
  UNKNOWN_SUSPICIOUS: "Unknown Suspicious",
};

export function ClassificationBadge({
  value,
}: {
  value: Classification | string | null | undefined;
}) {
  if (!value) return <span className="text-slate-400">—</span>;
  const key = (["BENIGN", "KNOWN_ATTACK", "UNKNOWN_SUSPICIOUS"].includes(value)
    ? value
    : "UNKNOWN_SUSPICIOUS") as Classification;
  const cls = key.toLowerCase();
  return (
    <span className={`classification-tag ${cls}`}>
      {CLASS_DISPLAY[value] ?? value}
    </span>
  );
}

const SEVERITY_BG: Record<RiskLevel, string> = {
  LOW: "bg-slate-500",
  MEDIUM: "bg-amber-500",
  HIGH: "bg-orange-500",
  CRITICAL: "bg-red-600",
};

export function SeverityBar({ level }: { level: RiskLevel | null | undefined }) {
  if (!level) return null;
  return (
    <span
      className={`inline-block h-2 w-2 rounded-full ${SEVERITY_BG[level] ?? "bg-slate-400"}`}
      title={level}
    />
  );
}

const SCENARIO_DISPLAY: Record<string, { title: string; desc: string }> = {
  normal: { title: "Normal Traffic", desc: "Routine benign network communications" },
  portscan: { title: "Port Scan", desc: "Reconnaissance: one host scanning multiple services" },
  dos_or_ddos: { title: "Denial of Service", desc: "Targeted flooding of a network service" },
  unknown: { title: "Anomalous Traffic", desc: "Unusual patterns not matching known attacks" },
};

export function scenarioDisplayName(name: string): string {
  return SCENARIO_DISPLAY[name]?.title ?? name;
}

export function scenarioDescription(name: string): string {
  return SCENARIO_DISPLAY[name]?.desc ?? "";
}

export function EmptyState({
  icon,
  title,
  description,
}: {
  icon?: string;
  title: string;
  description?: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      {icon && <div className="mb-3 text-3xl opacity-40">{icon}</div>}
      <div className="text-sm font-medium text-slate-500">{title}</div>
      {description && <div className="mt-1 text-sm text-slate-400">{description}</div>}
    </div>
  );
}
