"""Monotonic unique ids for simulation entities.

Replaces ``id(obj)`` as the identity key used by the Python↔Rust bridge,
snapshots and chunk freeze/rehydrate bookkeeping:

  * ``id()`` values are recycled after garbage collection (and with object
    pooling they are reused almost immediately), so two different entity
    lifetimes can collide on the same key;
  * CPython heap addresses exceed the 24-bit mantissa of float32, so passing
    ``id()`` through a float32 buffer silently corrupts the low bits — Rust
    then matches zombie rows onto the wrong entities.

A process-global monotonic counter avoids both problems. Ids fit in int64 and
in float64 exactly, so they survive any numeric transport layer.
"""
import itertools

# Global monotonic counter; never reset so ids stay unique for the whole
# process lifetime, even across world regenerations and pool recycling.
_UID_COUNTER = itertools.count(1)


def next_uid() -> int:
    """Return the next globally unique, monotonically increasing entity id."""
    return next(_UID_COUNTER)
