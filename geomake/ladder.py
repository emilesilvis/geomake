"""Graded easy->hard puzzle ladders with a validated difficulty ordering.

A ladder is a sequence of verified puzzles whose difficulty ramps gradually.
Difficulty is scored from recorded per-puzzle metadata (never guessed):

    score = (depth, solution steps, width, nonstandard shape, construction ops)

compared lexicographically.  The ladder is built to be monotone by
construction, then *independently validated*: every answer is re-verified
numerically, and the sequence itself is checked for monotonicity, gradual
depth increases, full easy->hard coverage, and recipe variety.  A ladder that
fails any check is rejected.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from .puzzle import Puzzle
from .recipes import RECIPES, build, by_depth
from .render import render
from .verify import verify

DEPTHS = (1, 2, 3)
MAX_ATTEMPTS_PER_CANDIDATE = 20


def score(pz: Puzzle) -> tuple:
    """Difficulty sort key, hardest components first (lexicographic)."""
    return (
        pz.depth,
        len(pz.solution_steps),
        pz.width,
        int(pz.nonstandard),
        len(pz.scene.ops),
    )


def _verified_build(name: str, rng: random.Random) -> Puzzle:
    for _ in range(MAX_ATTEMPTS_PER_CANDIDATE):
        seed = rng.randrange(2**31)
        pz = build(name, seed)
        if verify(pz, seed=seed).ok:
            return pz
    raise RuntimeError(f"could not build a verified {name} puzzle")


def _slots_per_depth(n: int) -> dict[int, int]:
    base, rem = divmod(n, len(DEPTHS))
    # remainder goes to the easy end: warming up beats a longer hard tail
    return {d: base + (1 if i < rem else 0) for i, d in enumerate(DEPTHS)}


def _pick_for_depth(depth: int, k: int, rng: random.Random) -> list[Puzzle]:
    """k verified puzzles at this depth, distinct recipes first, by score."""
    recipes = sorted(by_depth(depth))
    picked: list[Puzzle] = []
    while len(picked) < k:
        round_names = rng.sample(recipes, min(len(recipes), k - len(picked)))
        picked.extend(_verified_build(name, rng) for name in round_names)
    picked.sort(key=score)
    return picked


def build_ladder(n: int, seed: int) -> list[Puzzle]:
    if n < len(DEPTHS):
        raise ValueError(f"a ladder needs at least {len(DEPTHS)} puzzles to span all depths")
    rng = random.Random(seed)
    slots = _slots_per_depth(n)
    return [pz for d in DEPTHS for pz in _pick_for_depth(d, slots[d], rng)]


def validate_ladder(puzzles: list[Puzzle]) -> list[tuple[str, bool, str]]:
    """Independent checks on the finished sequence: (name, ok, detail)."""
    checks = []

    bad = [pz.recipe for pz in puzzles if not verify(pz, seed=pz.seed).ok]
    checks.append(("answers_verified", not bad, f"re-verification failed: {bad}" if bad else f"all {len(puzzles)} answers re-verified numerically"))

    scores = [score(pz) for pz in puzzles]
    drops = [i for i in range(1, len(scores)) if scores[i] < scores[i - 1]]
    checks.append(("difficulty_monotone", not drops, f"difficulty drops at positions {drops}" if drops else "difficulty score never decreases"))

    depths = [pz.depth for pz in puzzles]
    jumps = [i for i in range(1, len(depths)) if depths[i] - depths[i - 1] > 1]
    checks.append(("gradual_depth", not jumps, f"depth jumps by >1 at positions {jumps}" if jumps else "depth never jumps by more than one level"))

    covered = set(depths)
    checks.append(("covers_full_range", covered == set(DEPTHS), f"depths present: {sorted(covered)} (want {list(DEPTHS)})"))

    counts: dict[str, int] = {}
    for pz in puzzles:
        counts[pz.recipe] = counts.get(pz.recipe, 0) + 1
    per_depth_slots = _slots_per_depth(len(puzzles))
    max_repeat = max(2, max((-(-per_depth_slots[d] // len(by_depth(d))) for d in DEPTHS)))
    overused = {r: c for r, c in counts.items() if c > max_repeat}
    checks.append(("recipe_variety", not overused, f"recipes overused: {overused}" if overused else f"no recipe appears more than {max_repeat} times"))

    return checks


def generate_ladder(n: int, seed: int, outdir: str, max_rebuilds: int = 5) -> dict:
    """Build, validate, render, and export a ladder; returns the manifest."""
    for attempt in range(max_rebuilds):
        puzzles = build_ladder(n, seed + attempt)
        checks = validate_ladder(puzzles)
        if all(ok for _, ok, _ in checks):
            break
        failed = [name for name, ok, _ in checks if not ok]
        print(f"  ! ladder validation failed ({failed}) — rebuilding")
    else:
        raise RuntimeError(f"could not build a valid ladder after {max_rebuilds} attempts")

    out = Path(outdir)
    (out / "answers").mkdir(parents=True, exist_ok=True)
    entries = []
    for i, pz in enumerate(puzzles, start=1):
        stem = f"{i:02d}_{pz.recipe}_d{pz.depth}"
        render(pz, str(out / f"q{stem}.png"))
        render(pz, str(out / "answers" / f"a{stem}.png"), show_answer=True)
        rec = pz.to_record(image_path=f"q{stem}.png")
        rec["rank"] = i
        rec["answer_image"] = f"answers/a{stem}.png"
        rec["difficulty"]["score"] = list(score(pz))
        entries.append(rec)
        print(f"  [{i:02d}] d{pz.depth} {pz.recipe:28s} score={score(pz)}")

    manifest = {
        "n": n,
        "seed": seed,
        "validation": [{"check": name, "ok": ok, "detail": detail} for name, ok, detail in checks],
        "puzzles": entries,
    }
    (out / "ladder.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    for name, ok, detail in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}: {detail}")
    return manifest
