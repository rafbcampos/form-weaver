from __future__ import annotations

from pathlib import Path

import dspy


def get_default_path(module_name: str) -> Path:
    """Return default path: server/data/optimized/{module_name}.json"""
    return Path(__file__).resolve().parents[3] / "data" / "optimized" / f"{module_name}.json"


def save_optimized(program: dspy.Module, path: Path) -> None:
    """Save optimized program state using dspy's native save."""
    path.parent.mkdir(parents=True, exist_ok=True)
    program.save(str(path))


def load_optimized(program: dspy.Module, path: Path) -> dspy.Module:
    """Load optimized program state. Returns the program with state loaded."""
    program.load(str(path))
    return program
