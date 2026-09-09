import assert from 'node:assert/strict';
import test from 'node:test';
import { createLeaderboard } from '../leaderboard.js';

function storage() {
  const entries = new Map();
  return { getItem: key => entries.get(key) ?? null, setItem: (key, value) => entries.set(key, value), removeItem: key => entries.delete(key) };
}
const unavailable = () => { throw new Error('blocked'); };

test('a saved browser token survives reloads, while public reads carry no token', async () => {
  const saved = storage();
  const requests = [];
  const send = async (url, options) => {
    requests.push({ url, ...options });
    return Response.json({ name: 'Ada', solved: [], completedThrough: 0 });
  };
  const client = createLeaderboard('https://api.example', 'edition', [() => saved], send);
  assert.equal(await client.loadPlayer(), null);
  await client.savePlayer('Ada');
  const token = requests[0].headers.Authorization;
  assert.match(token, /^Bearer [a-f0-9]{64}$/);
  const reloaded = createLeaderboard('https://api.example', 'edition', [() => saved], send);
  await reloaded.check(1, '80/2');
  assert.equal(requests[1].headers.Authorization, token);
  assert.deepEqual(JSON.parse(requests[1].body), { day: 1, answer: '80/2' });
  await reloaded.loadBoard();
  assert.equal(requests[2].headers.Authorization, undefined);
  assert.equal(requests[2].credentials, 'omit');
  assert.equal(await createLeaderboard('https://another.example', 'edition', [() => saved], send).loadPlayer(), null);
});

test('tab storage works when persistent storage is blocked; no storage never creates a stranded player', async () => {
  const tab = storage();
  let calls = 0;
  const send = async () => { calls++; return Response.json({}); };
  const client = createLeaderboard('https://api.example', 'edition', [unavailable, () => tab], send);
  await client.savePlayer('Ada');
  assert.equal(calls, 1);
  const blocked = createLeaderboard('https://api.example', 'edition', [unavailable], send);
  assert.throws(() => blocked.savePlayer('Ada'), /Allow browser storage/);
  assert.equal(calls, 1);
});

test('registration retries reuse the token even when the first response is lost', async () => {
  const saved = storage();
  const tokens = [];
  const send = async (_, options) => {
    tokens.push(options.headers.Authorization);
    if (tokens.length === 1) throw new Error('offline');
    return Response.json({ name: 'Ada' });
  };
  const client = createLeaderboard('https://api.example', 'edition', [() => saved], send);
  await assert.rejects(client.savePlayer('Ada'), /offline/);
  await client.savePlayer('Ada');
  assert.equal(tokens[0], tokens[1]);
});

test('invalid credentials restore the name form, while server errors remain visible', async () => {
  const saved = storage();
  saved.setItem('geomake:player:https://api.example', 'a'.repeat(64));
  const client = createLeaderboard('https://api.example', 'edition', [() => saved], async () => Response.json({ error: 'Register again' }, { status: 401 }));
  assert.equal(await client.loadPlayer(), null);
  const offline = createLeaderboard('https://api.example', 'edition', [() => saved], async () => Response.json({ error: 'Try again' }, { status: 503 }));
  await assert.rejects(offline.loadPlayer(), /Try again/);
});

test('recovery validates before saving, updates both stores, and never sends a token in a URL', async () => {
  const persistent = storage(), tab = storage();
  const key = 'geomake:player:https://api.example';
  persistent.setItem(key, 'a'.repeat(64));
  tab.setItem(key, 'a'.repeat(64));
  const requests = [];
  const client = createLeaderboard('https://api.example', 'edition', [() => persistent, () => tab], async (url, options) => {
    requests.push({ url, ...options });
    return Response.json({ name: 'Emile', solved: [1], completedThrough: 1 });
  });
  await assert.rejects(client.restorePlayer('Emile'), /recovery code/i);
  assert.equal(requests.length, 0);
  await client.restorePlayer('b'.repeat(64));
  assert.equal(persistent.getItem(key), 'b'.repeat(64));
  assert.equal(tab.getItem(key), 'b'.repeat(64));
  assert.equal(requests[0].url.includes('b'.repeat(64)), false);
  assert.equal(requests[0].headers.Authorization, `Bearer ${'b'.repeat(64)}`);
  const offline = createLeaderboard('https://api.example', 'edition', [() => persistent], async () => { throw new Error('offline'); });
  await assert.rejects(offline.restorePlayer('c'.repeat(64)), /offline/);
  assert.equal(persistent.getItem(key), 'b'.repeat(64));
});

test('recovery reports when an older persistent token cannot be replaced instead of pretending to log in', async () => {
  const readOnly = { getItem: () => 'a'.repeat(64), setItem: unavailable };
  const tab = storage();
  const client = createLeaderboard('https://api.example', 'edition', [() => readOnly, () => tab], async () => Response.json({ name: 'Emile' }));
  await assert.rejects(client.restorePlayer('b'.repeat(64)), /browser storage/i);
});

test('logging out clears both browser tokens but keeps saved drafts and the recovery code valid on the server', async () => {
  const persistent = storage(), tab = storage();
  const key = 'geomake:player:https://api.example';
  for (const saved of [persistent, tab]) {
    saved.setItem(key, 'a'.repeat(64));
    saved.setItem('geomake:edition:player:emile:1:answer', '40');
  }
  let calls = 0;
  const client = createLeaderboard('https://api.example', 'edition', [() => persistent, () => tab], async () => { calls++; return Response.json({ name: 'Emile' }); });
  const code = client.recoveryCode();
  client.logOut();
  assert.equal(await client.loadPlayer(), null);
  assert.equal(calls, 0);
  assert.equal(persistent.getItem(key), null);
  assert.equal(tab.getItem(key), null);
  assert.equal(persistent.getItem('geomake:edition:player:emile:1:answer'), '40');
  assert.equal((await client.restorePlayer(code)).name, 'Emile');
});
