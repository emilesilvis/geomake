import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import { DatabaseSync } from 'node:sqlite';
import test from 'node:test';
import { createApp } from '../api.js';
import { createLeaderboard } from '../../reader/leaderboard.js';

const catalog = { edition: 'edition', puzzles: [
  { id: 'one', answer: 40 }, { id: 'two', answer: Math.PI }, { id: 'three', answer: 7 },
] };
const alice = 'a'.repeat(64), bob = 'b'.repeat(64), charlie = 'c'.repeat(64);

function setup(t) {
  const sqlite = new DatabaseSync(':memory:');
  const migrations = new URL('../migrations/', import.meta.url);
  for (const file of readdirSync(migrations).filter(name => name.endsWith('.sql')).sort()) {
    sqlite.exec(readFileSync(new URL(file, migrations), 'utf8'));
  }
  t.after(() => sqlite.close());
  const db = { async batch(statements) {
    sqlite.exec('BEGIN');
    try {
      const results = [];
      for (const statement of statements) results.push(await statement.run());
      sqlite.exec('COMMIT');
      return results;
    } catch (error) { sqlite.exec('ROLLBACK'); throw error; }
  }, prepare(sql) { return { bind(...args) {
    const statement = sqlite.prepare(sql);
    return {
      first: async () => statement.get(...args) ?? null,
      all: async () => ({ results: statement.all(...args) }),
      run: async () => statement.run(...args),
    };
  } }; } };
  let app = createApp(catalog);
  return {
    sqlite,
    send: (url, options) => app.fetch(new Request(url, options), { DB: db }),
    replaceCatalog(next) { app = createApp(next); },
    async request(path, { token, data, origin = 'https://puzzles.example', edition = 'edition', method } = {}) {
      const headers = { Origin: origin };
      if (token) headers.Authorization = `Bearer ${token}`;
      if (data !== undefined) headers['Content-Type'] = 'application/json';
      const request = new Request(`https://api.example${path}?edition=${edition}`, {
        method: method || (data === undefined ? 'GET' : 'POST'), headers,
        body: data === undefined ? undefined : JSON.stringify(data),
      });
      const response = await app.fetch(request, { DB: db, ALLOWED_ORIGINS: 'https://puzzles.example' });
      return { status: response.status, headers: response.headers, body: response.status === 204 ? null : await response.json() };
    },
  };
}

test('registration is idempotent; private tokens and other players cannot be overwritten by names', async t => {
  const { request, sqlite } = setup(t);
  const first = await request('/player', { token: alice, data: { name: '  Alice  ' } });
  assert.equal(first.status, 200);
  assert.equal(first.body.name, 'Alice');
  assert.equal(first.body.completedThrough, 0);
  const retry = await request('/player', { token: alice, data: { name: 'Alicia' } });
  assert.equal(retry.body.id, first.body.id);
  const second = await request('/player', { token: bob, data: { name: 'Alicia', id: first.body.id, completedThrough: 21 } });
  assert.notEqual(second.body.id, first.body.id);
  assert.equal(second.body.completedThrough, 0);
  assert.equal(sqlite.prepare('SELECT count(*) AS n FROM players').get().n, 2);
  const stored = sqlite.prepare('SELECT token_hash FROM players WHERE id=?').get(first.body.id).token_hash;
  assert.notEqual(stored, alice);
  assert.deepEqual((await request('/leaderboard')).body.players, []);
  await request('/check', { token: alice, data: { day: 1, answer: '40' } });
  const board = await request('/leaderboard');
  assert.equal(board.body.players.length, 1);
  assert.equal(JSON.stringify(board.body).includes(stored), false);
  assert.deepEqual(Object.keys(board.body.players[0]).sort(), ['id', 'name', 'rank', 'solved']);
});

test('a recovery code restores Emile’s eight solves after browser storage is lost, without changing Greyfox’s fourteen', async t => {
  const app = setup(t);
  app.replaceCatalog({ edition: 'edition', puzzles: Array.from({ length: 21 }, (_, i) => ({ id: `day-${i + 1}`, answer: 40 })) });
  const saved = new Map();
  const store = { getItem: key => saved.get(key) ?? null, setItem: (key, value) => saved.set(key, value) };
  const client = () => createLeaderboard('https://api.example', 'edition', [() => store], app.send);
  const original = client();
  const emile = await original.savePlayer('Emile');
  for (let day = 1; day <= 8; day++) await original.check(day, '40');
  await app.request('/player', { token: bob, data: { name: 'Greyfox' } });
  for (let day = 1; day <= 14; day++) await app.request('/check', { token: bob, data: { day, answer: '40' } });
  const code = original.recoveryCode();
  assert.match(code, /^(?:[a-f0-9]{8}-){7}[a-f0-9]{8}$/);
  saved.clear();
  const fresh = client();
  assert.equal(await fresh.loadPlayer(), null);
  assert.equal((await fresh.savePlayer('Emile')).completedThrough, 0, 'a public name alone is not a login');
  const recovered = await fresh.restorePlayer(`  ${code.toUpperCase()}  `);
  assert.equal(recovered.id, emile.id);
  assert.equal(recovered.completedThrough, 8);
  assert.equal((await client().loadPlayer()).completedThrough, 8, 'the recovered login survives navigation');
  assert.equal((await app.request('/player', { token: bob })).body.completedThrough, 14);
  assert.deepEqual((await app.request('/leaderboard')).body.players.map(row => [row.name, row.solved]), [['Greyfox', 14], ['Emile', 8]]);
  const before = fresh.recoveryCode();
  await assert.rejects(fresh.restorePlayer('f'.repeat(64)), /recovery code/i);
  assert.equal(fresh.recoveryCode(), before, 'a rejected code cannot replace the current login');
  assert.equal((await fresh.loadPlayer()).completedThrough, 8);
});

test('an operator can reconnect a replacement browser token while preserving the original login and solves', async t => {
  const { request, sqlite } = setup(t);
  const original = await request('/player', { token: alice, data: { name: 'Emile' } });
  await request('/check', { token: alice, data: { day: 1, answer: '40' } });
  const replacement = await request('/player', { token: bob, data: { name: 'Emile' } });
  sqlite.prepare('UPDATE player_tokens SET player_id=? WHERE player_id=?').run(original.body.id, replacement.body.id);
  assert.equal((await request('/player', { token: bob })).body.id, original.body.id);
  assert.equal((await request('/player', { token: alice })).body.completedThrough, 1);
  const renamed = await request('/player', { token: bob, data: { name: 'Emile restored' } });
  assert.equal(renamed.body.id, original.body.id);
  assert.equal(renamed.body.completedThrough, 1);
  assert.equal((await request('/player', { token: alice })).body.name, 'Emile restored');
  assert.equal(sqlite.prepare('SELECT count(*) AS n FROM solves').get().n, 1);
});

test('the token migration preserves historical solves and logins created by an old Worker during deployment', async t => {
  const { request, sqlite } = setup(t);
  const original = await request('/player', { token: alice, data: { name: 'Emile' } });
  await request('/check', { token: alice, data: { day: 1, answer: '40' } });
  const before = sqlite.prepare('SELECT * FROM solves').all();
  sqlite.exec('DROP TABLE player_tokens');
  sqlite.exec(readFileSync(new URL('../migrations/0002_player_tokens.sql', import.meta.url), 'utf8'));
  assert.deepEqual(sqlite.prepare('SELECT * FROM solves').all(), before);
  assert.equal((await request('/player', { token: alice })).body.id, original.body.id);
  // Simulate a registration performed by the pre-migration Worker.
  sqlite.exec('DELETE FROM player_tokens');
  assert.equal((await request('/player', { token: alice })).body.completedThrough, 1);
});

test('only correct consecutive answers advance progress, and retries count once', async t => {
  const { request } = setup(t);
  await request('/player', { token: alice, data: { name: 'Alice' } });
  assert.equal((await request('/check', { token: alice, data: { day: 2, answer: 'pi' } })).status, 409);
  const wrong = await request('/check', { token: alice, data: { day: 1, answer: '41', correct: true } });
  assert.equal(wrong.body.correct, false);
  assert.equal(wrong.body.player.completedThrough, 0);
  assert.deepEqual((await request('/leaderboard')).body.players, []);
  const right = await request('/check', { token: alice, data: { day: 1, answer: '80/2' } });
  assert.equal(right.body.correct, true);
  assert.equal(right.body.player.completedThrough, 1);
  assert.deepEqual((await request('/leaderboard')).body.players, [
    { id: right.body.player.id, name: 'Alice', solved: 1, rank: 1 },
  ]);
  await request('/check', { token: alice, data: { day: 1, answer: '40' } });
  const changedDraft = await request('/check', { token: alice, data: { day: 1, answer: 'wrong' } });
  assert.equal(changedDraft.status, 400);
  const next = await request('/check', { token: alice, data: { day: 2, answer: '3.14' } });
  assert.equal(next.body.player.completedThrough, 2);
  assert.deepEqual(next.body.player.solved, [1, 2]);
  assert.equal((await request('/leaderboard')).body.players[0].solved, 2);
});

test('names, authentication, CORS, stale editions and oversized requests are validated', async t => {
  const { request } = setup(t);
  assert.equal((await request('/player')).status, 401);
  assert.equal((await request('/player', { token: alice })).status, 401);
  for (const name of ['', ' '.repeat(3), 'x'.repeat(41), 'A\u202eB', 42]) {
    assert.equal((await request('/player', { token: alice, data: { name } })).status, 400);
  }
  assert.equal((await request('/player', { token: alice, data: { name: 'x'.repeat(3000) } })).status, 413);
  assert.equal((await request('/leaderboard', { origin: 'https://unrelated.example' })).status, 403);
  assert.equal((await request('/leaderboard', { edition: 'stale' })).status, 409);
  const preflight = await request('/check', { method: 'OPTIONS' });
  assert.equal(preflight.status, 204);
  assert.equal(preflight.headers.get('Access-Control-Allow-Origin'), 'https://puzzles.example');
  assert.equal(preflight.headers.get('Access-Control-Allow-Credentials'), null);
});

test('public ranks share ties; another player cannot submit using a public player ID', async t => {
  const { request } = setup(t);
  for (const [token, name] of [[alice, 'Alice'], [bob, 'Bob'], [charlie, '<img src=x onerror=alert(1)>']]) {
    await request('/player', { token, data: { name } });
  }
  await request('/check', { token: alice, data: { day: 1, answer: '40' } });
  await request('/check', { token: alice, data: { day: 2, answer: 'pi' } });
  await request('/check', { token: bob, data: { day: 1, answer: '40' } });
  await request('/check', { token: bob, data: { day: 2, answer: 'pi' } });
  assert.equal((await request('/leaderboard')).body.players.length, 2);
  await request('/check', { token: charlie, data: { day: 1, answer: '40' } });
  const board = (await request('/leaderboard')).body;
  assert.deepEqual(board.players.map(row => row.rank), [1, 1, 3]);
  assert.deepEqual(board.players.map(row => row.solved), [2, 2, 1]);
  assert.equal((await request('/check', { token: board.players[0].id, data: { day: 2, answer: 'pi' } })).status, 401);
  assert.deepEqual((await request('/player', { token: charlie })).body.solved, [1]);
});

test('appending puzzles preserves solves; changing a question does not inherit its predecessor’s solve', async t => {
  const app = setup(t);
  await app.request('/player', { token: alice, data: { name: 'Alice' } });
  await app.request('/check', { token: alice, data: { day: 1, answer: '40' } });
  app.replaceCatalog({ edition: 'extended', puzzles: [...catalog.puzzles, { id: 'four', answer: 9 }] });
  const extended = await app.request('/player', { token: alice, edition: 'extended' });
  assert.equal(extended.body.completedThrough, 1);
  assert.equal((await app.request('/leaderboard', { edition: 'extended' })).body.players[0].solved, 1);
  app.replaceCatalog({ edition: 'changed', puzzles: [{ id: 'one-revised', answer: 42 }, ...catalog.puzzles.slice(1)] });
  const changed = await app.request('/player', { token: alice, edition: 'changed' });
  assert.equal(changed.body.completedThrough, 0);
  assert.deepEqual(changed.body.solved, []);
  assert.deepEqual((await app.request('/leaderboard', { edition: 'changed' })).body.players, []);
});
