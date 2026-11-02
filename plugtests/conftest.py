"""Plug-in tests: each piece points its env var at its real implementation;
without the variable the test runs against the stand-in (so it passes today)."""

import importlib
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(env_var: str, default: str):
    """Import 'package.module:attribute' from an env var (or the default stand-in)."""
    target = os.environ.get(env_var, default)
    module, _, attr = target.partition(":")
    obj = importlib.import_module(module)
    for part in attr.split("."):
        obj = getattr(obj, part)
    return obj, target != default
