"""The second chapter is determined by public facts, not hidden coordinates."""

from collections import defaultdict

import pytest
import sympy as sp

from geomake.core import Polygon, dist
from geomake.recipes import build


def area(*points):
    return abs(Polygon(pts=points).area())


def on_segment(point, start, end):
    dx, dy = end[0] - start[0], end[1] - start[1]
    px, py = point[0] - start[0], point[1] - start[1]
    assert sp.simplify(dx * py - dy * px) == 0
    fraction = sp.simplify((px*dx + py*dy) / (dx*dx + dy*dy))
    assert 0 < fraction < 1


@pytest.mark.parametrize("seed", range(6))
def test_frame_has_the_stated_side_divisions_and_inner_area(seed):
    puzzle = build("tilted_square_frame", seed)
    outer = puzzle.scene.shapes["ABCD"]
    inner = puzzle.scene.shapes["EFGH"]
    p, q = puzzle.params["p"], puzzle.params["q"]
    assert inner.area() == puzzle.params["inner_area"]
    assert len({sp.simplify(dist(inner.pts[i], inner.pts[(i+1) % 4])) for i in range(4)}) == 1
    for i, point in enumerate(inner.pts):
        a, b = outer.pts[i], outer.pts[(i+1) % 4]
        on_segment(point, a, b)
        assert sp.simplify(dist(a, point) / dist(point, b)) == sp.Rational(p, q)
    assert puzzle.answer_exact == sp.Rational(2*p*q, p*p+q*q) * inner.area()


@pytest.mark.parametrize("seed", range(6))
def test_trapezoid_parallel_sides_crossing_and_given_areas(seed):
    puzzle = build("crossed_trapezoid", seed)
    A, B, C, D, O = (puzzle.scene.points[n] for n in "ABCDO")
    assert A[1] == B[1] and C[1] == D[1]
    on_segment(O, A, C)
    on_segment(O, B, D)
    top, bottom = puzzle.params["top_area"], puzzle.params["bottom_area"]
    assert area(C, D, O) == top
    assert area(A, B, O) == bottom
    assert area(A, O, D) == area(B, O, C) == sp.sqrt(top * bottom)
    assert puzzle.answer_exact == 2 * sp.sqrt(top * bottom)


@pytest.mark.parametrize("name", [
    "crossing_cevians", "cevian_area_recovery", "cevian_parallel_band",
    "three_cevians", "unequal_three_cevians",
])
@pytest.mark.parametrize("seed", range(6))
def test_triangle_divisions_intersections_and_public_area_derivations(name, seed):
    puzzle = build(name, seed)
    points = puzzle.scene.points
    A, B, C, D, E, P = (points[n] for n in "ABCDEP")
    p = puzzle.params.get("p", puzzle.params.get("ratio"))
    q = puzzle.params.get("q", puzzle.params.get("ratio", 1))
    on_segment(D, B, C)
    on_segment(E, C, A)
    on_segment(P, A, D)
    on_segment(P, B, E)
    assert sp.simplify(dist(B, D) / dist(D, C)) == p
    assert sp.simplify(dist(C, E) / dist(E, A)) == q
    total = area(A, B, C)
    if "total_area" in puzzle.params:
        assert total == puzzle.params["total_area"]
    if name == "crossing_cevians":
        assert puzzle.answer_exact == total * p / (2*p+1)
    elif name == "cevian_area_recovery":
        x, y = puzzle.params["abp_area"], puzzle.params["ape_area"]
        assert area(A, B, P) == x
        assert area(A, P, E) == y
        assert puzzle.answer_exact == sp.Rational(x*x, x+2*y)
    elif name == "cevian_parallel_band":
        F, G, H = (points[n] for n in "FGH")
        on_segment(F, A, C)
        on_segment(G, A, B)
        on_segment(H, A, B)
        assert G[1] == P[1] == F[1]
        assert H[1] == E[1]
        assert puzzle.answer_exact == total * (sp.Rational(p+1, 2*p+1)**2 - sp.Rational(1, 4))
    else:
        F, Q, R = (points[n] for n in "FQR")
        r = puzzle.params.get("r", puzzle.params.get("ratio"))
        on_segment(F, A, B)
        on_segment(Q, B, E)
        on_segment(Q, C, F)
        on_segment(R, C, F)
        on_segment(R, A, D)
        assert sp.simplify(dist(A, F) / dist(F, B)) == r
        fraction = sp.Rational((p*q*r-1)**2, (p*q+p+1)*(q*r+q+1)*(r*p+r+1))
        assert puzzle.answer_exact == total * fraction
        assert area(A, B, P) + area(B, C, Q) + area(C, A, R) + puzzle.answer_exact == total


@pytest.mark.parametrize("name", [
    "crossed_trapezoid", "crossing_cevians", "cevian_area_recovery",
    "cevian_parallel_band", "three_cevians", "unequal_three_cevians",
])
def test_identical_questions_survive_different_unrevealed_figures(name):
    groups = defaultdict(list)
    for seed in range(60):
        puzzle = build(name, seed)
        groups[puzzle.question].append(puzzle)
    varied = 0
    for puzzles in groups.values():
        figures = {tuple(p.scene.points.values()) for p in puzzles}
        if len(figures) > 1:
            varied += 1
            assert len({p.answer_exact for p in puzzles}) == 1
    assert varied >= 3
