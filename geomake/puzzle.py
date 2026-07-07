"""Puzzle assembly datatypes.

A recipe builds a Scene backwards from known quantities, then wraps it in a
Puzzle: which quantity is asked (target), which givens are revealed, the
exact answer (free by construction), and the solution chain.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import sympy as sp

from .core import Region, Shape, fmt_exact, fmt_latex


@dataclass
class Given:
    """A revealed quantity, with an annotation hint for the renderer.

    kind: 'side' (segment p1-p2), 'radius' (center->rim point), 'angle'
    (vertex, toward p1/p2), or 'text' (free-floating fact, e.g. an area).
    """

    label: str  # e.g. "6 cm" or "40°" or "area = 40"
    kind: str = "side"
    p1: Optional[tuple] = None
    p2: Optional[tuple] = None
    vertex: Optional[tuple] = None
    outside: bool = True  # side labels: place outside the figure


@dataclass
class Target:
    """kind: 'area' (of region) | 'length' (p1-p2) | 'angle' (at vertex)."""

    kind: str
    region: Optional[Region] = None
    p1: Optional[tuple] = None
    p2: Optional[tuple] = None
    vertex: Optional[tuple] = None
    # Optional exact value known by construction (e.g. an angle chosen up
    # front).  The verifier always re-measures the figure independently.
    value: Optional[object] = None

    def exact_value(self):
        if self.value is not None:
            return sp.sympify(self.value)
        if self.kind == "area":
            return self.region.area()
        if self.kind == "length":
            from .core import dist

            return sp.simplify(dist(self.p1, self.p2))
        if self.kind == "angle":
            from .core import angle_at

            return sp.simplify(angle_at(self.vertex, self.p1, self.p2))
        raise ValueError(self.kind)


@dataclass
class Puzzle:
    recipe: str
    question: str
    scene: object  # Scene
    target: Target
    givens: list = field(default_factory=list)
    solution_steps: list = field(default_factory=list)
    # difficulty metadata
    depth: int = 1  # length of the deduction chain
    width: int = 1  # max sub-results feeding one step
    nonstandard: bool = False  # non-standard/composite shape
    unit: str = "cm"
    params: dict = field(default_factory=dict)
    # extra region-equality claims to verify: (claimed_region, true_region)
    equal_region_claims: list = field(default_factory=list)
    seed: int | None = None

    @property
    def answer_exact(self):
        return sp.simplify(self.target.exact_value())

    @property
    def answer_float(self) -> float:
        return float(self.answer_exact)

    def answer_display(self) -> str:
        val = self.answer_exact
        unit = {
            "area": f"{self.unit}²",
            "length": self.unit,
            "angle": "°",
        }[self.target.kind]
        if self.target.kind == "angle":
            deg = sp.simplify(val * 180 / sp.pi)
            return f"{fmt_exact(deg)}{unit}"
        exact = fmt_exact(val)
        approx = f"{float(val):.2f}"
        if exact == approx.rstrip("0").rstrip(".") or "." not in approx and exact == approx:
            return f"{exact} {unit}"
        return f"{exact} {unit} ≈ {approx} {unit}"

    def to_record(self, image_path: str | None = None) -> dict:
        val = self.answer_exact
        rec = {
            "recipe": self.recipe,
            "question": self.question,
            "target_kind": self.target.kind,
            "answer": {
                "exact": fmt_exact(val),
                "latex": fmt_latex(val),
                "float": float(val),
                "display": self.answer_display(),
            },
            "solution_steps": self.solution_steps,
            "difficulty": {
                "depth": self.depth,
                "width": self.width,
                "nonstandard": self.nonstandard,
                "construction_steps": len(self.scene.ops),
            },
            "construction": self.scene.ops,
            "params": {k: str(v) for k, v in self.params.items()},
            "unit": self.unit,
            "seed": self.seed,
        }
        if self.target.kind == "angle":
            rec["answer"]["degrees"] = float(sp.deg(val))
        if image_path:
            rec["image"] = image_path
        return rec
