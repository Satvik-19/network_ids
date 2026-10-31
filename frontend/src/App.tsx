import { useEffect, useState } from "react";
import { api } from "./api/client";
import { IncidentDetail } from "./pages/IncidentDetail";
import { IncidentsPage } from "./pages/IncidentsPage";
import { SecurityMonitor } from "./pages/SecurityMonitor";
import { Playground } from "./pages/Playground";
import { usePolling } from "./api/usePolling";
import type { Health } from "./api/types";

type View = { name: "monitor" } | { name: "playground" } | { name: "incidents"; openId: number | null };

const NAV = [
  { id: "monitor", label: "Security Monitor" },
  { id: "incidents", label: "Incidents" },
  { id: "playground", label: "Security Playground" },
];

export default function App() {
  const [view, setView] = useState<View>({ name: "monitor" });
  const [health, setHealth] = useState<Health | null>(null);

  function refreshHealth() {
    return api
      .health()
      .then(setHealth)
      .catch(() => setHealth(null));
  }
  useEffect(() => { void refreshHealth(); }, []);
  usePolling(refreshHealth, 5000, true);

  function navTo(id: string) {
    if (id === "monitor") setView({ name: "monitor" });
    else if (id === "incidents") setView({ name: "incidents", openId: null });
    else if (id === "playground") setView({ name: "playground" });
  }

  const isActive = (id: string) =>
    view.name === id || (id === "incidents" && view.name === "incidents");

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-7xl px-4 py-6 lg:px-8">
        <header className="mb-6 flex flex-wrap items-end justify-between gap-3 border-b border-slate-800 pb-4">
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white lg:text-2xl">
              Network IDS
            </h1>
            <p className="mt-1 max-w-xl text-xs leading-relaxed text-slate-400">
              Replay network scenarios and inspect how the AI-powered IDS detects, scores
              and explains suspicious activity.
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <span
              className={`inline-block h-2 w-2 rounded-full ${
                health?.model_loaded ? "bg-emerald-400" : "bg-red-400"
              }`}
            />
            {health?.model_loaded ? "System ready" : health ? "Model unavailable" : "Backend unreachable"}
          </div>
        </header>
        {health && !health.model_loaded && (
          <p role="alert" className="mb-4 text-sm text-amber-300">{health.message}</p>
        )}

        <nav className="mb-6 flex gap-1">
          {NAV.map((item) => (
            <button
              key={item.id}
              onClick={() => navTo(item.id)}
              className={`rounded-lg px-3.5 py-1.5 text-sm font-medium transition-colors ${
                isActive(item.id)
                  ? "bg-white text-slate-900"
                  : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
              }`}
            >
              {item.label}
            </button>
          ))}
        </nav>

        <main>
          {view.name === "playground" && <Playground ready={health?.model_loaded === true} />}
          {view.name === "monitor" && (
            <SecurityMonitor ready={health?.model_loaded === true} onOpenIncident={(id) => setView({ name: "incidents", openId: id })} />
          )}
          {view.name === "incidents" &&
            (view.openId == null ? (
              <IncidentsPage onOpen={(id) => setView({ name: "incidents", openId: id })} />
            ) : (
              <IncidentDetail
                key={view.openId}
                incidentId={view.openId}
                onBack={() => setView({ name: "incidents", openId: null })}
              />
            ))}
        </main>
      </div>
    </div>
  );
}
