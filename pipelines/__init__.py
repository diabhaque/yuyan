"""Data pipeline framework: implement Pipeline.fetch(), get storage for free."""

from .base import Pipeline
from .registry import REGISTRY, get, register
from . import sources  # noqa: F401  -- import to populate the registry

__all__ = ["Pipeline", "register", "get", "REGISTRY"]
