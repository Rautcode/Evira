"""Filesystem path-safety helpers to prevent directory traversal."""

import os
from typing import Iterable


def resolve_within(base_dir: str, candidate: str) -> str:
    """Resolve ``candidate`` and ensure it stays inside ``base_dir``.

    Returns the absolute, real path on success. Raises ``ValueError`` if the
    resolved path escapes ``base_dir`` (e.g. via ``..`` or an absolute path)
    or if ``candidate`` is empty.
    """
    if not candidate:
        raise ValueError("Empty path")
    base_real = os.path.realpath(base_dir)
    target_real = os.path.realpath(os.path.join(base_real, candidate))
    # Guard with os.sep so "/data" doesn't match "/data-evil".
    if target_real != base_real and not target_real.startswith(base_real + os.sep):
        raise ValueError("Path escapes the permitted directory")
    return target_real


def is_within_any(candidate: str, allowed_dirs: Iterable[str]) -> bool:
    """Return True if ``candidate`` resolves inside one of ``allowed_dirs``."""
    target_real = os.path.realpath(candidate)
    for base in allowed_dirs:
        base_real = os.path.realpath(base)
        if target_real == base_real or target_real.startswith(base_real + os.sep):
            return True
    return False
