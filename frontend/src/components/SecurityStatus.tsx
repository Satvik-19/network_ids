import type { IncidentSummary, ReplayStatus } from "../api/types";
import { RiskBadge } from "./ui";
import { unknownExplanation } from "../lib/detection";

interface Props {
  status: ReplayStatus | null;
  incidents: IncidentSummary[];
}

type Tone = "healthy" | "info" | "suspicious" | "attack" | "unknown" | "neutral";

const TONE_STYLES: Record<Tone, { bar: string; title: string; body: string }> = {
  healthy: { bar: "bg-emerald-500", title: "text-emerald-300", body: "text-slate-400" },
  info: { bar: "bg-blue-400", title: "text-blue-300", body: "text-slate-400" },
  suspicious: { bar: "bg-amber-500", title: "text-amber-300", body: "text-slate-300" },
  attack: { bar: "bg-red-600", title: "text-red-400", body: "text-slate-300" },
  unknown: { bar: "bg-violet-500", title: "text-violet-300", body: "text-slate-300" },
  neutral: { bar: "bg-slate-600", title: "text-slate-300", body: "text-slate-500" },
};

// Derive the current security narrative from REAL runtime state + incident
// data. No scenario-specific hard-coded answers.
function derive(
  status: ReplayStatus | null,
  incidents: IncidentSummary[],
): { tone: Tone; title: string; body: string; meta?: string; risk?: string } {
  if (!status) {
    return {
      tone: "neutral",
      title: "No replay data",
      body: "Start a traffic scenario to see analysis.",
    };
  }

  const active = status.state === "RUNNING" || status.state === "PAUSED";
  const completed = status.state === "COMPLETED";

  if (status.state === "FAILED") {
    return {
      tone: "suspicious",
      title: "Replay failed",
      body: `${status.processed}/${status.total} flows analysed. ${status.error ?? "Check the backend and start a new run."}`,
    };
  }

  if (active && status.processed < status.total) {
    return {
      tone: "info",
      title: `Analysing traffic… ${status.processed}/${status.total} flows`,
      body: "The IDS is evaluating each replayed flow in sequence.",
    };
  }

  // Headline = highest-risk incident of the CURRENT run (run-scoped fetch).
  const head =
    incidents.length > 0
      ? [...incidents].sort((a, b) => (b.risk_score ?? 0) - (a.risk_score ?? 0))[0]
      : null;

  if (!head) {
    if (completed && status.suspicious === 0) {
      return {
        tone: "healthy",
        title: "No suspicious activity detected",
        body: `All ${status.total} analysed flows appear benign.`,
      };
    }
    if (status.suspicious === 0) {
      return {
        tone: "neutral",
        title: "Ready",
        body: "Choose a traffic scenario and press Start.",
      };
    }
    return {
      tone: "info",
      title: "No grouped incident yet",
      body: `${status.suspicious} suspicious flow${status.suspicious !== 1 ? "s" : ""} identified; waiting for more evidence.`,
    };
  }

  const meta =
    `${status.suspicious} suspicious flow${status.suspicious !== 1 ? "s" : ""} · ` +
    `${incidents.length} incident${incidents.length !== 1 ? "s" : ""}`;
  const risk = head.risk_level ?? status.max_risk_level ?? undefined;
  const src = head.source ?? "a host";
  const dst = head.destination ?? "a target";
  const port = head.service_port != null ? `:${head.service_port}` : "";
  const family = head.family ?? "";
  const cls = head.classification;

  if (cls === "UNKNOWN_SUSPICIOUS") {
    return {
      tone: "unknown",
      title: "Unrecognized suspicious behavior",
      body: unknownExplanation(head.label),
      meta,
      risk,
    };
  }

  if (/recon|scan/i.test(family)) {
    return {
      tone: "suspicious",
      title: "Reconnaissance detected",
      body: `${src} scanned multiple services on ${dst}.`,
      meta,
      risk,
    };
  }

  if (/denial|dos|ddos/i.test(family)) {
    return {
      tone: "attack",
      title: "Denial of Service detected",
      body: `Suspicious traffic from ${src} targeted ${dst}${port}.`,
      meta,
      risk,
    };
  }

  return {
    tone: "attack",
    title: "Suspicious activity detected",
    body: `Suspicious traffic from ${src} toward ${dst}.`,
    meta,
    risk,
  };
}

export function SecurityStatus({ status, incidents }: Props) {
  const { tone, title, body, meta, risk } = derive(status, incidents);
  const styles = TONE_STYLES[tone];

  return (
    <div className="relative overflow-hidden rounded-xl border border-slate-800 bg-slate-900">
      <div className={`absolute inset-y-0 left-0 w-1 ${styles.bar}`} />
      <div className="flex flex-col gap-2 py-4 pl-5 pr-5 md:flex-row md:items-center md:justify-between">
        <div>
          <div className={`text-base font-bold tracking-tight ${styles.title}`}>{title}</div>
          <div className={`mt-0.5 text-sm ${styles.body}`}>{body}</div>
        </div>
        {(meta || risk) && (
          <div className="flex shrink-0 items-center gap-3 text-sm text-slate-400">
            {meta && <span>{meta}</span>}
            {risk && <RiskBadge level={risk as "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"} />}
          </div>
        )}
      </div>
    </div>
  );
}
