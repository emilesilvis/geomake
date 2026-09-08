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

The existing `generate` and `ladder` commands remain useful for sampling and structural experiments. The `pilot` command follows an authored sequence. Its original week is retained; both seven-session continuations are required to increase strictly under the existing structural score from Day 7 onward. The conceptual order is explained below, while actual human difficulty still needs playtesting.

## The daily experience

Open today's shared puzzle. Start with paper and pencil, with an optional warm-up if the underlying fact feels rusty. Reveal a nudge only when desired, then a more specific hint, then a concrete setup. A completed explanation includes the useful idea and an invitation to extend it.

For separate solving, each person keeps their attempt private until ready to compare. For joint solving, take a moment to notice something independently before talking. The comparison prompt should invite a different approach or the moment the picture changed in your head. It should work even when one person has not finished.

The fuller reader originally proposed below is a possible future direction. The
current user preference is a spartan page matching emilesilvis.com, hosted by
its existing GitHub Pages setup. The implemented static reader keeps only the
puzzle, answer check, progressive hints, previous/next links and
a collapsed list for returning to unlocked puzzles. A correct answer unlocks
the next puzzle; later pages stay locked even when opened directly. Completion
is saved by the Cloudflare Worker in D1, while drafts and a private player token
stay in the browser. Hints remain available on the current puzzle. The reader's
Solution control and worked-solution payloads have been removed. It shares the
site's stylesheet and theme preference and asks only for a public name or nickname.

Potential later additions, if the pair finds them useful:

1. One common puzzle identity for the pair, with personal warm-ups and help when appropriate.
2. A readable diagram and complete givens on a phone; optional printable output for working on paper.
3. Progressive help, a place to keep rough reasoning, and a separate full explanation.
4. “Solved”, “paused”, and “read the explanation” as distinct, legitimate outcomes.
5. A deliberate “ready to compare” action; one person's completion should not expose their answer to the other automatically.
6. Persistent attempts and an archive. Missing a day leaves the next session available without creating mandatory catch-up work.

The initial trial avoided timing or ranking people. The user has since requested
a public leaderboard and selected Cloudflare Workers plus D1. The implemented
leaderboard ranks the number of correct solves, with equal ranks for ties.
It does not use speed as a scoring rule. A random browser token identifies each
player without a password or email; changing devices creates a separate player.

The trial implements the content and manual solve/discuss loop. It exports
Markdown and images, with separate hints and answers. `reader/build.py` also
exports a responsive static reader with answer checking and deliberate hint reveal.
Worked solutions remain in the Markdown pack and editor manifest. When built
with `--api-url`, answers are checked by the Worker, numeric check files are
omitted, and correct solves persist in D1. The server enforces sequential unlocks
and counts each solve once. Standalone builds retain browser-only completion and
public static numeric checks. Scheduled delivery and device linking are not implemented.

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

The first chapter introduced `sliding_triangle`, `tangent_chord_annulus`, and `rotated_square_overlap`; its other four sessions reused existing recipes. These seven sessions and their seeded questions are preserved when the continuation is added.

The pack is deliberately finite. A new seed changes its numerical edition; it does not create a new curriculum. The command rejects nonempty output folders so regenerating an edition cannot overwrite someone's feedback.

## The second week: seven harder rungs

Days 8–14 are seven new families, rather than new number seeds for the original
seven. They continue from Day 7's structural score without a downward step.
The first rung reverses an area decomposition; each later rung adds a transfer,
an unknown, or another region to coordinate. All seven fit the existing broad
Hard label. The generator checks strictly increasing scores from Day 7 onward
and rejects forward prerequisite references. These checks protect the intended
order; they do not establish a calibrated human rating.

| Day | Main puzzle | New demand | Builds on |
| --- | --- | --- | --- |
| 8 | A tilted inner square with its area and side-division ratios given | Recover the surrounding frame by reversing a four-triangle decomposition, without finding a side. | 4, 7 |
| 9 | A trapezoid with the top and bottom diagonal-triangle areas given | Take a square root to recover a length ratio, then transfer it through shared heights. | 1, 8 |
| 10 | Two dividing lines intersect inside a triangle | Move from side divisions to area ratios, to perpendicular heights, to an internal segment ratio. | 9 |
| 11 | The same sort of intersection with its side division hidden | Recover a third area from two given small areas using a ratio and a second, independent partition equation. | 10 |
| 12 | A strip between parallel sections through a midpoint and an intersection | Convert the internal ratio to a height measured from the opposite vertex, square the similarity scales, and subtract. | 9, 10, 11 |
| 13 | Three dividing lines with the same cyclic side ratio | Repeat the intersection argument three times and recognize the complement of the central triangle. | 10, 12 |
| 14 | Three dividing lines with unequal side ratios | Derive and combine three different corner areas, with no equal-area shortcut. | 11, 12, 13 |

Each addition has an optional warm-up, three separate hints, a complete
public-fact solution, a comparison prompt and a stretch with its own explanation.
This chapter brought the pack to fourteen main puzzles and thirteen warm-ups. Its seed
namespace stays fixed so the original seven questions and their answers do not
change when the manifest version advances to `two-week-ladder-v1`.

For the triangle constructions below, D is on BC, E on CA, P=AD∩BE, and T is
the area of ABC. With a third dividing line, F is on AB, Q=BE∩CF and R=CF∩AD.
The apex position and aspect ratio are hidden construction choices. They vary
across seeds while the same public question retains its answer.

| Family | Public facts → unique target |
| --- | --- |
| Tilted-square frame | For side parts px and qx, the four right-triangle corners total 2pqx². Subtracting them from the outer square leaves (p²+q²)x². Given inner area I, the frame is 2pqI/(p²+q²). |
| Crossed trapezoid | Parallel bases make the top and bottom diagonal triangles similar. If their areas are U and V, their linear ratio is √(U/V). A shared-height comparison then gives each side triangle area √(UV), so the target is 2√(UV). |
| Crossing dividing lines | BD:DC=t:1 and midpoint E imply area ABD : area ADE = 2t:1. Their common base AD turns this into a height ratio, and similar right triangles along BE give BP:PE=2t:1. ABE has area T/2, so ABP has tT/(2t+1). |
| Area recovery | Let X=area ABP, Y=area APE, u=area BDP and v=area DPE. Shared heights give u/v=X/Y. Midpoint E gives total area 2(X+Y) and equal areas ADE=CDE=Y+v, hence u+2v=X. Solving gives u=X²/(X+2Y). |
| Parallel band | With BD:DC=t:1 and midpoint E, P is at height th/(2t+1) above BC. The upper triangle cut by P's parallel therefore has linear scale (t+1)/(2t+1); the parallel through E has scale 1/2. The strip has area T[((t+1)/(2t+1))²−1/4]. |
| Three equal divisions | With BD:DC=CE:EA=AF:FB=t:1, common-base comparisons give each unshaded corner triangle the fraction t/(t²+t+1). Subtracting the three disjoint corners gives central fraction (t−1)²/(t²+t+1). This cyclic area argument does not assume an equilateral triangle. |
| Three unequal divisions | With ratios p:1, q:1 and r:1 in that same cyclic order, apply the common-base argument separately. The corner fractions are p/(pq+p+1), q/(qr+q+1) and r/(rp+r+1). Subtract their sum from 1. The displayed solution derives each fraction rather than requiring a memorized theorem. |

The numerical recipe suite checks every new family over 25 seeds. Additional
checks establish the stated side divisions, parallel sections, intersection
incidence, given areas, exact public-fact formulas and invariance under hidden
shape changes. The renderer keeps auxiliary proof lines out of the questions.
Only the dividing lines and parallels stated in each question are visible.

## The third week: reverse the reasoning, then nest it

Days 15–21 extend the same ladder, preserving the first fourteen seeded questions.
The pack contains twenty-one main sessions and twenty warm-ups, with three hints,
worked explanations, discussion prompts and optional stretches for every new
session. The manifest version is `three-week-ladder-v1`; the seed namespace stays
`first-week-v1`.

| Day | Main puzzle | New demand | Builds on | Solution steps |
| --- | --- | --- | --- | --- |
| 15 | Central area given only one corner area and the side divisions | Reverse a known fraction to recover the missing total. | 8, 14 | 11 |
| 16 | Central area with BD:DC hidden | Recover a side division from two areas before applying the decomposition. | 11, 14, 15 | 13 |
| 17 | Central area with both the total and AF:FB hidden | Use one corner to recover the total, then another to recover the missing division. | 15, 16 | 14 |
| 18 | A parallel cut across a corner triangle | Recover the total, compare two intersection positions on AD, divide their distance fractions, square the similarity scale and subtract. | 12, 15, 17 | 15 |
| 19 | A second, equal-division construction inside PQR | Find PQR first, then make it the reference whole for the inner proof. | 13, 14, 18 | 16 |
| 20 | Unequal divisions in both nested layers | Derive six distinct corner fractions while tracking two reference areas. | 14, 19 | 20 |
| 21 | Outer shading given only the innermost area | Derive both retained fractions, reverse both scales and subtract the intermediate area. | 15, 17, 20 | 23 |

All seven remain depth 3 with width 4. Their structural scores rise strictly
from Day 14's ten-step derivation; each added demand is explained above. The
longer solutions derive the reused facts rather than requiring a named theorem.
The automatic ordering check also rejects reversed rungs before exporting any
files. These are structural estimates, not measured player difficulty.

Write a=p/(pq+p+1), b=q/(qr+q+1), c=r/(rp+r+1) and f=1−a−b−c.
As in the second chapter, p, q and r are the cyclic side ratios and T is ABC's
area. All sampled products pqr exceed 1, so the three corner interiors are
disjoint. For nested constructions, U∈QR, V∈RP, W∈PQ, X=PU∩QV, Y=QV∩RW and
Z=RW∩PU. The inner ratios u, v, w use the same cyclic convention.

| Family | Public facts → unique target |
| --- | --- |
| Total recovery | Given X=area ABP, T=X/a, so PQR=fX/a. |
| Missing ratio | Given T and X=area ABP, ABE=T/(q+1) and APE=Y=T/(q+1)−X. Shared heights give BP:PE=X:Y=p(q+1):1, so p=X/[Y(q+1)]. The now-known three ratios determine fT. |
| Double recovery | First recover T=X/a. Given Z=area CAR, CDR=T/(p+1)−Z. Shared heights give AR:RD=Z:CDR=r(p+1):1, hence r=Z/[(p+1)CDR]. These uniquely determine the remaining corner and central areas. |
| Corner band | AP/AD=(p+1)/(pq+p+1) and AR/AD=r(p+1)/(rp+r+1). Their quotient is k=AP/AR. Since PS∥RC, APS has k² of ARC's area cT; the shaded band is cT(1−k²), with T recovered from ABP. |
| Equal inner divisions | The outer center has area K=fT. At inner ratio 2:1, each of PQX, QRY and RPZ has area 2K/7 by the shared-height argument. Their complement XYZ is K/7. |
| Unequal inner divisions | Relative to K=fT, the inner corner fractions are u/(uv+u+1), v/(vw+v+1) and w/(wu+w+1). Their complement has fraction g, giving XYZ=gfT. |
| Nested recovery | For given L=area XYZ, recover K=L/g and T=L/(fg). The asked outer frame is T−K=L(1−f)/(fg). |

The nested outer ratios are cyclic variants of (2,4,7), retaining fraction
25/66. Inner equal divisions retain 1/7; unequal cyclic variants of (2,1,3)
retain 1/10. These choices keep the visible center large enough for labels and
the given numbers manageable. Rotating ratios and changing the drawing are
practice variants; the seven new reasoning tasks are the authored progression.

## Why the first week's main puzzles are determined by their public facts

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

The four-week reserve is an operational target, not a claim about the number of ideas needed for enjoyment. The current pack supplies twenty-one main sessions; the remaining queue still needs authoring and playtesting. When a chapter is exhausted, move to a new concept or an explicitly chosen revisit. Resampling a scale parameter should not be silently advertised as a fresh discovery.

### Reuse and boundaries

Keep SymPy for exact expressions and Shapely/Monte Carlo for measurement checks. Keep the backwards construction DSL. Add the editorial curriculum alongside it, as the pilot already does with `Session` data.

Separate the data needed for four jobs: public statement/diagram facts; the private answer and derivation; editorial prerequisites/hints/variants; and each person's attempt. A daily edition freezes the puzzle version and seed so future recipe edits or different timezones cannot change a puzzle already being solved. Select the pair's calendar/timezone explicitly when adding dated delivery; the pilot avoids that issue by numbering sessions.

For answer checking, allow equivalent exact forms and reasonable decimals with target-specific units; preserve the ability to explain or self-report a solve. Avoid forcing a meaningful geometric argument into a numeric-only success metric.

Use a small explicit prerequisite graph first. A large adaptive-learning framework would need evidence and data we do not yet have. For future interactive diagrams, GeoGebra offers an existing embedding interface and object API; prototype it specifically when dragging constrained points or adding lines would improve these puzzles. It does not provide the curriculum or the shared ritual. [Official embedding guide](https://geogebra.github.io/docs/reference/en/GeoGebra_Apps_Embedding/), [API reference](https://geogebra.github.io/docs/reference/en/GeoGebra_Apps_API/)

A general geometry solver becomes useful if arbitrary givens are removed or arbitrary constructions are admitted. The first tool can use a smaller, reviewed library of proof-producing families. Any AI assistance should propose candidates for that authoring process; publication still requires the same factual and editorial review.

## Publication and completion evidence

For each candidate, verify the exact target against the constructed geometry, check geometric relationships used in the public statement, and review a derivation using only those public facts. Inspect the rendered diagram at the intended viewing size. Check that no construction helper, filename, title, hint ordering, or preview reveals the key move prematurely. Solve the instance from the question view before reviewing its recorded answer. Record equivalent variants intentionally.

Then test the sequence with the actual pair. The direction succeeds when they can reliably access fair puzzles, find a fitting entry, reach insights worth discussing, and want to return over repeated sessions. Neither passing tests nor a polished reader establishes that emotional outcome.

**Current status:** a researched design, a twenty-one-session content pilot, 35
recipe families, targeted diagram fixes, and a minimal reader for emilesilvis.com
with a Cloudflare Worker and D1 public leaderboard. Arithmetic parsing, static
export, player registration, sequential answer checking, rank ties and progress
preservation are tested. The open evidence is the pair's experience. Scheduled
delivery and a replenishable reviewed queue remain to be built.

### Verification record, 6 September 2026

- Starting code: `.venv/bin/python -m pytest tests -q` — 491 passed.
- New families and the changed leaf: `tests/test_recipes.py -k 'sliding_triangle or tangent_chord_annulus or rotated_square_overlap or leaf_lens'` — 108 passed, covering 25 numerical seeds per family plus exactness/depth checks.
- Public-fact, edition, and existing ladder checks: `tests/test_pilot.py tests/test_insight_recipes.py tests/test_ladder.py` — 36 passed.
- After the final marker-placement change: `tests/test_render.py tests/test_pilot.py` — 9 passed. The renderer checks exercise both Shapely placement and its fallback.
- Generated the final seed-7 edition in `out/daily-pilot/`; inspected all seven main and six warm-up diagrams. Checked the final editorial revisions, 21 hints, and every relative Markdown link. The leaf has no visible construction chord, and corner-region markers have space around them.
- `git diff --check` passed. Generated packs are ignored build artifacts and can be reproduced with the documented command into a fresh directory.

These results verify the implementation and the prepared trial, not either player's enjoyment. No paired playtest has yet been observed.

### Continuation verification, 7 September 2026

- Full Python suite: 852 passed, including 25 numerical seeds for each of the seven new families, public-fact derivations, hidden-shape invariance, continuation ordering and fourteen-page export coverage.
- After the final small-triangle layout adjustment: 75 focused continuation and unequal-division checks passed.
- JavaScript answer-parser suite: 3 passed. `git diff --check` passed.
- Generated and built the seed-7 fourteen-session pack. Visually checked all seven new main diagrams, corrected cramped labels and the narrow-strip marker, and verified the answer check, progressive hints, worked solution, archive and Day 7 → Day 8 navigation in the local browser reader.

### Third week and leaderboard verification, 8 September 2026

- Full Python suite after the seven new families: 1,092 passed. Final focused
  reader, third-week and renderer checks: 66 passed.
- JavaScript reader and backend checks: 19 passed, including arithmetic parsing,
  token persistence, registration retries, sequential server checks, duplicate
  solves, rank ties, body limits and progress across edition changes.
- Generated the final seed-7 pack in `out/daily-pilot-v3/` and inspected all seven
  new diagrams. Inner labels were spaced and reduced slightly for nested triangles.
- The first fourteen sessions reproduce published edition `7472b5f5c599085e`,
  allowing its browser drafts and verified completion to be recovered.
- Browser checks covered registration, incorrect/correct answers, the public
  solved count and persistence after reload. The Solution control is absent.
- Deployed the Worker and D1 database, then verified live CORS, registration,
  sequential unlocking, correct and incorrect answers, restored progress and
  public ranking. The temporary deployment-check player was removed.
