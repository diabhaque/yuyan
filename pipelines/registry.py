"""Registry mapping pipeline names to classes."""

REGISTRY: dict[str, type] = {}


def register(cls):
    """Class decorator: register a Pipeline under its `name`."""
    REGISTRY[cls.name] = cls
    return cls


def get(name: str):
    if name not in REGISTRY:
        raise KeyError(f"Unknown pipeline {name!r}. Available: {sorted(REGISTRY)}")
    return REGISTRY[name]
