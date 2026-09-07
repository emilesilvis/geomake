import assert from 'node:assert/strict';
import test from 'node:test';
import { createProgress } from '../progress.js';

function storage() {
  const entries = new Map();
  return {
    getItem: key => entries.get(key) ?? null,
    setItem: (key, value) => entries.set(key, value),
    clear: () => entries.clear(),
  };
}

const unavailable = () => { throw new Error('Storage blocked'); };

test('only consecutive completed puzzles unlock the next one', () => {
  const saved = storage();
  const progress = createProgress('edition', 3, [() => saved]);
  assert.equal(progress.completedThrough(), 0);
  progress.saveAnswer(1, '40');
  assert.equal(progress.completedThrough(), 0, 'an entered answer is not a checked answer');
  assert.equal(progress.markSolved(2), false, 'cannot skip the first puzzle');
  assert.equal(progress.markSolved(1), true);
  assert.equal(progress.completedThrough(), 1);
  assert.equal(progress.markSolved(3), false, 'cannot skip the second puzzle');
  assert.equal(progress.markSolved(2), true);
  assert.equal(progress.markSolved(3), true);
  assert.equal(progress.completedThrough(), 3);
  for (const day of [0, -1, 1.5, 4, NaN]) assert.equal(progress.markSolved(day), false);
});

test('completion survives reloads and editing an earlier answer, scoped to its edition', () => {
  const saved = storage();
  const stores = [() => saved];
  const original = createProgress('original', 3, stores);
  original.saveAnswer(1, '80/2');
  original.markSolved(1);
  const reloaded = createProgress('original', 3, stores);
  assert.equal(reloaded.loadAnswer(1), '80/2');
  assert.equal(reloaded.completedThrough(), 1);
  reloaded.saveAnswer(1, 'wrong');
  assert.equal(reloaded.completedThrough(), 1);
  assert.equal(reloaded.markSolved(1), true, 'a solved puzzle can be checked again');
  const changed = createProgress('changed', 3, stores);
  assert.equal(changed.completedThrough(), 0);
  assert.equal(changed.loadAnswer(1), '');
});

test('existing drafts remain available and completion markers must be consecutive', () => {
  const saved = storage();
  saved.setItem('geomake:edition:1:answer', '40');
  saved.setItem('geomake:edition:1:solved', 'garbage');
  saved.setItem('geomake:edition:2:solved', 'true');
  const progress = createProgress('edition', 3, [() => saved]);
  assert.equal(progress.loadAnswer(1), '40');
  assert.equal(progress.completedThrough(), 0);
  progress.markSolved(1);
  assert.equal(progress.completedThrough(), 2);
});

test('tab storage preserves progress when persistent storage is unavailable', () => {
  const tab = storage();
  const stores = [unavailable, () => tab];
  const progress = createProgress('edition', 3, stores);
  progress.saveAnswer(1, '40');
  assert.equal(progress.markSolved(1), true);
  const reloaded = createProgress('edition', 3, stores);
  assert.equal(reloaded.loadAnswer(1), '40');
  assert.equal(reloaded.completedThrough(), 1);
});

test('failed writes do not unlock a puzzle that would be locked after navigation', () => {
  const progress = createProgress('edition', 3, [unavailable, unavailable]);
  assert.equal(progress.loadAnswer(1), '');
  assert.equal(progress.saveAnswer(1, '40'), false);
  assert.equal(progress.markSolved(1), false);
  assert.equal(progress.completedThrough(), 0);
});

test('progress reflects completions from other pages and cleared storage', () => {
  const persistent = storage();
  const tab = storage();
  const current = createProgress('edition', 3, [() => persistent, () => tab]);
  const otherTab = createProgress('edition', 3, [() => persistent]);
  otherTab.markSolved(1);
  assert.equal(current.completedThrough(), 1);
  persistent.clear();
  assert.equal(current.completedThrough(), 0);
});
