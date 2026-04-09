"""Root conftest — shared pytest configuration."""
from __future__ import annotations

import os

# Prevent OpenBLAS deadlock on Windows (numpy/scipy thread contention).
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
