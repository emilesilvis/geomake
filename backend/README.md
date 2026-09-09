# Public puzzle progress

Cloudflare Worker: **https://geomake-leaderboard.crayfish.workers.dev**.
D1 database: `geomake-leaderboard`, in Western Europe. The account and database
IDs in `wrangler.jsonc` are public identifiers; authentication stays in Wrangler's
local credential store. This deployment does not opt in to a paid Workers plan.

The existing GitHub Pages site serves the reader. The Worker checks answers,
saves correct solves and serves the public leaderboard. Players use a name or
nickname and a random private browser token; there is no email or password flow.
The database stores each token's SHA-256 hash, never the token itself. Players can
save their private token as a recovery code and paste it into the reader to log
back in on another browser. Public rows
contain only an unrelated player ID, name, solved count and rank. Ties share a rank.
Players appear only after correctly solving at least one puzzle in the current edition.

## Build and deploy

Wrangler 4.129.1 is installed globally. Sign in with `wrangler login` on a new
machine, then confirm the account with `wrangler whoami`. From the repository root:

```sh
# Generate into an empty folder once. Reuse that manifest for both builds.
.venv/bin/python -m geomake pilot --seed 7 --out out/daily-pilot-v3
python3 backend/build.py --edition out/daily-pilot-v3/editor.json
node --test reader/tests/*.test.js backend/tests/*.test.js
wrangler d1 migrations apply geomake-leaderboard --remote --config backend/wrangler.jsonc
wrangler deploy --config backend/wrangler.jsonc
python3 reader/build.py --edition out/daily-pilot-v3/editor.json \
  --api-url https://geomake-leaderboard.crayfish.workers.dev
```

The database already exists; do not recreate it for updates. Copy the contents
of `reader/dist/` into the website repository's `apps/geomake/`, replacing the
previous generated export so obsolete answer and solution files disappear.
Its normal GitHub Pages workflow publishes `/geomake/`.

`backend/.generated/puzzles.json` contains the private numeric answer catalog and
is bundled only into the Worker. It must never be copied into the public reader.
Connected reader builds omit both `check.json` and `solution.json`.

Deploy the backend and reader from the same manifest. Every request carries the
edition identity, and an old page receives a reload message after an edition
change. Each solve has its own stable question fingerprint, so appending days or
editing hints keeps existing public credit. A changed question gets a new identity.

## Local development

```sh
python3 backend/build.py --edition out/daily-pilot-v3/editor.json
wrangler d1 migrations apply geomake-leaderboard --local --config backend/wrangler.jsonc
wrangler dev --config backend/wrangler.jsonc --local --port 8787
# In another terminal:
python3 reader/build.py --edition out/daily-pilot-v3/editor.json --api-url http://localhost:8787
python3 reader/serve.py
```

Local development uses a separate local database. Allowed browser origins are
listed in `wrangler.jsonc`; they include the website and the port-3000 preview.

## API behavior

All routes require `?edition=<edition ID>`. JSON writes and authenticated reads
use `Authorization: Bearer <64-character random hexadecimal token>`.

| Route | Behavior |
| --- | --- |
| `POST /player` | Save `{name}` using the browser's token; retries update the same player. |
| `GET /player` | Return the saved name, solved days and consecutive completion. |
| `POST /check` | Check `{day, answer}`; reject skipped days and count correct solves once. |
| `GET /leaderboard` | Public top 100 with at least one current puzzle solved, ordered by solved count, then name; ties share a rank. |

The answer parser accepts bounded arithmetic, not executable code. JSON bodies
are limited to 2 KiB. Names are normalized, limited to 40 characters and rendered
as text. Browser origins are checked and API responses are not cached.

Draft answers remain in the browser, scoped to the player. The server stores only
successful puzzle IDs and timestamps, not submitted answers or incorrect attempts.
Knowing a display name does not grant access. Recovery uses the same authenticated
`GET /player` as normal loading: the reader validates the code with the server
before replacing its saved login. Codes never appear in URLs or public responses.

`0002_player_tokens.sql` preserves existing tokens and permits multiple private
codes for one player without copying solves or adding duplicate leaderboard rows.
Apply the migration before deploying the Worker. It also accepts original tokens
from registrations handled by the old Worker during the deployment window.

If a player loses every copy of their code, operator recovery requires identifying
their existing player ID and checking the solve history. Back up the relevant
records first. Generate 32 random bytes, format them as 64 lowercase hex characters,
hash that string with SHA-256, and insert only the hash and existing player ID into
`player_tokens`. Deliver the code privately; do not commit it, embed it in a URL,
or change solve rows. Existing codes continue working. A known replacement browser
can instead be reconnected by updating its `player_tokens.player_id` after verifying
that the replacement record is empty and belongs to the same player. Name matching
alone must never provide automatic recovery.
