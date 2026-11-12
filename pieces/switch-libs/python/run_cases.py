import json
import sys
from pathlib import Path

from switch import decide

data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
failures = [
    c["name"]
    for c in data["cases"]
    if decide(
        c["config"],
        data["public_key_b64"],
        graft_id=data["graft_id"],
        order_ref=c["order_ref"],
        now=data["now"],
        action=c["action"],
        origin=c["origin"],
    )
    != c["expect"]
]
print(
    json.dumps(
        {
            "language": "python",
            "cases": len(data["cases"]),
            "failures": failures,
            "evidence": "SYNTHETIC_SWITCH_CONFORMANCE",
        }
    )
)
raise SystemExit(bool(failures))
