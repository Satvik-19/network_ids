import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import ts from 'typescript';
import cytoscape from 'cytoscape';

const source = await readFile(new URL('../src/lib/graph.ts', import.meta.url), 'utf8');
const js = ts.transpileModule(source, {compilerOptions: {module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2020}}).outputText;
const graph = await import(`data:text/javascript;base64,${Buffer.from(js).toString('base64')}`);
const flows = [
  {source:'s', destination:'d', service_port:80, classification:'BENIGN', risk_level:'LOW', risk_score:2.5},
  {source:'s', destination:'d', service_port:80, classification:'KNOWN_ATTACK', risk_level:'CRITICAL', risk_score:90},
  {source:'s', destination:'d', service_port:443, classification:'KNOWN_ATTACK', risk_level:'MEDIUM', risk_score:50},
];

test('production risk selectors match boolean edge attributes', () => {
  const data = graph.buildGraphData(flows);
  const cy = cytoscape({headless:true, elements:[
    ...data.nodes.map(n=>({data:n})), ...data.edges.map(e=>({data:e})),
  ]});
  try {
    assert.equal(typeof graph.SUSPICIOUS_EDGE_SELECTOR, 'string');
    assert.equal(cy.edges(graph.SUSPICIOUS_EDGE_SELECTOR).length, 2);
    assert.equal(cy.edges(graph.HIGH_RISK_EDGE_SELECTOR).length, 1);
  } finally { cy.destroy(); }
});

test('selection resolves hosts, services and edges to their actual evidence', () => {
  assert.equal(typeof graph.relatedFlows, 'function');
  assert.equal(graph.relatedFlows(flows, 's').length, 3);
  assert.equal(graph.relatedFlows(flows, 'd:80').length, 2);
  assert.equal(graph.relatedFlows(flows, 's->d:443').length, 1);
  assert.equal(graph.relatedFlows(flows, 'missing').length, 0);
});
