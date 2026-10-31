import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { ReplayStatus, ScenarioInfo } from "../api/types";
import { scenarioDescription, scenarioDisplayName } from "./ui";

interface Props {
  ready: boolean;
  status: ReplayStatus | null;
  onStarted: (s: ReplayStatus) => void;
  speed: number;
  onSpeed: (s: number) => void;
}

export function ReplayControls({ ready, status, onStarted, speed, onSpeed }: Props) {
  const [scenarios, setScenarios] = useState<ScenarioInfo[]>([]);
  const [scenario, setScenario] = useState("portscan");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const activeState = status?.state ?? "IDLE";

  useEffect(() => {
    api
      .scenarios()
      .then((list) => {
        setScenarios(list);
        if (list.length && !list.some((s) => s.name === scenario)) {
          setScenario(list[0].name);
        }
      })
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function run(action: () => Promise<ReplayStatus>) {
    setBusy(true);
    setError(null);
    try {
      const s = await action();
      onStarted(s);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  const canStart =
    ready && !busy && ["IDLE", "COMPLETED", "STOPPED", "FAILED"].includes(activeState);
  const canPause = !busy && activeState === "RUNNING";
  const canResume = !busy && activeState === "PAUSED";
  const canStop = !busy && (activeState === "RUNNING" || activeState === "PAUSED");

  const stateLabel: Record<string, string> = {
    IDLE: "Ready",
    RUNNING: "Replaying",
    PAUSED: "Paused",
    COMPLETED: "Completed",
    STOPPED: "Stopped",
    FAILED: "Failed",
  };

  const stateColor =
    activeState === "RUNNING"
      ? "bg-emerald-500"
      : activeState === "PAUSED"
        ? "bg-amber-500"
        : activeState === "COMPLETED"
          ? "bg-emerald-600"
          : "bg-slate-600";

  const btnBase =
    "rounded-lg px-3 py-1.5 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-40 transition-colors";

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
      <div className="flex flex-wrap items-end gap-4">
        <div className="flex-1 min-w-[180px]">
          <label className="mb-1 block text-xs font-medium text-slate-400">Traffic Scenario</label>
          <select
            value={scenario}
            onChange={(e) => setScenario(e.target.value)}
            disabled={!canStart}
            className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-white focus:border-blue-500 focus:outline-none disabled:opacity-50"
          >
            {scenarios.map((s) => (
              <option key={s.name} value={s.name}>
                {scenarioDisplayName(s.name)} ({s.flows} flows)
              </option>
            ))}
          </select>
          {scenarioDescription(scenario) && (
            <p className="mt-1 text-xs text-slate-500">{scenarioDescription(scenario)}</p>
          )}
        </div>

        <div>
          <label className="mb-1 block text-xs font-medium text-slate-400">Speed</label>
          <div className="flex gap-1">
            {(status?.speeds ?? [1, 5, 20]).map((spd) => (
              <button
                key={spd}
                onClick={() => onSpeed(spd)}
                className={`${btnBase} ${
                  speed === spd
                    ? "bg-white text-slate-900"
                    : "bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-slate-200"
                }`}
              >
                {spd}x
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-end gap-2">
          {["IDLE", "COMPLETED", "STOPPED", "FAILED"].includes(activeState) && (
            <button
              onClick={() => run(() => api.starting(scenario, speed))}
              disabled={!canStart}
              className={`${btnBase} bg-blue-600 text-white hover:bg-blue-700`}
            >
              Start
            </button>
          )}
          {activeState === "RUNNING" && (
            <button
              onClick={() => run(() => api.pausing())}
              disabled={!canPause}
              className={`${btnBase} bg-amber-600 text-white hover:bg-amber-700`}
            >
              Pause
            </button>
          )}
          {activeState === "PAUSED" && (
            <button
              onClick={() => run(() => api.resuming())}
              disabled={!canResume}
              className={`${btnBase} bg-blue-600 text-white hover:bg-blue-700`}
            >
              Resume
            </button>
          )}
          {canStop && (
            <button
              onClick={() => run(() => api.stopping())}
              disabled={!canStop}
              className={`${btnBase} bg-slate-700 text-slate-300 hover:bg-slate-600`}
            >
              Stop
            </button>
          )}
        </div>

        <div className="ml-auto flex items-center gap-2">
          <span
            className={`inline-block h-2 w-2 rounded-full ${stateColor} ${
              activeState === "RUNNING" ? "animate-pulse" : ""
            }`}
          />
          <span className="text-xs font-medium text-slate-300">
            {!ready && activeState === "IDLE" ? "Model unavailable" : stateLabel[activeState] ?? activeState}
          </span>
        </div>
      </div>
      {error && <p className="mt-2 text-sm text-red-400">{error}</p>}
    </div>
  );
}
