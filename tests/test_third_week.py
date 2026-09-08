"""Inverse and nested puzzles are uniquely determined by their public facts."""

from collections import defaultdict

import pytest
import sympy as sp

from geomake.core import Polygon, dist
from geomake.recipes import build


RECIPES = (
    "cevian_total_recovery", "cevian_missing_ratio", "cevian_double_recovery",
    "cevian_corner_band", "nested_three_cevians", "nested_unequal_cevians",
    "nested_cevian_recovery",
)


def area(*points):
    return abs(Polygon(pts=points).area())


def segment_fraction(point, a, b):
    dx, dy = b[0]-a[0], b[1]-a[1]
    px, py = point[0]-a[0], point[1]-a[1]
    assert sp.simplify(dx*py-dy*px) == 0
    fraction = sp.simplify((px*dx+py*dy)/(dx*dx+dy*dy))
    assert 0 < fraction < 1
    return fraction


def divisions_and_intersections(points, vertices, feet, crossings, ratios):
    for i in range(3):
        a, b, c = (points[vertices[(i+j) % 3]] for j in range(3))
        d, e = (points[feet[(i+j) % 3]] for j in range(2))
        x = points[crossings[i]]
        segment_fraction(d, b, c)
        assert sp.simplify(dist(b, d)/dist(d, c)) == ratios[i]
        segment_fraction(x, a, d)
        segment_fraction(x, b, e)


@pytest.mark.parametrize("seed", range(6))
@pytest.mark.parametrize("name", RECIPES)
def test_public_relationships_and_independently_derived_answers(name, seed):
    puzzle = build(name, seed)
    points, params = puzzle.scene.points, puzzle.params
    A, B, C, D, E, F, P, Q, R = (points[n] for n in "ABCDEFPQR")
    p, q, r = (params[n] for n in "pqr")
    divisions_and_intersections(points, "ABC", "DEF", "PQR", (p, q, r))
    measured_total = area(A, B, C)
    center_fraction = lambda a, b, c: sp.Rational(
        (a*b*c-1)**2, (a*b+a+1)*(b*c+b+1)*(c*a+c+1),
    )
    if name == "cevian_missing_ratio":
        # Derive the hidden p using only the public T, X and q.
        total, x = params["total_area"], params["abp_area"]
        y = sp.Rational(total, q+1)-x
        p = sp.simplify(x/(y*(q+1)))
        assert p == params["p"]
    elif name.startswith("cevian_"):
        x = params["abp_area"]
        total = x * sp.Rational(p*q+p+1, p)
        assert area(A, B, P) == x
        if name == "cevian_double_recovery":
            # The total must be recovered before the hidden r can be found.
            z = params["car_area"]
            assert area(C, A, R) == z
            r = sp.simplify(z / ((total/(p+1)-z)*(p+1)))
            assert r == params["r"]
    else:
        u, v, w = (params[n] for n in "uvw")
        divisions_and_intersections(points, "PQR", "UVW", "XYZ", (u, v, w))
        X, Y, Z = (points[n] for n in "XYZ")
        inner_fraction = center_fraction(u, v, w)
        if name == "nested_cevian_recovery":
            known = params["xyz_area"]
            assert area(X, Y, Z) == known
            total = known / (inner_fraction*center_fraction(p, q, r))
        else:
            total = params["total_area"]
        assert area(X, Y, Z) == total*center_fraction(p, q, r)*inner_fraction
    assert measured_total == total
    assert area(P, Q, R) == total*center_fraction(p, q, r)
    if name == "cevian_corner_band":
        S = points["S"]
        ap, ar = segment_fraction(P, A, D), segment_fraction(R, A, D)
        assert ap < ar
        assert segment_fraction(S, A, C) == ap/ar
        assert sp.simplify((S[0]-P[0])*(C[1]-R[1])-(S[1]-P[1])*(C[0]-R[0])) == 0
        expected = total*sp.Rational(r, r*p+r+1)*(1-(ap/ar)**2)
    elif name == "nested_cevian_recovery":
        expected = total*(1-center_fraction(p, q, r))
    elif name.startswith("nested_"):
        expected = total*center_fraction(p, q, r)*inner_fraction
    else:
        expected = total*center_fraction(p, q, r)
    assert sp.simplify(puzzle.answer_exact-expected) == 0


@pytest.mark.parametrize("name", RECIPES)
def test_identical_public_facts_allow_different_drawings_but_only_one_answer(name):
    groups = defaultdict(list)
    for seed in range(60):
        puzzle = build(name, seed)
        groups[puzzle.question].append(puzzle)
    varied = 0
    for puzzles in groups.values():
        if len({tuple(p.scene.points.values()) for p in puzzles}) > 1:
            varied += 1
            assert len({p.answer_exact for p in puzzles}) == 1
    assert varied >= 3


def test_reversed_rung_is_rejected_before_export(tmp_path, monkeypatch):
    from geomake import pilot

    sessions = list(pilot.SESSIONS)
    sessions[15], sessions[16] = sessions[16], sessions[15]
    # Isolate the difficulty guard from the separate prerequisite guard.
    from dataclasses import replace

    monkeypatch.setattr(pilot, "SESSIONS", tuple(replace(s, builds_on=()) for s in sessions))
    out = tmp_path / "bad-order"
    with pytest.raises(ValueError, match="increase in difficulty"):
        pilot.generate_pilot(7, str(out))
    assert not out.exists()
