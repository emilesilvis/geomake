import assert from 'node:assert/strict';
import test from 'node:test';
import { evaluateAnswer, matchesAnswer } from '../answer.js';

test('accepts exact geometry answers and ordinary arithmetic precedence', () => {
  for (const [input, expected] of [
    ['80/2', 40], ['16 − 4π', 16 - 4 * Math.PI], ['2sqrt(2)', 2 * Math.sqrt(2)],
    ['π × (14/2)²', 49 * Math.PI], ['(3+2)(4-1)', 15], ['-2^2', -4],
    ['2^3^2', 512], ['2^-3', 0.125], ['√(9) + .5', 3.5],
    ['4e1 cm²', 40], ['40 sq. cm', 40], ['40 cm^2', 40],
  ]) assert.ok(Math.abs(evaluateAnswer(input) - expected) < 1e-10, input);
});

test('accepts two decimal places without accepting materially wrong answers', () => {
  assert.equal(matchesAnswer('153.94', 49 * Math.PI), true);
  assert.equal(matchesAnswer('153.93', 49 * Math.PI), false);
  assert.equal(matchesAnswer('39.9', 40), false);
});

test('rejects code, malformed arithmetic and unbounded calculations', () => {
  for (const input of [
    '', '1 2', '2..3', '1.2.3', 'Math.PI', 'alert(1)', 'globalThis', '0x28',
    '2;40', '2,40', '2=', 'sqrt(-1)', '1/0', '2^65', '10^20', '1e999',
    '(2+3', '2+3)', '*2', '()','('.repeat(33) + '1' + ')'.repeat(33), '1'.repeat(161),
  ]) assert.throws(() => evaluateAnswer(input), undefined, input);
});
