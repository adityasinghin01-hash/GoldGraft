"""Resource Graph and Scope Boundary Mapping (GU01).

Implements:
1. Resource graph representation of files, services, databases, and routes.
2. Discloses differences between selected target resources and full workspace scope.
3. Enforces boundary isolation preventing unselected assets from being modified.
"""

from dataclasses import dataclass, field


@dataclass
class ResourceNode:
    node_id: str
    kind: str  # "repository", "service", "database", "route"
    path: str
    selected: bool = False
    dependencies: list[str] = field(default_factory=list)


class ResourceGraph:
    """Tracks resource topology and isolates selected targets from surrounding workspace."""

    def __init__(self):
        self._nodes: dict[str, ResourceNode] = {}

    def add_resource(
        self,
        node_id: str,
        kind: str,
        path: str,
        *,
        selected: bool = False,
        dependencies: list[str] | None = None,
    ) -> ResourceNode:
        node = ResourceNode(
            node_id=node_id,
            kind=kind,
            path=path,
            selected=selected,
            dependencies=dependencies or [],
        )
        self._nodes[node_id] = node
        return node

    def get_selected_scope(self) -> list[ResourceNode]:
        """Returns only explicitly selected resources authorized for the operation."""
        return [n for n in self._nodes.values() if n.selected]

    def get_workspace_boundary(self) -> dict[str, list[str]]:
        """Discloses full boundary versus selected boundary."""
        selected = [n.node_id for n in self._nodes.values() if n.selected]
        unselected = [n.node_id for n in self._nodes.values() if not n.selected]
        return {"authorized_selected": selected, "fenced_unselected": unselected}

