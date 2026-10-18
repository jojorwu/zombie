"""Shared pytest fixtures for the whole test-suite."""
from __future__ import annotations

import pytest

from src.core.executors import shutdown_all_executors


@pytest.fixture(scope="session", autouse=True)
def _shutdown_global_executors() -> object:
    """Join module-level thread pools after the last test in the session.

    Without this, ThreadPoolExecutors created at import time leak worker
    threads into interpreter teardown and can race with other atexit hooks.
    """
    yield
    shutdown_all_executors(wait=False)
