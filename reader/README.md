# Puzzle reader

Plain HTML, CSS and JavaScript for **emilesilvis.com/geomake/**, with a
[Cloudflare Worker and D1 backend](../backend/README.md) for public progress.
The page uses the host's `/static/css/style.css` and existing `theme` preference.
It shows a name prompt, puzzle, answer check, progressive hints, previous/next
links, and collapsed “All puzzles” and “Leaderboard” lists.
Every puzzle has a stable, bookmarkable URL.
Solve them in order: checking a correct answer unlocks the next puzzle. The
Next link and archive keep later puzzles locked, and opening a locked URL
shows a link to the first unfinished puzzle. Solved puzzles remain available
to revisit, even if you change their entered answers. Hints are available on the
current puzzle without unlocking the next one. Worked solutions are neither
shown nor exported by the reader.

Pages and archive entries show the generator's estimated difficulty label:
Easy (depth 1), Medium (depth 2), or Hard (depth 3). The exporter requires a
label on every puzzle. Labels are excluded from the edition identity, so
adding or recalibrating them preserves existing saved answers.

The default authored pack has twenty-one puzzles. Puzzles 8–21 continue upward
from Puzzle 7, combining area ratios, similarity and intersecting lines. The
third week adds missing-area and side-division recovery, then nested triangles
and a final inverse problem. They remain in the broad Hard band. Navigation and
the archive include the whole pack; the first fourteen questions retain their seeds.

From the geomake repository root:

```sh
# Generate once into an empty folder, if this edition does not exist yet.
.venv/bin/python -m geomake pilot --seed 7 --out out/daily-pilot
python3 reader/build.py
python3 reader/serve.py
# Open http://localhost:3000/geomake/
node --test reader/tests/*.test.js
.venv/bin/python -m pytest tests/test_reader.py
```

Those commands build the standalone reader. To connect the deployed leaderboard,
build with the **same manifest used to deploy the backend**:

```sh
python3 reader/build.py --edition out/daily-pilot-v3/editor.json \
  --api-url https://geomake-leaderboard.crayfish.workers.dev
```

Players enter a name or nickname before solving. Their name and solved-puzzle
count appear on the public leaderboard after their first correct solve; equal
counts share a rank. A random private token saved in
the browser identifies the player, so there is no password or email signup.
Changing the name keeps the same progress. Open **Your recovery code** and save
the code somewhere private. After clearing browser storage or switching devices,
choose **Log in with a recovery code** and paste it to restore the same player.
The code grants access to that player's progress; a display name alone does not.
Invalid codes and network failures leave the current login unchanged. If the
code itself is lost, the site operator can issue a replacement after verifying
which player record belongs to the requester.

The Worker checks answers and saves correct solves in D1. Skipped puzzles are
rejected by the server, and repeating a correct answer cannot increase the count.
Connected exports contain neither numeric answer files nor worked solutions.
Draft answers remain in browser storage, separately for each player. When first
registering, saved completion from identical earlier seven- or fourteen-puzzle
standalone editions is imported after its saved answers pass the server checks.
Recovery logins load only that player's server progress and do not import another
player's cached answers. Stable puzzle identities preserve public solves when days are appended.

`build.py --edition path/to/editor.json --out path/to/output` can export another
authored edition. Output may be empty or an earlier generated reader. It is
replaced only after the new edition builds successfully. Different edition
content has a different identifier, so saved answers cannot attach to a changed
puzzle. Generation seeds alone do not produce new geometric ideas.

For the existing website, copy the **contents of `reader/dist/`** into
**`apps/geomake/`** in `emilesilvis/emilesilvis.github.io`. Its existing `build.py`
copies that folder to `/geomake/`; its GitHub Pages workflow publishes it.
The CSS file remains shared with the rest of the website. `host-style.css` is
a snapshot of that stylesheet for the local preview only, with blank-line
whitespace normalized (source Git blob `7dd53042746af49f15fb7bf3ea0fe1a0e1439854`).
It is not included in the export.

JavaScript and browser storage are required for names, answer checks and progress.
When localStorage is unavailable, sessionStorage preserves the player for the
current tab. Hints are fetched only on request. Full worked solutions remain in
the Markdown pilot and editor manifest.

Omitting `--api-url` builds a standalone reader with no name prompt, leaderboard,
or uploads. Its numeric checks are public static files and progress is saved only
in the browser. The standalone gate guides navigation and is editable by the visitor.

The three-week pack remains self-paced. There is no calendar lock or automatic supply of
future weeks. The fuller warm-ups, extensions and discussion prompts remain in
the Markdown pilot rather than adding controls to this page.
