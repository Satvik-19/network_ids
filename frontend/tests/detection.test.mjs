import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import ts from 'typescript';

async function load() {
  const path = new URL('../src/lib/detection.ts', import.meta.url);
  assert.ok(existsSync(path), 'Shared detection display semantics are missing');
  const js = ts.transpileModule(readFileSync(path, 'utf8'), {
    compilerOptions: {module:ts.ModuleKind.ESNext, target:ts.ScriptTarget.ES2020},
  }).outputText;
  return import(`data:text/javascript;base64,${Buffer.from(js).toString('base64')}`);
}

test('anomaly display uses recorded threshold and preserves missing history', async () => {
  const {isAnomalyFlagged} = await load();
  assert.equal(isAnomalyFlagged(-0.1, -0.09), true);
  assert.equal(isAnomalyFlagged(-0.1, -0.12), false);
  assert.equal(isAnomalyFlagged(-0.09, -0.09), false);
  assert.equal(isAnomalyFlagged(-0.1, null), null);
  assert.equal(isAnomalyFlagged(null, -0.09), null);
});

test('unknown explanation distinguishes benign and low-confidence attack predictions', async () => {
  const {unknownExplanation} = await load();
  assert.match(unknownExplanation('BENIGN'), /predicted benign/);
  const uncertain = unknownExplanation('DDoS');
  assert.match(uncertain, /DDoS/);
  assert.match(uncertain, /without sufficient confidence/);
  assert.doesNotMatch(uncertain, /predicted benign/);
});
