import { useState } from "react";
import { api } from "../api/client";
import type { EnvironmentProfile, PlaygroundProfile, PlaygroundResult } from "../api/types";
import { RiskDistribution } from "../components/RiskDistribution";
import { ClassificationBadge, RiskBadge } from "../components/ui";
import { scenarioOutcome, unknownExplanation } from "../lib/detection";
import { SignedContributions } from "../components/SignedContributions";

const panel = "playground-section";
const input = "mt-1 block w-full rounded border border-slate-700 bg-slate-950 px-3 py-2 text-sm";
const button = "rounded-lg bg-white px-4 py-2 text-sm font-medium text-slate-900 disabled:opacity-40";
const services = [
  ["web", "Web / HTTP(S)"], ["ssh", "SSH"], ["ftp", "FTP"],
  ["database", "Database"], ["file_sharing", "File sharing"],
] as const;

export function Playground({ ready }: { ready: boolean }) {
  const [profile, setProfile] = useState<EnvironmentProfile>({ environment: "home", scale: "1-10", exposure: "internal", services: [] });
  const [plan, setPlan] = useState<PlaygroundProfile | null>(null);
  const [result, setResult] = useState<PlaygroundResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selection, setSelection] = useState(0);
  const [savedId, setSavedId] = useState("");

  function change(next: EnvironmentProfile) {
    setProfile(next); setPlan(null); setResult(null); setError(null); setSelection(0);
  }

  async function perform(action: () => Promise<void>) {
    setBusy(true); setError(null);
    try { await action(); }
    catch (e) { setError(e instanceof Error ? e.message : String(e)); }
    finally { setBusy(false); }
  }

  const assessment = result?.assessment;
  const flows = result?.scenarios.flatMap(s => s.flows.map(f => ({ ...f, scenario: s.name }))) ?? [];
  const selected = flows[selection];
  const overlap = result?.scenarios.reduce((n, s) => n + s.training_feature_matches, 0) ?? 0;

  return <div className="space-y-4">
    <div>
      <h1 className="text-xl font-bold">Personalized Security Playground</h1>
      <p className="mt-2 text-sm text-amber-200">Simulated scenario evaluation only. This does not inspect or certify your real network.</p>
      <p className="mt-1 text-sm text-slate-400">Choose an environment to select prepared CICIDS2017 scenarios. The existing frozen hybrid IDS evaluates each flow.</p>
    </div>

    <form className={panel} onSubmit={e => { e.preventDefault(); void perform(async () => {
      setResult(null); setSelection(0); setPlan(await api.createProfile(profile));
    }); }}>
      <fieldset disabled={busy} className="space-y-4">
        <legend className="mb-3 text-sm font-semibold">Environment profile</legend>
        <div className="grid gap-4 sm:grid-cols-3">
          <label className="text-sm">Environment
            <select className={input} value={profile.environment} onChange={e => change({ ...profile, environment: e.target.value as EnvironmentProfile["environment"] })}>
              <option value="home">Personal / Home</option><option value="lab">College / Lab</option>
              <option value="small_organisation">Small organisation</option><option value="web_server">Web application / Server</option>
            </select>
          </label>
          <label className="text-sm">Approximate scale
            <select className={input} value={profile.scale} onChange={e => change({ ...profile, scale: e.target.value as EnvironmentProfile["scale"] })}>
              <option value="1-10">1–10 devices</option><option value="10-50">10–50 devices</option><option value="50+">50+ devices</option>
            </select>
          </label>
          <label className="text-sm">Internet exposure
            <select className={input} value={profile.exposure} onChange={e => change({ ...profile, exposure: e.target.value as EnvironmentProfile["exposure"] })}>
              <option value="internal">Internal only</option><option value="some_public">Some public services</option><option value="public">Public-facing</option>
            </select>
          </label>
        </div>
        <div className="flex flex-wrap gap-5">{services.map(([value, label]) =>
          <label key={value} className="flex items-center gap-2 text-sm"><input type="checkbox" checked={profile.services.includes(value)} onChange={e => change({
            ...profile, services: e.target.checked ? [...profile.services, value] : profile.services.filter(s => s !== value),
          })} />{label}</label>
        )}</div>
        <button className={button} type="submit">Preview scenarios</button>
      </fieldset>
    </form>

    {error && <p role="alert" className="text-sm text-red-300">{error}</p>}
    {busy && <p role="status" className="text-sm text-slate-300">Evaluating or loading prepared evidence…</p>}
    {plan && <section className={panel}>
      <h2 className="font-semibold">Selected scenarios</h2>
      <ul className="mt-3 space-y-2 text-sm">{plan.suite.map(s => <li key={s.name}>
        <span className="font-mono text-slate-200">{s.name}</span> — {s.reason} · {s.available ? `${s.flow_count} flows` : "Unavailable"}
      </li>)}</ul>
      {!!plan.unsupported_services.length && <p className="mt-3 text-sm text-amber-200">No prepared coverage: {plan.unsupported_services.join(", ")}. These services are not assessed.</p>}
      <p className="my-3 text-sm text-slate-400">Unknown-attack detection is not established. The unknown fixture contains benign anomaly challenges and measures false alerts.</p>
      <button className={button} disabled={busy || !ready} onClick={() => void perform(async () => {
        setResult(null); setSelection(0);
        const run = await api.runPlayground(plan.id);
        setResult(await api.playgroundResults(run.run_id)); setSavedId(String(run.run_id));
      })}>Run scenario suite</button>
      {!ready && <p className="mt-2 text-sm text-amber-200">The model must be ready before running scenarios.</p>}
    </section>}

    <form className="flex flex-wrap items-end gap-3" onSubmit={e => { e.preventDefault(); void perform(async () => {
      setResult(null); setPlan(null); setSelection(0); setResult(await api.playgroundResults(Number(savedId)));
    }); }}>
      <label className="text-sm text-slate-400">Saved run ID<input className={input} type="number" min="1" step="1" required value={savedId} onChange={e => setSavedId(e.target.value)} /></label>
      <button className={button} disabled={busy || !savedId}>Load saved result</button>
    </form>

    {result && <section className="space-y-4" aria-label="Scenario assessment">
      <div className={panel}>
        <h2 className="font-semibold">Scenario readiness · Run {result.run_id} · {result.status}</h2>
        <p className="mt-1 text-sm text-slate-400">Saved profile: {result.profile.environment?.replace(/_/g, " ")} · {result.profile.scale} devices · {result.profile.exposure?.replace(/_/g, " ")} · {result.profile.services?.join(", ") || "no selected services"}</p>
        {result.error && <p role="alert" className="mt-3 text-red-300">{result.error}</p>}
        {assessment && <>
          <p className="mt-4 text-3xl font-semibold">{assessment.score == null ? "Score unavailable" : `${assessment.score.toFixed(2)} / 100`}</p>
          <p className="mt-1 text-sm text-slate-400">Assessment: {assessment.status.replace(/_/g, " ")}. This score describes only this selected scenario suite; it is not a real-network security rating.</p>
          <dl className="my-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
            {[["Detected threats", assessment.detected], ["Missed threats", assessment.missed], ["False alerts", assessment.false_alerts], ["Correct benign", assessment.correct_benign]].map(([label, value]) => <div key={label}>
              <dt className="text-sm text-slate-400">{label}</dt><dd className="text-xl font-semibold">{value}</dd>
            </div>)}
          </dl>
          <p className="text-sm">Strongest tested areas: {assessment.strongest.join(", ") || "None"}.</p>
          <p className="mt-1 text-sm">Weakest tested areas / blind spots: {assessment.blind_spots.join(", ") || "None observed in these fixtures"}.</p>
          <p className="mt-3 text-sm text-slate-400">Score = 100 × ({assessment.weights.detection_weight} × mean attack-scenario recall + {assessment.weights.false_alert_weight} × benign specificity). Recall: {assessment.mean_scenario_recall == null ? "not applicable" : `${(100 * assessment.mean_scenario_recall).toFixed(2)}%`}; specificity: {assessment.benign_specificity == null ? "not applicable" : `${(100 * assessment.benign_specificity).toFixed(2)}%`}. Missing scenarios or absent attack/benign evidence suppress the score. Weakest/strongest areas use mean recall and specificity within each scenario.</p>
        </>}
        <p className="mt-4 text-sm">Scenario coverage: {result.coverage.executed ?? 0} / {result.coverage.selected ?? 0} selected scenarios executed.</p>
        <p className="mt-1 text-sm text-amber-200">Unavailable: {result.coverage.unavailable?.join(", ") || "None"}. Uncovered services: {result.coverage.unsupported_services?.join(", ") || "None selected"}. Unknown-attack detection: not established.</p>
        <p className="mt-3 text-sm text-slate-400">Small, prepared fixtures are demonstration evidence. {overlap} evaluated vectors exactly match deployed-training features; legacy source-row identity is uncertain. Synthetic communication metadata is not captured traffic. Use the locked held-out comparison for model metrics.</p>
      </div>
      {!!flows.length && <>
        <div className={`${panel} overflow-x-auto`}>
          <h2 className="mb-3 font-semibold">Scenario result matrix</h2>
          <table className="w-full text-left text-sm"><thead className="text-sm text-slate-400"><tr>
            <th scope="col">Scenario</th><th scope="col">Attack flows</th><th scope="col">Detected</th><th scope="col">Missed</th><th scope="col">Benign flows</th><th scope="col">False alerts</th>
          </tr></thead><tbody>{result.scenarios.map(s => <tr key={s.name} className="border-t border-slate-800">
            <th scope="row" className="py-3 font-mono font-normal">{s.name}</th>
            {[s.counts.malicious, s.counts.detected, s.counts.missed, s.counts.benign, s.counts.false_alerts].map((v, i) => <td key={i}>{v}</td>)}
          </tr>)}</tbody></table>
        </div>
        <RiskDistribution flows={flows.map(f => f.output)} />
        <div className={panel}>
          <h2 className="font-semibold">Flow evidence and explanation</h2>
          <label className="mt-3 block text-sm">Select evaluated flow<select className={input} value={selection} onChange={e => setSelection(Number(e.target.value))}>
            {flows.map((f, i) => <option key={i} value={i}>{f.scenario} #{f.seq} · {scenarioOutcome(f.truth_label, f.output.classification)}</option>)}
          </select></label>
          {selected && <div className="mt-3 space-y-3 text-sm">
            <p>Evaluation truth: <strong>{selected.truth_label}</strong> · {scenarioOutcome(selected.truth_label, selected.output.classification)}</p>
            <div className="flex gap-2"><ClassificationBadge value={selected.output.classification} /><RiskBadge level={selected.output.risk_level} /></div>
            <p>Supervised prediction: {selected.output.label} · confidence {(selected.output.confidence * 100).toFixed(2)}% · risk {selected.output.risk_score.toFixed(2)}.</p>
            <p>Anomaly score: {selected.output.anomaly_score.toFixed(5)}; recorded threshold: {selected.output.anomaly_threshold}. Known-confidence threshold: {result.context.thresholds?.known_confidence ?? "unavailable"}.</p>
            <p className="text-slate-300">{selected.output.classification === "UNKNOWN_SUSPICIOUS" ? unknownExplanation(selected.output.label) : selected.output.classification === "KNOWN_ATTACK" ? "The supervised attack prediction passed the known-confidence gate." : "The hybrid pipeline returned benign. A malicious evaluation label therefore counts as a missed threat."}</p>
            <p className="text-sm text-slate-400">TreeSHAP explains the supervised prediction, not Isolation Forest or the risk score. Evaluation truth is never a model input.</p>
            {selected.output.top_features.length ? <SignedContributions features={selected.output.top_features} label={selected.output.label} /> : <p className="text-sm text-slate-400">No TreeSHAP stored for benign decisions; this runner follows the replay policy of explaining suspicious flows.</p>}
          </div>}
        </div>
      </>}
    </section>}
  </div>;
}
