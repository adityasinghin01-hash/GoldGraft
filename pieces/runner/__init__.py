"""Runner package for GoldGraft (pieces.runner).

Implements isolated container runner (GU04) conforming to the runner contract.
"""

from .container_runner import ContainerRunner, Runner

__all__ = ["ContainerRunner", "Runner"]
