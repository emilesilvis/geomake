"""Twenty-one authored sessions, with two progressively harder continuations.

Question pages contain only public givens. Hints and explanations live in
separate files. The editor manifest deliberately contains spoilers.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from .puzzle import Puzzle
from .ladder import score
from .recipes import build
from .render import render
from .verify import verify

PILOT_VERSION = "three-week-ladder-v1"
# Appending sessions must not resample any previously published questions.
SEED_NAMESPACE = "first-week-v1"


@dataclass(frozen=True)
class Session:
    recipe: str
    warmup: str | None
    insight: str
    prerequisites: tuple[str, ...]
    hints: tuple[str, str, str]
    takeaway: str
    discuss: str
    extension: str
    extension_answer: str
    builds_on: tuple[int, ...] = ()


SESSIONS = (
    Session(
        "sliding_triangle", "tri_right_area",
        "A position can change without changing an area.",
        ("rectangle area", "triangle area"),
        (
            "Which measurements would you normally use to find a triangle's area?",
            "Compare the triangle's base and perpendicular height with those of the rectangle.",
            "Write the two area formulas using the same base b and height h. You already know the product b × h.",
        ),
        "An unknown can be irrelevant. Look for a relationship before hunting for every length.",
        "Which missing measurements initially bothered you? Did you both dismiss them in the same way?",
        "If the third vertex leaves the rectangle, where could it lie while the full triangle still has half the rectangle's area? Keep the same base.",
        "Anywhere on the line containing the top edge, even beyond its endpoints: the perpendicular height is unchanged. A parallel line the same distance below the base works too. These are exactly the points at the required distance from the base line.",
    ),
    Session(
        "square_minus_incircle", "circle_area",
        "Find a difficult region by subtracting a simpler one.",
        ("square area", "circle area", "diameter and radius"),
        (
            "Would it be easier to measure the blue pieces together or to find what is missing?",
            "The circle touches all four sides. Compare its diameter with a side of the square.",
            "If the square's side is s, use s² for the whole and π(s/2)² for the white part, then subtract.",
        ),
        "Several awkward pieces can have a simple total. Whole minus part is a reusable move.",
        "Did you start with a blue corner or with the whole square? What made you switch approaches?",
        "What fraction of the square is shaded? Would changing the size of the square change that fraction?",
        "The fraction is (s² − πs²/4)/s² = 1 − π/4. It is the same for every size.",
    ),
    Session(
        "four_quarter_circles", None,
        "Rearrange pieces mentally to recognize a familiar total.",
        ("whole minus part", "quarter-circle area"),
        (
            "Look at the white pieces first. What do they have in common?",
            "Imagine putting the four white pieces together. What shape would they make?",
            "The four quarter circles total one circle of radius half the square's side. Subtract that total from the square.",
        ),
        "A change of layout need not change the area. This intentionally echoes the previous session with the same square size.",
        "Compare your result with Day 2. Can you explain the relationship without doing either calculation again?",
        "A fifth quarter circle of the same radius is also removed, with some overlap. Can you simply subtract five quarter-circle areas?",
        "No. Overlapping removed regions would be counted more than once. Subtract the area of their union, accounting for the overlaps.",
    ),
    Session(
        "circle_minus_insquare", "square_diagonal",
        "A diagonal can determine an area without finding a side.",
        ("circle area", "whole minus part", "triangle area or Pythagoras"),
        (
            "Which length of the inner square can you read from the circle?",
            "Draw the inner square's two diagonals. How do they relate to the circle's radius?",
            "The diagonals split the square into four right triangles, each with legs equal to the radius. Add their areas, then subtract from the circle.",
        ),
        "Choose the quantity you need. Finding a square's side first is optional when its diagonals are known.",
        "Did either of you use Pythagoras? Can the other explain an area-only route?",
        "For a square with diagonal d, derive its area directly in terms of d.",
        "The two diagonals form four right triangles with legs d/2. Their total area is 4 × ½ × (d/2)² = d²/2. Pythagoras gives the same result.",
    ),
    Session(
        "leaf_lens", "quarter_circle_corner",
        "Add an auxiliary line, or count an overlap twice and correct it.",
        ("triangle area", "quarter-circle area", "whole minus part"),
        (
            "The curved region is unfamiliar. Can a straight line split it into more recognizable pieces?",
            "Join the two points where the arcs meet. On each side you now have a quarter-circle segment.",
            "Each segment is a quarter circle minus a right triangle occupying half the square. There are two equal segments.",
        ),
        "An added line can turn a strange shape into familiar ones. The optional stretch asks for a second method using whole regions.",
        "Compare a method using a diagonal with a method that counts the two quarter discs. Which is more convincing to each of you?",
        "Can you find the leaf area without splitting it into two segments? Explain what is counted twice.",
        "The two quarter discs together cover the square. In their summed areas, every point in the square is counted once and every point in the leaf once more. Subtracting the square leaves exactly the leaf.",
    ),
    Session(
        "tangent_chord_annulus", "annulus",
        "Determine a difference of squares without determining either radius.",
        ("circle area", "Pythagoras", "a tangent is perpendicular to its radius"),
        (
            "Write the ring's area using two unnamed radii. What combination of them do you actually need?",
            "Join the center to the touching point and to an endpoint of the segment. A radius to a tangent is perpendicular to it, making a right triangle.",
            "The touching point bisects the segment. If its half-length is h, Pythagoras gives R² = r² + h². Substitute that relationship into the ring's area.",
        ),
        "Do not solve for quantities the question never needs. An equation can determine their difference while leaving both unknown.",
        "When did you stop trying to find both radii? Which earlier puzzle encouraged that change?",
        "If the whole tangent segment doubles in length, how does the ring's area change?",
        "It quadruples: for segment length L, the area is π(L/2)². This is true even if the individual radii change.",
    ),
    Session(
        "rotated_square_overlap", "overlap_squares_center",
        "Rotational symmetry fixes an area despite an unknown angle.",
        ("square area", "quarter-turn symmetry"),
        (
            "Would turning the upper square a little necessarily change the overlap? Try a rough sketch of an easier orientation.",
            "Extend its two sides through the shared center into full lines. Think about a quarter-turn of the fixed square.",
            "A 90° rotation takes each of the four sectors of the fixed square to the next. They have equal area. Check that the other two sides of the tilted square do not truncate the overlap.",
        ),
        "Symmetry can determine a quantity when a measurement is missing. The angle is unnecessary; the fixed square's quarter-turn symmetry does the work.",
        "Compare the uncertainty here with Day 1. What is changing, and what stays invariant?",
        "Would the same quarter-area argument work if the fixed square were replaced by a non-square rectangle?",
        "Not in general. Center an 8 × 2 rectangle at the origin and cut it with the perpendicular lines y = x and y = −x. Its upper sector is a triangle with base 2 and height 1, so its area is 1, not a quarter of 16. A sufficiently large tilted square can cover that sector. The rectangle lacks the quarter-turn symmetry used in the proof.",
    ),
    Session(
        "tilted_square_frame", "square_diagonal",
        "Reverse an area relationship to recover a frame without finding any lengths.",
        ("right-triangle area", "whole minus part", "area scales with length squared"),
        (
            "The white square's area is known, but none of its sides are. Can the four blue corners help relate the inner and outer areas?",
            "Each corner is a right triangle. Write the two pieces of an outer side as px and qx, using the given ratio p:q.",
            "The outer area is (p+q)²x² and the four corners total 2pqx². The inner area is therefore (p²+q²)x². Use the known inner area to find x², then the frame.",
        ),
        "A repeated decomposition gives an area ratio. Work backward from the known area, keeping the unknown length squared throughout.",
        "How did Day 7's repeated pieces help here? Did either of you calculate a side that turned out to be unnecessary?",
        "Among all positive division ratios p:q, when does the frame occupy the largest fraction of the outer square?",
        "Its fraction is 2pq/(p+q)². Since (p−q)² ≥ 0, (p+q)² ≥ 4pq, so the fraction is at most 1/2, reached when p=q: all four points are midpoints.",
        builds_on=(4, 7),
    ),
    Session(
        "crossed_trapezoid", "sliding_triangle",
        "Recover a length ratio from two areas, then transfer it through shared heights.",
        ("similar triangles", "squared scale factors", "triangles with a shared height"),
        (
            "Focus first on the two unshaded triangles. What does the pair of parallel sides tell you about their angles?",
            "The top and bottom triangles are similar. Their area ratio is the square of their length ratio, so take its square root.",
            "Compare AOD with COD using their bases AO and OC on the same diagonal. Their common height from D makes their area ratio AO:OC. Repeat for BOC.",
        ),
        "Use squared ratios for similar figures and unsquared base ratios for triangles sharing a height. Switching between those two comparisons is the new move.",
        "Where did you need a square root, and where would taking one have been a mistake?",
        "If the top and bottom triangle areas are U and V, express the whole trapezoid's area using only U and V.",
        "Each side triangle has area √(UV), so the whole area is U+V+2√(UV) = (√U+√V)². Horizontal shearing does not change that conclusion.",
        builds_on=(1, 8),
    ),
    Session(
        "crossing_cevians", "sliding_triangle",
        "Transfer an area ratio into a hidden segment ratio across an intersection.",
        ("shared bases and heights", "similar right triangles", "midpoint area ratios"),
        (
            "Find areas or area ratios involving D and E before trying to locate P. The position of the intersection can be recovered indirectly.",
            "Compare triangles ABD and ADE. First use BD:DC, then the fact that E halves AC. These triangles share base AD.",
            "Their area ratio equals the ratio of their heights to AD. Because B, P and E are collinear, that is also BP:PE. Use it to split triangle ABE, which has half of ABC's area.",
        ),
        "A line intersection can be located by ratios of heights. Shared-base area comparisons supply those ratios without coordinates or measured lengths.",
        "Which was easier to see: the two perpendicular heights, or the small similar triangles that turn their ratio into BP:PE?",
        "Keep E at the midpoint, but let BD:DC = t:1. What fraction of ABC is ABP?",
        "Area ABD : area ADE = 2t:1, so BP:PE = 2t:1. ABP takes 2t/(2t+1) of ABE, which is half of ABC. The fraction is t/(2t+1).",
        builds_on=(9,),
    ),
    Session(
        "cevian_area_recovery", "crossing_cevians",
        "Use two known small areas to recover another when the side division is hidden.",
        ("intersection area ratios", "equal areas from a midpoint", "simultaneous linear equations"),
        (
            "The two given triangles fill ABE. What does E being a midpoint tell you about the whole triangle?",
            "Call the areas of BDP and DPE u and v. Comparing bases on BE gives u:v from the two given areas. You still need a second equation.",
            "ADE and CDE have equal area. If the given areas are X for ABP and Y for APE, the whole area is 2(X+Y), but also X+u+2(Y+v). Thus u+2v=X and u/v=X/Y.",
        ),
        "The same geometry can be solved backward. Combine a ratio with an area partition to replace a missing side-division fact.",
        "Which of your two equations described a ratio, and which described the whole picture? Could either one determine the answer alone?",
        "With X = area ABP and Y = area APE, can you also recover BD:DC?",
        "Let v = area DPE. Shared heights give area BDP = (X/Y)v. Then area ABD : area ADC = [X+(X/Y)v] : [2(Y+v)] = X:2Y. These triangles share a height from A, so BD:DC = X:2Y.",
        builds_on=(10,),
    ),
    Session(
        "cevian_parallel_band", "crossing_cevians",
        "Turn an intersection ratio into a height, square the scale, and subtract nested areas.",
        ("intersection ratios", "similar-triangle area ratios", "whole minus part"),
        (
            "The blue strip is the difference between two triangles with vertex A. Both are similar to ABC because their bases are parallel to BC.",
            "The parallel through E gives a half-size triangle. To find the other scale, first recover BP:PE using the argument from Day 10.",
            "If BD:DC=t:1, then BP:PE=2t:1. With whole height h, P is at height th/(2t+1) above BC. The triangle above P's parallel has linear scale (t+1)/(2t+1). Square both triangle scales and subtract their areas.",
        ),
        "An internal ratio becomes a distance from a baseline, then a similarity scale, then an area. Keep those quantities distinct through the longer chain.",
        "Did you initially measure P's height from BC or from A? How did you catch which one the area calculation needed?",
        "For BD:DC=t:1, derive the fraction of ABC occupied by the strip and describe what happens as t becomes very large.",
        "The fraction is ((t+1)/(2t+1))²−1/4 = (4t+3)/(4(2t+1)²). It tends to zero as t grows: P approaches E and the two parallel sections approach each other.",
        builds_on=(9, 10, 11),
    ),
    Session(
        "three_cevians", "crossing_cevians",
        "Repeat an intersection argument around a triangle, then remove three corner regions.",
        ("intersection ratios", "cyclic reuse of an argument", "disjoint area decomposition"),
        (
            "Could you find the three larger triangles ABP, BCQ and CAR instead of attacking the tiny central triangle directly?",
            "Start with ABP. Compare ABD and ADE on their common base AD to recover BP:PE. E is no longer necessarily a midpoint, so include its stated division ratio.",
            "For a common side ratio t:1, ABE has 1/(t+1) of the whole area and BP:PE=t(t+1):1. Thus ABP has t/(t²+t+1) of the whole. Cycle the vertex names to obtain the other two corner areas, then subtract all three.",
        ),
        "Equal division ratios allow the same proof to run three times. This is symmetry of the area relationships; the drawing need not have rotational symmetry.",
        "What justified equal corner areas even though the outer triangle did not look equilateral?",
        "Replace the common ratio by any t:1 with t>1. What fraction is central? What happens at t=1?",
        "The fraction is 1−3t/(t²+t+1) = (t−1)²/(t²+t+1). At t=1 the three lines are medians and meet at a single point, so the central area is zero.",
        builds_on=(10, 12),
    ),
    Session(
        "unequal_three_cevians", "three_cevians",
        "Remove the equal-ratio shortcut and coordinate three different intersection calculations.",
        ("three-line triangle decomposition", "shared-height ratios", "combining unequal fractions"),
        (
            "The same three corner triangles still fill the unshaded region, but their areas need separate calculations because the side ratios differ.",
            "For ABP, compare ABD with ADE to obtain BP:PE, then take the corresponding fraction of ABE. Repeat with BCE and BEF for the next corner.",
            "Writing BD:DC=p:1, CE:EA=q:1 and AF:FB=r:1, the corner fractions are p/(pq+p+1), q/(qr+q+1) and r/(rp+r+1). Derive each from shared heights, then subtract their sum from 1.",
        ),
        "The final rung combines the whole chain: side divisions, shared-base heights, intersection ratios, area fractions, and a three-part subtraction without an equal-area shortcut.",
        "How did you organize the three calculations so that each ratio stayed attached to the correct corner? Compare your notation before comparing arithmetic.",
        "What condition on positive p, q and r makes the central area vanish? Use the corner-fraction expression to find a condition, rather than assuming all three ratios must be equal.",
        "Subtracting the three corner fractions and simplifying gives (pqr−1)²/[(pq+p+1)(qr+q+1)(rp+r+1)]. The denominators are positive, so the area vanishes exactly when pqr=1. The three dividing lines then meet at one point, even when the three ratios differ.",
        builds_on=(11, 12, 13),
    ),
    Session(
        "cevian_total_recovery", "unequal_three_cevians",
        "An area fraction can recover the missing whole before measuring the central region.",
        ("unequal three-line decomposition", "reversing an area fraction"),
        (
            "Day 14 gave the whole triangle's area. Here only one corner area is known. Can you first express that corner as a fraction of the whole?",
            "Write T for the unknown total. The side divisions still determine BP:PE and therefore the fraction of T occupied by ABP.",
            "For BD:DC=p:1 and CE:EA=q:1, ABP has fraction p/(pq+p+1). Divide its given area by this fraction to recover T, then find the other two corner areas and subtract all three.",
        ),
        "Keep the total symbolic until a known part fixes its scale. The remaining area calculations can then reuse the forward argument.",
        "Did you recover the total first, or express every other area directly as a multiple of ABP? Compare the two routes.",
        "Could a given area for BCQ or CAR replace the given ABP area?",
        "Yes. With positive side ratios, each corner occupies a known positive fraction of the total. Divide the given corner area by its own fraction, then use the recovered total.",
        builds_on=(8, 14),
    ),
    Session(
        "cevian_missing_ratio", "cevian_total_recovery",
        "Use an area measurement to recover an unstated geometric constraint.",
        ("shared-height area ratios", "inverse intersection reasoning", "unequal corner fractions"),
        (
            "Before locating D, use the known division of AC to find the area of ABE. How much of ABE remains outside ABP?",
            "ABP and APE share a height to BE, so their areas determine BP:PE. Now run the shared-base height argument backward to find BD:DC.",
            "Let X=area ABP and Y=area APE. If BD:DC=t:1 and CE:EA=q:1, then BP:PE=t(q+1):1. Thus t=X/[Y(q+1)]. Use this recovered ratio to calculate the remaining corners.",
        ),
        "An area can encode a missing side division. Recover the geometric constraint before applying the area decomposition.",
        "At which point did you know D's position was uniquely determined, without measuring it on the diagram?",
        "For fixed total T and CE:EA=q:1, what happens to ABP's area as BD:DC=t:1 increases?",
        "Its fraction t/[(q+1)t+1] increases toward 1/(q+1). Equivalently, it is 1/[q+1+1/t], whose denominator decreases. ABP approaches the whole of ABE without reaching it for a finite positive t.",
        builds_on=(11, 14, 15),
    ),
    Session(
        "cevian_double_recovery", "cevian_missing_ratio",
        "Recover the total and a hidden side division in the right dependency order.",
        ("inverse area scale", "inverse intersection ratio", "area partitions"),
        (
            "Two things are missing, but the known side divisions already fix ABP's fraction of the whole. Start with the unknown that this resolves.",
            "Once the total is known, find CAD and subtract the given CAR. The remaining triangle CDR shares its height to AD with CAR.",
            "Recover AR:RD as area CAR : area CDR. If AF:FB=t:1 and BD:DC=p:1, the shared-height argument gives AR:RD=t(p+1):1. Solve for t, then calculate BCQ and subtract the three corners.",
        ),
        "Resolve dependent unknowns in sequence: one known corner fixes the whole, a second fixes a line, and that line determines the remaining area.",
        "Which fact unlocked each stage? Could you explain why trying to recover the hidden side division first was less direct?",
        "With BD:DC=p:1 fixed, what upper bound must CAR's area satisfy for F to lie strictly inside AB?",
        "CAR is strictly smaller than CAD, whose area is T/(p+1). Their ratio is AR/AD<1. Equality would push R to D and require the limiting division AF:FB to be unbounded.",
        builds_on=(15, 16),
    ),
    Session(
        "cevian_corner_band", "cevian_parallel_band",
        "Compare two intersection positions on the same line before applying similarity.",
        ("recovering a whole area", "part-to-whole segment ratios", "squared similarity scales"),
        (
            "The shaded quadrilateral is ARC minus APS. The parallel sides make those two triangles similar, but their scale is AP:AR, not a ratio to all of AD.",
            "Recover the total from ABP. Use shared-height areas to find AP/AD, and a separate intersection comparison to find AR/AD.",
            "For side ratios p:1, q:1 and r:1, AP/AD=(p+1)/(pq+p+1) and AR/AD=r(p+1)/(rp+r+1). Divide these to get AP/AR. Square that scale to find APS as a fraction of ARC, then subtract.",
        ),
        "Two ratios measured from one vertex can be divided to change the reference segment. Only then do you have the linear scale that similarity needs.",
        "Where would using AP/AD directly as the similarity scale lead you astray? Draw the two reference triangles.",
        "What happens to the shaded band when pqr approaches 1 from above?",
        "AP/AR=(rp+r+1)/[r(pq+p+1)] tends to 1. P and R approach the same point, APS approaches ARC, and the shaded band shrinks to zero.",
        builds_on=(12, 15, 17),
    ),
    Session(
        "nested_three_cevians", "three_cevians",
        "Apply a familiar area argument again inside a triangle you first have to recover.",
        ("unequal outer corner fractions", "equal cyclic inner fractions", "changing the reference whole"),
        (
            "Treat this as two successive puzzles. First ignore the lines inside PQR and find the area of PQR itself.",
            "Now let PQR be the whole triangle. Its three side divisions are equal, so the argument from Day 13 applies even if this triangle looks irregular.",
            "For the inner 2:1 divisions, each corner PQX, QRY and RPZ occupies 2/7 of PQR. Subtract all three from PQR. Take care to apply these fractions to PQR's area, not ABC's.",
        ),
        "A derived figure can become the starting figure for a second proof. Fractions from successive layers multiply because their reference wholes differ.",
        "How did you keep the two sets of vertex names and the two whole areas separate?",
        "If another equal 2:1 construction were repeated inside XYZ, what fraction of XYZ would the new center occupy?",
        "It would occupy 1/7 of XYZ. After n such equal-division layers inside PQR, the remaining area is area(PQR)/7ⁿ; no equilateral-shape assumption is needed.",
        builds_on=(13, 14, 18),
    ),
    Session(
        "nested_unequal_cevians", "nested_three_cevians",
        "Coordinate two full area decompositions without an equal-corner shortcut in either layer.",
        ("nested reference triangles", "three unequal intersection arguments", "multiplying area fractions"),
        (
            "Find PQR from ABC first. Then look only at PQR and its internal side divisions; the inner corners no longer have equal areas.",
            "Rename the whole area K=area PQR. Derive PQX, QRY and RPZ separately, using the same shared-height comparisons as for the outer corners.",
            "If QU:UR=u:1, RV:VP=v:1 and PW:WQ=w:1, the inner corner fractions of K are u/(uv+u+1), v/(vw+v+1) and w/(wu+w+1). Subtract them from 1 and multiply by the previously found K.",
        ),
        "The proof can be reused across layers, but the ratios and the reference area must be reassigned each time. Each layer has its own three unequal corners.",
        "Did a table of ratios help more than repeatedly annotating the picture? Compare how you avoided mixing the layers.",
        "Would swapping the two sets of side ratios between the outer and inner layers change XYZ's fraction of ABC?",
        "No. Each set produces its own central-area fraction, independent of the starting triangle's shape. The two fractions multiply, so their order does not change the final area fraction, although the diagram and the intermediate area change.",
        builds_on=(14, 19),
    ),
    Session(
        "nested_cevian_recovery", "nested_unequal_cevians",
        "Reverse both layers from the smallest known area, then choose the correct complement.",
        ("two unequal decompositions", "inverse area scaling", "tracking nested complements"),
        (
            "The known area is at the very center, while the requested region is outside PQR. First determine the fraction retained by each layer without knowing either whole area.",
            "Work outward: divide XYZ's area by its fraction of PQR to recover PQR. Then divide by PQR's fraction of ABC to recover ABC.",
            "Let f be PQR/ABC and g be XYZ/PQR, found by the two three-corner decompositions. For given area X of XYZ, PQR=X/g and ABC=X/(fg). The requested frame is X/(fg)−X/g.",
        ),
        "The final rung combines forward geometric derivations, two inverse scale steps, and a complement whose inner boundary is the intermediate triangle.",
        "Which area would you accidentally subtract if you focused only on the known number? Explain the boundary of the requested shading before doing arithmetic.",
        "Suppose a third inner construction retains a fraction h of XYZ and its center has known area L. Express the same outer frame using f, g, h and L.",
        "Recover PQR=L/(gh) and ABC=L/(fgh). The outer frame is L/(fgh)−L/(gh)=L(1−f)/(fgh). Each reversed layer requires division by its own retained fraction.",
        builds_on=(15, 17, 20),
    ),
)


def _seed(seed: int, key: str) -> int:
    digest = hashlib.sha256(f"{SEED_NAMESPACE}:{seed}:{key}".encode()).digest()
    return int.from_bytes(digest[:4], "big")


def _verified_puzzles(seed: int) -> list[tuple[Puzzle, Puzzle | None]]:
    """Freeze a whole edition before writing it; no silent recipe substitution."""
    puzzles = []
    for day, session in enumerate(SESSIONS, 1):
        if any(prior < 1 or prior >= day for prior in session.builds_on):
            raise ValueError(f"Day {day} must build only on earlier sessions")
        # These two recipes sample the same side first. Keeping their seed
        # equal makes the deliberate area comparison exact, not coincidental.
        key = "paired-square" if day in (2, 3) else f"day-{day}"
        main = build(session.recipe, _seed(seed, key))
        warmup = build(session.warmup, _seed(seed, f"warmup-{day}")) if session.warmup else None
        puzzles.append((main, warmup))
    # Preserve the original week; the continuation must climb from its last
    # puzzle under the existing structural score as well as the authored ideas.
    scores = [score(main) for main, _ in puzzles[6:]]
    if any(after <= before for before, after in zip(scores, scores[1:])):
        raise ValueError("The continuation must increase in difficulty at every rung")
    for main, warmup in puzzles:
        for puzzle in (main, warmup):
            if puzzle is None:
                continue
            result = verify(puzzle, seed=puzzle.seed)
            if not result.ok:
                failed = [name for name, ok, _ in result.checks if not ok]
                raise RuntimeError(f"Pilot verification failed for {puzzle.recipe}: {failed}")
    return puzzles


def _write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _solution(puzzle: Puzzle) -> str:
    return f"**{puzzle.answer_display()}**\n\n" + "\n".join(
        f"{i}. {step}" for i, step in enumerate(puzzle.solution_steps, 1)
    )


def generate_pilot(seed: int, outdir: str) -> dict:
    """Export question pages, optional help, discussion, and a feedback sheet."""
    out = Path(outdir)
    if out.exists() and any(out.iterdir()):
        raise ValueError(f"{out} is not empty; choose a new folder to preserve your edition and notes")
    puzzles = _verified_puzzles(seed)
    (out / "images").mkdir(parents=True, exist_ok=True)
    records = []
    index = []
    for day, (session, (main, warmup)) in enumerate(zip(SESSIONS, puzzles), 1):
        slug = f"day-{day:02d}"
        # The Markdown/browser page carries the label, so the diagram stays plain.
        render(main, str(out / "images" / f"{slug}.png"), show_difficulty=False)
        warmup_link = ""
        if warmup:
            render(warmup, str(out / "images" / f"{slug}-warmup.png"), show_difficulty=False)
            warmup_link = f"[Optional warm-up](warmups/{slug}.md) · "
            _write(out / "warmups" / f"{slug}.md", (
                f"# Day {day} · optional warm-up\n\nEstimated difficulty: {warmup.difficulty_label}\n\n{warmup.question}\n\n"
                f"![Warm-up diagram](../images/{slug}-warmup.png)\n\n"
                f"[Warm-up explanation](../solutions/{slug}-warmup.md) · [Main puzzle](../{slug}.md)"
            ))
            _write(out / "solutions" / f"{slug}-warmup.md", (
                f"# Day {day} · warm-up explanation\n\n{_solution(warmup)}\n\n"
                f"[Main puzzle](../{slug}.md)"
            ))
        _write(out / f"{slug}.md", (
            f"# Day {day}\n\nEstimated difficulty: {main.difficulty_label}\n\n{main.question}\n\n"
            f"![Geometry diagram for Day {day}; the stated relationships and measurements are given in the question](images/{slug}.png)\n\n"
            "Use the stated relationships, not measurements taken from the drawing. "
            "An exact answer using π or square roots is welcome; a decimal is fine for discussion.\n\n"
            f"{warmup_link}[First hint](hints/{slug}-1.md) · "
            f"[Explanation and optional stretch](solutions/{slug}.md)\n\n"
            "You can stop with an idea, an unfinished attempt, or a solution. "
            "If solving separately, save your reasoning before comparing.\n\n"
            f"[All days](START_HERE.md) · [Record how it felt](FEEDBACK.md)"
        ))
        for level, hint in enumerate(session.hints, 1):
            next_link = (f"[Another hint]({slug}-{level+1}.md)" if level < 3
                         else f"[Explanation](../solutions/{slug}.md)")
            _write(out / "hints" / f"{slug}-{level}.md", (
                f"# Day {day} · hint {level}\n\n{hint}\n\n"
                f"[Back to the puzzle](../{slug}.md) · {next_link}"
            ))
        _write(out / "solutions" / f"{slug}.md", (
            f"# Day {day} · explanation\n\n{_solution(main)}\n\n"
            f"## The useful idea\n\n{session.takeaway}\n\n"
            f"## Compare notes\n\n{session.discuss}\n\n"
            f"## Optional stretch\n\n{session.extension}\n\n"
            f"[Stretch explanation]({slug}-stretch.md) · [Back to the puzzle](../{slug}.md)\n\n"
            f"[Record how it felt](../FEEDBACK.md)"
        ))
        _write(out / "solutions" / f"{slug}-stretch.md", (
            f"# Day {day} · stretch explanation\n\n{session.extension_answer}\n\n"
            f"[Back to today's explanation]({slug}.md)"
        ))
        record = main.to_record(image_path=f"images/{slug}.png")
        record.update({
            "day": day, "insight": session.insight,
            "prerequisites": list(session.prerequisites), "hints": list(session.hints),
            "takeaway": session.takeaway, "discussion": session.discuss,
            "extension": session.extension, "extension_answer": session.extension_answer,
            "warmup": warmup.to_record(image_path=f"images/{slug}-warmup.png") if warmup else None,
        })
        if session.builds_on:
            record["builds_on"] = list(session.builds_on)
        records.append(record)
        index.append(f"- [Day {day}]({slug}.md) · {main.difficulty_label} (estimated)")

    _write(out / "START_HERE.md", (
        f"# {len(SESSIONS)} days of geometry, for two\n\n"
        "One common puzzle each day, an optional warm-up when you want it, and a stretch after the explanation. "
        "Start on any day of the week and go in order. Missing a day creates no catch-up work.\n\n"
        "Allow roughly 10–20 minutes as an initial experiment, not a deadline. "
        "Try with paper and pencil. Work together, or use identical copies and compare your thinking afterward. "
        "Both people should use the same edition seed.\n\n"
        "Some sessions introduce an idea; others ask you to recognize it in a new setting. "
        "Later sessions may take longer. Warm-ups and hints are part of solving; use them freely.\n\n"
        "Days 8–21 form a harder ladder: each adds a reasoning step or combines ideas from earlier days. "
        "The Easy/Medium/Hard labels are broad estimates; the later Hard puzzles continue to increase in structural difficulty.\n\n"
        + "\n".join(index) + "\n\n"
        "The question pages do not print answers. Hints, explanations, and stretch answers open separately. "
        "The `editor.json` file contains all solutions; it is for reviewing the pack after solving.\n\n"
        "After each session, [record how it felt](FEEDBACK.md). This is a content playtest: "
        "it does not rate either player, schedule future puzzles, or sync progress between devices. "
        "Its purpose is to discover which kinds of puzzle make you want another day.\n\n"
        f"Edition: `{PILOT_VERSION}` · seed `{seed}`"
    ))
    rows = "\n".join(f"| {day} | | | | | | |" for day in range(1, len(SESSIONS) + 1))
    _write(out / "FEEDBACK.md", (
        "# How did it feel?\n\n"
        "Keep one copy per person, or write two entries per day. Use a separate notes file or paper "
        "if your Markdown viewer cannot edit. Record an unfinished attempt as honestly as a solve.\n\n"
        "Help: none / warm-up / hint 1–3 / explanation. Effort: light / fitting / stuck. "
        "Enjoyment: flat / pleasant / satisfying. The last three are different questions. "
        "Approximate time is optional and is not a competition.\n\n"
        "| Day | Person | Finished / paused / read solution | Help | Effort | Enjoyment | Click moment / want more? |\n"
        "| --- | --- | --- | --- | --- | --- | --- |\n" + rows + "\n\n"
        "After each week: Which puzzle would you send to a friend? Which felt like work? "
        "Did comparing explanations add something? Would you prefer one puzzle, several short rungs, "
        "or a harder puzzle you return to? Note familiarity as well: a puzzle you already know cannot calibrate a new insight."
    ))
    manifest = {"version": PILOT_VERSION, "seed": seed, "sessions": records}
    _write(out / "editor.json", json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"{len(SESSIONS)}-day pilot: {out / 'START_HERE.md'}")
    return manifest
