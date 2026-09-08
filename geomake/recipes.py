"""Puzzle recipes: parameterized backwards constructions.

Each recipe samples small integer parameters, builds the figure from them
(the answer is therefore free by construction), chooses which givens to
reveal, and emits the solution chain.  Difficulty metadata follows the
GeomVerse convention: depth = length of the deduction chain, width = max
sub-results feeding one step.
"""

from __future__ import annotations

import math
import random

import sympy as sp

from .core import P, Polygon, Region, dist, fmt_exact, midpoint
from .puzzle import Given, Puzzle, Target
from .scene import Scene

RECIPES: dict = {}  # name -> (fn, depth)


def recipe(name: str, depth: int):
    def deco(fn):
        RECIPES[name] = (fn, depth)
        return fn

    return deco


def _side(label, p1, p2, outside=True):
    return Given(label=label, kind="side", p1=p1, p2=p2, outside=outside)


def _num(x):
    return fmt_exact(sp.sympify(x))


# ============================================================ depth 1


@recipe("rect_area", 1)
def rect_area(rng: random.Random) -> Puzzle:
    w = rng.randint(4, 12)
    h = rng.choice([x for x in range(3, 10) if x != w])
    S = Scene()
    r = S.place_rect("ABCD", w, h)
    a, b, c, d = r.pts
    return Puzzle(
        recipe="rect_area",
        question=f"A rectangle is {w} cm long and {h} cm wide. Find the shaded area.",
        scene=S,
        target=Target("area", region=Region.prim(r)),
        givens=[_side(f"{w}", a, b), _side(f"{h}", b, c)],
        solution_steps=[f"Area of rectangle = {w} × {h} = {w*h} cm²"],
        depth=1,
        width=1,
        params={"w": w, "h": h},
    )


@recipe("tri_right_area", 1)
def tri_right_area(rng: random.Random) -> Puzzle:
    a = rng.randint(4, 12)
    b = rng.choice([x for x in range(3, 10) if x != a])
    S = Scene()
    t = S.place_right_triangle("ABC", a, b)
    A, B, C = t.pts
    ans = sp.Rational(a * b, 2)
    return Puzzle(
        recipe="tri_right_area",
        question=f"A right triangle has legs {a} cm and {b} cm. Find the shaded area.",
        scene=S,
        target=Target("area", region=Region.prim(t)),
        givens=[_side(f"{a}", A, B), _side(f"{b}", A, C)],
        solution_steps=[f"Area = ½ × {a} × {b} = {_num(ans)} cm²"],
        depth=1,
        width=1,
        params={"a": a, "b": b},
    )


@recipe("circle_area", 1)
def circle_area(rng: random.Random) -> Puzzle:
    r = rng.randint(2, 9)
    S = Scene()
    c = S.place_circle("O", (0, 0), r)
    rim = P(r * sp.cos(sp.pi / 6), r * sp.sin(sp.pi / 6))
    S.add_line(c.center, rim)
    return Puzzle(
        recipe="circle_area",
        question=f"A circle has radius {r} cm. Find the shaded area.",
        scene=S,
        target=Target("area", region=Region.prim(c)),
        givens=[Given(label=f"{r}", kind="radius", p1=c.center, p2=rim)],
        solution_steps=[f"Area = πr² = π × {r}² = {r*r}π ≈ {float(sp.pi*r*r):.2f} cm²"],
        depth=1,
        width=1,
        params={"r": r},
    )


@recipe("triangle_angle_sum", 1)
def triangle_angle_sum(rng: random.Random) -> Puzzle:
    alpha = rng.randrange(30, 80, 5)
    beta = rng.randrange(30, 80, 5)
    gamma = 180 - alpha - beta
    c = 8
    ta, tb = sp.tan(sp.rad(alpha)), sp.tan(sp.rad(beta))
    x = sp.simplify(c * tb / (ta + tb))
    y = sp.simplify(x * ta)
    S = Scene()
    t = S.place_triangle("ABC", [(0, 0), (c, 0), (x, y)])
    A, B, C = t.pts
    return Puzzle(
        recipe="triangle_angle_sum",
        question=(
            f"In the triangle, two angles measure {alpha}° and {beta}°. "
            "Find the angle marked with a question mark."
        ),
        scene=S,
        target=Target("angle", vertex=C, p1=A, p2=B, value=sp.rad(gamma)),
        givens=[
            Given(label=f"{alpha}°", kind="angle", vertex=A, p1=B, p2=C),
            Given(label=f"{beta}°", kind="angle", vertex=B, p1=A, p2=C),
        ],
        solution_steps=[f"Angles in a triangle sum to 180°: 180 − {alpha} − {beta} = {gamma}°"],
        depth=1,
        width=1,
        params={"alpha": alpha, "beta": beta},
    )


@recipe("square_diagonal", 1)
def square_diagonal(rng: random.Random) -> Puzzle:
    a = rng.randint(3, 12)
    S = Scene()
    sq = S.place_square("ABCD", a)
    A, B, C, D = sq.pts
    S.add_line(A, C, style="dashed")
    ans = sp.sqrt(2) * a
    return Puzzle(
        recipe="square_diagonal",
        question=f"A square has side {a} cm. How long is its diagonal?",
        scene=S,
        target=Target("length", p1=A, p2=C),
        givens=[_side(f"{a}", A, B)],
        solution_steps=[
            f"Pythagoras: d = √({a}² + {a}²) = {a}√2 ≈ {float(ans):.2f} cm",
        ],
        depth=1,
        width=1,
        params={"a": a},
    )


# ============================================================ depth 2


@recipe("square_minus_incircle", 2)
def square_minus_incircle(rng: random.Random) -> Puzzle:
    a = rng.randrange(4, 14, 2)
    S = Scene()
    sq = S.place_square("ABCD", a)
    c = S.inscribe_circle_in_square("O", sq)
    A, B, _, _ = sq.pts
    r = a // 2
    region = Region.diff(sq, c)
    return Puzzle(
        recipe="square_minus_incircle",
        question=(
            f"A circle is inscribed in a square of side {a} cm. "
            "Find the shaded area (inside the square, outside the circle)."
        ),
        scene=S,
        target=Target("area", region=region),
        givens=[_side(f"{a}", A, B)],
        solution_steps=[
            f"Square area = {a}² = {a*a} cm²",
            f"Inscribed circle radius = {a}/2 = {r}, so circle area = π × {r}² = {r*r}π cm²",
            f"Shaded = {a*a} − {r*r}π ≈ {float(a*a - sp.pi*r*r):.2f} cm²",
        ],
        depth=2,
        width=2,
        params={"a": a},
    )


@recipe("rect_minus_semicircle", 2)
def rect_minus_semicircle(rng: random.Random) -> Puzzle:
    h = rng.randrange(4, 12, 2)
    w = rng.randint(max(4, h // 2 + 2), 14)
    S = Scene()
    r_ = S.place_rect("ABCD", w, h)
    A, B, C, D = r_.pts
    semi = S.semicircle_on_side("S", B, C)  # diameter = right side, bulges inward
    rad = h // 2
    region = Region.diff(r_, semi)
    return Puzzle(
        recipe="rect_minus_semicircle",
        question=(
            f"A semicircle is cut out of a {w} cm × {h} cm rectangle; its diameter "
            "is the right side of the rectangle. Find the shaded area."
        ),
        scene=S,
        target=Target("area", region=region),
        givens=[_side(f"{w}", A, B), _side(f"{h}", B, C)],
        solution_steps=[
            f"Rectangle area = {w} × {h} = {w*h} cm²",
            f"Semicircle radius = {h}/2 = {rad}, area = π × {rad}²/2 = {_num(sp.Rational(rad**2,2))}π cm²",
            f"Shaded = {w*h} − {_num(sp.Rational(rad**2,2))}π ≈ {float(w*h - sp.pi*rad**2/2):.2f} cm²",
        ],
        depth=2,
        width=2,
        nonstandard=True,
        params={"w": w, "h": h},
    )


@recipe("circle_minus_insquare", 2)
def circle_minus_insquare(rng: random.Random) -> Puzzle:
    r = rng.randint(2, 8)
    S = Scene()
    c = S.place_circle("O", (0, 0), r)
    sq = S.inscribe_square_in_circle("PQRS", c, tilted=True)
    rim = P(r * sp.cos(sp.pi / 3), r * sp.sin(sp.pi / 3))
    S.add_line(c.center, rim)
    region = Region.diff(c, sq)
    return Puzzle(
        recipe="circle_minus_insquare",
        question=(
            f"A square is inscribed in a circle of radius {r} cm. "
            "Find the shaded area (inside the circle, outside the square)."
        ),
        scene=S,
        target=Target("area", region=region),
        givens=[Given(label=f"{r}", kind="radius", p1=c.center, p2=rim)],
        solution_steps=[
            f"Circle area = π × {r}² = {r*r}π cm²",
            f"The square's diagonal is a diameter = {2*r}, so its area = {2*r}²/2 = {2*r*r} cm²",
            f"Shaded = {r*r}π − {2*r*r} ≈ {float(sp.pi*r*r - 2*r*r):.2f} cm²",
        ],
        depth=2,
        width=2,
        params={"r": r},
    )


@recipe("l_shape", 2)
def l_shape(rng: random.Random) -> Puzzle:
    w = rng.randint(7, 14)
    h = rng.randint(6, 12)
    cw = rng.randint(2, w - 3)
    ch = rng.randint(2, h - 3)
    S = Scene()
    outer = S.place_rect("ABCD", w, h)
    notch = S.place_rect("PQRS", cw, ch, origin=(w - cw, h - ch))
    A, B, C, D = outer.pts
    Pn, Qn, Rn, Sn = notch.pts
    region = Region.diff(outer, notch)
    ans = w * h - cw * ch
    return Puzzle(
        recipe="l_shape",
        question=(
            f"A {cw} cm × {ch} cm rectangle is removed from the corner of a "
            f"{w} cm × {h} cm rectangle. Find the shaded area."
        ),
        scene=S,
        target=Target("area", region=region),
        givens=[
            _side(f"{w}", A, B),
            _side(f"{h}", D, A),
            _side(f"{cw}", Sn, Rn),
            _side(f"{ch}", Qn, Rn),
        ],
        solution_steps=[
            f"Full rectangle = {w} × {h} = {w*h} cm²",
            f"Removed corner = {cw} × {ch} = {cw*ch} cm²",
            f"Shaded = {w*h} − {cw*ch} = {ans} cm²",
        ],
        depth=2,
        width=2,
        nonstandard=True,
        params={"w": w, "h": h, "cw": cw, "ch": ch},
    )


@recipe("overlap_squares_center", 2)
def overlap_squares_center(rng: random.Random) -> Puzzle:
    a = rng.randrange(4, 14, 2)
    S = Scene()
    s1 = S.place_square("ABCD", a)
    s2 = S.place_square("EFGH", a, origin=(sp.Rational(a, 2), sp.Rational(a, 2)))
    ov = S.overlap_rect_of_squares("OV", s1, s2)
    A, B, _, _ = s1.pts
    region = Region.prim(ov)
    true_region = Region.inter(s1, s2)
    half = a // 2
    return Puzzle(
        recipe="overlap_squares_center",
        question=(
            f"Two squares of side {a} cm overlap: a corner of one lies exactly at "
            "the center of the other, and their corresponding sides are parallel. "
            "Find the shaded overlap area."
        ),
        scene=S,
        target=Target("area", region=region),
        givens=[_side(f"{a}", A, B)],
        solution_steps=[
            f"The overlapping corner sits at the center, so the overlap is a "
            f"{half} × {half} square",
            f"Shaded = {half}² = {half*half} cm²",
        ],
        depth=2,
        width=2,
        params={"a": a},
        equal_region_claims=[(region, true_region)],
    )


@recipe("isosceles_base_angle", 2)
def isosceles_base_angle(rng: random.Random) -> Puzzle:
    gamma = rng.randrange(20, 122, 2)  # apex angle, even -> integer base angles
    beta = (180 - gamma) // 2
    hb = 3  # half base
    h = sp.simplify(hb * sp.tan(sp.rad(beta)))
    S = Scene()
    t = S.place_triangle("ABC", [(-hb, 0), (hb, 0), (0, h)])
    B_, C_, A_ = t.pts  # base left, base right, apex
    S.add_line(A_, B_)  # tick marks would go here; equal sides drawn anyway
    return Puzzle(
        recipe="isosceles_base_angle",
        question=(
            f"An isosceles triangle has apex angle {gamma}° (between its two equal "
            "sides). Find the base angle marked with a question mark."
        ),
        scene=S,
        target=Target("angle", vertex=B_, p1=C_, p2=A_, value=sp.rad(beta)),
        givens=[Given(label=f"{gamma}°", kind="angle", vertex=A_, p1=B_, p2=C_)],
        solution_steps=[
            "The base angles of an isosceles triangle are equal",
            f"Angle sum: 2 × base + {gamma} = 180, so base = (180 − {gamma})/2 = {beta}°",
        ],
        depth=2,
        width=1,
        params={"gamma": gamma},
    )


@recipe("quarter_circle_corner", 2)
def quarter_circle_corner(rng: random.Random) -> Puzzle:
    a = rng.randint(3, 10)
    S = Scene()
    sq = S.place_square("ABCD", a)
    q = S.quarter_circle_at_corner("Q", sq, corner=0)
    A, B, _, _ = sq.pts
    region = Region.diff(sq, q)
    return Puzzle(
        recipe="quarter_circle_corner",
        question=(
            f"A quarter circle of radius {a} cm is drawn inside a square of side "
            f"{a} cm, centered at one corner. Find the shaded area outside the "
            "quarter circle."
        ),
        scene=S,
        target=Target("area", region=region),
        givens=[_side(f"{a}", A, B)],
        solution_steps=[
            f"Square area = {a}² = {a*a} cm²",
            f"Quarter circle area = π × {a}²/4 = {_num(sp.Rational(a*a,4))}π cm²",
            f"Shaded = {a*a} − {_num(sp.Rational(a*a,4))}π ≈ {float(a*a - sp.pi*a*a/4):.2f} cm²",
        ],
        depth=2,
        width=2,
        params={"a": a},
    )


@recipe("annulus", 2)
def annulus(rng: random.Random) -> Puzzle:
    r = rng.randint(2, 6)
    R = r + rng.randint(2, 5)
    S = Scene()
    co = S.place_circle("O", (0, 0), R)
    ci = S.place_circle("I", (0, 0), r)
    rimR = P(R * sp.cos(sp.pi / 6), R * sp.sin(sp.pi / 6))
    rimr = P(r * sp.cos(4 * sp.pi / 3), r * sp.sin(4 * sp.pi / 3))
    S.add_line(co.center, rimR)
    S.add_line(ci.center, rimr)
    region = Region.diff(co, ci)
    return Puzzle(
        recipe="annulus",
        question=(
            f"Two concentric circles have radii {R} cm and {r} cm. "
            "Find the shaded area of the ring between them."
        ),
        scene=S,
        target=Target("area", region=region),
        givens=[
            Given(label=f"{R}", kind="radius", p1=co.center, p2=rimR),
            Given(label=f"{r}", kind="radius", p1=ci.center, p2=rimr),
        ],
        solution_steps=[
            f"Outer circle area = π × {R}² = {R*R}π cm²",
            f"Inner circle area = π × {r}² = {r*r}π cm²",
            f"Ring = {R*R}π − {r*r}π = {R*R - r*r}π ≈ {float(sp.pi*(R*R-r*r)):.2f} cm²",
        ],
        depth=2,
        width=2,
        params={"R": R, "r": r},
    )


# ============================================================ depth 3


@recipe("leaf_lens", 3)
def leaf_lens(rng: random.Random) -> Puzzle:
    a = rng.randint(3, 10)
    S = Scene()
    sq = S.place_square("ABCD", a)
    A, B, C, D = sq.pts
    # two quarter-circle arcs across the square, lens between them
    q1 = S.quarter_circle_at_corner("Q1", sq, corner=0)  # center A, through B and D
    q2 = S.quarter_circle_at_corner("Q2", sq, corner=2)  # center C, through B and D
    seg1 = S.segment_between("L1", A, a, 0, sp.pi / 2, visible=False)
    seg2 = S.segment_between("L2", C, a, sp.pi, 3 * sp.pi / 2, visible=False)
    region = Region.union(seg1, seg2)
    half = sp.Rational(a * a, 2)
    quarter = sp.Rational(a * a, 4)
    return Puzzle(
        recipe="leaf_lens",
        question=(
            f"Inside a square of side {a} cm, two quarter-circle arcs of radius "
            f"{a} cm are drawn, centered at opposite corners. Find the shaded "
            "leaf-shaped area between them."
        ),
        scene=S,
        target=Target("area", region=region),
        givens=[_side(f"{a}", A, B)],
        solution_steps=[
            f"Quarter circle area = π × {a}²/4 = {_num(quarter)}π cm²",
            f"Half-square triangle area = {a}²/2 = {_num(half)} cm²",
            f"One circular segment = {_num(quarter)}π − {_num(half)} cm²",
            f"Leaf = 2 segments = {_num(2*quarter)}π − {a*a} ≈ "
            f"{float(sp.pi*a*a/2 - a*a):.2f} cm²",
        ],
        depth=3,
        width=2,
        nonstandard=True,
        params={"a": a},
        equal_region_claims=[(region, Region.inter(q1, q2))],
    )


@recipe("square_circle_square", 3)
def square_circle_square(rng: random.Random) -> Puzzle:
    a = rng.randrange(4, 14, 2)
    S = Scene()
    sq = S.place_square("ABCD", a)
    c = S.inscribe_circle_in_square("O", sq)
    inner = S.inscribe_square_in_circle("PQRS", c, tilted=True)
    A, B, _, _ = sq.pts
    r = a // 2
    region = Region.diff(c, inner)
    return Puzzle(
        recipe="square_circle_square",
        question=(
            f"A circle is inscribed in a square of side {a} cm, and a smaller "
            "square is inscribed in the circle. Find the shaded area inside the "
            "circle but outside the smaller square."
        ),
        scene=S,
        target=Target("area", region=region),
        givens=[_side(f"{a}", A, B)],
        solution_steps=[
            f"Circle radius = {a}/2 = {r}",
            f"Circle area = π × {r}² = {r*r}π cm²",
            f"Inner square diagonal = diameter = {a}, so its area = {a}²/2 = {a*a//2} cm²",
            f"Shaded = {r*r}π − {a*a//2} ≈ {float(sp.pi*r*r - a*a/2):.2f} cm²",
        ],
        depth=3,
        width=2,
        params={"a": a},
    )


@recipe("four_quarter_circles", 3)
def four_quarter_circles(rng: random.Random) -> Puzzle:
    a = rng.randrange(4, 14, 2)
    S = Scene()
    sq = S.place_square("ABCD", a)
    A, B, _, _ = sq.pts
    r = sp.Rational(a, 2)
    quarters = [S.quarter_circle_at_corner(f"Q{i}", sq, corner=i, r=r) for i in range(4)]
    region = Region.diff(sq, *quarters)
    ri = a // 2
    return Puzzle(
        recipe="four_quarter_circles",
        question=(
            f"In a square of side {a} cm, a quarter circle of radius {ri} cm is "
            "drawn at each corner. Find the shaded area in the middle."
        ),
        scene=S,
        target=Target("area", region=region),
        givens=[_side(f"{a}", A, B)],
        solution_steps=[
            f"Square area = {a}² = {a*a} cm²",
            f"Each quarter circle has radius {a}/2 = {ri}, area = π × {ri}²/4 = "
            f"{_num(sp.Rational(ri*ri,4))}π cm²",
            f"Four quarters = 4 × {_num(sp.Rational(ri*ri,4))}π = {_num(sp.Rational(ri*ri))}π "
            "cm² (a full circle)",
            f"Shaded = {a*a} − {ri*ri}π ≈ {float(a*a - sp.pi*ri*ri):.2f} cm²",
        ],
        depth=3,
        width=4,
        params={"a": a},
    )


@recipe("chained_rect_square_circle", 3)
def chained_rect_square_circle(rng: random.Random) -> Puzzle:
    h = rng.randrange(4, 12, 2)
    w = rng.choice([x for x in range(4, 13) if x != h])
    area_rect = w * h
    S = Scene()
    r_ = S.place_rect("ABCD", w, h)
    sq = S.place_square("DEFG", h, origin=(w, 0))
    c = S.inscribe_circle_in_square("O", sq)
    A, B, _, _ = r_.pts
    rad = h // 2
    region = Region.prim(c)
    return Puzzle(
        recipe="chained_rect_square_circle",
        question=(
            f"The rectangle has area {area_rect} cm² and its bottom side is {w} cm. "
            "A square shares the rectangle's right side, and a circle is inscribed "
            "in the square. Find the shaded area of the circle."
        ),
        scene=S,
        target=Target("area", region=region),
        givens=[
            _side(f"{w}", A, B),
            Given(label=f"area = {area_rect}", kind="text", p1=midpoint(r_.pts[0], r_.pts[2])),
        ],
        solution_steps=[
            f"Rectangle height = area / width = {area_rect}/{w} = {h}",
            f"The square shares that side, so its side is {h}; "
            f"inscribed circle radius = {h}/2 = {rad}",
            f"Circle area = π × {rad}² = {rad*rad}π ≈ {float(sp.pi*rad*rad):.2f} cm²",
        ],
        depth=3,
        width=1,
        params={"w": w, "h": h},
    )


@recipe("square_plus_semicircle", 3)
def square_plus_semicircle(rng: random.Random) -> Puzzle:
    a = rng.randrange(4, 14, 2)
    S = Scene()
    sq = S.place_square("ABCD", a)
    A, B, C, D = sq.pts
    semi = S.semicircle_on_side("S", D, C)  # left of D->C is up: bulges outside
    region = Region.union(sq, semi)
    r = a // 2
    return Puzzle(
        recipe="square_plus_semicircle",
        question=(
            f"A semicircle sits on top of a square of side {a} cm, its diameter "
            "being the square's top side. Find the total shaded area."
        ),
        scene=S,
        target=Target("area", region=region),
        givens=[_side(f"{a}", A, B)],
        solution_steps=[
            f"Square area = {a}² = {a*a} cm²",
            f"Semicircle radius = {a}/2 = {r}, area = π × {r}²/2 = {_num(sp.Rational(r*r,2))}π cm²",
            f"Total = {a*a} + {_num(sp.Rational(r*r,2))}π ≈ {float(a*a + sp.pi*r*r/2):.2f} cm²",
        ],
        depth=3,
        width=2,
        nonstandard=True,
        params={"a": a},
    )


# ============================================================ insight families


@recipe("sliding_triangle", 2)
def sliding_triangle(rng: random.Random) -> Puzzle:
    w = rng.randint(6, 12)
    h = rng.randint(4, 8)
    x = sp.Rational(rng.choice([2, 3, 7, 8]), 10) * w
    S = Scene()
    S.place_rect("ABCD", w, h)
    triangle = S.place_triangle("ABP", [(0, 0), (w, 0), (x, h)])
    area = w * h
    return Puzzle(
        recipe="sliding_triangle",
        question=(
            f"The rectangle has area {area} cm². The shaded triangle uses the "
            "whole bottom side as its base, and its third vertex lies on the "
            "top side. Find the shaded area."
        ),
        scene=S,
        target=Target("area", region=Region.prim(triangle)),
        givens=[Given(label=f"rectangle area = {area} cm²", kind="text", p1=P(w / sp.Integer(2), h * sp.Rational(6, 5)))],
        solution_steps=[
            "Let the rectangle's width and height be b and h. Its area is b × h.",
            "The triangle has the same base b and perpendicular height h, wherever its top vertex sits.",
            f"Triangle area = ½ × b × h = ½ × {area} = {_num(sp.Rational(area, 2))} cm².",
        ],
        depth=2,
        params={"w": w, "h": h, "x": x, "rectangle_area": area},
    )


@recipe("tangent_chord_annulus", 3)
def tangent_chord_annulus(rng: random.Random) -> Puzzle:
    r = rng.randint(2, 6)
    half = rng.randint(3, 7)
    R = sp.sqrt(r * r + half * half)
    S = Scene()
    outer = S.place_circle("O", (0, 0), R)
    inner = S.place_circle("I", (0, 0), r)
    A, B = P(-half, r), P(half, r)
    S.add_line(A, B)
    return Puzzle(
        recipe="tangent_chord_annulus",
        question=(
            f"The two circles have the same center. The {2*half} cm segment "
            "has both endpoints on the outer circle and is tangent to the "
            "inner circle (it just touches it). Find the shaded area between the circles."
        ),
        scene=S,
        target=Target("area", region=Region.diff(outer, inner)),
        givens=[_side(f"{2*half} cm", A, B)],
        solution_steps=[
            "Join the common center to the touching point and to either endpoint of the segment.",
            f"A radius is perpendicular to a tangent. The perpendicular from a circle's center bisects a chord, so half the segment is {half} cm.",
            f"If the radii are R and r, Pythagoras gives R² = r² + {half}², hence R² − r² = {half*half}.",
            f"Ring area = πR² − πr² = π(R² − r²) = {half*half}π cm². Neither radius is needed separately.",
        ],
        depth=3,
        width=2,
        params={"r": r, "R": R, "half_chord": half, "chord": 2 * half},
    )


@recipe("rotated_square_overlap", 3)
def rotated_square_overlap(rng: random.Random) -> Puzzle:
    a = rng.randrange(4, 14, 2)
    angle = rng.choice([sp.pi / 12, sp.pi / 6, sp.pi / 5])
    S = Scene()
    fixed = S.place_square("ABCD", a)
    center = P(sp.Rational(a, 2), sp.Rational(a, 2))
    turned = S.place_rotated_square("EFGH", a, center, angle)
    half = sp.Rational(a, 2)
    # For the sampled angles (strictly between 0 and 45 degrees), the two
    # rays hit the right and top edges. This polygon is independently
    # checked against the true intersection of the two squares.
    offset = sp.simplify(half * sp.tan(angle))
    overlap = Polygon(name="overlap", pts=(
        center, P(a, half + offset), P(a, a), P(half - offset, a),
    ))
    region = Region.prim(overlap)
    return Puzzle(
        recipe="rotated_square_overlap",
        question=(
            f"Both squares have side {a} cm. A corner of the tilted square "
            "lies exactly at the center of the other square. Find their shaded "
            "overlap area. The angle of rotation is not given."
        ),
        scene=S,
        target=Target("area", region=region),
        givens=[_side(f"{a} cm", fixed.pts[0], fixed.pts[1])],
        solution_steps=[
            "Extend the two sides through the central corner into full perpendicular lines.",
            "A 90° rotation about the fixed square's center maps the square to itself and each of the four sectors to the next. All four pieces have equal area.",
            f"Every point in the fixed square is at most {a}/√2 cm from its center, less than {a} cm. The tilted square's far sides cannot cut off any of its sector.",
            f"The overlap is one of the four equal pieces: {a}²/4 = {a*a//4} cm², regardless of the rotation.",
        ],
        depth=3,
        width=4,
        nonstandard=True,
        params={"a": a, "angle": angle},
        equal_region_claims=[(region, Region.inter(fixed, turned))],
    )


# ---------------------------------------------------------------------------


def _along(a, b, fraction):
    return P(*(sp.simplify(x + fraction * (y - x)) for x, y in zip(a, b)))


def _point_label(label, point, scale, dx=0, dy=0):
    return Given(label=label, kind="text", p1=P(
        point[0] + sp.Rational(str(dx)) * scale,
        point[1] + sp.Rational(str(dy)) * scale,
    ))


def _centroid(*points):
    return P(*(sum(p[i] for p in points) / len(points) for i in (0, 1)))


def _cevian_scene(rng, area, p, q=1, r=None):
    """Public triangle and dividing lines; aspect ratio and apex position vary.

    BD:DC = p:1, CE:EA = q:1, and optionally AF:FB = r:1.
    No area-ratio construction helpers are drawn.
    """
    width = max(4, math.isqrt(2 * int(area)) + rng.choice([-2, 0, 2]))
    height = sp.Rational(2 * area, width)
    apex = sp.Rational(rng.choice([3, 4, 6, 7]), 10) * width
    scene = Scene()
    outer = scene.place_triangle("ABC", [P(apex, height), P(0, 0), P(width, 0)])
    A, B, C = outer.pts
    for name, point in zip("ABC", outer.pts):
        scene.pt(name, point)
    D = scene.pt("D", _along(B, C, sp.Rational(p, p + 1)))
    E = scene.pt("E", _along(C, A, sp.Rational(q, q + 1)))
    scene.add_line(A, D)
    scene.add_line(B, E)
    Pn = scene.intersect_lines("P", A, D, B, E)
    scale = max(width, height)
    givens = [
        _point_label("A", A, scale, dy=.05),
        _point_label("B", B, scale, dx=-.04, dy=-.04),
        _point_label("C", C, scale, dx=.04, dy=-.04),
        _point_label("D", D, scale, dy=-.05),
        _point_label("E", E, scale, dx=.045, dy=.02),
        _point_label("P", Pn, scale, dx=-.04, dy=.015),
    ]
    if r is not None:
        F = scene.pt("F", _along(A, B, sp.Rational(r, r + 1)))
        scene.add_line(C, F)
        Q = scene.intersect_lines("Q", B, E, C, F)
        R = scene.intersect_lines("R", C, F, A, D)
        givens.extend([
            _point_label("F", F, scale, dx=-.045),
            _point_label("Q", Q, scale, dx=.055),
            _point_label("R", R, scale, dx=-.035, dy=.05),
        ])
    return scene, outer, givens


@recipe("tilted_square_frame", 3)
def tilted_square_frame(rng: random.Random) -> Puzzle:
    p, q = rng.choice([(1, 2), (1, 3), (2, 3)])
    unit = rng.randint(2, 4)
    side = (p + q) * unit
    scene = Scene()
    outer = scene.place_square("ABCD", side)
    A, B, C, D = outer.pts
    inner_points = tuple(_along(outer.pts[i], outer.pts[(i + 1) % 4], sp.Rational(p, p + q)) for i in range(4))
    inner = scene.add(Polygon(name="EFGH", pts=inner_points))
    scene._log("join_side_divisions", square=outer.name, ratio=f"{p}:{q}", name=inner.name)
    for name, point in zip("ABCDEFGH", outer.pts + inner_points):
        scene.pt(name, point)
    inner_area = (p*p + q*q) * unit*unit
    answer = 2 * p * q * unit*unit
    givens = [Given(label=f"{inner_area} cm²", kind="text", p1=P(side / sp.Integer(2), side / sp.Integer(2)))]
    for name, point, dx, dy in zip("ABCDEFGH", outer.pts + inner_points,
                                 [-.04, .04, .04, -.04, 0, .05, 0, -.05],
                                 [-.04, -.04, .04, .04, -.05, 0, .05, 0]):
        givens.append(_point_label(name, point, side, dx, dy))
    return Puzzle(
        recipe="tilted_square_frame",
        question=(f"ABCD is a square. Points E, F, G and H lie on AB, BC, CD and DA, respectively, "
                  f"with AE:EB = BF:FC = CG:GD = DH:HA = {p}:{q}. "
                  f"The inner square EFGH has area {inner_area} cm². Find the total shaded area of the four corners."),
        scene=scene, target=Target("area", region=Region.diff(outer, inner)), givens=givens,
        solution_steps=[
            f"Write the two parts of each outer side as {p}x and {q}x. The outer square has area {p+q}²x² = {(p+q)**2}x².",
            f"Each corner is a right triangle with perpendicular legs {p}x and {q}x, so its area is {_num(sp.Rational(p*q, 2))}x².",
            f"Together the four corners have area {2*p*q}x². Subtracting them leaves inner area {p*p+q*q}x².",
            f"The given inner area therefore fixes x² = {inner_area}/{p*p+q*q} = {unit*unit}. No side length is needed.",
            f"The shaded frame has area {2*p*q} × {unit*unit} = {answer} cm².",
        ],
        depth=3, width=2, nonstandard=True,
        params={"p": p, "q": q, "unit": unit, "inner_area": inner_area},
    )


@recipe("crossed_trapezoid", 3)
def crossed_trapezoid(rng: random.Random) -> Puzzle:
    a, b = rng.choice([(2, 3), (2, 5), (3, 4)])
    k = rng.randint(2, 4)
    stretch = rng.choice([sp.Integer(1), sp.Rational(3, 2), sp.Integer(2)])
    height = (a + b) * k / stretch
    offset = (b - a + rng.choice([-1, 0, 1])) * stretch
    scene = Scene()
    A, B, C, D = P(0, 0), P(2*b*stretch, 0), P(offset+2*a*stretch, height), P(offset, height)
    outer = scene.add(Polygon(name="ABCD", pts=(A, B, C, D)))
    scene._log("place_trapezoid", name=outer.name, bottom=2*b*stretch, top=2*a*stretch, height=height, offset=offset)
    for name, point in zip("ABCD", outer.pts):
        scene.pt(name, point)
    scene.add_line(A, C)
    scene.add_line(B, D)
    O = scene.intersect_lines("O", A, C, B, D)
    left = Polygon(name="AOD", pts=(A, O, D))
    right = Polygon(name="BOC", pts=(B, C, O))
    top, bottom = k*a*a, k*b*b
    scale = max(2*b*stretch, height)
    givens = [
        Given(label=f"{top} cm²", kind="text", p1=_centroid(C, D, O)),
        Given(label=f"{bottom} cm²", kind="text", p1=_centroid(A, B, O)),
        *[_point_label(name, point, scale, dx, dy) for name, point, dx, dy in [
            ("A", A, -.04, -.04), ("B", B, .04, -.04),
            ("C", C, .04, .04), ("D", D, -.04, .04), ("O", O, .045, 0),
        ]],
    ]
    return Puzzle(
        recipe="crossed_trapezoid",
        question=(f"In trapezoid ABCD, AB is parallel to CD. Diagonals AC and BD meet at O. "
                  f"Triangle COD has area {top} cm² and triangle AOB has area {bottom} cm². "
                  "Find the total shaded area of triangles AOD and BOC."),
        scene=scene, target=Target("area", region=Region.union(left, right)), givens=givens,
        solution_steps=[
            "Triangles COD and AOB are similar: their angles at O are equal, and the parallel sides give equal corresponding angles.",
            f"Areas scale as the square of lengths. Their area ratio {top}:{bottom} gives length ratio {_num(sp.Rational(a,b))}, so AO:OC = BO:OD = {b}:{a}.",
            "Triangles AOD and COD share the perpendicular height from D to AC. Their area ratio is therefore AO:OC.",
            f"Thus area AOD = {top} × {b}/{a} = {k*a*b} cm².",
            f"Similarly, BOC and DOC share the height from C to BD. Area BOC = {top} × {b}/{a} = {k*a*b} cm².",
            f"The two shaded triangles have disjoint interiors, so their total area is {k*a*b} + {k*a*b} = {2*k*a*b} cm².",
        ],
        depth=3, width=2, nonstandard=True,
        params={"a": a, "b": b, "k": k, "stretch": stretch, "offset": offset, "top_area": top, "bottom_area": bottom},
    )


@recipe("crossing_cevians", 3)
def crossing_cevians(rng: random.Random) -> Puzzle:
    p = rng.choice([2, 3])
    area = 2 * (2*p + 1) * rng.randint(4, 9)
    scene, outer, givens = _cevian_scene(rng, area, p)
    A, B, C, D, E, Pn = (scene.points[name] for name in "ABCDEP")
    target = Polygon(name="ABP", pts=(A, B, Pn))
    answer = sp.Rational(p * area, 2*p + 1)
    return Puzzle(
        recipe="crossing_cevians",
        question=(f"Triangle ABC has area {area} cm². D lies on BC with BD:DC = {p}:1, "
                  "and E is the midpoint of AC. Segments AD and BE meet at P. Find the shaded area of triangle ABP."),
        scene=scene, target=Target("area", region=Region.prim(target)), givens=givens,
        solution_steps=[
            f"Triangles ABD and ADC share the height from A to BC, so their areas are in the ratio {p}:1.",
            f"E is the midpoint of AC, so area ADE is half of area ADC. Therefore area ABD : area ADE = {2*p}:1.",
            f"ABD and ADE share base AD. Their perpendicular heights from B and E to AD are consequently in the ratio {2*p}:1.",
            f"B, P and E lie on one straight line, with P on AD. Their heights to AD scale with distance from P (similar right triangles), giving BP:PE = {2*p}:1.",
            f"Area ABE is half of ABC, or {area//2} cm². ABP and APE share the height from A to BE, so ABP takes {2*p}/{2*p+1} of ABE.",
            f"Shaded area = {area//2} × {2*p}/{2*p+1} = {_num(answer)} cm².",
        ],
        depth=3, width=3, nonstandard=True,
        params={"p": p, "total_area": area},
    )


@recipe("cevian_area_recovery", 3)
def cevian_area_recovery(rng: random.Random) -> Puzzle:
    p = rng.choice([2, 3])
    y = rng.randint(4, 9)
    x = 2*p*y
    area = 2 * (x + y)
    scene, outer, givens = _cevian_scene(rng, area, p)
    A, B, C, D, E, Pn = (scene.points[name] for name in "ABCDEP")
    target = Polygon(name="BDP", pts=(B, D, Pn))
    givens.extend([
        Given(label=str(x), kind="text", p1=_centroid(A, B, Pn)),
        Given(label=str(y), kind="text", p1=_centroid(A, Pn, E)),
    ])
    answer = sp.Rational(x*x, x+2*y)
    return Puzzle(
        recipe="cevian_area_recovery",
        question=("E is the midpoint of side AC of triangle ABC. D lies on BC, and AD meets BE at P. "
                  f"Triangle ABP has area {x} cm²; triangle APE has area {y} cm². "
                  "The position of D is otherwise unknown. Find the shaded area of triangle BDP."),
        scene=scene, target=Target("area", region=Region.prim(target)), givens=givens,
        solution_steps=[
            f"Area ABE = {x} + {y} = {x+y} cm². Because E is the midpoint of AC, the whole area ABC is {area} cm².",
            f"ABP and APE share a height to BE, so BP:PE = {x}:{y}.",
            f"Write u = area BDP and v = area DPE. These triangles also share a height to BE, giving u/v = {x}/{y}.",
            f"Triangles ADE and CDE have equal bases AE and CE and the same height from D. Each has area {y} + v.",
            f"Partition ABC into ABP, BDP, ADE and CDE: {area} = {x} + u + 2({y} + v). Thus u + 2v = {x}.",
            f"Substitute u = ({x}/{y})v: v = ({x} × {y})/({x} + 2 × {y}) = {_num(sp.Rational(x*y, x+2*y))} cm².",
            f"The required area is u = {x}²/({x} + 2 × {y}) = {_num(answer)} cm². No side ratio for D was needed.",
        ],
        depth=3, width=3, nonstandard=True,
        params={"p": p, "abp_area": x, "ape_area": y},
    )


@recipe("cevian_parallel_band", 3)
def cevian_parallel_band(rng: random.Random) -> Puzzle:
    p = rng.choice([2, 3])
    k = rng.randint(1, 3)
    area = 4 * (2*p + 1)**2 * k
    scene, outer, givens = _cevian_scene(rng, area, p)
    A, B, C, D, E, Pn = (scene.points[name] for name in "ABCDEP")
    fraction = sp.Rational(p+1, 2*p+1)
    G = scene.pt("G", _along(A, B, fraction))
    F = scene.pt("F", _along(A, C, fraction))
    H = scene.pt("H", midpoint(A, B))
    band = scene.add(Polygon(name="band", pts=(H, G, F, E)))
    scale = max(C[0] - B[0], A[1] - B[1])
    givens[-1] = _point_label("P", Pn, scale, dx=.035, dy=-.05)
    scene._log("parallel_sections", triangle=outer.name, through=("E", "P"), parallel="BC")
    upper = Polygon(name="AGF", pts=(A, G, F))
    cap = Polygon(name="AHE", pts=(A, H, E))
    answer = (4*p + 3) * k
    return Puzzle(
        recipe="cevian_parallel_band",
        question=(f"Triangle ABC has area {area} cm². D lies on BC with BD:DC = {p}:1, "
                  "E is the midpoint of AC, and AD meets BE at P. Two segments parallel to BC "
                  "run across the triangle, one through E and one through P. Find the shaded area of the strip between them."),
        scene=scene, target=Target("area", region=Region.prim(band), marker_size=16), givens=givens,
        solution_steps=[
            f"Shared heights give area ABD : area ADC = {p}:1; E halves AC, so area ABD : area ADE = {2*p}:1.",
            f"ABD and ADE share base AD. Comparing their heights, then the similar right triangles along BE, gives BP:PE = {2*p}:1.",
            f"Let the whole triangle's height above BC be h. E is at height h/2, so P is at ({2*p}/{2*p+1})(h/2) = {p}h/{2*p+1}.",
            f"The distance from A down to the parallel through P is therefore h − {p}h/{2*p+1} = {p+1}h/{2*p+1}.",
            f"The triangle above that lower parallel is similar to ABC. Its area is ({p+1}/{2*p+1})² × {area} = {4*(p+1)**2*k} cm².",
            f"The triangle above the parallel through E has half the linear scale of ABC, so its area is {area}/4 = {area//4} cm².",
            "The shaded strip is the larger of those two nested triangles minus the smaller. Subtract their areas, not their linear scale factors.",
            f"Shaded area = {4*(p+1)**2*k} − {area//4} = {answer} cm².",
        ],
        depth=3, width=3, nonstandard=True,
        params={"p": p, "total_area": area},
        equal_region_claims=[(Region.prim(band), Region.diff(upper, cap))],
    )


@recipe("three_cevians", 3)
def three_cevians(rng: random.Random) -> Puzzle:
    m = rng.choice([2, 3])
    denominator = m*m + m + 1
    area = denominator * rng.randint(6, 15)
    scene, outer, givens = _cevian_scene(rng, area, m, m, m)
    A, B, C, Pn, Q, R = (scene.points[name] for name in "ABCPQR")
    target = Polygon(name="PQR", pts=(Pn, Q, R))
    corner = sp.Rational(m * area, denominator)
    complement = Region.diff(outer, Polygon(name="ABP", pts=(A, B, Pn)),
                             Polygon(name="BCQ", pts=(B, C, Q)), Polygon(name="CAR", pts=(C, A, R)))
    return Puzzle(
        recipe="three_cevians",
        question=(f"Triangle ABC has area {area} cm². D, E and F lie on BC, CA and AB, respectively, "
                  f"with BD:DC = CE:EA = AF:FB = {m}:1. Draw AD, BE and CF. "
                  "P is the intersection of AD and BE, Q of BE and CF, and R of CF and AD. Find the shaded area of triangle PQR."),
        scene=scene, target=Target("area", region=Region.prim(target)), givens=givens,
        solution_steps=[
            f"Write T = {area}, the area of ABC. Because AE:AC = 1:{m+1}, area ABE = T/{m+1}.",
            f"BD:DC = {m}:1 gives area ABD = {m}T/{m+1} and area ADC = T/{m+1}.",
            f"Within ADC, E divides AC with AE:AC = 1:{m+1}. Hence area ADE = T/{(m+1)**2}.",
            f"ABD and ADE share AD, so their heights are in the ratio {m*(m+1)}:1. Since BE crosses AD at P, BP:PE has that same ratio.",
            f"ABP therefore takes {m*(m+1)}/{denominator} of ABE: area ABP = {m}T/{denominator} = {_num(corner)} cm².",
            f"Repeat the argument with the vertex names cycled A→B→C. The three side-division ratios are the same, so BCQ and CAR each also have area {_num(corner)} cm². The outer triangle need not be equilateral.",
            "ABP, BCQ and CAR have disjoint interiors and fill everything outside PQR. Subtract all three from ABC.",
            f"Shaded area = {area} − 3 × {_num(corner)} = {_num(area-3*corner)} cm².",
        ],
        depth=3, width=4, nonstandard=True,
        params={"ratio": m, "total_area": area},
        equal_region_claims=[(Region.prim(target), complement)],
    )


@recipe("unequal_three_cevians", 3)
def unequal_three_cevians(rng: random.Random) -> Puzzle:
    p, q, r = rng.choice([(2, 1, 3), (2, 3, 1), (2, 1, 4), (3, 1, 2)])
    d1, d2, d3 = p*q+p+1, q*r+q+1, r*p+r+1
    area = math.lcm(d1, d2, d3) * rng.randint(1, 3)
    scene, outer, givens = _cevian_scene(rng, area, p, q, r)
    A, B, C, Pn, Q, R = (scene.points[name] for name in "ABCPQR")
    target = Polygon(name="PQR", pts=(Pn, Q, R))
    a1, a2, a3 = (sp.Rational(n*area, d) for n, d in [(p, d1), (q, d2), (r, d3)])
    complement = Region.diff(outer, Polygon(name="ABP", pts=(A, B, Pn)),
                             Polygon(name="BCQ", pts=(B, C, Q)), Polygon(name="CAR", pts=(C, A, R)))
    return Puzzle(
        recipe="unequal_three_cevians",
        question=(f"Triangle ABC has area {area} cm². D, E and F lie on BC, CA and AB, respectively. "
                  f"This time BD:DC = {p}:1, CE:EA = {q}:1 and AF:FB = {r}:1. "
                  "P is the intersection of AD and BE, Q of BE and CF, and R of CF and AD. "
                  "Find the shaded area of triangle PQR."),
        scene=scene, target=Target("area", region=Region.prim(target)), givens=givens,
        solution_steps=[
            f"Let T = {area}. The first base ratio gives area ABD = {p}T/{p+1} and area ADC = T/{p+1}.",
            f"AE:AC = 1:{q+1}, so area ADE = T/{(p+1)*(q+1)}. Comparing heights on base AD gives BP:PE = {p*(q+1)}:1.",
            f"Area ABE = T/{q+1}. Thus area ABP = ({p*(q+1)}/{d1}) × T/{q+1} = {p}T/{d1} = {_num(a1)} cm².",
            f"For the next corner, area BCE = {q}T/{q+1}. Because BF:BA = 1:{r+1}, area BEF = T/{(q+1)*(r+1)}.",
            f"BCE and BEF share base BE. Their height ratio gives CQ:QF = {q*(r+1)}:1.",
            f"Area BCF = T/{r+1}, so area BCQ = ({q*(r+1)}/{d2}) × T/{r+1} = {q}T/{d2} = {_num(a2)} cm².",
            f"For the last corner, area CAF = {r}T/{r+1}. Since CD:CB = 1:{p+1}, area CFD = T/{(r+1)*(p+1)}.",
            f"CAF and CFD share base CF. Their height ratio gives AR:RD = {r*(p+1)}:1.",
            f"Area CAD = T/{p+1}, so area CAR = ({r*(p+1)}/{d3}) × T/{p+1} = {r}T/{d3} = {_num(a3)} cm².",
            f"These three corner triangles fill the unshaded region without overlap. PQR has area {area} − {_num(a1)} − {_num(a2)} − {_num(a3)} = {_num(area-a1-a2-a3)} cm².",
        ],
        depth=3, width=4, nonstandard=True,
        params={"p": p, "q": q, "r": r, "total_area": area},
        equal_region_claims=[(Region.prim(target), complement)],
    )


# ============================================================ third chapter


def _corner_fractions(p, q, r):
    return tuple(sp.Rational(n, d) for n, d in (
        (p, p*q+p+1), (q, q*r+q+1), (r, r*p+r+1),
    ))


def _corner_fraction_steps(vertices, feet, crossings, ratios, total):
    """Derive each corner from public side divisions, with a named whole area."""
    steps = []
    for i in range(3):
        a, b, c = (vertices[(i+j) % 3] for j in range(3))
        d, e = (feet[(i+j) % 3] for j in range(2))
        x = crossings[i]
        p, q = (ratios[(i+j) % 3] for j in range(2))
        denominator = p*q+p+1
        steps.extend([
            f"Using shared heights in {vertices}, whose area is {total}, area {a+b+d} = {p}{total}/{p+1}. "
            f"Since {a+e}:{a+c} = 1:{q+1}, area {a+d+e} = {total}/{(p+1)*(q+1)}.",
            f"{a+b+d} and {a+d+e} share base {a+d}. Their height ratio is {p*(q+1)}:1. "
            f"The similar right triangles along {b+e} therefore give {b+x}:{x+e} = {p*(q+1)}:1.",
            f"Area {a+b+e} = {total}/{q+1}. Splitting it on {b+e} gives area {a+b+x} = "
            f"({p*(q+1)}/{denominator}) × {total}/{q+1} = {_num(sp.Rational(p, denominator))} × {total}.",
        ])
    return steps


def _three_line_statement(divisions):
    return ("D, E and F lie on BC, CA and AB of triangle ABC, respectively. "
            f"{divisions} P is the intersection of AD and BE, Q of BE and CF, "
            "and R of CF and AD. ")


def _central_regions(scene, vertices="ABC", crossings="PQR"):
    a, b, c = (scene.points[n] for n in vertices)
    p, q, r = (scene.points[n] for n in crossings)
    center = Polygon(name=crossings, pts=(p, q, r))
    corners = [Polygon(name=name, pts=points) for name, points in (
        (vertices[:2]+crossings[0], (a, b, p)),
        (vertices[1:]+crossings[1], (b, c, q)),
        (vertices[2]+vertices[0]+crossings[2], (c, a, r)),
    )]
    return center, Region.diff(scene.shapes[vertices], *corners)


def _recovery_parameters(rng):
    p, q, r = rng.choice([(2, 1, 3), (2, 3, 1), (2, 1, 4), (3, 1, 2)])
    total = math.lcm(*(f.q for f in _corner_fractions(p, q, r))) * rng.randint(2, 5)
    return p, q, r, total


@recipe("cevian_total_recovery", 3)
def cevian_total_recovery(rng: random.Random) -> Puzzle:
    p, q, r, total = _recovery_parameters(rng)
    fractions = _corner_fractions(p, q, r)
    x = fractions[0] * total
    scene, outer, givens = _cevian_scene(rng, total, p, q, r)
    center, complement = _central_regions(scene)
    steps = _corner_fraction_steps("ABC", "DEF", "PQR", (p, q, r), "T")
    steps.insert(3, f"The given area ABP is {_num(x)} cm², so {_num(fractions[0])} × T = {_num(x)}. "
                   f"Recover the whole area: T = {_num(x)} ÷ {_num(fractions[0])} = {total} cm².")
    answer = total * (1 - sum(fractions))
    steps.append(f"ABP, BCQ and CAR have disjoint interiors and fill the complement of PQR. "
                 f"Subtract their areas from the recovered whole: {total} − "
                 f"{' − '.join(_num(total*f) for f in fractions)} = {_num(answer)} cm².")
    return Puzzle(
        recipe="cevian_total_recovery",
        question=_three_line_statement(f"BD:DC = {p}:1, CE:EA = {q}:1 and AF:FB = {r}:1.")
                 + f"Triangle ABP has area {_num(x)} cm². Find the shaded area of PQR.",
        scene=scene, target=Target("area", region=Region.prim(center), value=answer), givens=givens,
        solution_steps=steps, depth=3, width=4, nonstandard=True,
        params={"p": p, "q": q, "r": r, "abp_area": x},
        equal_region_claims=[(Region.prim(center), complement)],
    )


@recipe("cevian_missing_ratio", 3)
def cevian_missing_ratio(rng: random.Random) -> Puzzle:
    p, q, r, total = _recovery_parameters(rng)
    fractions = _corner_fractions(p, q, r)
    x = fractions[0] * total
    y = sp.Rational(total, q+1) - x
    scene, outer, givens = _cevian_scene(rng, total, p, q, r)
    center, complement = _central_regions(scene)
    answer = total * (1 - sum(fractions))
    steps = [
        f"Let T = {total}. CE:EA = {q}:1 gives area ABE = T/{q+1} = {_num(x+y)} cm².",
        f"The known ABP leaves area APE = {_num(x+y)} − {_num(x)} = {_num(y)} cm².",
        f"ABP and APE have a common height to BE, so BP:PE = {_num(x)}:{_num(y)} = {p*(q+1)}:1.",
        "The heights from B and E to AD are in that same ratio, by similar right triangles along BE. "
        "Thus area ABD : area ADE = BP:PE.",
        f"Write the unknown BD:DC as t:1. Shared heights give ABD = tT/(t+1) and "
        f"ADE = T/[{q+1}(t+1)], so their area ratio is {q+1}t:1.",
        f"Equating ratios gives {q+1}t = {p*(q+1)}, hence t = {p}. The missing side division has been recovered.",
        *_corner_fraction_steps("ABC", "DEF", "PQR", (p, q, r), "T")[3:],
        f"Subtract the three disjoint corner triangles: area PQR = {total} − {_num(x)} − "
        f"{_num(fractions[1]*total)} − {_num(fractions[2]*total)} = {_num(answer)} cm².",
    ]
    return Puzzle(
        recipe="cevian_missing_ratio",
        question=_three_line_statement(f"CE:EA = {q}:1 and AF:FB = {r}:1; the division BD:DC is unknown.")
                 + f"ABC has area {total} cm² and ABP has area {_num(x)} cm². Find the shaded area of PQR.",
        scene=scene, target=Target("area", region=Region.prim(center), value=answer), givens=givens,
        solution_steps=steps, depth=3, width=4, nonstandard=True,
        params={"p": p, "q": q, "r": r, "total_area": total, "abp_area": x},
        equal_region_claims=[(Region.prim(center), complement)],
    )


@recipe("cevian_double_recovery", 3)
def cevian_double_recovery(rng: random.Random) -> Puzzle:
    p, q, r, total = _recovery_parameters(rng)
    fractions = _corner_fractions(p, q, r)
    x, y, z = (f*total for f in fractions)
    scene, outer, givens = _cevian_scene(rng, total, p, q, r)
    center, complement = _central_regions(scene)
    remaining = sp.Rational(total, p+1) - z
    answer = total - x - y - z
    steps = [
        *_corner_fraction_steps("ABC", "DEF", "PQR", (p, q, r), "T")[:3],
        f"The given ABP now determines the missing total: T = {_num(x)} ÷ {_num(fractions[0])} = {total} cm².",
        f"Area CAD = T/{p+1} = {_num(z+remaining)} cm², and its part CAR is given as {_num(z)} cm².",
        f"The rest of CAD is CDR, of area {_num(z+remaining)} − {_num(z)} = {_num(remaining)} cm².",
        f"CAR and CDR share the height from C to AD. Hence AR:RD = {_num(z)}:{_num(remaining)} = {r*(p+1)}:1.",
        f"Write AF:FB = t:1. Shared heights give CAF = tT/(t+1) and CFD = T/[{p+1}(t+1)]. "
        f"Comparing their heights on CF gives AR:RD = {p+1}t:1.",
        f"Therefore {p+1}t = {r*(p+1)} and t = {r}. Both the total and the hidden side division are now known.",
        *_corner_fraction_steps("ABC", "DEF", "PQR", (p, q, r), "T")[3:6],
        "ABP, BCQ and CAR fill the region outside PQR with disjoint interiors, so their areas can be subtracted together.",
        f"Shaded area = {total} − {_num(x)} − {_num(y)} − {_num(z)} = {_num(answer)} cm².",
    ]
    return Puzzle(
        recipe="cevian_double_recovery",
        question=_three_line_statement(f"BD:DC = {p}:1 and CE:EA = {q}:1; the division AF:FB is unknown.")
                 + f"ABP has area {_num(x)} cm² and CAR has area {_num(z)} cm². "
                 "The total area of ABC is unknown. Find the shaded area of PQR.",
        scene=scene, target=Target("area", region=Region.prim(center), value=answer), givens=givens,
        solution_steps=steps, depth=3, width=4, nonstandard=True,
        params={"p": p, "q": q, "r": r, "abp_area": x, "car_area": z},
        equal_region_claims=[(Region.prim(center), complement)],
    )


@recipe("cevian_corner_band", 3)
def cevian_corner_band(rng: random.Random) -> Puzzle:
    p, q, r, total = _recovery_parameters(rng)
    f1, _, f3 = _corner_fractions(p, q, r)
    x, z = f1*total, f3*total
    scene, outer, givens = _cevian_scene(rng, total, p, q, r)
    A, B, C, D, Pn, R = (scene.points[n] for n in "ABCDPR")
    ap = sp.Rational(p+1, p*q+p+1)
    ar = sp.Rational(r*(p+1), r*p+r+1)
    ratio = ap/ar
    S = scene.pt("S", _along(A, C, ratio))
    scene.add_line(Pn, S)
    scene._log("parallel_section", through="P", parallel="RC", endpoint="S")
    scale = max(C[0]-B[0], A[1]-B[1])
    givens.append(_point_label("S", S, scale, dx=.045))
    cap = Polygon(name="APS", pts=(A, Pn, S))
    corner = Polygon(name="ARC", pts=(A, R, C))
    band = Polygon(name="PRCS", pts=(Pn, R, C, S))
    answer = z*(1-ratio**2)
    steps = [
        *_corner_fraction_steps("ABC", "DEF", "PQR", (p, q, r), "T")[:3],
        f"Use the given ABP to recover T = {_num(x)} ÷ {_num(f1)} = {total} cm².",
        f"Area ABD = {p}T/{p+1} = {_num(sp.Rational(p*total,p+1))}. "
        f"Subtract ABP to find BDP = {_num(sp.Rational(p*total,p+1)-x)} cm².",
        "ABP and BDP share the height from B to AD, so AP:PD equals their area ratio.",
        f"Convert that part-to-part ratio to a fraction of all AD: AP/AD = ABP/ABD = {_num(ap)}.",
        f"Shared heights also give CAF = {r}T/{r+1} and CFD = T/{(r+1)*(p+1)}.",
        f"CAF and CFD share CF; comparing heights along AD gives AR:RD = {r*(p+1)}:1.",
        f"Therefore AR/AD = {_num(ar)}. The points occur in the order A, P, R, D.",
        f"Both distances start at A, so AP/AR = (AP/AD)/(AR/AD) = {_num(ap)} ÷ {_num(ar)} = {_num(ratio)}.",
        "PS is parallel to RC, so triangles APS and ARC are similar with that linear scale factor.",
        f"Triangles ARC and ADC share the height from C to AD. Area ARC = (AR/AD) × T/{p+1} = {_num(z)} cm².",
        f"Square the similarity scale: area APS = ({_num(ratio)})² × {_num(z)} = {_num(z*ratio**2)} cm².",
        f"The shaded quadrilateral PRCS is ARC minus APS: {_num(z)} − {_num(z*ratio**2)} = {_num(answer)} cm².",
    ]
    return Puzzle(
        recipe="cevian_corner_band",
        question=_three_line_statement(f"BD:DC = {p}:1, CE:EA = {q}:1 and AF:FB = {r}:1.")
                 + f"ABP has area {_num(x)} cm². Through P, draw PS parallel to RC, meeting AC at S. "
                 "Find the shaded area of quadrilateral PRCS.",
        scene=scene, target=Target("area", region=Region.prim(band), value=answer, marker_size=18), givens=givens,
        solution_steps=steps, depth=3, width=4, nonstandard=True,
        params={"p": p, "q": q, "r": r, "abp_area": x},
        equal_region_claims=[(Region.prim(band), Region.diff(corner, cap))],
    )


def _nested_cevian_scene(rng, total, outer_ratios, inner_ratios):
    scene, outer, givens = _cevian_scene(rng, total, *outer_ratios)
    center, outer_complement = _central_regions(scene)
    scene.add(center)
    Pn, Q, R = center.pts
    u, v, w = inner_ratios
    U = scene.pt("U", _along(Q, R, sp.Rational(u, u+1)))
    V = scene.pt("V", _along(R, Pn, sp.Rational(v, v+1)))
    W = scene.pt("W", _along(Pn, Q, sp.Rational(w, w+1)))
    for a, b in ((Pn, U), (Q, V), (R, W)):
        scene.add_line(a, b)
    X = scene.intersect_lines("X", Pn, U, Q, V)
    Y = scene.intersect_lines("Y", Q, V, R, W)
    Z = scene.intersect_lines("Z", R, W, Pn, U)
    inner, inner_complement = _central_regions(scene, "PQR", "XYZ")
    scale = max(max(point[i] for point in center.pts)-min(point[i] for point in center.pts) for i in (0, 1))
    # Side labels sit outside PQR; crossing labels sit in their adjacent white
    # corner. Fixed screen offsets would collide when the triangle is sheared.
    for name, point, a, b in (("U", U, Q, R), ("V", V, R, Pn), ("W", W, Pn, Q)):
        offset = sp.Rational(4, 100)*scale/dist(a, b)
        position = P(point[0]+offset*(b[1]-a[1]), point[1]-offset*(b[0]-a[0]))
        givens.append(Given(label=name, kind="text", p1=position, font_size=11))
    for name, point, a, b in (("X", X, Pn, Q), ("Y", Y, Q, R), ("Z", Z, R, Pn)):
        toward = midpoint(a, b)
        offset = sp.Rational(7, 100)*scale/dist(point, toward)
        givens.append(Given(label=name, kind="text", p1=_along(point, toward, offset), font_size=11))
    claims = [(Region.prim(center), outer_complement), (Region.prim(inner), inner_complement)]
    return scene, outer, center, inner, givens, claims


def _nested_statement(outer_ratios, inner_ratios):
    p, q, r = outer_ratios
    u, v, w = inner_ratios
    return (_three_line_statement(f"BD:DC = {p}:1, CE:EA = {q}:1 and AF:FB = {r}:1.")
            + "Inside PQR, U lies on QR, V on RP and W on PQ, with "
            f"QU:UR = {u}:1, RV:VP = {v}:1 and PW:WQ = {w}:1. "
            "X is the intersection of PU and QV, Y of QV and RW, and Z of RW and PU. ")


def _nested_parameters(rng, *, equal_inner=False):
    # Cyclic variants preserve the area fractions (25/66 outside, 1/7 or
    # 1/10 inside), keeping arithmetic modest and the central diagram roomy.
    outer = rng.choice([(2, 4, 7), (4, 7, 2), (7, 2, 4)])
    inner = (2, 2, 2) if equal_inner else rng.choice([(2, 1, 3), (1, 3, 2), (3, 2, 1)])
    total = (462 if equal_inner else 132) * rng.randint(1, 3)
    return outer, inner, total


@recipe("nested_three_cevians", 3)
def nested_three_cevians(rng: random.Random) -> Puzzle:
    ratios, inner_ratios, total = _nested_parameters(rng, equal_inner=True)
    fractions = _corner_fractions(*ratios)
    middle = total*(1-sum(fractions))
    answer = middle/7
    scene, outer, center, inner, givens, claims = _nested_cevian_scene(rng, total, ratios, inner_ratios)
    steps = [
        *_corner_fraction_steps("ABC", "DEF", "PQR", ratios, "T"),
        f"With T = {total}, remove the three disjoint outer corners. Area PQR = {total} × "
        f"(1 − {' − '.join(_num(f) for f in fractions)}) = {_num(middle)} cm².",
        f"Now treat PQR as the whole triangle, with area K = {_num(middle)}. The inner side ratios refer to this triangle.",
        "QU:UR = RV:VP = 2:1 gives area PQU = 2K/3 and area PUV = K/9 by shared heights.",
        "Those triangles share PU, so comparing their heights along QV gives QX:XV = 6:1.",
        "PQV has area K/3; PQX takes 6/7 of it, so area PQX = 2K/7.",
        "Cycling P, Q and R gives the same fraction for QRY and RPZ. The inner corner areas are equal even though PQR is not equilateral.",
        f"The three disjoint inner corners leave XYZ = K − 3(2K/7) = K/7 = {_num(answer)} cm².",
    ]
    return Puzzle(
        recipe="nested_three_cevians",
        question=_nested_statement(ratios, inner_ratios) + f"ABC has area {total} cm². Find the shaded area of XYZ.",
        scene=scene, target=Target("area", region=Region.prim(inner), value=answer, marker_size=16), givens=givens,
        solution_steps=steps, depth=3, width=4, nonstandard=True,
        params=dict(zip(("p", "q", "r", "u", "v", "w"), ratios+inner_ratios), total_area=total),
        equal_region_claims=claims,
    )


@recipe("nested_unequal_cevians", 3)
def nested_unequal_cevians(rng: random.Random) -> Puzzle:
    ratios, inner_ratios, total = _nested_parameters(rng)
    outer_fractions = _corner_fractions(*ratios)
    inner_fractions = _corner_fractions(*inner_ratios)
    middle = total*(1-sum(outer_fractions))
    answer = middle*(1-sum(inner_fractions))
    scene, outer, center, inner, givens, claims = _nested_cevian_scene(rng, total, ratios, inner_ratios)
    steps = [
        *_corner_fraction_steps("ABC", "DEF", "PQR", ratios, "T"),
        f"With T = {total}, remove the three disjoint outer corners to obtain PQR. "
        f"Its area is K = {total} × (1 − {' − '.join(_num(f) for f in outer_fractions)}) = {_num(middle)} cm².",
        *_corner_fraction_steps("PQR", "UVW", "XYZ", inner_ratios, "K"),
        f"The inner corners PQX, QRY and RPZ are disjoint. Subtract them from PQR, whose area is K: "
        f"XYZ = {_num(middle)} × (1 − {' − '.join(_num(f) for f in inner_fractions)}) = {_num(answer)} cm².",
    ]
    return Puzzle(
        recipe="nested_unequal_cevians",
        question=_nested_statement(ratios, inner_ratios) + f"ABC has area {total} cm². Find the shaded area of XYZ.",
        scene=scene, target=Target("area", region=Region.prim(inner), value=answer, marker_size=14), givens=givens,
        solution_steps=steps, depth=3, width=4, nonstandard=True,
        params=dict(zip(("p", "q", "r", "u", "v", "w"), ratios+inner_ratios), total_area=total),
        equal_region_claims=claims,
    )


@recipe("nested_cevian_recovery", 3)
def nested_cevian_recovery(rng: random.Random) -> Puzzle:
    ratios, inner_ratios, total = _nested_parameters(rng)
    outer_fractions = _corner_fractions(*ratios)
    inner_fractions = _corner_fractions(*inner_ratios)
    outer_fraction, inner_fraction = 1-sum(outer_fractions), 1-sum(inner_fractions)
    middle = total*outer_fraction
    known = middle*inner_fraction
    answer = total-middle
    scene, outer, center, inner, givens, claims = _nested_cevian_scene(rng, total, ratios, inner_ratios)
    steps = [
        *_corner_fraction_steps("ABC", "DEF", "PQR", ratios, "T"),
        f"Subtract the outer corner fractions: if ABC has area T, PQR has area K = "
        f"(1 − {' − '.join(_num(f) for f in outer_fractions)}) × T = {_num(outer_fraction)} × T.",
        *_corner_fraction_steps("PQR", "UVW", "XYZ", inner_ratios, "K"),
        f"Subtract the inner corner fractions: XYZ has area "
        f"(1 − {' − '.join(_num(f) for f in inner_fractions)}) × K = {_num(inner_fraction)} × K.",
        f"Work outward from the given XYZ: K = {_num(known)} ÷ {_num(inner_fraction)} = {_num(middle)} cm².",
        f"Reverse the outer fraction as well: T = {_num(middle)} ÷ {_num(outer_fraction)} = {total} cm².",
        f"The shading is ABC outside PQR, so subtract the intermediate area, not the innermost one: "
        f"{total} − {_num(middle)} = {_num(answer)} cm².",
    ]
    return Puzzle(
        recipe="nested_cevian_recovery",
        question=_nested_statement(ratios, inner_ratios) + f"XYZ has area {_num(known)} cm². "
                 "Find the total shaded area inside ABC but outside PQR.",
        scene=scene, target=Target("area", region=Region.diff(outer, center), value=answer), givens=givens,
        solution_steps=steps, depth=3, width=4, nonstandard=True,
        params=dict(zip(("p", "q", "r", "u", "v", "w"), ratios+inner_ratios), xyz_area=known),
        equal_region_claims=claims,
    )


def by_depth(depth: int) -> list[str]:
    return [name for name, (_, d) in RECIPES.items() if d == depth]


def build(name: str, seed: int) -> Puzzle:
    fn, _ = RECIPES[name]
    rng = random.Random(seed)
    pz = fn(rng)
    pz.seed = seed
    return pz
