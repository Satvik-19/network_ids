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
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  useEffect(() => { document.documentElement.dataset.theme = theme; }, [theme]);

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
    <div className="console-shell">
      <aside className="console-rail">
        <div className="brand-mark" aria-hidden="true">N / IDS</div>
        <h1>Network IDS</h1>
        <p className="meta">Security evaluation console</p>
        <nav aria-label="Workspace">
          {NAV.map((item, index) => <button key={item.id} onClick={() => navTo(item.id)} aria-current={isActive(item.id) ? "page" : undefined}>
            <span className="nav-number">0{index + 1}</span>{item.label}
          </button>)}
        </nav>
        <div className="rail-context">
          <div className="flex items-center gap-2">
            <span
              className={`inline-block h-2 w-2 rounded-full ${
                health?.model_loaded ? "bg-emerald-400" : "bg-red-400"
              }`}
            />
            {health?.model_loaded ? "Inference ready" : health ? "Model unavailable" : "Backend unreachable"}
          </div>
          <p className="meta mt-2">XGBoost + Isolation Forest</p>
          <p className="scope-note">Prepared scenarios.<br />No live network capture.</p>
        </div>
        <button className="theme-toggle" onClick={() => setTheme(theme === "dark" ? "light" : "dark")} aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}>{theme === "dark" ? "Light" : "Dark"} appearance <span aria-hidden="true">◐</span></button>
      </aside>
      <div className="console-main">
        <header className="workspace-header"><div><p className="eyebrow">Workspace / {view.name === "incidents" && view.openId != null ? `Incident ${view.openId}` : view.name}</p><h2>{NAV.find(n => n.id === view.name)?.label}</h2></div><span className="meta">CICIDS2017 · academic prototype</span></header>
        {health && !health.model_loaded && (
          <p role="alert" className="mb-4 text-sm text-amber-300">{health.message}</p>
        )}

        <main id="workspace-content">
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
