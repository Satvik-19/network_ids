import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import ts from 'typescript';
const source = await readFile(new URL('../src/lib/charts.ts', import.meta.url), 'utf8');
const js = ts.transpileModule(source, {compilerOptions:{module:ts.ModuleKind.ESNext}}).outputText;
const {signedContributions, RISK_DOMAIN} = await import(`data:text/javascript;base64,${Buffer.from(js).toString('base64')}`);

test('risk uses one fixed scale for every run', () => assert.deepEqual(RISK_DOMAIN, [0,100]));
test('signed SHAP geometry preserves direction, proportion and zero without clipping', () => {
  const {extent, bars} = signedContributions([2.799, -0.3039, 0]);
  assert.equal(extent, 2.799);
  assert.deepEqual(bars[0], {left:50,width:50});
  assert.equal(bars[1].left + bars[1].width, 50);
  assert.ok(Math.abs(bars[1].width / bars[0].width - 0.3039 / 2.799) < 1e-12);
  assert.deepEqual(bars[2], {left:50,width:0});
  assert.equal(signedContributions([]).extent, 1);
});
