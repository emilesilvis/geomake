"""Check the public geometric relationships, including hidden-parameter freedom."""

from collections import defaultdict

import pytest
import sympy as sp

from geomake.core import P, dist, midpoint
from geomake.recipes import build
from geomake.scene import Scene


@pytest.mark.parametrize("name,public,hidden", [
    ("sliding_triangle", "rectangle_area", ("w", "h", "x")),
    ("tangent_chord_annulus", "chord", ("r",)),
    ("rotated_square_overlap", "a", ("angle",)),
])
def test_same_givens_allow_different_figures_but_only_one_answer(name, public, hidden):
    groups = defaultdict(list)
    for seed in range(40):
        puzzle = build(name, seed)
        groups[puzzle.params[public]].append(puzzle)
    nontrivial = 0
    for puzzles in groups.values():
        constructions = {tuple(p.params[k] for k in hidden) for p in puzzles}
        if len(constructions) > 1:
            nontrivial += 1
            answer = puzzles[0].answer_exact
            assert all(sp.simplify(p.answer_exact - answer) == 0 for p in puzzles)
    assert nontrivial >= 3, "exercise genuinely different hidden configurations"


@pytest.mark.parametrize("seed", range(6))
def test_tangent_chord_really_has_the_stated_endpoints_length_and_tangency(seed):
    puzzle = build("tangent_chord_annulus", seed)
    outer, inner = puzzle.scene.shapes["O"], puzzle.scene.shapes["I"]
    A, B = puzzle.scene.lines[0][:2]
    touch = midpoint(A, B)
    assert outer.center == inner.center
    assert sp.simplify(dist(A, B) - puzzle.params["chord"]) == 0
    assert sp.simplify(dist(A, outer.center) - outer.r) == 0
    assert sp.simplify(dist(B, outer.center) - outer.r) == 0
    assert sp.simplify(dist(touch, inner.center) - inner.r) == 0
    radius = (touch[0] - inner.center[0], touch[1] - inner.center[1])
    chord = (B[0] - A[0], B[1] - A[1])
    assert sp.simplify(radius[0] * chord[0] + radius[1] * chord[1]) == 0


@pytest.mark.parametrize("turn", range(16))
def test_quarter_overlap_holds_outside_the_generators_sampled_angles(turn):
    geometry = pytest.importorskip("shapely.geometry")
    scene = Scene()
    side = 8
    fixed = scene.place_square("fixed", side)
    turned = scene.place_rotated_square("turned", side, P(4, 4), turn * sp.pi / 8)
    assert all(sp.simplify(dist(turned.pts[i], turned.pts[(i + 1) % 4]) - side) == 0 for i in range(4))
    fixed_poly = geometry.Polygon(fixed.boundary())
    turned_poly = geometry.Polygon(turned.boundary())
    assert fixed_poly.intersection(turned_poly).area == pytest.approx(fixed_poly.area / 4)


def test_leaf_does_not_draw_the_solution_chord(tmp_path, monkeypatch):
    from geomake import render as renderer

    puzzle = build("leaf_lens", seed=7)
    drawn = []
    monkeypatch.setattr(renderer, "_outline", lambda ax, shape: drawn.append(shape.name))
    renderer.render(puzzle, str(tmp_path / "leaf.png"))
    assert set(drawn) == {"ABCD", "Q1", "Q2"}
    assert not puzzle.scene.lines
    assert puzzle.equal_region_claims, "verify the target equals the actual arc overlap"
