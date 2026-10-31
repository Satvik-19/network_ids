# Network IDS console design - implemented 2026-10-31

The approved Network IDS 1.1.0 Hue language is implemented in the existing frontend.
See DEC-023 for authorization and TESTING.md for executed validation. Phase 5
research/features remain deferred. Backend, ML, API contracts, thresholds, dataset
fixtures, classifications and incident grouping are unchanged from a597863.

## Design and implementation

IBM Plex Sans400/500/600, IBM Plex Mono400/500,14px body and12px secondary metadata.
Charcoal/light CSS tokens,4px controls, flat sections, continuous metric strip,
120-180ms functional transitions, keyboard focus and reduced-motion support.
Desktop navigation becomes a rail; narrow navigation remains labelled and wraps.
Monitor leads with observed communications and grouped incidents; fixed-scale
risk and raw-count distribution support the evidence below. Existing incident
detail and Playground retain their requests/actions and use the same language.

Host graph: unique source/destination IP nodes, one directed edge per observed
pair, ports/count/max recorded risk in connection evidence. Append-only lane slots
persist across polling, selection and filters; a new run resets graph context.
No force simulation, port nodes, invented protocol or inferred physical topology.
Two-lane graphs fit narrow screens; mixed-role diagrams scroll locally. Host
controls and connection rows support keyboard selection. Selected edges retain
severity color and gain a dashed line rather than replacing risk with blue.
SVG uses existing React and browser APIs; no new library. Cytoscape package cleanup
was deliberately excluded from this visual change.

Risk axes stay0-100; null risk is unavailable. Count charts retain identical bars
for identical counts. SHAP bars share a symmetric extent across each flow's stored
features, align with zero, retain exact signed-value evidence and label XGBoost
raw-margin units. Outlined negatives and solid positives do not reinterpret the
hybrid verdict or anomaly score. Shared component covers incidents and Playground.

## Files

- frontend/src/tokens.css: frozen approved dark/light semantic values.
- frontend/tailwind.config.js: bridge existing utility names to those tokens.
- frontend/index.html and src/index.css: fonts, layout, controls, graph and SHAP.
- src/App.tsx: rail/navigation/theme presentation; original page/health behavior.
- src/lib/graph.ts and components/CommGraph.tsx: host aggregation and stable SVG.
- components/{AttackTimeline,RiskDistribution,SummaryCards,SecurityStatus,
  ReplayControls,IncidentList,TrafficTable,ui,SignedContributions}.tsx.
- pages/{SecurityMonitor,IncidentDetail,Playground}.tsx: layout and shared visuals.
- tests/{graph,charts}.test.mjs: graph/scale/evidence regression checks.

## External design outputs

All nine remain under `C:/Users/BIT/.codex/skills/network-ids-design/`:
design-model.yaml, SKILL.md, references/{tokens,components,platform-mapping}.md,
preview.html, component-library.html, landing-page.html and app-screen.html.
They were updated directly and validated, and are intentionally outside this Git
repository. Frontend operation does not depend on their presence.

## Validation and review

10 frontend tests PASS; standalone TypeScript PASS; production build PASS.
142 Python tests PASS in226.99s. Original live Uvicorn gate PASS using disposable
DB/evidence. Official Hue PASS0errors/0warnings; Windows npx YAML subprocess was
skipped, covered by independent strict duplicate-key YAML parsing. Nine-file UTF-8
and token invariants PASS. See TESTING.md for commands and browser assertions.

All four previews inspected in desktop and375/390px narrow views, dark/light.
Working application Monitor, incidents and Playground inspected in both themes
and narrow/desktop layouts. Corrected clipped graph/SHAP/count specimens, misplaced
theme controls, overview gaps, severity readability and crowded incident rows.

Screenshots live outside Git in:
`C:/Users/BIT/.codex/visualizations/2026/10/31/01a190b1-c153-7631-8524-fe5cd5593b3e/`

- nids-application-dark.png / nids-application-light.png
- nids-application-narrow.png / nids-incident-light.png
- nids-playground-light.png
- nids-preview-dark.png / nids-overview-dark.png
- nids-components-dark.png / nids-narrative-dark.png

Remaining: existing >500kB JS build warning, Internet-loaded Plex fonts with local
fallbacks, local scrolling for wide evidence/complex diagrams. No deployment,
font vendoring, dependency cleanup or enterprise-scale graph work was performed.
Unrelated pre-existing untracked files are preserved and excluded from commits.
