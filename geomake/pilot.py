"""An authored, seven-session playtest; a hypothesis about enjoyment, not a rating.

Question pages contain only public givens. Hints and explanations live in
separate files. The editor manifest deliberately contains spoilers.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from .puzzle import Puzzle
from .recipes import build
from .render import render
from .verify import verify

PILOT_VERSION = "first-week-v1"


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
)


def _seed(seed: int, key: str) -> int:
    digest = hashlib.sha256(f"{PILOT_VERSION}:{seed}:{key}".encode()).digest()
    return int.from_bytes(digest[:4], "big")


def _verified_puzzles(seed: int) -> list[tuple[Puzzle, Puzzle | None]]:
    """Freeze a whole edition before writing it; no silent recipe substitution."""
    puzzles = []
    for day, session in enumerate(SESSIONS, 1):
        # These two recipes sample the same side first. Keeping their seed
        # equal makes the deliberate area comparison exact, not coincidental.
        key = "paired-square" if day in (2, 3) else f"day-{day}"
        main = build(session.recipe, _seed(seed, key))
        warmup = build(session.warmup, _seed(seed, f"warmup-{day}")) if session.warmup else None
        puzzles.append((main, warmup))
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
        records.append(record)
        index.append(f"- [Day {day}]({slug}.md) · {main.difficulty_label} (estimated)")

    _write(out / "START_HERE.md", (
        "# Seven days of geometry, for two\n\n"
        "One common puzzle each day, an optional warm-up when you want it, and a stretch after the explanation. "
        "Start on any day of the week and go in order. Missing a day creates no catch-up work.\n\n"
        "Allow roughly 10–20 minutes as an initial experiment, not a deadline. "
        "Try with paper and pencil. Work together, or use identical copies and compare your thinking afterward. "
        "Both people should use the same edition seed.\n\n"
        "Some sessions introduce an idea; others ask you to recognize it in a new setting. "
        "Later sessions may take longer. Warm-ups and hints are part of solving; use them freely.\n\n"
        + "\n".join(index) + "\n\n"
        "The question pages do not print answers. Hints, explanations, and stretch answers open separately. "
        "The `editor.json` file contains all solutions; it is for reviewing the pack after solving.\n\n"
        "After each session, [record how it felt](FEEDBACK.md). This is a content playtest: "
        "it does not rate either player, schedule future puzzles, or sync progress between devices. "
        "Its purpose is to discover which kinds of puzzle make you want another day.\n\n"
        f"Edition: `{PILOT_VERSION}` · seed `{seed}`"
    ))
    rows = "\n".join(f"| {day} | | | | | | |" for day in range(1, 8))
    _write(out / "FEEDBACK.md", (
        "# How did it feel?\n\n"
        "Keep one copy per person, or write two entries per day. Use a separate notes file or paper "
        "if your Markdown viewer cannot edit. Record an unfinished attempt as honestly as a solve.\n\n"
        "Help: none / warm-up / hint 1–3 / explanation. Effort: light / fitting / stuck. "
        "Enjoyment: flat / pleasant / satisfying. The last three are different questions. "
        "Approximate time is optional and is not a competition.\n\n"
        "| Day | Person | Finished / paused / read solution | Help | Effort | Enjoyment | Click moment / want more? |\n"
        "| --- | --- | --- | --- | --- | --- | --- |\n" + rows + "\n\n"
        "After the week: Which puzzle would you send to a friend? Which felt like work? "
        "Did comparing explanations add something? Would you prefer one puzzle, several short rungs, "
        "or a harder puzzle you return to? Note familiarity as well: a puzzle you already know cannot calibrate a new insight."
    ))
    manifest = {"version": PILOT_VERSION, "seed": seed, "sessions": records}
    _write(out / "editor.json", json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"Seven-day pilot: {out / 'START_HERE.md'}")
    return manifest
