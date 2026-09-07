# geomake

Generator for "find the shaded area / angle / length" geometry puzzles (the
Facebook genre) with controllable difficulty.

Everything is generated **backwards / diagram-first**: the figure is
constructed from known quantities, so the answer is free by construction.
No solver anywhere — a subset of givens is revealed, the rest is hidden, and
the claimed answer is then **verified numerically** against an independent
measurement of the figure before the puzzle is accepted.

## Quick start

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[verify,test]'

# 20 puzzles, mixed difficulty -> out/puzzle_*.png + out/puzzles.json(l)
.venv/bin/python -m geomake generate --n 20 --seed 42 --out out

# only depth-3 puzzles, answer printed on the figure (answer-key mode)
.venv/bin/python -m geomake generate --n 6 --depth 3 --show-answer --out out3

# a specific recipe
.venv/bin/python -m geomake generate --n 4 --recipe leaf_lens --out lens

# graded easy->hard ladder (validated ordering) + answer key in ladder/answers/
.venv/bin/python -m geomake ladder --n 12 --seed 7 --out ladder

# fourteen authored daily sessions for two, with optional help and discussion
.venv/bin/python -m geomake pilot --seed 7 --out out/daily-pilot
# Open out/daily-pilot/START_HERE.md; share the whole folder with your partner.

# Minimal browser reader, matching emilesilvis.com's existing stylesheet
python3 reader/build.py
python3 reader/serve.py
# Open http://localhost:3000/geomake/

.venv/bin/python -m geomake recipes     # list all recipes by depth
.venv/bin/python -m pytest tests/       # every recipe x 25 random seeds
```

## Toward a daily puzzle tool

`geomake pilot` produces a fourteen-day content trial: one shared main puzzle per
day, thirteen optional warm-ups, three separately revealed hints per main puzzle,
worked explanations, optional extensions, and prompts to compare approaches.
The question pages include the full statement alongside the diagram. Both
players should use the same edition seed and preserve the folder structure.
Output folders must be empty, so generating another edition cannot overwrite
feedback. The `editor.json` manifest contains spoilers.

The original seven puzzles introduce invariance, decomposition, and symmetry.
Seven new puzzles continue from Day 7 in increasing structural difficulty:
reverse area ratios, similarity, intersecting lines, recovering missing areas,
parallel strips, and two three-line triangle challenges. Each new session names
the earlier ideas it builds on; the generator checks that its difficulty score
strictly increases from the preceding rung. The original seven questions keep
their seeds and answers. Player experience is still needed to calibrate the
progression; changing the edition seed supplies variations of the same ideas. The
[static reader](reader/README.md) shows the question, answer check, progressive
hints, solution, previous/next links and a collapsed list of all puzzles. It uses emilesilvis.com's stylesheet
and existing GitHub Pages hosting, and remembers entered answers in the current
browser. Correct answers unlock puzzles in order; the Next link, archive, and
direct puzzle URLs follow the same saved progress. It does not schedule future
days or synchronize player progress.

See the [daily-tool design and build sequence](docs/daily-puzzle-tool.md) and
the [primary-source research](docs/puzzle-design-research.md). The design
document contains spoilers; use the generated `START_HERE.md` to solve.

## Architecture

```
recipes.py    parameterized backwards constructions (the puzzle library)
   |            samples small integers -> builds figure -> picks givens
   v
scene.py      construction DSL: ordered ops (place_square, inscribe_circle,
   |          quarter_circle_at_corner, semicircle_on_side, ...); every new
   |          entity is defined by prior ones, so layout is trivial and an
   |          auditable construction trace is recorded per puzzle
   v
core.py       exact symbolic state: all coordinates/areas/angles are sympy
   |          expressions (rationals, radicals, pi); regions are small CSG
   |          trees (diff/union) whose exact area is computable because the
   |          construction guarantees containment/disjointness — those
   |          assumptions are *recorded*, not trusted
   v
verify.py     numerical verification by random seeds: shapely boolean ops
   |          (and an independent Monte Carlo fallback on the region
   |          indicator) re-measure every area, length, angle, and every
   |          recorded assumption; failing puzzles are rejected and resampled
   v
render.py     matplotlib rendering: shaded region, outlines, dimension /
              angle / radius annotations, red "?" on the asked quantity

pilot.py      authored daily sessions: prerequisites, graduated hints,
              explanations, comparisons, extensions, and a feedback sheet
```

### Difficulty axes (GeomVerse conventions)

| axis | meaning | knob |
|---|---|---|
| **depth** | length of the deduction chain | `--depth 1..3` |
| **width** | max sub-results feeding one step | per-recipe metadata |
| **non-standard shapes** | composite figures (L-shape, lens, cut-outs) | per-recipe flag |
| construction steps | length of the DSL trace | recorded per puzzle |

Depth 1 = one formula (rectangle area, angle sum). Depth 2 = two chained
results (square − inscribed circle). Depth 3 = longer chains, branching, or
figure-to-figure chaining (rectangle area → shared side → square → inscribed
circle), where the given for one shape must be *derived* from another.

Every generated puzzle also has an **estimated difficulty label**: depth 1 →
**Easy**, depth 2 → **Medium**, depth 3 → **Hard**. The label is exported in
`difficulty.label` and shown on standalone puzzle images, pilot question
pages, and the browser reader and archive. The other scoring factors order
puzzles within a band; these broad labels are not calibrated player ratings.

### Recipes (28)

- **depth 1** — `rect_area`, `tri_right_area`, `circle_area`,
  `triangle_angle_sum`, `square_diagonal`
- **depth 2** — `square_minus_incircle`, `rect_minus_semicircle`,
  `circle_minus_insquare`, `l_shape`, `overlap_squares_center`,
  `isosceles_base_angle`, `quarter_circle_corner`, `annulus`, `sliding_triangle`
- **depth 3** — `leaf_lens`, `square_circle_square`, `four_quarter_circles`,
  `chained_rect_square_circle`, `square_plus_semicircle`,
  `tangent_chord_annulus`, `rotated_square_overlap`, `tilted_square_frame`,
  `crossed_trapezoid`, `crossing_cevians`, `cevian_area_recovery`,
  `cevian_parallel_band`, `three_cevians`, `unequal_three_cevians`

Targets cover **area** (shaded region), **length**, and **angle**.

### Ladders: a validated easy->hard sequence

`geomake ladder` builds a sequence that ramps gradually, for solving in
order under a structural score. This is not a calibrated measure of human
difficulty or enjoyment. Difficulty is scored from recorded metadata — `(depth, solution
steps, width, nonstandard shape, construction ops)`, lexicographic — and the
finished sequence is independently validated before it is accepted:

- every answer re-verified numerically (same checks as `generate`)
- the difficulty score never decreases along the sequence
- depth never jumps by more than one level between adjacent puzzles
- all depths 1–3 are covered (starts easy, ends hard)
- recipe variety (no recipe over-represented)

Output: `qNN_<recipe>_dK.png` question images (solve in filename order),
`answers/aNN_*.png` answer-key images, and `ladder.json` with the ordering,
per-puzzle scores, solutions, and the validation report.

## Output: human-facing and dataset at once

Each puzzle is emitted in both forms from the same pipeline, so the
human-vs-training-data decision doesn't fork the architecture:

- `puzzle_NNN_<recipe>_dK.png` — rendered figure with a red `?`
- `puzzles.json` / `puzzles.jsonl` — per puzzle: question text, exact answer
  (`36 − 9π`, latex, float, display form), step-by-step solution chain
  (worked mathematical explanation), difficulty metadata, the full construction trace, the
  sampled parameters, and the seed (fully reproducible)

## Verification model

The generator's exact answers rest on construction-time claims. All of them
are checked numerically per puzzle, and again across 25 random seeds per
recipe in the test suite:

- **area targets** — true set-semantics area via shapely booleans *plus* an
  independent Monte Carlo estimate from the region's `contains_pt` indicator
- **subset / disjoint assumptions** behind every exact `diff` / `union` area
- **equal-region claims** (e.g. "the overlap of these two squares is this
  rectangle") — symmetric-difference area ≈ 0
- **length / angle targets** — re-measured from float coordinates
- degenerate constructions (non-positive answers) are rejected

Numerical checks establish facts about the constructed figure. They do not
establish that arbitrary subsets of givens determine a unique answer, or that
the puzzle is satisfying. The curated pilot includes an explicit public-fact
derivation for each family in its design notes, tests hidden-parameter
invariance, and keeps construction helpers out of question outlines. Actual
player feedback remains necessary to calibrate the progression.

## Extending

Add a recipe: write one function in `recipes.py` decorated with
`@recipe(name, depth)`. Sample parameters from `rng`, build the figure with
`Scene` ops, wrap the asked quantity in a `Target`, list the revealed
`Given`s and the solution steps. Verification and rendering are automatic.
If a recipe needs a new construction op, add it to `Scene` (keep it defined
purely in terms of prior entities) and, if it introduces a new primitive
shape, give it exact `area()` plus float `contains_pt`/`boundary` in
`core.py` — that is all the verifier and renderer need.
