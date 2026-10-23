"""Deprecated shim: sensory event classes moved to ``src.entities.events``.

The old module name implied perception logic, but it only ever contained
environmental event dataclasses (noise and scent). Keep this shim so that
external code and tests importing ``src.entities.sensory`` keep working.
"""
from src.entities.events import NoiseEvent, ScentTrail

__all__ = ["NoiseEvent", "ScentTrail"]
