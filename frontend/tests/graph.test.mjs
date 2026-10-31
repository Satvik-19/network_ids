import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import ts from 'typescript';

const source = await readFile(new URL('../src/lib/graph.ts', import.meta.url), 'utf8');
const js = ts.transpileModule(source, {compilerOptions: {module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2020}}).outputText;
const graph = await import(`data:text/javascript;base64,${Buffer.from(js).toString('base64')}`);
const flows = [
  {source:'s', destination:'d', service_port:80, classification:'BENIGN', risk_level:'LOW', risk_score:2.5},
  {source:'s', destination:'d', service_port:80, classification:'KNOWN_ATTACK', risk_level:'CRITICAL', risk_score:90},
  {source:'s', destination:'d', service_port:443, classification:'KNOWN_ATTACK', risk_level:'MEDIUM', risk_score:50},
];

test('production edge tones distinguish false flags and preserve highest risk', () => {
  assert.equal(graph.edgeTone(graph.buildGraphData([flows[0]]).edges[0]), 'neutral');
  assert.equal(graph.edgeTone(graph.buildGraphData([flows[2]]).edges[0]), 'suspicious');
  assert.equal(graph.edgeTone(graph.buildGraphData(flows).edges[0]), 'high');
});

test('selection resolves hosts, services and edges to their actual evidence', () => {
  assert.equal(typeof graph.relatedFlows, 'function');
  assert.equal(graph.relatedFlows(flows, 's').length, 3);
  assert.equal(graph.relatedFlows(flows, 'd:80').length, 2);
  assert.equal(graph.relatedFlows(flows, 's->d:443').length, 1);
  assert.equal(graph.relatedFlows(flows, 'missing').length, 0);
  assert.equal(graph.relatedFlows(flows, 's->d').length, 3);
});

test('only actual hosts are nodes and services aggregate on directed relationships', () => {
  const data = graph.buildGraphData(flows);
  assert.deepEqual(data.nodes.map(n => n.id).sort(), ['d', 's']);
  assert.equal(data.edges.length, 1);
  assert.deepEqual(data.edges[0].ports, [80, 443]);
  assert.equal(data.edges[0].flow_count, 3);
  assert.equal(data.edges[0].risk_score, 90);
  assert.equal(data.edges[0].target, 'd');
  const reverse = graph.buildGraphData([...flows, {...flows[0], source:'d', destination:'s'}]);
  assert.equal(reverse.edges.length, 2);
});

test('host positions survive polling, filtering and new hosts without overlap', () => {
  const data = graph.buildGraphData(flows);
  const positions = graph.placeHosts(data, {});
  const expanded = graph.buildGraphData([...flows, {...flows[0], source:'another'}]);
  const next = graph.placeHosts(expanded, positions);
  assert.deepEqual(next.s, positions.s);
  assert.deepEqual(next.d, positions.d);
  assert.notDeepEqual(next.another, next.s);
  assert.deepEqual(graph.placeHosts(data, next).s, positions.s);
  assert.deepEqual(graph.placeHosts({...data, edges:[]}, next).d, positions.d);
  assert.deepEqual(graph.placeHosts(graph.buildGraphData([...flows].reverse()), {}), positions);
});

test('missing hosts never invent nodes or edges; unavailable risk stays unavailable', () => {
  assert.deepEqual(graph.buildGraphData([{...flows[0], source:null}]), {nodes:[],edges:[]});
  const data = graph.buildGraphData([{...flows[0], risk_score:null, classification:null, service_port:null}]);
  assert.equal(data.edges[0].risk_score, null);
  assert.equal(data.edges[0].suspicious, false);
  assert.deepEqual(data.edges[0].ports, []);
});
