"""Individually verified offline role implementations, loaded by own runtime policy."""

IMPLEMENTED_ROLES = (
    "Sentinel",
    "Gardener",
    "Builder",
    "Explorer",
    "Scribe",
    "Architect",
    "Grafter",
    "Adversary",
    "Healer",
    "Librarian",
    "Orchard Analyst",
)

ROLE_DEFINITIONS = {
    "Orchard Analyst": ("aggregate", (), ("DashboardSpec/1",), ("aggregate.read",)),
    "Librarian": (
        "learn",
        ("selfcheck_recipe",),
        ("Recipe/1", "DetectionRule/1", "ExecutionProposal/1"),
        ("recipe.stage", "execution.request", "execution.status"),
    ),
    "Healer": (
        "diagnose",
        (),
        ("HealNote/1",),
        ("status.read", "evidence.read", "safety.request_hold"),
    ),
    "Adversary": (
        "derive_guards",
        ("run_mutant",),
        ("ScenarioSet/1", "MutantSet/1", "ExecutionProposal/1"),
        ("source.read", "scenario.stage", "execution.request", "execution.status", "evidence.read"),
    ),
    "Grafter": (
        "candidate_patch",
        (),
        ("ChangeList/2",),
        ("source.read", "dependency.inspect", "candidate.patch"),
    ),
    "Architect": (
        "architect",
        (),
        ("TargetPlan/1",),
        ("recipe.lookup", "docs.lookup", "evidence.read"),
    ),
    "Scribe": (
        "scribe_draft",
        ("scribe_final",),
        ("Contract/1", "TriangleRequest/1"),
        ("source.read", "evidence.read"),
    ),
    "Explorer": (
        "run_scenario",
        (),
        ("ExecutionProposal/1",),
        ("execution.request", "execution.status", "evidence.read"),
    ),
    "Builder": (
        "build_baseline",
        ("build_candidate", "validate_driver"),
        ("ExecutionProposal/1",),
        (
            "recipe.lookup",
            "dependency.inspect",
            "evidence.read",
            "execution.request",
            "execution.status",
        ),
    ),
    "Sentinel": ("audit", (), ("Alert/1",), ("audit.summary", "safety.request_hold")),
    "Gardener": ("propose_plan", (), ("PlanProposal/1",), ("status.read",)),
}
