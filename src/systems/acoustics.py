"""
Deprecated: The canonical implementation of SoundUtility now lives in the
leaf module ``src.systems.sound`` (stdlib-only, no circular-import risk).

This module is kept as a thin re-export for backwards compatibility.
"""
from src.systems.sound import SoundUtility

__all__ = ["SoundUtility"]
