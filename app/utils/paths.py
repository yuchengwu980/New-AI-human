from __future__ import annotations

import os
import sys
from pathlib import Path


def resource_root() -> Path:
    """Directory used to read bundled/static resources."""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return Path(getattr(sys, '_MEIPASS'))
    return Path(__file__).resolve().parents[2]


def runtime_root() -> Path:
    """Writable directory used by application runtime data."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent
    return Path.cwd()


def resource_path(relative_path: str) -> Path:
    return resource_root() / relative_path


def runtime_path(relative_path: str) -> Path:
    return runtime_root() / relative_path


def ensure_dir(path: str | Path) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)
