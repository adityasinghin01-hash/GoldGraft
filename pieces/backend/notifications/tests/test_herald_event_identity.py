"""The same committed Surveyor result always yields the same notification key."""

import time

from pieces.agents.source_inventory import build_static_inventory, package_from_sources
from scripts.live_herald_zapier_send import preview_for


def report(stamp):
    case = {"id": "c", "shop_id": "s", "files": {"r.php": "<?php\n$m='RefundTransaction';\n"}}
    inventory = build_static_inventory(package_from_sources(shop_id="s", files=case["files"]))
    turns = [{"provider_observation": {"body": {"recorded_at_utc": stamp}}}]
    return {"passed": True, "inventory": inventory, "turns": turns}, case


def test_replays_of_one_result_share_an_event_key_and_new_results_do_not():
    first, case = report("2026-11-11T08:03:58+00:00")
    a = preview_for(first, case, "private_status")
    time.sleep(0.01)  # a later replay must not change the logical event
    b = preview_for(first, case, "private_status")
    assert a["event_key"] == b["event_key"] and a["delivery"] == "NOT SENT"
    later, _ = report("2026-11-11T09:00:00+00:00")
    assert preview_for(later, case, "private_status")["event_key"] != a["event_key"]
