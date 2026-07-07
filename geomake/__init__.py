"""geomake — backwards-constructed geometry puzzle generator."""

from .puzzle import Given, Puzzle, Target
from .recipes import RECIPES, build, by_depth
from .scene import Scene
from .verify import verify

__version__ = "0.1.0"
__all__ = ["Scene", "Puzzle", "Given", "Target", "RECIPES", "build", "by_depth", "verify"]
