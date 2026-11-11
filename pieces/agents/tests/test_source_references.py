"""Source admission must not lose dependencies or execute untrusted source."""

import pytest
from goldgraft_foundation.offline_profile import load_runtime_profile

from pieces.agents.roles import surveyor_configuration
from pieces.agents.scheduler import tick
from pieces.agents.source_inventory import (
    build_static_inventory,
    discover_component_gaps,
    package_from_sources,
)

from .test_runtime import NOW
from .test_source_inventory import run_package


@pytest.mark.parametrize(
    "expression",
    [
        "require $path;",
        "include('lib/' . $part . '.php');",
        "require __DIR__ . '/lib/' . $part;",
        'include "$path";',
        'include "lib/{$name}.php";',
        'include dirname(__FILE__) . "/lib.php";',
        "require 'lib.php' . $suffix;",
        "include ('lib.php') ?: false;",
        "eval($untrusted);",
    ],
)
def test_computed_source_reference_cannot_be_declared_complete(expression):
    gaps = discover_component_gaps(
        {"checkout.php": "<?php\n" + expression, "lib.php": "<?php"}
    )
    assert gaps
    assert all(gap["required_for_scope"] and gap["path"] is None for gap in gaps)
    assert {gap["reason_code"] for gap in gaps} == {"UNRESOLVED_SOURCE_REFERENCE"}


@pytest.mark.parametrize(
    "source",
    [
        '<?php\n// require "missing.php";\n',
        '<?php\n/* include "missing.php"; */\n',
        '<?php\n# include "missing.php";\n',
        "<?php\n$help = 'require \"missing.php\";';\n",
        '<p>include "missing.php";</p><?php echo "catalogue"; ?>',
        '<?php $object->include("missing.php");',
        '<?php Catalog::require("missing.php");',
    ],
)
def test_non_dependency_text_does_not_invent_a_required_component(source):
    assert discover_component_gaps({"checkout.php": source}) == []


@pytest.mark.parametrize(
    "statement",
    [
        'REQUIRE_ONCE "lib.php";',
        'require\n/* source comment */\n("lib.php");',
        'include (__DIR__ . "/lib.php");',
    ],
)
def test_complete_literal_expression_is_resolved_without_execution(statement):
    assert discover_component_gaps(
        {"checkout.php": "<?php\n" + statement, "lib.php": "<?php"}
    ) == []
    missing = discover_component_gaps({"checkout.php": "<?php\n" + statement})
    assert len(missing) == 1
    assert missing[0]["path"] == "lib.php"
    assert missing[0]["reason_code"] == "MISSING_REFERENCED_SOURCE_COMPONENT"


@pytest.mark.parametrize(
    "source",
    [
        '<?php include "unfinished',
        '<?php /* unfinished comment',
        '<?php $source = <<<DOC\nrequire "lib.php";\nDOC;\n',
        '<?php $source = `printf unsafe`;',
    ],
)
def test_unsupported_or_incomplete_lexical_context_holds(source):
    gaps = discover_component_gaps({"checkout.php": source})
    assert gaps and all(g["required_for_scope"] for g in gaps)
    assert {g["reason_code"] for g in gaps} == {"UNSUPPORTED_SOURCE_SYNTAX"}


def test_caller_cannot_clear_computed_dependency_to_bypass_role_admission(tmp_path):
    package = package_from_sources(
        shop_id="forged-completeness",
        files={"checkout.php": "<?php\nrequire $path;\n"},
    )
    package["snapshot"]["completeness"] = "complete_for_declared_scope"
    package["omissions"]["items"] = []
    ports = load_runtime_profile(
        "offline",
        tmp_path / "forged.sqlite",
        fixture="surveyor_inventory",
        configuration=dict(
            surveyor_configuration(), offline_final_payload=build_static_inventory(package)
        ),
        inputs=package,
        clock=lambda: NOW,
    )
    tick("fake:runtime-run", NOW, ports)
    result = ports.control.result("survey")
    assert result.outcome == "blocked"
    assert result.issue.code == "MISSING_EVIDENCE"
    assert result.output_refs == []
    assert ports.model.total_dispatches() == ports.tools.total_dispatches() == 0


def test_dynamic_include_holds_before_any_scripted_turn_or_tool(tmp_path):
    ports, package = run_package(tmp_path, {"checkout.php": "<?php\ninclude $path;\n"})
    assert package["snapshot"]["completeness"] == "incomplete"
    assert ports.control.result("survey").outcome == "blocked"
    assert ports.model.total_dispatches() == ports.tools.total_dispatches() == 0


def test_php_attribute_context_is_not_discarded_as_a_hash_comment():
    gaps = discover_component_gaps(
        {"checkout.php": "<?php #[Meta] function pay() { require $path; }"}
    )
    assert gaps and {g["reason_code"] for g in gaps} == {"UNSUPPORTED_SOURCE_SYNTAX"}


def test_interpolated_string_cannot_hide_executable_source_loading():
    gaps = discover_component_gaps(
        {"checkout.php": '<?php $text = "${include $path}";'}
    )
    assert gaps and {g["reason_code"] for g in gaps} == {"UNRESOLVED_SOURCE_REFERENCE"}
