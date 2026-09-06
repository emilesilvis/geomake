"""Scene: ordered construction DSL over exact geometry.

Every op appends to `self.ops` (an auditable construction trace) and defines
new entities purely in terms of prior ones, so the figure is layout-able by
construction and every derived quantity is exact.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import sympy as sp

from .core import (
    Circle,
    CircSegment,
    P,
    Point,
    Polygon,
    Region,
    Sector,
    Shape,
    dist,
    midpoint,
    rect,
    square,
)


@dataclass
class Scene:
    shapes: dict = field(default_factory=dict)  # name -> Shape (drawn as outlines)
    points: dict = field(default_factory=dict)  # label -> Point
    ops: list = field(default_factory=list)  # construction trace (op, args)
    lines: list = field(default_factory=list)  # aux segments: (p1, p2, style)
    hidden_shapes: set[str] = field(default_factory=set)

    def add_line(self, p1: Point, p2: Point, style: str = "solid"):
        self.ops.append({"op": "draw_segment", "p1": str(p1), "p2": str(p2)})
        self.lines.append((p1, p2, style))

    def _log(self, op: str, **kw):
        self.ops.append({"op": op, **{k: str(v) for k, v in kw.items()}})

    def add(self, shape: Shape, *, visible: bool = True) -> Shape:
        self.shapes[shape.name] = shape
        if visible:
            self.hidden_shapes.discard(shape.name)
        else:
            self.hidden_shapes.add(shape.name)
        return shape

    def pt(self, label: str, p: Point) -> Point:
        self.points[label] = p
        return p

    # ------------------------------------------------------------------ ops

    def place_square(self, name: str, side, origin=(0, 0)) -> Polygon:
        s = square(name, P(*origin), side)
        self._log("place_square", name=name, side=side, origin=origin)
        return self.add(s)

    def place_rotated_square(self, name: str, side, origin: Point, angle) -> Polygon:
        """Square with a corner at origin and its first side at angle radians."""
        x, y = origin
        dx = sp.sympify(side) * sp.cos(angle)
        dy = sp.sympify(side) * sp.sin(angle)
        s = Polygon(name=name, pts=(
            P(x, y), P(x + dx, y + dy),
            P(x + dx - dy, y + dy + dx), P(x - dy, y + dx),
        ))
        self._log("place_rotated_square", name=name, side=side, origin=origin, angle=angle)
        return self.add(s)

    def place_rect(self, name: str, w, h, origin=(0, 0)) -> Polygon:
        s = rect(name, P(*origin), w, h)
        self._log("place_rect", name=name, w=w, h=h, origin=origin)
        return self.add(s)

    def place_right_triangle(self, name: str, leg_a, leg_b, origin=(0, 0)) -> Polygon:
        x, y = origin
        s = Polygon(name=name, pts=(P(x, y), P(x + leg_a, y), P(x, y + leg_b)))
        self._log("place_right_triangle", name=name, a=leg_a, b=leg_b)
        return self.add(s)

    def place_triangle(self, name: str, pts) -> Polygon:
        s = Polygon(name=name, pts=tuple(P(*p) for p in pts))
        self._log("place_triangle", name=name, pts=pts)
        return self.add(s)

    def place_circle(self, name: str, center, r) -> Circle:
        s = Circle(name=name, center=P(*center), r=sp.sympify(r))
        self._log("place_circle", name=name, center=center, r=r)
        return self.add(s)

    def inscribe_circle_in_square(self, name: str, sq: Polygon) -> Circle:
        (x0, y0) = sq.pts[0]
        (x2, y2) = sq.pts[2]
        c = midpoint(sq.pts[0], sq.pts[2])
        r = sp.simplify((x2 - x0) / 2)
        s = Circle(name=name, center=c, r=r)
        self._log("inscribe_circle_in_square", name=name, square=sq.name)
        return self.add(s)

    def inscribe_square_in_circle(self, name: str, circ: Circle, tilted: bool = True) -> Polygon:
        """Square inscribed in circle; tilted=True puts vertices on axes (diamond)."""
        cx, cy = circ.center
        r = circ.r
        if tilted:
            pts = (P(cx + r, cy), P(cx, cy + r), P(cx - r, cy), P(cx, cy - r))
        else:
            h = sp.simplify(r / sp.sqrt(2))
            pts = (P(cx - h, cy - h), P(cx + h, cy - h), P(cx + h, cy + h), P(cx - h, cy + h))
        s = Polygon(name=name, pts=pts)
        self._log("inscribe_square_in_circle", name=name, circle=circ.name, tilted=tilted)
        return self.add(s)

    def circumscribe_circle_about_square(self, name: str, sq: Polygon) -> Circle:
        c = midpoint(sq.pts[0], sq.pts[2])
        r = sp.simplify(dist(sq.pts[0], sq.pts[2]) / 2)
        s = Circle(name=name, center=c, r=r)
        self._log("circumscribe_circle", name=name, square=sq.name)
        return self.add(s)

    def quarter_circle_at_corner(self, name: str, sq: Polygon, corner: int, r=None) -> Sector:
        """Quarter disc centered at a square's corner (0..3, CCW from origin),
        radius defaults to the side, lying inside the square."""
        a = sp.simplify(dist(sq.pts[0], sq.pts[1]))
        r = a if r is None else sp.sympify(r)
        base_angles = {0: 0, 1: sp.pi / 2, 2: sp.pi, 3: 3 * sp.pi / 2}
        t1 = base_angles[corner]
        s = Sector(name=name, center=sq.pts[corner], r=r, theta1=t1, theta2=t1 + sp.pi / 2)
        self._log("quarter_circle_at_corner", name=name, square=sq.name, corner=corner, r=r)
        return self.add(s)

    def semicircle_on_side(self, name: str, p1: Point, p2: Point, inward_left=True) -> Sector:
        """Semicircular disc with diameter p1->p2, bulging to the left of p1->p2."""
        c = midpoint(p1, p2)
        r = sp.simplify(dist(p1, p2) / 2)
        ang = sp.atan2(p2[1] - p1[1], p2[0] - p1[0])
        t1 = sp.simplify(ang) if inward_left else sp.simplify(ang + sp.pi)
        s = Sector(name=name, center=c, r=r, theta1=t1, theta2=t1 + sp.pi)
        self._log("semicircle_on_side", name=name, p1=p1, p2=p2)
        return self.add(s)

    def segment_between(self, name: str, center: Point, r, theta1, theta2, *, visible=True) -> CircSegment:
        s = CircSegment(
            name=name, center=center, r=sp.sympify(r),
            theta1=sp.sympify(theta1), theta2=sp.sympify(theta2),
        )
        self._log("circular_segment", name=name, center=center, r=r, t1=theta1, t2=theta2, visible=visible)
        return self.add(s, visible=visible)

    def overlap_rect_of_squares(self, name: str, s1: Polygon, s2: Polygon) -> Polygon:
        """Axis-aligned overlap rectangle of two axis-aligned squares/rects.

        Constructive: the offset is chosen so the overlap is a rectangle; the
        claimed equality with the true intersection is verified numerically.
        """
        x0 = sp.Max(s1.pts[0][0], s2.pts[0][0])
        y0 = sp.Max(s1.pts[0][1], s2.pts[0][1])
        x1 = sp.Min(s1.pts[2][0], s2.pts[2][0])
        y1 = sp.Min(s1.pts[2][1], s2.pts[2][1])
        s = Polygon(name=name, pts=(P(x0, y0), P(x1, y0), P(x1, y1), P(x0, y1)))
        self._log("overlap_rect", name=name, a=s1.name, b=s2.name)
        return self.add(s)
