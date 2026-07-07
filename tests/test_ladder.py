"""Ladders must ramp gradually and pass every independent validation check."""

import pytest

from geomake.ladder import build_ladder, score, validate_ladder

SEEDS = [0, 1, 2]


@pytest.mark.parametrize("seed", SEEDS)
def test_ladder_validates(seed):
    puzzles = build_ladder(n=9, seed=seed)
    failed = [(name, detail) for name, ok, detail in validate_ladder(puzzles) if not ok]
    assert not failed, f"ladder seed={seed} failed checks: {failed}"


def test_ladder_is_monotone_and_spans_depths():
    puzzles = build_ladder(n=12, seed=0)
    scores = [score(pz) for pz in puzzles]
    assert scores == sorted(scores)
    assert puzzles[0].depth == 1 and puzzles[-1].depth == 3
    assert {pz.depth for pz in puzzles} == {1, 2, 3}


def test_ladder_too_short_rejected():
    with pytest.raises(ValueError):
        build_ladder(n=2, seed=0)
