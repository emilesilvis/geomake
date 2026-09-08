import assert from 'node:assert/strict';
import test from 'node:test';
import { createLeaderboard } from '../leaderboard.js';

function storage() {
  const entries = new Map();
  return { getItem: key => entries.get(key) ?? null, setItem: (key, value) => entries.set(key, value) };
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
