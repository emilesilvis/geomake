"""Matplotlib rendering: shaded region, outlines, given/target annotations."""

from __future__ import annotations

import math

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import patches

from .core import pfloat
from .puzzle import Puzzle

SHADE = "#88b6d6"
BG = "white"
LINE = "#1a1a2e"
QMARK = "#c1121f"


def _fill(ax, shape, color, z):
    ax.add_patch(
        patches.Polygon(shape.boundary(512), closed=True, facecolor=color,
                        edgecolor="none", antialiased=False, zorder=z)
    )


def _outline(ax, shape, z=5):
    pts = shape.boundary(512)
    xs = [p[0] for p in pts] + [pts[0][0]]
    ys = [p[1] for p in pts] + [pts[0][1]]
    ax.plot(xs, ys, color=LINE, lw=1.6, zorder=z, solid_capstyle="round")


def _scene_bbox(puzzle: Puzzle):
    xs, ys = [], []
    for s in puzzle.scene.shapes.values():
        x0, y0, x1, y1 = s.bbox()
        xs += [x0, x1]
        ys += [y0, y1]
    for p1, p2, _ in puzzle.scene.lines:
        for p in (p1, p2):
            fx, fy = pfloat(p)
            xs.append(fx)
            ys.append(fy)
    return min(xs), min(ys), max(xs), max(ys)


def _rep_point(region):
    """A point comfortably inside the region, for placing the '?'."""
    try:
        from .verify import HAVE_SHAPELY, _region_to_shapely

        if HAVE_SHAPELY:
            from shapely.ops import polylabel

            geometry = _region_to_shapely(region)
            if geometry.geom_type == "MultiPolygon":
                geometry = max(geometry.geoms, key=lambda part: part.area)
            x0, y0, x1, y1 = geometry.bounds
            # A merely interior point can lie in a sliver too narrow for the
            # label. Maximize clearance from the boundary, including holes.
            p = polylabel(geometry, tolerance=max(x1 - x0, y1 - y0) / 256)
            return (p.x, p.y)
    except Exception:
        pass
    import random

    rng = random.Random(7)
    x0, y0, x1, y1 = region.bbox()
    hits = []
    while len(hits) < 60:
        x = x0 + rng.random() * (x1 - x0)
        y = y0 + rng.random() * (y1 - y0)
        if region.contains_pt(x, y):
            hits.append((x, y))
    # Averaging interior points can land in a hole or between disconnected
    # pieces. Choose an actual hit with room around it instead.
    edges = []
    for shape in region.primitives():
        points = shape.boundary(64)
        edges.extend(zip(points, points[1:] + points[:1]))

    def clearance(point):
        px, py = point
        distances = []
        for (ax, ay), (bx, by) in edges:
            dx, dy = bx - ax, by - ay
            length2 = dx * dx + dy * dy
            t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / length2)) if length2 else 0
            distances.append((px - ax - t * dx)**2 + (py - ay - t * dy)**2)
        return min(distances)

    return max(hits, key=clearance)


def _side_label(ax, given, center, scale):
    (x1, y1), (x2, y2) = pfloat(given.p1), pfloat(given.p2)
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    dx, dy = x2 - x1, y2 - y1
    ln = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / ln, dx / ln  # unit normal
    # choose the normal pointing away from the figure center
    if (mx - center[0]) * nx + (my - center[1]) * ny < 0:
        nx, ny = -nx, -ny
    off = 0.06 * scale if given.outside else -0.06 * scale
    ax.text(
        mx + nx * off, my + ny * off, given.label,
        ha="center", va="center", fontsize=13, color=LINE, zorder=9,
    )


def _angle_arc(ax, vertex, p1, p2, label, scale, color=LINE):
    vx, vy = pfloat(vertex)
    a1 = math.degrees(math.atan2(pfloat(p1)[1] - vy, pfloat(p1)[0] - vx))
    a2 = math.degrees(math.atan2(pfloat(p2)[1] - vy, pfloat(p2)[0] - vx))
    # draw the arc spanning the smaller sweep from a1 to a2
    d = (a2 - a1) % 360
    if d > 180:
        a1, a2 = a2, a1
        d = 360 - d
    r = 0.14 * scale
    ax.add_patch(
        patches.Arc((vx, vy), 2 * r, 2 * r, angle=0, theta1=a1, theta2=a1 + d, color=color, lw=1.4, zorder=8)
    )
    bis = math.radians(a1 + d / 2)
    ax.text(
        vx + 1.55 * r * math.cos(bis), vy + 1.55 * r * math.sin(bis), label,
        ha="center", va="center", fontsize=12.5, color=color, zorder=9,
        fontweight="bold" if "?" in label else "normal",
    )


def render(puzzle: Puzzle, path: str, show_answer: bool = False, *, show_difficulty: bool = True):
    x0, y0, x1, y1 = _scene_bbox(puzzle)
    scale = max(x1 - x0, y1 - y0)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2

    fig, ax = plt.subplots(figsize=(5.6, 5.6))
    ax.set_aspect("equal")
    ax.axis("off")

    # shaded region: paint positives, then carve holes in background color
    t = puzzle.target
    if t.kind == "area":
        for shape, positive in t.region.shaded_pieces():
            _fill(ax, shape, SHADE if positive else BG, z=2 if positive else 3)

    # Construction helpers can define the answer without revealing a solution
    # line in the question (e.g. the chord splitting a leaf into segments).
    for s in puzzle.scene.shapes.values():
        if s.name not in puzzle.scene.hidden_shapes:
            _outline(ax, s)
    for p1, p2, style in puzzle.scene.lines:
        (ax1, ay1), (ax2, ay2) = pfloat(p1), pfloat(p2)
        ax.plot(
            [ax1, ax2], [ay1, ay2], color=LINE, lw=1.4, zorder=6,
            linestyle="--" if style == "dashed" else "-",
        )

    # givens
    for g in puzzle.givens:
        if g.kind == "side":
            _side_label(ax, g, (cx, cy), scale)
        elif g.kind == "radius":
            (rx1, ry1), (rx2, ry2) = pfloat(g.p1), pfloat(g.p2)
            mx, my = (rx1 + rx2) / 2, (ry1 + ry2) / 2
            dx, dy = rx2 - rx1, ry2 - ry1
            ln = math.hypot(dx, dy) or 1.0
            ax.text(
                mx - dy / ln * 0.05 * scale, my + dx / ln * 0.05 * scale, g.label,
                ha="center", va="center", fontsize=13, color=LINE, zorder=9,
            )
            ax.plot([rx1], [ry1], marker="o", ms=3.5, color=LINE, zorder=9)
        elif g.kind == "angle":
            _angle_arc(ax, g.vertex, g.p1, g.p2, g.label, scale)
        elif g.kind == "text":
            tx, ty = pfloat(g.p1)
            ax.text(tx, ty, g.label, ha="center", va="center", fontsize=g.font_size, color=LINE, zorder=9)

    # target marker
    if t.kind == "area":
        qx, qy = _rep_point(t.region)
        ax.text(qx, qy, "?", ha="center", va="center", fontsize=t.marker_size, color=QMARK,
                fontweight="bold", zorder=10)
    elif t.kind == "length":
        (lx1, ly1), (lx2, ly2) = pfloat(t.p1), pfloat(t.p2)
        mx, my = (lx1 + lx2) / 2, (ly1 + ly2) / 2
        dx, dy = lx2 - lx1, ly2 - ly1
        ln = math.hypot(dx, dy) or 1.0
        ax.text(mx - dy / ln * 0.06 * scale, my + dx / ln * 0.06 * scale, "?",
                ha="center", va="center", fontsize=22, color=QMARK, fontweight="bold", zorder=10)
    elif t.kind == "angle":
        _angle_arc(ax, t.vertex, t.p1, t.p2, "?", scale, color=QMARK)

    if show_answer:
        ax.set_title(puzzle.answer_display(), fontsize=12, color=LINE)
    if show_difficulty:
        ax.text(0.5, -0.035, f"Estimated difficulty: {puzzle.difficulty_label}",
                transform=ax.transAxes, ha="center", va="top", fontsize=10, color="#666666")

    pad = 0.16 * scale
    ax.set_xlim(x0 - pad, x1 + pad)
    ax.set_ylim(y0 - pad, y1 + pad)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
