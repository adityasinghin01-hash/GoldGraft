"""Validate our offline pack with pinned unchanged team Python models; no network."""

import argparse
import hashlib
import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHOP = ROOT / "pieces/shops/legacy-php-shop"
TEAM_REVISION = "da2b5f02d5559c510de6b3b9d81e58400bdf6c89"
PINNED = {
    "common.py": "5458d26aa2e8ce9f9d6e021886a2d2264bdf03ed",
    "currencies.py": "5ceb30bbec615e22865d1ae8aef531508b2fe27c",
    "money.py": "d1cf07c250fd98e8ad90640fb4a9fe7904dbbe12",
    "survey.py": "a7017844e905f7387a992e893c43bab0c0936243",
    "runner.py": "85fae6dc38052bd7e92aa8c48c4862da29c82f9e",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contracts-path", type=Path, default=ROOT / ".context/team-contracts")
    args = parser.parse_args()
    try:
        for name, expected in PINNED.items():
            path = args.contracts_path / "goldgraft_contracts" / name
            if path.is_symlink() or any(p.is_symlink() for p in path.parents):
                raise ValueError("linked_contract_source")
            data = path.read_bytes()
            actual = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
            if actual != expected:
                raise ValueError("pinned_contract_source_changed")
        sys.path.insert(0, str(args.contracts_path.resolve()))
        model = importlib.import_module("goldgraft_contracts.runner").ShopPack
        manifest = json.loads((SHOP / "goldgraft-shop.yaml").read_text(encoding="utf-8"))
        pack = model.model_validate(manifest)
        if pack.shop_id != SHOP.name or pack.scenarios_supported or pack.env_needed:
            raise ValueError("offline_scope_mismatch")
        if not (SHOP / manifest["buyer_script"]).is_file():
            raise ValueError("buyer_missing")
        if pack.source.commit not in (SHOP / "NOTICE.md").read_text(encoding="utf-8"):
            raise ValueError("source_notice_missing")
        for item in manifest["answer_key"]["touchpoints"]:
            location = item["location"]
            path = SHOP / location["file"]
            if not path.resolve().is_relative_to(SHOP.resolve()) or not path.is_file():
                raise ValueError("touchpoint_file_missing")
            if not 1 <= location["line"] <= len(path.read_text(encoding="utf-8").splitlines()):
                raise ValueError("touchpoint_line_missing")
        print(
            json.dumps(
                {
                    "status": "PASS",
                    "schema": "ShopPack/1",
                    "evidence": "UNCHANGED_TEAM_MODEL_VALIDATION",
                    "team_revision": TEAM_REVISION,
                    "shop_count": 1,
                    "touchpoints": len(manifest["answer_key"]["touchpoints"]),
                    "declared_payment_scenarios": 0,
                    "qualified_shop_count": 0,
                }
            )
        )
        return 0
    except (OSError, ValueError, KeyError, TypeError, ImportError):
        print(
            json.dumps(
                {
                    "status": "BLOCKED",
                    "reason": "pinned_contracts_dependencies_or_local_pack_invalid",
                    "qualified_shop_count": 0,
                }
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
