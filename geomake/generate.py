"""Batch generation: sample recipes at a difficulty, verify, render, export."""

from __future__ import annotations

import json
import random
from pathlib import Path

from .puzzle import Puzzle
from .recipes import RECIPES, build, by_depth
from .render import render
from .verify import verify

MAX_ATTEMPTS_PER_PUZZLE = 20


def generate_one(depth: int | None, rng: random.Random, recipe: str | None = None) -> Puzzle:
    """Build one verified puzzle; retries with fresh seeds on verify failure."""
    for _ in range(MAX_ATTEMPTS_PER_PUZZLE):
        if recipe is not None:
            name = recipe
        else:
            pool = by_depth(depth) if depth else list(RECIPES)
            name = rng.choice(pool)
        seed = rng.randrange(2**31)
        pz = build(name, seed)
        res = verify(pz, seed=seed)
        if res.ok:
            return pz
        failed = [c for c in res.checks if not c[1]]
        print(f"  ! verification failed for {name} (seed {seed}): {failed} — retrying")
    raise RuntimeError(f"could not generate a verified puzzle (depth={depth}, recipe={recipe})")


def generate_batch(
    n: int,
    depth: int | None,
    seed: int,
    outdir: str,
    recipe: str | None = None,
    show_answer: bool = False,
) -> list[dict]:
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    records = []
    for i in range(n):
        pz = generate_one(depth, rng, recipe=recipe)
        img = f"puzzle_{i:03d}_{pz.recipe}_d{pz.depth}.png"
        render(pz, str(out / img), show_answer=show_answer)
        rec = pz.to_record(image_path=img)
        rec["id"] = i
        records.append(rec)
        print(f"  [{i}] d{pz.depth} {pz.recipe}: {pz.answer_display()}")
    (out / "puzzles.json").write_text(json.dumps(records, indent=2, ensure_ascii=False))
    with (out / "puzzles.jsonl").open("w") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return records
