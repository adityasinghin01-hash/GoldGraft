"""Shop-socket entry point. Contracts only; execution is delegated to the host.

The reviewed local host profile admits only the explicit operator fixture. A
different agent candidate needs qualified protected execution, not implicit host
execution. Source data and ordinary imports never authorize external effects.
"""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


def execute(run_dir, output, *, php="php"):
    root = Path(__file__).resolve().parents[3]
    result = subprocess.run(
        [
            sys.executable,
            str(root / "scripts/execute_shop_recipe.py"),
            "--execute-reviewed-host",
            "--run-dir",
            str(run_dir),
            "--output",
            str(output),
            "--php",
            str(php),
        ],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=180,
    )
    if result.returncode:
        (Path(run_dir) / "recipe-execution.log").write_text(
            result.stdout + result.stderr, encoding="utf-8"
        )
        raise ValueError("reviewed local host recipe held; see its private execution log")
    return json.loads((Path(output) / "REPORT.json").read_text(encoding="utf-8"))


def _domain():
    path = Path(__file__).parent.parent / "legacy-php-shop/lifecycle_recipes.py"
    spec = importlib.util.spec_from_file_location("vijay_domain_recipes", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def state_recipe(*args, **kwargs):
    return _domain().state_recipe(*args, **kwargs)


def finalisation_recipe(*args, **kwargs):
    return _domain().finalisation_recipe(*args, **kwargs)


def exit_check_recipe(*args, **kwargs):
    return _domain().exit_check_recipe(*args, **kwargs)
