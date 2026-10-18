"""Central registry for module-level thread pools.

Pools created at import time keep worker threads alive for the whole process;
without an explicit shutdown they are only joined during interpreter teardown,
which can hang or race with atexit handlers (and never happens in long-lived
hosts that embed the simulator).  Register every global executor here and call
``shutdown_all_executors()`` from the application entrypoint / test teardown.

This module lives in ``src.core`` on purpose: it is imported by leaf modules
in several packages (simulation, world) and must not pull any of their
barrels into the import graph.
"""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

_REGISTRY: dict[str, ThreadPoolExecutor] = {}


def register_executor(name: str, pool: ThreadPoolExecutor) -> None:
    """Register a module-level pool so it can be shut down deterministically."""
    _REGISTRY[name] = pool


def shutdown_all_executors(wait: bool = True) -> None:
    """Shut down every registered pool exactly once.

    Safe to call multiple times (e.g. app exit + pytest teardown); subsequent
    calls are no-ops because pools are removed from the registry first.
    """
    pools = list(_REGISTRY.items())
    _REGISTRY.clear()
    for name, pool in pools:
        try:
            pool.shutdown(wait=wait)
        except RuntimeError:
            # Already shut down elsewhere — nothing to do.
            pass
        logger.debug("Shut down executor %r", name)
