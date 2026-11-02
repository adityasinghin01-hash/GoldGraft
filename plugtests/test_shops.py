"""Every test shop folder is complete, licensed, secret-free and has a valid manifest.

Shops live in pieces/shops/<shop>/ (all-rounder) and fixtures/shops/<shop>/ (examples).
"""

import re

import pytest
import yaml
from goldgraft_contracts.registry import validate

from .conftest import ROOT

SHOPS = sorted(p.parent for p in [*(ROOT / "pieces" / "shops").glob("*/goldgraft-shop.yaml"),
                                  *(ROOT / "fixtures" / "shops").glob("*/goldgraft-shop.yaml")])
SECRET = re.compile(r"(sk-ant-|ghp_|gho_|AKIA[0-9A-Z]{12}|-----BEGIN [A-Z ]*PRIVATE KEY"
                    r"|access_token\"?\s*[:=]\s*\"A21AA)")


def test_at_least_the_example_shop_exists():
    assert any(s.name == "legacy-php-shop" for s in SHOPS)


@pytest.mark.parametrize("shop", SHOPS, ids=lambda p: p.name)
def test_shop_folder(shop):
    manifest = yaml.safe_load((shop / "goldgraft-shop.yaml").read_text())
    pack = validate("ShopPack/1", manifest)
    assert pack.shop_id == shop.name, "folder name must equal shop_id"
    notice = (shop / "NOTICE.md").read_text()
    assert pack.source.commit in notice, "NOTICE.md must name the frozen commit"
    assert re.search(r"(?i)licen[cs]e|MIT|BSD|GPL|Apache", notice), "NOTICE.md must name a licence"
    start = manifest["start"]
    if "compose_file" in start:
        assert (shop / start["compose_file"]).exists()
    assert (shop / manifest["buyer_script"]).exists()
    assert manifest["answer_key"]["touchpoints"], "answer key must list every old PayPal spot"
    for name in manifest.get("env_needed", []):
        assert re.fullmatch(r"[A-Z][A-Z0-9_]*", name), "env_needed holds names only"
    for path in shop.rglob("*"):
        if path.is_file() and path.suffix in {".php", ".js", ".ts", ".py", ".rb", ".yml",
                                              ".yaml", ".json", ".env", ".md", ".html"}:
            assert not SECRET.search(path.read_text(errors="ignore")), f"secret-like text in {path}"
