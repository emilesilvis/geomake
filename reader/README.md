# Puzzle reader

Plain HTML, CSS and JavaScript for **emilesilvis.com/geomake/**. No runtime
framework, account, database, or build dependencies. The page uses the host's
`/static/css/style.css` and its existing `theme` preference. Only the puzzle,
answer check, progressive hints, solution, previous/next links and a collapsed
“All puzzles” list are shown. Every puzzle has a stable, bookmarkable URL.

Pages and archive entries show the generator's estimated difficulty label:
Easy (depth 1), Medium (depth 2), or Hard (depth 3). The exporter requires a
label on every puzzle. Labels are excluded from the edition identity, so
adding or recalibrating them preserves existing saved answers.

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

The statement and diagram work without JavaScript. Hints and explanations are
fetched only on request; an answer check fetches just the numeric answer.
These are public static files, so a visitor who inspects them can read answers.
Entered answers are remembered only in that browser, using a namespaced
localStorage key. They are never uploaded; this reader does not synchronize
devices or maintain player accounts. Browser storage is optional for solving.

The week remains self-paced. There is no calendar lock or automatic supply of
future weeks. The fuller warm-ups, extensions and discussion prompts remain in
the Markdown pilot rather than adding controls to this page.
