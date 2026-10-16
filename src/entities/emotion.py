"""Leaf module defining the survivor emotional state machine levels.

Extracted from ``src.entities.survivor.survivor`` so that sibling modules
(e.g. ``actions.py``, ``looting.py``) can reference the constants without a
lazy import workaround for the actions <-> survivor circular dependency.
"""


class EmotionalState:
    """Survivor emotional state machine levels (leaf definition)."""
    CALM = "CALM"
    CONFIDENT = "CONFIDENT"
    PANICKED = "PANICKED"
    TERRIFIED = "TERRIFIED"
    ENRAGED = "ENRAGED"
