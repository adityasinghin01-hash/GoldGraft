"""Durable composition of the published fixture runner and independent proof library.

The only supported source here is the existing synthetic-c4 fixture pack. Its
capture identities are preserved exactly. This is an offline reference flow.
"""

import hashlib
import json
from pathlib import Path

from goldgraft_contracts.api import CmelView, Graft, ProofView, ScenarioList
from goldgraft_contracts.registry import validate
from goldgraft_foundation.blobs import LocalBlobStore
from goldgraft_foundation.ledger import Ledger, canonical

from integration.offline import FIXTURE, fixture_proof, fixture_spec
from pieces.proof.mutation import mutation_coverage
from pieces.proof.proof import Proof
from pieces.runner.container_runner import ContainerRunner

PRODUCER = {"kind": "service", "name": "pushed-fixture-integration", "version": "1"}
COMPLETE = "PUSHED_FIXTURE_PROOF_COMPLETE; synthetic results, no merchant authority"


class FixtureRun:
    shop_id = "shop-cutover-legacy"
    graft_id = "synthetic-c4"

    def __init__(self, directory: Path):
        self.directory = Path(directory).resolve()
        self.store = LocalBlobStore(self.directory / "blobs")
        self.ledger = Ledger(f"sqlite:///{self.directory / 'ledger.sqlite'}", blob_store=self.store)
        self.runner = ContainerRunner(blob_store=self.store)
        self.engine = Proof()

    def _append(self, tx, schema, payload, *, kind="ARTIFACT"):
        body = canonical(payload)
        args = {"payload_ref": self.store.put(body)} if len(body) > 16384 else {"payload": payload}
        return tx.append(type=kind, producer=PRODUCER, schema=schema, **args)

    def start(self, key: str, request: dict) -> Graft:
        fingerprint = hashlib.sha256(canonical({"key": key, "request": request})).hexdigest()
        reason = "PUSHED_FIXTURE_START request=" + fingerprint
        with self.ledger.transaction(self.graft_id) as tx:
            rows = tx.read()
            if rows:
                if self.ledger.payload(rows[0]).get("reason") != reason:
                    raise ValueError("CONFLICT immutable fixture request")
                if self.ledger.payload(rows[-1]).get("reason") != COMPLETE:
                    raise ValueError("MISSING_EVIDENCE incomplete fixture run")
            else:
                # The transaction serializes concurrent starts; errors roll back every entry.
                report = fixture_proof(self.runner, self.engine, fixture_spec())
                mutation_input = self._read("mutants/runs.json")
                mutation_ref = self.store.put(canonical(mutation_input))
                self._append(
                    tx,
                    "StageChange/1",
                    {
                        "graft_id": self.graft_id,
                        "from_stage": None,
                        "to_stage": "RECORDED",
                        "attempt": 1,
                        "reason": reason,
                        "actor": {"kind": "service", "name": PRODUCER["name"]},
                        "evidence_refs": [mutation_ref],
                    },
                    kind="STAGE",
                )
                self._append(tx, "JobSpec/1", fixture_spec().model_dump(mode="json"))
                self._append(tx, "JobResult/1", report["job_result"])
                self._append(tx, "Contract/1", self._read("contract.json"))
                self._append(tx, "TargetPlan/1", self._read("target_plan.json"))
                for capture in report["captures"]:
                    self._append(tx, "RawCapture/1", capture)
                for streams in report["cmel"].values():
                    for events in streams.values():
                        for event in events:
                            self._append(tx, "CMEL/1", event)
                for verdict in report["verdicts"]:
                    self._append(tx, "Verdict/1", verdict, kind="VERDICT")
                for scenario in fixture_spec().scenario_ids:
                    self._append(tx, "Scenario/1", self._read(f"scenarios/{scenario}.json"))
                mutations = mutation_input["runs"]
                mutants = [
                    validate("Mutant/1", self._read(f"mutants/{r['mutant']}.json"))
                    for r in mutations
                ]
                for mutant in mutants:
                    self._append(tx, "Mutant/1", mutant.model_dump(mode="json"))
                strength = self.engine.proof_strength(
                    mutants,
                    {r["mutant"]: r["grades"] for r in mutations},
                    reviewed_equivalent={
                        r["mutant"] for r in mutations if r["equivalence"] == "DROPPED"
                    },
                )
                self._append(tx, "ProofStrength/1", strength.model_dump(mode="json"))
                self._append(
                    tx,
                    "StageChange/1",
                    {
                        "graft_id": self.graft_id,
                        "from_stage": "RECORDED",
                        "to_stage": "PARTIAL",
                        "attempt": 1,
                        "reason": COMPLETE,
                        "actor": {"kind": "service", "name": PRODUCER["name"]},
                        "evidence_refs": report["capture_refs"],
                    },
                    kind="STAGE",
                )
        return self.graft()

    @staticmethod
    def _read(name):
        return json.loads((FIXTURE / name).read_text())

    def events(self, after=0):
        if not self.ledger.verify_chain(self.graft_id).ok:
            raise ValueError("DENIED corrupted evidence ledger")
        return self.ledger.read(self.graft_id, after_seq=after)

    def _payloads(self, schema):
        rows = self.events()
        if not rows or self.ledger.payload(rows[-1]).get("reason") != COMPLETE:
            raise LookupError("fixture run has not completed")
        return [validate(schema, self.ledger.payload(r)) for r in rows if r.schema_ == schema]

    def graft(self):
        stages = self._payloads("StageChange/1")
        verdicts = self._payloads("Verdict/1")
        entries = self.events()
        return Graft.model_validate(
            {
                "graft_id": self.graft_id,
                "shop_id": self.shop_id,
                "stage": stages[-1].to_stage,
                "lane": "NO-RUNTIME",
                "started_at": entries[0].ts,
                "stages": [{"stage": s.to_stage, "minutes": 0.0, "usd": 0.0} for s in stages],
                "ledger_root": entries[-1].entry_hash,
                "card": {
                    "old_pieces_found": 0,
                    "pieces_upgraded": 0,
                    "scenarios_total": len(verdicts),
                    "scenarios_pass": sum(v.grade in {"PASS", "PASS_FIXED"} for v in verdicts),
                    "problems": sum(v.grade == "PROBLEM" for v in verdicts),
                    "proof_strength_score": None,
                    "cost_usd": 0.0,
                    "minutes": (entries[-1].ts - entries[0].ts).total_seconds() / 60,
                    "notes": {
                        "_label": "SYNTHETIC published fixture evidence; no source modified",
                        "old_pieces_found": "Source inventory is outside this fixture proof run",
                        "proof_strength_score": (
                            "Proof endpoint uses published fixture mutant outcomes"
                        ),
                        "unverified": str(sum(v.grade == "UNVERIFIED" for v in verdicts)),
                    },
                },
            }
        )

    def scenarios(self):
        verdicts = {v.scenario_id: v for v in self._payloads("Verdict/1")}
        return ScenarioList(
            graft_id=self.graft_id,
            scenarios=[
                {"scenario": s, "verdict": verdicts[s.id]} for s in self._payloads("Scenario/1")
            ],
        )

    def cmel(self, scenario_id):
        scenario_id = scenario_id.upper()
        if scenario_id not in {v.scenario_id for v in self._payloads("Verdict/1")}:
            raise LookupError("unknown fixture scenario")
        events = self._payloads("CMEL/1")
        return CmelView(
            graft_id=self.graft_id,
            scenario_id=scenario_id,
            **{
                field: [e for e in events if e.scenario_id == scenario_id and e.variant == variant]
                for field, variant in (("old", "OLD"), ("old_twin", "OLD_TWIN"), ("new", "NEW"))
            },
        )

    def proof(self):
        mutation_ref = self._payloads("StageChange/1")[0].evidence_refs[0]
        mutation_bytes = self.store.get(mutation_ref)
        if mutation_ref != "blob://" + hashlib.sha256(mutation_bytes).hexdigest():
            raise ValueError("DENIED fixture input blob integrity")
        mutations = json.loads(mutation_bytes)["runs"]
        mutants = self._payloads("Mutant/1")
        coverage = mutation_coverage(
            self._payloads("Contract/1")[0],
            self._payloads("Scenario/1"),
            mutants,
            {r["mutant"]: r["grades"] for r in mutations},
        )
        return ProofView(
            graft_id=self.graft_id,
            mutants=mutants,
            triangle=coverage,
            proof_strength=self._payloads("ProofStrength/1")[0],
        )
