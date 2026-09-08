import { matchesAnswer } from '../reader/answer.js';

class HttpError extends Error {
  constructor(status, message) { super(message); this.status = status; }
}

export function createApp(catalog) {
  const ids = catalog.puzzles.map(puzzle => puzzle.id);
  const placeholders = ids.map(() => '?').join(',');

  async function player(request, db, required = true) {
    const token = /^Bearer ([a-f0-9]{64})$/.exec(request.headers.get('Authorization') || '')?.[1];
    if (!token) throw new HttpError(401, 'Enter your name to save progress.');
    const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(token));
    const hash = Array.from(new Uint8Array(digest), byte => byte.toString(16).padStart(2, '0')).join('');
    const row = await db.prepare('SELECT id, name FROM players WHERE token_hash = ?').bind(hash).first();
    if (!row && required) throw new HttpError(401, 'Enter your name to save progress.');
    return { row, hash };
  }

  async function profile(db, row) {
    const { results } = await db.prepare('SELECT puzzle_id FROM solves WHERE player_id = ?').bind(row.id).all();
    const solvedIds = new Set(results.map(result => result.puzzle_id));
    const solved = ids.flatMap((id, index) => solvedIds.has(id) ? [index + 1] : []);
    let completedThrough = 0;
    while (completedThrough < ids.length && solvedIds.has(ids[completedThrough])) completedThrough++;
    return { id: row.id, name: row.name, solved, completedThrough };
  }

  async function body(request) {
    if (!request.headers.get('Content-Type')?.startsWith('application/json')) {
      throw new HttpError(415, 'Send JSON.');
    }
    // Bound the actual stream, including chunked requests with no Content-Length.
    const reader = request.body?.getReader();
    if (!reader) throw new HttpError(400, 'Missing request body.');
    const chunks = [];
    let size = 0;
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      size += value.length;
      if (size > 2048) { await reader.cancel(); throw new HttpError(413, 'Request is too large.'); }
      chunks.push(value);
    }
    try {
      const bytes = new Uint8Array(size);
      let offset = 0;
      for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.length; }
      const value = JSON.parse(new TextDecoder().decode(bytes));
      if (!value || Array.isArray(value) || typeof value !== 'object') throw new Error();
      return value;
    } catch { throw new HttpError(400, 'Invalid JSON.'); }
  }

  async function route(request, env) {
    const url = new URL(request.url);
    if (url.searchParams.get('edition') !== catalog.edition) {
      throw new HttpError(409, 'The puzzles have been updated. Reload this page.');
    }
    if (request.method === 'GET' && url.pathname === '/leaderboard') {
      const { results } = await env.DB.prepare(`
        SELECT p.id, p.name, COUNT(s.puzzle_id) AS solved
        FROM players p LEFT JOIN solves s ON s.player_id = p.id AND s.puzzle_id IN (${placeholders})
        GROUP BY p.id ORDER BY solved DESC, p.name COLLATE NOCASE, p.id LIMIT 100
      `).bind(...ids).all();
      let rank = 0;
      return { total: ids.length, players: results.map((row, i) => {
        if (i === 0 || row.solved !== results[i - 1].solved) rank = i + 1;
        return { ...row, rank };
      }) };
    }
    if (request.method === 'POST' && url.pathname === '/player') {
      const data = await body(request);
      const name = typeof data.name === 'string' ? data.name.normalize('NFC').trim().replace(/\s+/g, ' ') : '';
      if (!name || [...name].length > 40 || /[\p{Cc}\p{Cf}]/u.test(name)) {
        throw new HttpError(400, 'Use a name between 1 and 40 characters.');
      }
      const { hash } = await player(request, env.DB, false);
      // The browser saves its random token before this request, so retrying a
      // lost registration response updates the same player rather than duplicating it.
      await env.DB.prepare(`INSERT INTO players(id, token_hash, name) VALUES(?, ?, ?)
        ON CONFLICT(token_hash) DO UPDATE SET name = excluded.name`).bind(crypto.randomUUID(), hash, name).run();
      const { row } = await player(request, env.DB);
      return profile(env.DB, row);
    }
    if (request.method === 'GET' && url.pathname === '/player') {
      const { row } = await player(request, env.DB);
      return profile(env.DB, row);
    }
    if (request.method === 'POST' && url.pathname === '/check') {
      const { row } = await player(request, env.DB);
      const data = await body(request);
      if (!Number.isInteger(data.day) || data.day < 1 || data.day > ids.length) {
        throw new HttpError(400, 'Choose a valid puzzle.');
      }
      const current = await profile(env.DB, row);
      if (data.day > current.completedThrough + 1) throw new HttpError(409, 'Solve the earlier puzzles first.');
      let correct;
      try { correct = matchesAnswer(data.answer, catalog.puzzles[data.day - 1].answer); }
      catch (error) { throw new HttpError(400, error.message); }
      if (correct) {
        await env.DB.prepare('INSERT INTO solves(player_id, puzzle_id) VALUES(?, ?) ON CONFLICT DO NOTHING')
          .bind(row.id, ids[data.day - 1]).run();
      }
      return { correct, player: correct ? await profile(env.DB, row) : current };
    }
    throw new HttpError(404, 'Not found.');
  }

  return {
    async fetch(request, env) {
      const origin = request.headers.get('Origin');
      const allowed = (env.ALLOWED_ORIGINS || '').split(',').map(value => value.trim());
      const headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Cache-Control': 'no-store',
        'Vary': 'Origin',
        'X-Content-Type-Options': 'nosniff',
      };
      if (origin && !allowed.includes(origin)) {
        return new Response(JSON.stringify({ error: 'Origin is not allowed.' }), { status: 403, headers });
      }
      if (origin) headers['Access-Control-Allow-Origin'] = origin;
      if (request.method === 'OPTIONS') {
        return new Response(null, { status: 204, headers: {
          ...headers, 'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Authorization, Content-Type', 'Access-Control-Max-Age': '86400',
        } });
      }
      try {
        return new Response(JSON.stringify(await route(request, env)), { headers });
      } catch (error) {
        const status = error instanceof HttpError ? error.status : 500;
        if (status === 500) console.error('Leaderboard request failed:', error.message);
        const message = status === 500 ? 'Could not save or load progress. Please try again.' : error.message;
        return new Response(JSON.stringify({ error: message }), { status, headers });
      }
    },
  };
}
