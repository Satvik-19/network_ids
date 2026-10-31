/** Minimal API client — relative /api calls, proxied to the backend by Vite. */
import type {
  BenignBaselinesOut,
  IncidentDetail,
  IncidentList,
  ReplayFlowsOut,
  ReplayStatus,
  ScenarioInfo,
  Health,
} from "./types";

const BASE = "/api";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { headers: { Accept: "application/json" } });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body?.detail ?? detail;
    } catch {
      /* keep statusText */
    }
    throw new Error(`${res.status} ${detail}`);
  }
  return (await res.json()) as T;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const b = await res.json();
      detail = b?.detail ?? detail;
    } catch {
      /* keep statusText */
    }
    throw new Error(`${res.status} ${detail}`);
  }
  return (await res.json()) as T;
}

export const api = {
  health: () => get<Health>("/health"),
  scenarios: () => get<ScenarioInfo[]>("/replay/scenarios"),
  replayStatus: () => get<ReplayStatus>("/replay/status"),
  starting: (scenario: string, speed: number) =>
    post<ReplayStatus>("/replay/start", { scenario, speed }),
  pausing: () => post<ReplayStatus>("/replay/pause", {}),
  resuming: () => post<ReplayStatus>("/replay/resume", {}),
  stopping: () => post<ReplayStatus>("/replay/stop", {}),
  recentFlows: (limit = 100, runId?: string | null) =>
    get<ReplayFlowsOut>(
      runId
        ? `/replay/flows?run_id=${encodeURIComponent(runId)}&limit=${limit}`
        : `/replay/flows?limit=${limit}`,
    ),
  incidents: (runId?: string | null) =>
    get<IncidentList>(runId ? `/incidents?run_id=${encodeURIComponent(runId)}` : "/incidents"),
  incidentDetail: (id: number) => get<IncidentDetail>(`/incidents/${id}`),
  baselines: () => get<BenignBaselinesOut>("/baselines/benign"),
};
