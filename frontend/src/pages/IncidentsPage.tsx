import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";
import type { IncidentSummary } from "../api/types";
import { IncidentList } from "../components/IncidentList";

export function IncidentsPage({ onOpen }: { onOpen: (id: number) => void }) {
  const [incidents, setIncidents] = useState<IncidentSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(() => {
    api
      .incidents()
      .then((r) => {
        setIncidents(r.incidents);
        setError(null);
      })
      .catch((e) => setError(e instanceof Error ? e.message : String(e)));
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <div className="space-y-4">
      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-2 text-sm text-red-400">
          Backend unavailable: {error}
        </div>
      )}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-white">Incidents</h2>
        <button
          onClick={refresh}
          className="rounded-lg bg-slate-800 px-3 py-1.5 text-sm text-slate-300 hover:bg-slate-700"
        >
          Refresh
        </button>
      </div>
      <IncidentList incidents={incidents} onOpen={onOpen} />
    </div>
  );
}
