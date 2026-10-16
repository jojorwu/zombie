"""
Deprecated shim. The canonical ModUtility CLI tool now lives in
``src.modding.mod_tools`` (it depends on ``src.modding.LuaModManager``, so
keeping it under ``src.systems`` created a systems <-> modding import cycle).

Maintained for backwards compatibility.
"""
from src.modding.mod_tools import ModUtility

__all__ = ["ModUtility"]
