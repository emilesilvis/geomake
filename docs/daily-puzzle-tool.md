# A daily geometry ladder for two

**Recommendation: build a small, shared puzzle journal around an authored progression of ideas. Use geomake to produce and check its variations.** The promise is that an idea you discover today helps you see something tomorrow, and that comparing your approaches is part of the reward.

This document contains puzzle spoilers. The generated `START_HERE.md` is the entry point for solving.

## What we know, and what remains a hypothesis

The repository began as a reliable way to construct figures with known answers. It had 18 recipes, exact arithmetic, numerical checks, and a command that sorted puzzles by structural complexity. It did not have player history, hints, conceptual prerequisites, shared daily editions, or evidence about either player's enjoyment.

The desired experience is personal: two adults solving regularly. Their geometry background, preferred duration, familiar puzzles, and preference for simultaneous versus separate solving have not yet been established. The trial therefore assumes one common main puzzle, optional support, and an optional extension; 10–20 minutes is a starting experiment, not a difficulty claim. Both modes of solving work with the same pack.

The [research notes](puzzle-design-research.md) compare primary sources. The useful precedents are:

- **Euclidea:** learn constructions and then reuse them; an optional more elegant solution can extend a completed puzzle. [Creator's description](https://www.euclidea.xyz/)
- **NRICH:** accessible entry, substantial extensions, and discussion of reasoning. Prerequisite knowledge and difficulty finding a first move are different problems. [Task-design approach](https://nrich.maths.org/articles/low-threshold-high-ceiling-introduction)
- **Mathigon:** explicitly relate concepts and prerequisites, and supply help during exploration. [Design principles](https://mathigon.org/about)
- **GeomVerse:** retain backwards generation and proof-structure metadata. Its paper includes a small human comparison, but explicitly acknowledges limited creativity demands. It does not validate our lexicographic difficulty score or an enjoyment ladder. [Paper](https://arxiv.org/pdf/2312.12241)

These are ingredients, not a ready-made system that guarantees satisfaction. Learning research on delayed revisits is relevant, but its school-study results do not establish what these two players will enjoy.

## What needs to change in the generator

| Current evidence | Consequence | Direction |
| --- | --- | --- |
| `ladder.score()` orders by depth, number of solution strings, width, nonstandard flag, then construction operations. | Splitting one explanation into two strings can change a rank. More construction work can be invisible to a solver. | Keep the score as a structural descriptor; choose daily content by prerequisites, intended discovery, and observed experience. |
| `square_plus_semicircle` is depth 3; `rect_minus_semicircle` is depth 2. Both use diameter → radius → semicircle area and combine it with a quadrilateral area. | A higher declared depth need not introduce a harder idea. | Audit proof moves and likely entry points separately from arithmetic and diagram complexity. |
| For side s, `square_minus_incircle`, `quarter_circle_corner`, and `four_quarter_circles` all give s²(1 − π/4). | Distinct recipe names are not sufficient evidence of fresh thinking. | Make such equivalences intentional comparisons, with a reason to revisit them. |
| Most families only sample lengths or angles within a fixed construction. | More seeds mostly produce more practice instances. | Author changes in the given information, decomposition, required justification, or combination of ideas. |
| `verify()` measures the constructed target and its region assumptions. | A valid figure is not a proof that the displayed facts determine a unique answer. | Review a derivation from public facts for every curated family, then test hidden-parameter freedom and numerical geometry. |
| The original renderer outlined every constructed shape, including both circular segments inside `leaf_lens`. | The answer construction exposed the auxiliary diagonal in the question. | Keep construction helpers available for verification while hiding them from question outlines. This is implemented. |
| Original question PNGs carried annotations, while essential relationships sometimes lived only in the JSON question. | Passing around an image alone can omit the actual problem statement. | Deliver the statement and diagram together. The trial does this in each day page. |

The existing `generate` and `ladder` commands remain useful for sampling and structural experiments. The new `pilot` command follows an authored sequence; it makes no monotonic-human-difficulty claim.

## The daily experience

Open today's shared puzzle. Start with paper and pencil, with an optional warm-up if the underlying fact feels rusty. Reveal a nudge only when desired, then a more specific hint, then a concrete setup. A completed explanation includes the useful idea and an invitation to extend it.

For separate solving, each person keeps their attempt private until ready to compare. For joint solving, take a moment to notice something independently before talking. The comparison prompt should invite a different approach or the moment the picture changed in your head. It should work even when one person has not finished.

The fuller reader originally proposed below is a possible future direction. The
current user preference is a spartan page matching emilesilvis.com, hosted by
its existing GitHub Pages setup. The implemented static reader keeps only the
puzzle, answer check, progressive hints, explanation, previous/next links and
a collapsed list for returning to any puzzle.
It shares the site's stylesheet and theme preference, with no branding,
account requirement, feedback dashboard or synchronized notebook.

Potential later additions, if the pair finds them useful:

1. One common puzzle identity for the pair, with personal warm-ups and help when appropriate.
2. A readable diagram and complete givens on a phone; optional printable output for working on paper.
3. Progressive help, a place to keep rough reasoning, and a separate full explanation.
4. “Solved”, “paused”, and “read the explanation” as distinct, legitimate outcomes.
5. A deliberate “ready to compare” action; one person's completion should not expose their answer to the other automatically.
6. Persistent attempts and an archive. Missing a day leaves the next session available without creating mandatory catch-up work.

Start without timing or ranking people. A cleaner second solution is a better candidate for a shared challenge than speed, given the stated purpose. This default is a product hypothesis that the pair can revise.

The trial implements the content and manual solve/discuss loop. It exports Markdown and images, with separate hints and answers. `reader/build.py` also exports a responsive static reader with answer checking and deliberate hint/solution reveal. Answers are remembered only in the current browser. It does not implement scheduled delivery, accounts, or synchronization; static answer files are publicly inspectable.

## Two timescales of progression

Within a day, an optional warm-up leads into one main discovery and a stretch. Across days, insights accumulate and reappear. A week should have some easier returns as well as new ground; difficulty cannot rise forever.

An initial editorial rhythm to try is three new discoveries, two transformed revisits, one delayed return, and one special challenge across seven sessions. That is a candidate cadence, not an experimentally established optimum. The current pilot emphasizes foundational area reasoning before its final two challenges, so the feedback can expose where that particular transition is too steep.

Each content family needs:

- The intended realization, stated privately in one sentence.
- Prerequisites and a useful easier entry when a prerequisite is missing.
- A proof from the displayed facts, including any required shape relationships.
- Three authored hints that progressively reduce the search space.
- A satisfying explanation, a plausible alternate route where available, and an extension.
- A description of what changes between variants. Scaling numbers alone counts as replay.
- Links to earlier ideas it uses and later puzzles where the idea pays off.

For two players, simple editorial selection is a useful starting point. Choose a common main puzzle whose prerequisite support is available to both; give the more fluent player an extension. If one is repeatedly stuck before finding an entry, repair that prerequisite. If both find a family effortless and flat, advance the idea rather than enlarge the numbers. If a difficult puzzle felt rewarding, do not automatically make the next one easier just because it took time.

Track correctness, help, effort, familiarity, and enjoyment separately. Keep concept familiarity provisional: one correct answer may be a remembered puzzle, a guess, or a shared solve. There is too little personal data at the start to justify a fitted difficulty model.

## The concrete first week

Run:

```bash
.venv/bin/python -m geomake pilot --seed 7 --out out/daily-pilot
```

Open `out/daily-pilot/START_HERE.md`. Share the whole folder, preserving relative paths, so both people receive the same questions. Every question has three separately linked hints, an explanation, a comparison prompt, and a separately revealed stretch answer. Six sessions also have an optional generated warm-up. Day 3 intentionally follows directly from Day 2.

| Day | Main puzzle | Intended discovery | Connection |
| --- | --- | --- | --- |
| 1 | A triangle inside a rectangle whose total area is given | Missing lengths and an unknown vertex position can be irrelevant. | Establish base/height reasoning for later decompositions. |
| 2 | A square outside its inscribed circle | Whole minus part makes disconnected pieces easy to measure. | Introduce the main area move. |
| 3 | A square with four quarter-circle cutouts | Reassembled pieces can have the same total as a familiar shape. | Same square size as Day 2, deliberately; compare after solving. |
| 4 | A circle outside an inscribed square | The diagonal gives the required area without finding a side. | Reuse subtraction and triangle decomposition. |
| 5 | Two arcs making a leaf | Discover an auxiliary line; then seek a second, whole-region argument. | Combine Days 1–4; the question diagram no longer gives away the line. |
| 6 | A ring with only a tangent chord length given | A difference of squares can be determined while both radii remain unknown. | Return to Day 1's unnecessary unknowns, now using Pythagoras. |
| 7 | Two equal squares overlapping at one square's center | Quarter-turn symmetry makes the rotation angle irrelevant. | Return to invariance through a different kind of argument. |

The new families are `sliding_triangle`, `tangent_chord_annulus`, and `rotated_square_overlap`. The remaining content reuses the existing generator. This is one authored week, not seven days of independently sampled “hard” puzzles.

The pack is deliberately finite. A new seed changes its numerical edition; it does not create a new curriculum. The command rejects nonempty output folders so regenerating an edition cannot overwrite someone's feedback.

## Why the main puzzles are determined by their public facts

These are mathematical arguments about the families. The automated checks complement them; they do not replace them with a general solvability proof.

| Family | Public facts → unique target |
| --- | --- |
| Sliding triangle | Rectangle area A = bh; the triangle shares its entire base and perpendicular height. Its area is bh/2 = A/2 for every permitted vertex position and every rectangle aspect ratio. |
| Square minus incircle | Square side s and inscribed circle imply radius s/2. The remaining area is s² − π(s/2)². |
| Four quarter circles | The stated corner radii are s/2. The quarter discs have disjoint interiors and total area π(s/2)². Subtract from s². |
| Circle minus inscribed square | Circle radius r implies the square's diagonals are both 2r. Its four center triangles have total area 2r²; the remainder is πr² − 2r². |
| Leaf | A diagonal between the arc intersections splits the leaf into two equal segments. Each is a quarter disc minus half the square, giving πs²/2 − s². The numerical equality claim additionally compares those segments with the actual quarter-disc intersection. |
| Tangent-chord ring | For chord length L, the radius to the touching point is perpendicular to and bisects the chord. Thus R² − r² = (L/2)² and ring area is π(L/2)². Individual radii are unnecessary. |
| Rotated-square overlap | Perpendicular lines through the fixed square's center divide it into four equal-area sectors by quarter-turn symmetry. Every point of that square is within a/√2 of its center, so the other square's far sides at distance a cannot truncate the selected sector. The overlap is a²/4 at every rotation. |

The new regression checks vary hidden configurations while keeping public quantities fixed; check tangent-chord endpoints, length, and perpendicularity; and measure rotated overlap at 16 angles spanning a full turn, including angles outside the generator's sample. The existing recipe suite measures actual target regions over 25 seeds per family.

## Build the enduring tool in these increments

| Increment | Concrete result | Evidence required before relying on it |
| --- | --- | --- |
| **1. Calibrate the content** | Both people try the first week; record help, effort, familiarity, satisfaction, and whether comparison added something. Revise the order and entry support. | Actual attempts from both players. At present this evidence is missing. |
| **2. Deliver the daily ritual** | A small shared reader serves an immutable daily edition, stores separate attempts, preserves reveal state on reload, and lets either player pause or open the archive. Paper remains supported. | Two independent devices get the same puzzle; attempts and spoilers stay separate; refresh/date changes preserve work; both can reach a discussion without a correctness gate. |
| **3. Sustain the supply** | Author and review a rolling four-week queue. Expand into shared bases/heights, similar triangles, area ratios, angle chasing, tangency, and symmetry, following the pair's preferences. | Every scheduled main puzzle passes the publication checks below. The queue distinguishes new reasoning from intentional replay, and review throughput replenishes a week as a week is consumed. |
| **4. Improve selection** | Use personal prerequisite observations and puzzle feedback to select common tasks with appropriate support. Include delayed reuse of successful ideas. | Subsequent attempts show that support helps the struggling player and extensions remain interesting to the other. A correct answer alone is not evidence of this. |

The four-week reserve is an operational target, not a claim about the number of ideas needed for enjoyment. The current pack supplies seven main sessions; the remaining queue still needs authoring and playtesting. When a chapter is exhausted, move to a new concept or an explicitly chosen revisit. Resampling a scale parameter should not be silently advertised as a fresh discovery.

### Reuse and boundaries

Keep SymPy for exact expressions and Shapely/Monte Carlo for measurement checks. Keep the backwards construction DSL. Add the editorial curriculum alongside it, as the pilot already does with `Session` data.

Separate the data needed for four jobs: public statement/diagram facts; the private answer and derivation; editorial prerequisites/hints/variants; and each person's attempt. A daily edition freezes the puzzle version and seed so future recipe edits or different timezones cannot change a puzzle already being solved. Select the pair's calendar/timezone explicitly when adding dated delivery; the pilot avoids that issue by numbering sessions.

For answer checking, allow equivalent exact forms and reasonable decimals with target-specific units; preserve the ability to explain or self-report a solve. Avoid forcing a meaningful geometric argument into a numeric-only success metric.

Use a small explicit prerequisite graph first. A large adaptive-learning framework would need evidence and data we do not yet have. For future interactive diagrams, GeoGebra offers an existing embedding interface and object API; prototype it specifically when dragging constrained points or adding lines would improve these puzzles. It does not provide the curriculum or the shared ritual. [Official embedding guide](https://geogebra.github.io/docs/reference/en/GeoGebra_Apps_Embedding/), [API reference](https://geogebra.github.io/docs/reference/en/GeoGebra_Apps_API/)

A general geometry solver becomes useful if arbitrary givens are removed or arbitrary constructions are admitted. The first tool can use a smaller, reviewed library of proof-producing families. Any AI assistance should propose candidates for that authoring process; publication still requires the same factual and editorial review.

## Publication and completion evidence

For each candidate, verify the exact target against the constructed geometry, check geometric relationships used in the public statement, and review a derivation using only those public facts. Inspect the rendered diagram at the intended viewing size. Check that no construction helper, filename, title, hint ordering, or preview reveals the key move prematurely. Solve the instance from the question view before reviewing its recorded answer. Record equivalent variants intentionally.

Then test the sequence with the actual pair. The direction succeeds when they can reliably access fair puzzles, find a fitting entry, reach insights worth discussing, and want to return over repeated sessions. Neither passing tests nor a polished reader establishes that emotional outcome.

**Current status:** a researched design, an executable content pilot, three new verified families, targeted diagram fixes, and a minimal static reader for emilesilvis.com. Arithmetic parsing and static export are tested, including malformed input, spoiler separation in question pages, subdirectory links and preservation of an existing export after a failed rebuild. The open evidence is the pair's experience. Scheduled delivery and a replenishable reviewed queue remain to be built.

### Verification record, 6 September 2026

- Starting code: `.venv/bin/python -m pytest tests -q` — 491 passed.
- New families and the changed leaf: `tests/test_recipes.py -k 'sliding_triangle or tangent_chord_annulus or rotated_square_overlap or leaf_lens'` — 108 passed, covering 25 numerical seeds per family plus exactness/depth checks.
- Public-fact, edition, and existing ladder checks: `tests/test_pilot.py tests/test_insight_recipes.py tests/test_ladder.py` — 36 passed.
- After the final marker-placement change: `tests/test_render.py tests/test_pilot.py` — 9 passed. The renderer checks exercise both Shapely placement and its fallback.
- Generated the final seed-7 edition in `out/daily-pilot/`; inspected all seven main and six warm-up diagrams. Checked the final editorial revisions, 21 hints, and every relative Markdown link. The leaf has no visible construction chord, and corner-region markers have space around them.
- `git diff --check` passed. Generated packs are ignored build artifacts and can be reproduced with the documented command into a fresh directory.

These results verify the implementation and the prepared trial, not either player's enjoyment. No paired playtest has yet been observed.
