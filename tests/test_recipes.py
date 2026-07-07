"""Every recipe must verify numerically across many random seeds."""

import sympy as sp
import pytest

from geomake.recipes import RECIPES, build
from geomake.verify import verify

SEEDS = list(range(25))


@pytest.mark.parametrize("name", sorted(RECIPES))
@pytest.mark.parametrize("seed", SEEDS)
def test_recipe_verifies(name, seed):
    pz = build(name, seed)
    res = verify(pz, seed=seed)
    failed = [c for c in res.checks if not c[1]]
    assert res.ok, f"{name} seed={seed} failed checks: {failed}"


@pytest.mark.parametrize("name", sorted(RECIPES))
def test_answer_is_exact_and_positive(name):
    pz = build(name, seed=3)
    val = pz.answer_exact
    # exact: no floats hiding in the expression
    assert not val.atoms(sp.Float), f"{name}: answer contains a float: {val}"
    assert float(val) > 0
    assert pz.solution_steps, "every puzzle carries a solution chain"
    assert len(pz.scene.ops) >= 1, "construction trace must be recorded"


@pytest.mark.parametrize("name", sorted(RECIPES))
def test_declared_depth_matches_registry(name):
    fn, depth = RECIPES[name]
    pz = build(name, seed=1)
    assert pz.depth == depth
