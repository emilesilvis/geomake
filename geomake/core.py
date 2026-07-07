"""Exact geometry core.

Every coordinate and quantity is an exact sympy expression (rationals,
radicals, pi).  Shapes know their exact area; regions are small CSG trees
whose exact area is computable *because the construction guarantees the
required set relations* (containment / disjointness / equality), which are
recorded as assumptions and later checked numerically by the verifier.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable, Sequence

import sympy as sp

# ---------------------------------------------------------------------------
# points

Point = tuple  # (sympy expr, sympy expr)


def P(x, y) -> Point:
    return (sp.sympify(x), sp.sympify(y))


def pfloat(p: Point) -> tuple[float, float]:
    return (float(p[0]), float(p[1]))


def midpoint(a: Point, b: Point) -> Point:
    return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)


def dist(a: Point, b: Point):
    return sp.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def angle_at(vertex: Point, p1: Point, p2: Point):
    """Exact angle p1-vertex-p2 (radians, sympy expr in [0, pi])."""
    v1 = (p1[0] - vertex[0], p1[1] - vertex[1])
    v2 = (p2[0] - vertex[0], p2[1] - vertex[1])
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    n1 = sp.sqrt(v1[0] ** 2 + v1[1] ** 2)
    n2 = sp.sqrt(v2[0] ** 2 + v2[1] ** 2)
    return sp.acos(sp.simplify(dot / (n1 * n2)))


# ---------------------------------------------------------------------------
# shapes


@dataclass(frozen=True)
class Shape:
    name: str = ""

    def area(self):  # -> sympy expr
        raise NotImplementedError

    def contains_pt(self, x: float, y: float, eps: float = 1e-9) -> bool:
        """Float membership test (closed set), used by the MC verifier."""
        raise NotImplementedError

    def bbox(self) -> tuple[float, float, float, float]:
        raise NotImplementedError

    def boundary(self, n: int = 256) -> list[tuple[float, float]]:
        """Float polygon approximating the shape, CCW, for rendering/shapely."""
        raise NotImplementedError


@dataclass(frozen=True)
class Polygon(Shape):
    """Simple polygon, vertices CCW, exact coordinates."""

    pts: tuple = ()

    def area(self):
        s = sp.Integer(0)
        n = len(self.pts)
        for i in range(n):
            x1, y1 = self.pts[i]
            x2, y2 = self.pts[(i + 1) % n]
            s += x1 * y2 - x2 * y1
        return sp.simplify(s / 2)

    def contains_pt(self, x, y, eps=1e-9):
        # winding via crossing count on float coords; boundary counts as inside
        pts = [pfloat(p) for p in self.pts]
        n = len(pts)
        inside = False
        for i in range(n):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % n]
            # on-segment check
            if (
                min(x1, x2) - eps <= x <= max(x1, x2) + eps
                and min(y1, y2) - eps <= y <= max(y1, y2) + eps
            ):
                cross = (x2 - x1) * (y - y1) - (y2 - y1) * (x - x1)
                seg2 = (x2 - x1) ** 2 + (y2 - y1) ** 2
                if seg2 > 0 and cross * cross <= eps * seg2:
                    return True
            if (y1 > y) != (y2 > y):
                xin = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
                if xin > x:
                    inside = not inside
        return inside

    def bbox(self):
        pts = [pfloat(p) for p in self.pts]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return (min(xs), min(ys), max(xs), max(ys))

    def boundary(self, n=256):
        return [pfloat(p) for p in self.pts]


@dataclass(frozen=True)
class Circle(Shape):
    center: Point = (sp.Integer(0), sp.Integer(0))
    r: object = sp.Integer(1)  # sympy expr

    def area(self):
        return sp.simplify(sp.pi * self.r**2)

    def contains_pt(self, x, y, eps=1e-9):
        cx, cy = pfloat(self.center)
        rr = float(self.r)
        return (x - cx) ** 2 + (y - cy) ** 2 <= rr * rr + eps

    def bbox(self):
        cx, cy = pfloat(self.center)
        rr = float(self.r)
        return (cx - rr, cy - rr, cx + rr, cy + rr)

    def boundary(self, n=256):
        cx, cy = pfloat(self.center)
        rr = float(self.r)
        return [
            (cx + rr * math.cos(2 * math.pi * i / n), cy + rr * math.sin(2 * math.pi * i / n))
            for i in range(n)
        ]


@dataclass(frozen=True)
class Sector(Shape):
    """Circular sector (pie slice) from theta1 to theta2 CCW, exact angles."""

    center: Point = (sp.Integer(0), sp.Integer(0))
    r: object = sp.Integer(1)
    theta1: object = sp.Integer(0)
    theta2: object = sp.pi / 2

    def _sweep(self):
        return sp.simplify(self.theta2 - self.theta1)

    def area(self):
        return sp.simplify(self._sweep() / 2 * self.r**2)

    def contains_pt(self, x, y, eps=1e-9):
        cx, cy = pfloat(self.center)
        rr = float(self.r)
        dx, dy = x - cx, y - cy
        if dx * dx + dy * dy > rr * rr + eps:
            return False
        ang = math.atan2(dy, dx)
        t1, t2 = float(self.theta1), float(self.theta2)
        while ang < t1 - 1e-12:
            ang += 2 * math.pi
        return ang <= t2 + 1e-9

    def bbox(self):
        pts = self.boundary(128)
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return (min(xs), min(ys), max(xs), max(ys))

    def boundary(self, n=256):
        cx, cy = pfloat(self.center)
        rr = float(self.r)
        t1, t2 = float(self.theta1), float(self.theta2)
        arc = [
            (cx + rr * math.cos(t1 + (t2 - t1) * i / n), cy + rr * math.sin(t1 + (t2 - t1) * i / n))
            for i in range(n + 1)
        ]
        return [(cx, cy)] + arc


@dataclass(frozen=True)
class CircSegment(Shape):
    """Minor circular segment: region between chord and arc, theta1->theta2 CCW."""

    center: Point = (sp.Integer(0), sp.Integer(0))
    r: object = sp.Integer(1)
    theta1: object = sp.Integer(0)
    theta2: object = sp.pi / 2

    def _sweep(self):
        return sp.simplify(self.theta2 - self.theta1)

    def area(self):
        th = self._sweep()
        return sp.simplify((th - sp.sin(th)) / 2 * self.r**2)

    def _chord_pts(self):
        cx, cy = pfloat(self.center)
        rr = float(self.r)
        t1, t2 = float(self.theta1), float(self.theta2)
        a = (cx + rr * math.cos(t1), cy + rr * math.sin(t1))
        b = (cx + rr * math.cos(t2), cy + rr * math.sin(t2))
        return a, b

    def contains_pt(self, x, y, eps=1e-9):
        cx, cy = pfloat(self.center)
        rr = float(self.r)
        if (x - cx) ** 2 + (y - cy) ** 2 > rr * rr + eps:
            return False
        a, b = self._chord_pts()
        # segment lies left of chord a->b?  arc midpoint decides orientation
        t1, t2 = float(self.theta1), float(self.theta2)
        tm = (t1 + t2) / 2
        mx, my = cx + rr * math.cos(tm), cy + rr * math.sin(tm)
        side_m = (b[0] - a[0]) * (my - a[1]) - (b[1] - a[1]) * (mx - a[0])
        side_p = (b[0] - a[0]) * (y - a[1]) - (b[1] - a[1]) * (x - a[0])
        return side_p * side_m >= -eps * abs(side_m)

    def bbox(self):
        pts = self.boundary(128)
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return (min(xs), min(ys), max(xs), max(ys))

    def boundary(self, n=256):
        cx, cy = pfloat(self.center)
        rr = float(self.r)
        t1, t2 = float(self.theta1), float(self.theta2)
        return [
            (cx + rr * math.cos(t1 + (t2 - t1) * i / n), cy + rr * math.sin(t1 + (t2 - t1) * i / n))
            for i in range(n + 1)
        ]


def square(name: str, origin: Point, side) -> Polygon:
    x, y = origin
    a = sp.sympify(side)
    return Polygon(name=name, pts=(P(x, y), P(x + a, y), P(x + a, y + a), P(x, y + a)))


def rect(name: str, origin: Point, w, h) -> Polygon:
    x, y = origin
    w, h = sp.sympify(w), sp.sympify(h)
    return Polygon(name=name, pts=(P(x, y), P(x + w, y), P(x + w, y + h), P(x, y + h)))


# ---------------------------------------------------------------------------
# regions (CSG with recorded assumptions)


@dataclass
class Region:
    """node kind: 'prim' | 'diff' | 'union'.

    diff  assumes every subtrahend is contained in the minuend and the
          subtrahends are pairwise disjoint;
    union assumes the parts are pairwise interior-disjoint.
    Assumptions are returned by `assumptions()` for numeric verification.
    """

    kind: str
    shape: Shape | None = None
    parts: list = field(default_factory=list)  # list[Region]

    @staticmethod
    def prim(shape: Shape) -> "Region":
        return Region("prim", shape=shape)

    @staticmethod
    def diff(base: "Region | Shape", *holes: "Region | Shape") -> "Region":
        return Region("diff", parts=[_as_region(base)] + [_as_region(h) for h in holes])

    @staticmethod
    def union(*parts: "Region | Shape") -> "Region":
        return Region("union", parts=[_as_region(p) for p in parts])

    @staticmethod
    def inter(*parts: "Region | Shape") -> "Region":
        """True set intersection. No exact area — used only as a ground-truth
        membership reference when verifying an equal-region claim."""
        return Region("inter", parts=[_as_region(p) for p in parts])

    # -- exact area under assumptions
    def area(self):
        if self.kind == "prim":
            return self.shape.area()
        if self.kind == "diff":
            a = self.parts[0].area()
            for h in self.parts[1:]:
                a = a - h.area()
            return sp.simplify(a)
        if self.kind == "union":
            return sp.simplify(sum((p.area() for p in self.parts), sp.Integer(0)))
        raise ValueError(f"no exact area for region kind {self.kind!r}")

    # -- true set-semantics membership (ignores assumptions) for verification
    def contains_pt(self, x: float, y: float) -> bool:
        if self.kind == "prim":
            return self.shape.contains_pt(x, y)
        if self.kind == "diff":
            if not self.parts[0].contains_pt(x, y):
                return False
            return not any(h.contains_pt(x, y) for h in self.parts[1:])
        if self.kind == "union":
            return any(p.contains_pt(x, y) for p in self.parts)
        if self.kind == "inter":
            return all(p.contains_pt(x, y) for p in self.parts)
        raise ValueError(self.kind)

    def bbox(self):
        boxes = [self.shape.bbox()] if self.kind == "prim" else [p.bbox() for p in self.parts]
        return (
            min(b[0] for b in boxes),
            min(b[1] for b in boxes),
            max(b[2] for b in boxes),
            max(b[3] for b in boxes),
        )

    def assumptions(self) -> list[tuple]:
        """[(rel, region_a, region_b), ...] with rel in {'subset','disjoint'}."""
        out = []
        if self.kind == "diff":
            base, holes = self.parts[0], self.parts[1:]
            for h in holes:
                out.append(("subset", h, base))
            for i in range(len(holes)):
                for j in range(i + 1, len(holes)):
                    out.append(("disjoint", holes[i], holes[j]))
        if self.kind == "union":
            for i in range(len(self.parts)):
                for j in range(i + 1, len(self.parts)):
                    out.append(("disjoint", self.parts[i], self.parts[j]))
        if self.kind != "prim":
            for p in self.parts:
                out.extend(p.assumptions())
        return out

    def primitives(self) -> list[Shape]:
        if self.kind == "prim":
            return [self.shape]
        out = []
        for p in self.parts:
            out.extend(p.primitives())
        return out

    def shaded_pieces(self, positive=True) -> list[tuple[Shape, bool]]:
        """(shape, is_positive) pieces in paint order for the renderer.

        Painting positives then negatives in white reproduces the region,
        given the recorded containment assumptions.
        """
        out = []
        if self.kind == "prim":
            out.append((self.shape, positive))
        elif self.kind == "diff":
            out.extend(self.parts[0].shaded_pieces(positive))
            for h in self.parts[1:]:
                out.extend(h.shaded_pieces(not positive))
        elif self.kind == "union":
            for p in self.parts:
                out.extend(p.shaded_pieces(positive))
        return out


def _as_region(x) -> Region:
    return x if isinstance(x, Region) else Region.prim(x)


# ---------------------------------------------------------------------------
# formatting helpers


def fmt_exact(expr) -> str:
    """Human-friendly exact string: -18 + 9*pi -> '9π − 18'."""
    import re

    expr = sp.nsimplify(sp.simplify(expr))
    if expr.is_Add:
        # positive terms first, so we never lead with a minus sign
        pos = [t for t in expr.args if not t.could_extract_minus_sign()]
        neg = [t for t in expr.args if t.could_extract_minus_sign()]
        s = " + ".join(sp.sstr(t) for t in pos)
        for t in neg:
            s += f" - {sp.sstr(-t)}"
    else:
        s = sp.sstr(expr)
    s = s.replace("*pi", "π").replace("pi", "π").replace("*", "·")
    s = s.replace("sqrt", "√").replace(" - ", " − ")
    s = re.sub(r"√\((\d+)\)", r"√\1", s)
    s = s.replace("·√", "√")
    return s


def fmt_latex(expr) -> str:
    return sp.latex(sp.nsimplify(sp.simplify(expr)))
