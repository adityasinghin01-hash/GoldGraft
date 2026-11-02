"""Offline validation of boundary payloads and independent C4 answer-key invariants."""

import copy
import hashlib
import json
import re
from collections import Counter
from fractions import Fraction
from pathlib import Path
from urllib.parse import parse_qsl

import pytest
from cmel_reference import map_capture
from goldgraft_contracts.base_rules import BASE_RULES
from goldgraft_contracts.registry import validate
from heal_reference import counts_from_events, decision, probabilities
from union_reference import grade, identity, projection, rule_hits

ROOT = Path(__file__).resolve().parents[1]
PROOF = ROOT / "proof/legacy-php-shop"
SCENARIOS = (
    "HAPPY",
    "PENDING",
    "REFUND",
    "REFUND_TWICE",
    "DOUBLE",
    "DECLINE",
    "NOTIFY_FORGED",
    "NOTIFY_DUP",
    "PARITY_EXTRA",
)
VARIANTS = ("OLD", "OLD_TWIN", "NEW")
EXPECTED = {
    "HAPPY": "PASS",
    "PENDING": "PROBLEM",
    "REFUND": "PASS",
    "REFUND_TWICE": "PASS_FIXED",
    "DOUBLE": "PASS",
    "DECLINE": "PASS",
    "NOTIFY_FORGED": "PASS",
    "NOTIFY_DUP": "UNVERIFIED",
    "PARITY_EXTRA": "PROBLEM",
}


def load(path):
    return json.loads(path.read_text())


def inventory():
    rows = {}
    for line in (ROOT / "INDEX.md").read_text().splitlines():
        match = re.match(r"\| \[([^]]+)\]\([^)]+\) \| ([^|]+) \|", line)
        if match:
            assert match[1] not in rows
            rows[match[1]] = match[2].strip()
    return rows


def leaves(value, prefix=""):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from leaves(child, prefix + "." + key if prefix else key)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from leaves(child, f"{prefix}[{index}]")
    else:
        yield prefix, value


def resolve(ref):
    file, pointer = ref.split("#", 1)
    value = load(PROOF / file)
    for part in pointer.lstrip("/").split("/"):
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def test_inventory_complete_and_labelled():
    actual = {
        str(p.relative_to(ROOT))
        for p in ROOT.rglob("*")
        if p.is_file() and not set(p.parts) & {"__pycache__", ".pytest_cache", ".ruff_cache"}
    }
    assert set(inventory()) == actual
    assert "PLAN.md" not in actual
    index = (ROOT / "INDEX.md").read_text()
    for line in index.splitlines():
        if line.startswith("| ["):
            assert "S — SYNTHETIC" in line or "R — REAL source" in line
            assert "https://" in line
    assert "not a recording and not a claim about the real shop" in index


@pytest.mark.parametrize("name,schema", list(inventory().items()))
def test_every_payload_validates_against_its_registry_boundary(name, schema):
    path = ROOT / name
    if schema == "LedgerEntry/1 JSONL":
        for line in path.read_text().splitlines():
            validate("LedgerEntry/1", json.loads(line))
        return
    if path.suffix not in {".json", ".yaml"}:
        return
    value = load(path)
    if schema == "reference":
        # These requested derived tables have NO registry boundary; do not invent one.
        assert value["_label"].startswith("SYNTHETIC —")
        assert value["_source"] and all(s.startswith("https://") for s in value["_source"])
        return
    assert schema.endswith("/1") or schema.endswith("/1[]"), name
    for record in value if schema.endswith("[]") else [value]:
        validate(schema.removesuffix("[]"), record)
        assert "_label" not in record and "_source" not in record


def test_vendor_is_byte_identical_to_pinned_git_blobs():
    base = ROOT / "shops/legacy-php-shop"
    manifest = load(base / "vendor_hashes.json")
    assert manifest["commit"] == "aedc11dde1a8793285665ca2188aff62ab5aab65"
    assert len(manifest["files"]) == 16  # 15 sample files and the upstream MIT licence
    actual = {
        "src/" + str(p.relative_to(base / "src")) for p in (base / "src").rglob("*") if p.is_file()
    }
    assert actual == set(manifest["files"]) - {"LICENSE.cutover"}
    for name, expected in manifest["files"].items():
        data = (base / name).read_bytes()
        blob = b"blob " + str(len(data)).encode() + b"\0" + data
        assert hashlib.sha1(blob).hexdigest() == expected, name
    assert "MIT License" in (base / "LICENSE.cutover").read_text()
    assert "not modified" in (base / "NOTICE.md").read_text()


def test_touchpoint_recall_key_and_real_code_locations():
    pack = load(ROOT / "shops/legacy-php-shop/goldgraft-shop.yaml")
    tps = pack["answer_key"]["touchpoints"]
    assert len(tps) == len({tp["id"] for tp in tps}) == 24
    assert Counter(tp["family"] for tp in tps) == {"EC_NVP": 11, "IPN": 6, "CHECKOUT_JS_V4": 7}
    expected_sites = {
        ("SetExpressCheckout", "src/api/create-payment.php", 20),
        ("GetExpressCheckoutDetails", "src/api/execute-payment.php", 12),
        ("DoExpressCheckoutPayment", "src/api/execute-payment.php", 15),
        ("RefundTransaction", "src/api/refund.php", 11),
        ("_notify-validate", "src/ipn.php", 9),
        ("checkout.js script", "src/index.php", 31),
        ("paypal.Button.render", "src/index.php", 38),
    }
    assert expected_sites <= {
        (tp["operation"], tp["location"]["file"], tp["location"]["line"]) for tp in tps
    }
    for tp in tps:
        assert tp["lenses"] == ["code"] and tp["live"] is False
        lines = (ROOT / "shops/legacy-php-shop" / tp["location"]["file"]).read_text().splitlines()
        assert lines[tp["location"]["line"] - 1].strip()
    flow = pack["answer_key"]["money_flow"]
    assert not flow["recurring"]
    assert {"file": "src/api/execute-payment.php", "line": 23} in flow["mark_paid"]
    assert {"file": "src/lib/orders_store.php", "line": 11} in flow["mark_paid"]
    assert pack["start"] == {"compose_file": "docker-compose.yml"}
    assert pack["buyer_script"] == "buyer.spec.ts"


def test_contract_and_target_plan():
    contract = load(PROOF / "contract.json")
    assert [r["id"] for r in contract["rules"]] == [f"R{i:02}" for i in range(1, 18)]
    for actual, base in zip(contract["rules"], BASE_RULES, strict=False):
        assert actual["title"] == base.title
        assert actual["predicate"] == base.predicate_idea
        assert actual["severity"] == base.severity.value
    assert "src/api/create-payment.php:10-16" in contract["rules"][-1]["sources"]["code"]
    plan = load(PROOF / "target_plan.json")
    assert {"V6", "ORDERS_V2", "WEBHOOKS"} <= set(plan["target_experience"])
    assert len(plan["items"]) == 24
    ids = {d["id"] for d in plan["deltas"]}
    assert {
        "D_TOKEN_ORDER",
        "D_TXN_CAPTURE",
        "D_NOTIFY",
        "D_APPROVE",
        "D_REFUND",
        "D_LEDGER_READ",
    } == ids
    for item in plan["items"]:
        assert set(item["delta_ids"]) <= ids
        assert item["mapping_id"].startswith("https://developer.paypal.com/")
    assert any("remain NVP" in rule for rule in plan["origin_rules"])


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_scenario_complete_and_mapper_answers(scenario):
    case = load(PROOF / f"scenarios/{scenario}.json")
    verdict = load(PROOF / f"expected/{scenario}.verdict.json")
    assert case["id"] == verdict["scenario_id"] == scenario
    assert verdict["grade"] == EXPECTED[scenario]
    assert case["assured"]["flake_free_runs"] == 0  # never claim real execution assurance
    for variant in VARIANTS:
        filename = f"{scenario}.{variant}.json"
        raw = load(PROOF / "raw" / filename)
        cmel = load(PROOF / "cmel" / filename)
        assert raw["variant"] == variant and raw["scenario_id"] == scenario
        assert cmel == map_capture(raw, filename)
        assert [e["seq"] for e in cmel] == list(range(len(cmel)))
        for event in cmel:
            assert event["variant"] == variant and event["scenario_id"] == scenario
            exchange = resolve(event["raw_ref"])
            assert event["t_ms"] == exchange["t_ms"]
            if event["source"] == "PAYPAL_LEDGER":
                assert exchange["headers"]["X-GoldGraft-Ledger"] in {"capture", "refund", "order"}
        # Every tagged response is paired with a tagged outbound lookup.
        for index, exchange in enumerate(raw["exchanges"]):
            if exchange["direction"] == "PAYPAL_TO_SHOP" and exchange["headers"].get(
                "X-GoldGraft-Ledger"
            ):
                previous = raw["exchanges"][index - 1]
                assert previous["direction"] == "SHOP_TO_PAYPAL"
                assert previous["url"] == exchange["url"]
                assert (
                    previous["headers"]["X-GoldGraft-Ledger"]
                    == exchange["headers"]["X-GoldGraft-Ledger"]
                )


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_noise_twins_only_differ_in_declared_safe_fields(scenario):
    old = load(PROOF / f"cmel/{scenario}.OLD.json")
    twin = load(PROOF / f"cmel/{scenario}.OLD_TWIN.json")
    assert len(old) == len(twin)
    observed = set()
    for a, b in zip(old, twin, strict=True):
        la, lb = dict(leaves(a)), dict(leaves(b))
        assert la.keys() == lb.keys()
        for key in la:
            if la[key] != lb[key]:
                observed.add(key)
                assert key in a["noise"] and key in b["noise"]
                assert key in {
                    "run_id",
                    "variant",
                    "raw_ref",
                    "t_ms",
                    "pp.legacy_token",
                    "pp.txn_id",
                    "pp.refund_id",
                    "pp.debug_id",
                }
        assert a.get("money") == b.get("money")
        assert a["kind"] == b["kind"] and a.get("status_norm") == b.get("status_norm")
    assert {"run_id", "variant", "raw_ref", "t_ms", "pp.legacy_token"} <= observed
    noise = load(PROOF / f"expected/{scenario}.verdict.json")["noise_masked"]
    assert observed <= set(noise)
    assert not any("money" in name or "status" in name or "kind" in name for name in noise)


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_tri_witness_grades_rule_hits_parity_and_resolvable_evidence(scenario):
    old_raw, new_raw = [load(PROOF / f"raw/{scenario}.{v}.json") for v in ("OLD", "NEW")]
    old, new = [load(PROOF / f"cmel/{scenario}.{v}.json") for v in ("OLD", "NEW")]
    verdict = load(PROOF / f"expected/{scenario}.verdict.json")
    result, new_hits, old_hits, parity = grade(old_raw, old, new_raw, new, verdict)
    assert result == EXPECTED[scenario]
    expected_hits = {(h["side"], h["rule"]) for h in verdict["rule_hits"]}
    assert expected_hits == {("NEW", h) for h in new_hits} | {("OLD", h) for h in old_hits}
    assert bool(verdict["parity_diff"]) == parity
    plan_ids = {d["id"] for d in load(PROOF / "target_plan.json")["deltas"]}
    assert set(verdict["deltas_applied"]) <= plan_ids
    for hit in verdict["rule_hits"]:
        assert hit["evidence"]
        for ref in hit["evidence"]:
            assert resolve(ref)
    if scenario == "PENDING":
        assert new_hits == {"R01", "R07"}
    if scenario == "PARITY_EXTRA":
        assert not new_hits and not old_hits
        extra = resolve(verdict["parity_diff"][0]["event"])
        assert extra["kind"] == "INTENT" and extra["money"] == {"minor": 1250, "currency": "USD"}


def test_ledger_failure_precedes_rules_and_noise_cannot_erase_money():
    raw = load(PROOF / "raw/HAPPY.NEW.json")
    events = load(PROOF / "cmel/HAPPY.NEW.json")
    old_raw = load(PROOF / "raw/HAPPY.OLD.json")
    old = load(PROOF / "cmel/HAPPY.OLD.json")
    verdict = load(PROOF / "expected/HAPPY.verdict.json")
    bad = copy.deepcopy(events)
    next(e for e in bad if e["kind"] == "CAPTURE")["money"]["minor"] = 1
    assert grade(old_raw, old, raw, bad, verdict)[0] == "PROBLEM"
    for x in raw["exchanges"]:
        if x["direction"] == "PAYPAL_TO_SHOP" and x["headers"].get("X-GoldGraft-Ledger"):
            x["status"] = 503
    assert grade(old_raw, old, raw, bad, verdict)[0] == "UNVERIFIED"
    good = load(PROOF / "cmel/HAPPY.NEW.json")
    # Without the declared vocabulary deltas, IDs do not magically match.
    p = projection(old, noise=[], old=True, deltas=[])
    n = projection(good, noise=[], old=False, deltas=[])
    assert p != n


def test_refund_refusal_is_never_a_fabricated_success():
    for variant in VARIANTS:
        raw = load(PROOF / f"raw/REFUND_TWICE.{variant}.json")
        events = load(PROOF / f"cmel/REFUND_TWICE.{variant}.json")
        for source in ("PAYPAL_CALL", "PAYPAL_LEDGER"):
            refunds = [e for e in events if e["kind"] == "REFUND" and e["source"] == source]
            assert len(refunds) == 1 and refunds[0]["money"]["minor"] == 2500
        db = [
            x["db_change"]["after"] for x in raw["exchanges"] if x["direction"] == "SHOP_DB_WRITE"
        ]
        assert db[-1]["refunded_minor"] == (2500 if variant == "NEW" else 5000)
        if variant == "NEW":
            requests = [
                x
                for x in raw["exchanges"]
                if x["direction"] == "SHOP_TO_PAYPAL" and x["url"].endswith("/refund")
            ]
            assert len(requests) == 2
            assert (
                requests[0]["headers"]["PayPal-Request-Id"]
                != requests[1]["headers"]["PayPal-Request-Id"]
            )
    assert rule_hits(
        load(PROOF / "raw/REFUND_TWICE.OLD.json"), load(PROOF / "cmel/REFUND_TWICE.OLD.json")
    ) == {"R11"}


def test_double_and_duplicate_notifications_preserve_one_charge_and_state_change():
    for variant in VARIANTS:
        double = load(PROOF / f"cmel/DOUBLE.{variant}.json")
        assert sum(e["kind"] == "APPROVE" for e in double) == 2
        captures = [e for e in double if e["kind"] == "CAPTURE" and e["source"] == "PAYPAL_CALL"]
        assert len(captures) == len({identity(e) for e in captures}) == 1
        raw = load(PROOF / f"raw/DOUBLE.{variant}.json")
        replies = [
            x["body_json"] for x in raw["exchanges"] if "/api/confirmation-result" in x["url"]
        ]
        assert len(replies) == 2 and replies[0] == replies[1]
        dup = load(PROOF / f"cmel/NOTIFY_DUP.{variant}.json")
        assert sum(e["kind"] == "NOTIFY" for e in dup) == 2
        assert sum(e["kind"] == "SHOP_PAID" for e in dup) == 1


def test_canonical_money_and_redaction():
    for path in PROOF.rglob("*.json"):
        data = load(path)
        for key, value in leaves(data):
            if (
                key.endswith("minor")
                or key.endswith("total_minor")
                or key.endswith("refunded_minor")
            ):
                assert type(value) is int, (path, key)
            if key.endswith("currency") and isinstance(value, str):
                assert re.fullmatch("[A-Z]{3}", value), (path, key)
        if path.parent.name == "raw":
            for exchange in data["exchanges"]:
                for name, value in exchange["headers"].items():
                    if name.lower() == "authorization":
                        assert value == "[REDACTED]"
                fields = dict(parse_qsl(exchange.get("body_text", "")))
                for name in ("PWD", "SIGNATURE", "USER"):
                    if name in fields:
                        assert fields[name] == "[REDACTED]"


def apply_patch(source, patch):
    """Strict unified-diff application: validate old/new line numbers and context."""
    lines, output, cursor = source.splitlines(True), [], 0
    chunks = patch.splitlines(True)
    assert chunks[:2] == ["--- a/payments.php\n", "+++ b/payments.php\n"]
    index = 2
    while index < len(chunks):
        match = re.fullmatch(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@\n", chunks[index])
        assert match, chunks[index]
        start, old_count, new_start, new_count = (
            int(match[1]) - 1,
            int(match[2] or 1),
            int(match[3]) - 1,
            int(match[4] or 1),
        )
        assert start >= cursor
        output.extend(lines[cursor:start])
        cursor = start
        assert len(output) == new_start
        removed = added = 0
        index += 1
        while index < len(chunks) and not chunks[index].startswith("@@"):
            line = chunks[index]
            if line.startswith((" ", "-")):
                assert lines[cursor] == line[1:]
                cursor += 1
                removed += 1
            if line.startswith((" ", "+")):
                output.append(line[1:])
                added += 1
            index += 1
        assert removed == old_count and added == new_count
    output.extend(lines[cursor:])
    return "".join(output)


@pytest.mark.parametrize("number", range(1, 13))
def test_mutant_patch_applies_at_the_reported_source_line(number):
    mutant = load(PROOF / f"mutants/M{number:02}.json")
    assert mutant["id"] == f"M{number:02}" and mutant["op"] == f"M{number}"
    source = (PROOF / mutant["location"]["file"]).read_text()
    patched = apply_patch(source, mutant["patch"])
    assert patched != source and patched.startswith("<?php")
    line = mutant["location"]["line"] - 1
    assert source.splitlines()[line] != patched.splitlines()[line]
    assert 0 < mutant["location"]["line"] <= len(source.splitlines())


def test_mutant_strength_and_expected_run_bookkeeping():
    table = load(PROOF / "mutants/runs.json")
    strength = load(PROOF / "expected/proof_strength.json")
    assert len(table["runs"]) == 12
    killed = dropped = 0
    for run in table["runs"]:
        mutant = load(PROOF / f"mutants/{run['mutant']}.json")
        assert set(run["linked_scenarios"]) == set(run["grades"]) == set(run["baseline_grades"])
        assert set(run["linked_scenarios"]) <= set(SCENARIOS)
        expected_kills = [
            s
            for s, g in run["grades"].items()
            if g == "PROBLEM" and run["baseline_grades"][s] != "PROBLEM"
        ]
        assert mutant["killed_by"] == expected_kills
        assert run["killed"] == bool(expected_kills)
        killed += run["killed"]
        if run["equivalence"] == "DROPPED":
            assert mutant["equivalent_suspect"] and run["equivalence_reason"]
            assert not run["killed"]
            dropped += 1
    assert strength == {
        "total": 12,
        "equivalent_dropped": dropped,
        "killed": killed,
        "score": killed / (12 - dropped),
    }
    assert (killed, dropped) == (4, 1)
    assert table["surviving"] == ["M01", "M04", "M05", "M09", "M10", "M11", "M12"]
    assert strength["score"] < 1


@pytest.mark.parametrize(
    "case,action",
    [
        ("healthy", "STEP_UP"),
        ("thin", "HOLD"),
        ("worse", "CUTBACK"),
        ("money_break", "CUTBACK"),
        ("unverified_notify", "CUTBACK"),
        ("slightly_worse", "HOLD"),
    ],
)
def test_heal_expected_matches_exact_integration_and_guard_evidence(case, action):
    events = load(PROOF / f"heal/case_{case}.events.json")
    expected = load(PROOF / f"heal/case_{case}.expected.json")
    evidence = load(PROOF / f"heal/case_{case}.evidence.json")
    assert expected == decision(
        events, stage=evidence["stage_pct"], hard_stop=evidence["hard_stop"]
    )
    assert expected["action"] == action
    safe, worse = probabilities(*counts_from_events(events))
    assert safe + worse == 1
    assert Fraction(evidence["exact_not_worse"]) == safe
    assert Fraction(evidence["exact_worse"]) == worse
    assert evidence["prob_new_not_worse"] == float(safe)
    assert evidence["prob_new_worse"] == float(worse)
    assert all(p >= Fraction(99, 100) or p <= Fraction(80, 100) for p in (safe, worse))
    if evidence["hard_stop"]:
        guard = evidence["guard_results"][0]
        assert guard["path"] == "NEW" and guard["order_ref"] in {e["order_ref"] for e in events}
        assert safe > Fraction(99, 100) and expected["to_stage_pct"] == 0
        # Same good traffic would promote without this hard-stop evidence.
        assert decision(events)["action"] == "STEP_UP"
        if case == "money_break":
            assert guard["rule"] == "R02" and guard["expected"] != guard["ledger"]
        else:
            assert guard["verification_status"] == "FAILURE" and guard["acted_on"]


def test_heal_reference_against_independent_closed_form_anchors():
    # Independent probability for two uniform priors: triangle with side (1-d).
    safe, worse = probabilities(0, 0, 0, 0)
    assert worse == Fraction(49, 50) ** 2 / 2 and safe == 1 - worse
    # At zero margin, identically distributed independent Betas split evenly.
    for n, success in ((0, 0), (3, 2), (8, 0), (8, 8)):
        safe, worse = probabilities(n, success, n, success, Fraction(0))
        assert safe == worse == Fraction(1, 2)
    # At margin=1, new cannot be strictly more than one worse on [0,1].
    assert probabilities(3, 2, 4, 1, Fraction(1)) == (1, 0)
    with pytest.raises(ValueError):
        probabilities(1, 2, 1, 1)


def test_recipe_confidence_means():
    cases = load(PROOF / "recipes/confidence_cases.json")["cases"]
    assert len(cases) == 6 and (cases[0]["passes"], cases[0]["fails"]) == (0, 0)
    for case in cases:
        a, b = case["passes"] + 1, case["fails"] + 1
        assert (case["posterior_alpha"], case["posterior_beta"]) == (a, b)
        assert case["expected_mean"] == float(Fraction(a, a + b))


def digest(certificate):
    fields = {
        k: v for k, v in certificate.items() if k not in {"signature", "rekor_entry", "ots_proof"}
    }
    return hashlib.sha256(
        json.dumps(fields, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def test_summary_certificate_subset_strength_and_tampered_hash():
    verdicts = [load(PROOF / f"expected/{s}.verdict.json") for s in SCENARIOS]
    summary = load(PROOF / "expected/summary.json")
    assert summary["by_scenario"] == EXPECTED
    counts = Counter(v["grade"] for v in verdicts)
    assert summary["counts"] == {
        g: counts[g] for g in ("PASS", "PASS_FIXED", "PROBLEM", "UNVERIFIED", "N/A")
    }
    assert summary["scenarios"] == len(SCENARIOS) == 9
    valid, tampered = [load(PROOF / f"certificate/{name}.json") for name in ("valid", "tampered")]
    strength = load(PROOF / "expected/proof_strength.json")
    verify = load(PROOF / "certificate/expected_verify.json")
    subset = [v for v in verdicts if v["scenario_id"] in summary["certificate_subset"]]
    assert len(subset) == valid["results"]["scenarios"] == 7
    assert verify["covered_scenarios"] == summary["certificate_subset"]
    assert (
        summary["certificate_excluded"]
        == verify["excluded_scenarios"]
        == ["PENDING", "PARITY_EXTRA"]
    )
    for key, grade_name in (
        ("pass", "PASS"),
        ("pass_fixed", "PASS_FIXED"),
        ("problem", "PROBLEM"),
        ("unverified", "UNVERIFIED"),
        ("n_a", "N/A"),
    ):
        assert valid["results"][key] == sum(v["grade"] == grade_name for v in subset)
    assert valid["proof_strength"] == {
        "mutants_total": strength["total"],
        **{k: v for k, v in strength.items() if k != "total"},
    }
    assert digest(valid) == verify["trusted_payload_sha256"]
    assert digest(tampered) != verify["trusted_payload_sha256"]
    a, b = dict(leaves(valid)), dict(leaves(tampered))
    assert [key for key in a if a[key] != b[key]] == ["cost.tokens"]
    assert verify["tampered"]["failed_check"] == "payload_hash_mismatch"
    assert valid["signature"] == tampered["signature"] == "FAKE-SIGNATURE-FOR-TESTS"
    assert "FAKE" in valid["rekor_entry"] and not verify["valid"]["signature_verified"]
    assert not verify["valid"]["eligible"] and not summary["full_shop_eligible"]
    evidence = valid["paypal_evidence"][0]
    happy = load(PROOF / "cmel/HAPPY.NEW.json")
    capture = next(e for e in happy if e["kind"] == "CAPTURE" and e["source"] == "PAYPAL_CALL")
    assert all(evidence[k] == capture["pp"][k] for k in ("order_id", "capture_id", "debug_id"))


def test_survey_precision_and_recall_are_against_exact_touchpoint_locations():
    key = load(ROOT / "shops/legacy-php-shop/goldgraft-shop.yaml")["answer_key"]["touchpoints"]
    reported = load(PROOF / "survey/rootmap_with_one_miss.json")["touchpoints"]
    scores = load(PROOF / "survey/expected_scores.json")

    def signature(tp):
        return tp["family"], tp["operation"], tp["location"]["file"], tp["location"]["line"]

    truth, found = {signature(tp) for tp in key}, {signature(tp) for tp in reported}
    tp, fn, fp = len(truth & found), len(truth - found), len(found - truth)
    assert (tp, fn, fp) == (23, 1, 1)
    assert scores["recall"] == tp / (tp + fn) == 23 / 24
    assert scores["precision"] == tp / (tp + fp) == 23 / 24


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_public_paypal_wire_fields_and_notification_postback(scenario):
    for variant in VARIANTS:
        raw = load(PROOF / f"raw/{scenario}.{variant}.json")
        previous_notification = None
        create_keys = []
        for x in raw["exchanges"]:
            body = x.get("body_json")
            fields = dict(parse_qsl(x.get("body_text", "")))
            if "PAYERID" in fields:
                assert re.fullmatch("[A-Z0-9]{13}", fields["PAYERID"])
            if x["direction"] == "PAYPAL_NOTIFY_TO_SHOP":
                previous_notification = x
            if x["direction"] == "SHOP_TO_PAYPAL" and fields.get("cmd") == "_notify-validate":
                assert previous_notification
                assert (
                    x["body_text"] == "cmd=_notify-validate&" + previous_notification["body_text"]
                )
            if x["direction"] == "SHOP_TO_PAYPAL" and x["url"].endswith(
                "/verify-webhook-signature"
            ):
                assert set(body) == {
                    "auth_algo",
                    "cert_url",
                    "transmission_id",
                    "transmission_sig",
                    "transmission_time",
                    "webhook_id",
                    "webhook_event",
                }
                assert re.fullmatch("[a-zA-Z0-9]+", body["webhook_id"])
                assert body["webhook_event"] == previous_notification["body_json"]
            if (
                x["direction"] == "SHOP_TO_PAYPAL"
                and x["method"] == "POST"
                and x["url"].endswith("/v2/checkout/orders")
            ):
                create_keys.append(x["headers"]["PayPal-Request-Id"])
                assert body["intent"] == "CAPTURE"
                amount = body["purchase_units"][0]["amount"]
                assert set(amount) == {"currency_code", "value"}
                assert isinstance(amount["value"], str)
            if x["direction"] == "PAYPAL_TO_SHOP" and isinstance(body, dict):
                for unit in body.get("purchase_units", []):
                    for capture in unit.get("payments", {}).get("captures", []):
                        assert "supplementary_data" not in capture
                        assert {"id", "status", "amount", "final_capture"} <= capture.keys()
            if "TRANSACTIONTYPE" in fields:
                assert fields["TRANSACTIONTYPE"] in {"cart", "express-checkout"}
        assert len(create_keys) == len(set(create_keys))
