"""Puzzle recipes: parameterized backwards constructions.

Each recipe samples small integer parameters, builds the figure from them
(the answer is therefore free by construction), chooses which givens to
reveal, and emits the solution chain.  Difficulty metadata follows the
GeomVerse convention: depth = length of the deduction chain, width = max
sub-results feeding one step.
"""

from __future__ import annotations

import random

import sympy as sp

from .core import P, Region, fmt_exact, midpoint
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
            "the center of the other. Find the shaded overlap area."
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
    seg1 = S.segment_between("L1", A, a, 0, sp.pi / 2)
    seg2 = S.segment_between("L2", C, a, sp.pi, 3 * sp.pi / 2)
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


# ---------------------------------------------------------------------------


def by_depth(depth: int) -> list[str]:
    return [name for name, (_, d) in RECIPES.items() if d == depth]


def build(name: str, seed: int) -> Puzzle:
    fn, _ = RECIPES[name]
    rng = random.Random(seed)
    pz = fn(rng)
    pz.seed = seed
    return pz
