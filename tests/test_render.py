"""The area marker must sit in the asked region, with room to read it."""

import importlib

import pytest

from geomake.recipes import build
from geomake.render import _rep_point

verify = importlib.import_module("geomake.verify")


@pytest.mark.parametrize("name", ["annulus", "square_minus_incircle", "leaf_lens"])
def test_fallback_marker_stays_in_the_shading(name, monkeypatch):
    monkeypatch.setattr(verify, "HAVE_SHAPELY", False)
    region = build(name, seed=7).target.region
    x, y = _rep_point(region)
    assert region.contains_pt(x, y)


def test_corner_marker_has_space_instead_of_sitting_in_a_sliver():
    geometry = pytest.importorskip("shapely.geometry")
    region = build("square_minus_incircle", seed=7).target.region
    x, y = _rep_point(region)
    shape = verify._region_to_shapely(region)
    x0, _, x1, _ = region.bbox()
    assert shape.boundary.distance(geometry.Point(x, y)) > 0.07 * (x1 - x0)
