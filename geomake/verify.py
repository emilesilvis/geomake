"""Numerical verification of generated puzzles.

The generator's exact answers rest on construction-time assumptions
(containment, disjointness, claimed region equalities).  This module
instantiates the figure with concrete floats and checks every claim
independently:

  * area targets   — true set-semantics area (shapely boolean ops if
                     available, else Monte Carlo on the region indicator)
                     must match the exact symbolic answer;
  * length/angle   — re-measured from float coordinates;
  * assumptions    — subset/disjoint/equal-region checked pointwise.

A puzzle that fails any check is rejected by the generator.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from .core import Region, pfloat
from .puzzle import Puzzle

try:
    from shapely.geometry import Polygon as ShPolygon
    from shapely.ops import unary_union

    HAVE_SHAPELY = True
except Exception:  # pragma: no cover
    HAVE_SHAPELY = False

AREA_RTOL = 5e-4
MC_RTOL = 3e-2
MC_SAMPLES = 60_000


@dataclass
class VerifyResult:
    ok: bool
    checks: list = field(default_factory=list)  # (name, ok, detail)

    def add(self, name: str, ok: bool, detail: str = ""):
        self.checks.append((name, ok, detail))
        if not ok:
            self.ok = False


# ---------------------------------------------------------------------------
# shapely backend


def _shape_to_shapely(shape, n=2048):
    pts = shape.boundary(n)
    return ShPolygon(pts).buffer(0)


def _region_to_shapely(region: Region):
    if region.kind == "prim":
        return _shape_to_shapely(region.shape)
    parts = [_region_to_shapely(p) for p in region.parts]
    if region.kind == "diff":
        g = parts[0]
        for h in parts[1:]:
            g = g.difference(h)
        return g
    if region.kind == "union":
        return unary_union(parts)
    if region.kind == "inter":
        g = parts[0]
        for h in parts[1:]:
            g = g.intersection(h)
        return g
    raise ValueError(region.kind)


# ---------------------------------------------------------------------------
# Monte Carlo backend (independent of shapely; uses region indicator only)


def _mc_area(contains, bbox, rng: random.Random, n=MC_SAMPLES) -> float:
    x0, y0, x1, y1 = bbox
    box = (x1 - x0) * (y1 - y0)
    hits = sum(
        1 for _ in range(n) if contains(x0 + rng.random() * (x1 - x0), y0 + rng.random() * (y1 - y0))
    )
    return box * hits / n


def _bbox_union(a, b):
    return (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))


# ---------------------------------------------------------------------------


def _check_area(res: VerifyResult, region: Region, exact: float, rng: random.Random):
    if HAVE_SHAPELY:
        got = _region_to_shapely(region).area
        rel = abs(got - exact) / max(abs(exact), 1e-12)
        res.add("area(shapely)", rel < AREA_RTOL, f"exact={exact:.6f} measured={got:.6f}")
    got_mc = _mc_area(region.contains_pt, region.bbox(), rng)
    rel = abs(got_mc - exact) / max(abs(exact), 1e-12)
    res.add("area(mc)", rel < MC_RTOL, f"exact={exact:.6f} mc={got_mc:.6f}")


def _check_relation(res: VerifyResult, rel: str, a: Region, b: Region, rng: random.Random):
    """subset: a ⊆ b;  disjoint: interiors of a, b do not overlap."""
    if HAVE_SHAPELY:
        ga, gb = _region_to_shapely(a), _region_to_shapely(b)
        if rel == "subset":
            leak = ga.difference(gb.buffer(1e-6)).area
            res.add("subset", leak < AREA_RTOL * max(ga.area, 1e-9), f"leak={leak:.2e}")
        else:
            ov = ga.intersection(gb).area
            res.add("disjoint", ov < AREA_RTOL * max(ga.area + gb.area, 1e-9), f"overlap={ov:.2e}")
        return
    # MC fallback
    bbox = _bbox_union(a.bbox(), b.bbox())
    x0, y0, x1, y1 = bbox
    bad = 0
    n = MC_SAMPLES // 3
    for _ in range(n):
        x = x0 + rng.random() * (x1 - x0)
        y = y0 + rng.random() * (y1 - y0)
        ia, ib = a.contains_pt(x, y), b.contains_pt(x, y)
        if rel == "subset" and ia and not ib:
            bad += 1
        if rel == "disjoint" and ia and ib:
            bad += 1
    res.add(rel, bad / n < 5e-3, f"bad_frac={bad/n:.4f}")


def _check_equal_region(res: VerifyResult, claimed: Region, true: Region, rng: random.Random):
    if HAVE_SHAPELY:
        gc, gt = _region_to_shapely(claimed), _region_to_shapely(true)
        xor = gc.symmetric_difference(gt).area
        res.add("equal_region", xor < AREA_RTOL * max(gt.area, 1e-9), f"xor={xor:.2e}")
        return
    bbox = _bbox_union(claimed.bbox(), true.bbox())
    x0, y0, x1, y1 = bbox
    bad = 0
    n = MC_SAMPLES // 3
    for _ in range(n):
        x = x0 + rng.random() * (x1 - x0)
        y = y0 + rng.random() * (y1 - y0)
        if claimed.contains_pt(x, y) != true.contains_pt(x, y):
            bad += 1
    res.add("equal_region", bad / n < 5e-3, f"bad_frac={bad/n:.4f}")


def verify(puzzle: Puzzle, seed: int = 0) -> VerifyResult:
    rng = random.Random(seed ^ 0x5EED)
    res = VerifyResult(ok=True)
    t = puzzle.target
    exact = float(puzzle.answer_exact)

    if t.kind == "area":
        _check_area(res, t.region, exact, rng)
        for rel, a, b in t.region.assumptions():
            _check_relation(res, rel, a, b, rng)
    elif t.kind == "length":
        (x1, y1), (x2, y2) = pfloat(t.p1), pfloat(t.p2)
        got = math.hypot(x2 - x1, y2 - y1)
        res.add("length", abs(got - exact) < 1e-8 * max(1.0, exact), f"{got} vs {exact}")
    elif t.kind == "angle":
        (vx, vy) = pfloat(t.vertex)
        (x1, y1), (x2, y2) = pfloat(t.p1), pfloat(t.p2)
        a1 = math.atan2(y1 - vy, x1 - vx)
        a2 = math.atan2(y2 - vy, x2 - vx)
        got = abs(a1 - a2)
        got = min(got, 2 * math.pi - got)
        res.add("angle", abs(got - exact) < 1e-9 + 1e-8 * exact, f"{got} vs {exact}")

    for claimed, true in puzzle.equal_region_claims:
        _check_equal_region(res, claimed, true, rng)

    # sanity: positive answers only (a degenerate construction would show here)
    res.add("positive_answer", exact > 1e-9, f"answer={exact}")
    return res
