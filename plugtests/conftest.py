"""Plug-in tests: each piece points its env var at its real implementation;
without the variable the test runs against the stand-in (so it passes today)."""

import importlib
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(env_var: str, default: str):
    """Import 'package.module:attribute' from an env var (or the default stand-in)."""
    target = os.environ.get(env_var, default)
    module, _, attr = target.partition(":")
    obj = importlib.import_module(module)
    for part in attr.split("."):
        obj = getattr(obj, part)
    return obj, target != default


def pytest_collection_modifyitems(items):
    if os.environ.get("GOLDGRAFT_LIVE") != "1":
        skip = pytest.mark.skip(reason="live tests require GOLDGRAFT_LIVE=1")
        for item in items:
            if item.get_closest_marker("live"):
                item.add_marker(skip)
