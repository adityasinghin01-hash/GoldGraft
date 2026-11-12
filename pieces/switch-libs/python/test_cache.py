import json
import sys
from pathlib import Path

from switch import VerifiedConfigCache, route_existing

d = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
c = VerifiedConfigCache(d["graft_id"], d["key"])
assert c.accept(d["initial"], d["now"])
d["initial"]["stage_pct"] = 100
assert c.current(d["now"])["stage_pct"] == 1
assert not c.accept(d["older"], d["now"])
assert not c.accept(d["same_version_changed"], d["now"])
assert not c.accept(d["expired"], d["now"])
assert c.current(d["now"])["stage_pct"] == 1
returned = c.current(d["now"])
returned["stage_pct"] = 100
assert c.current(d["now"])["stage_pct"] == 1
assert c.accept(d["newer"], d["now"])
assert c.current(d["now"])["version"] == 4
assert c.current(d["expires"]) is None
assert route_existing("CAPTURE", "NEW") == "NEW"
try:
    route_existing("REFUND", None)
except ValueError:
    pass
else:
    raise AssertionError("unknown_origin_accepted")
print(json.dumps({"cases": 12, "failures": [], "evidence": "LOCAL_SYNTHETIC_CACHE"}))
