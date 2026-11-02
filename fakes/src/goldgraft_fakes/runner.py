"""Offline runner: returns C4 recordings, never starts a shop or a network job."""

from goldgraft_contracts.runner import JobResult, JobSpec, RawCapture

from ._fixtures import PROOF, boundary, example

PREFIX = "fixtures://proof/legacy-php-shop/raw/"
SHOP_REF = "fixtures://shops/legacy-php-shop/goldgraft-shop.yaml"


class FakeRunner:
    def run_job(self, spec: JobSpec) -> JobResult:
        if spec.shop_pack_ref != SHOP_REF:
            raise LookupError(f"FakeRunner has no shop pack {spec.shop_pack_ref!r}; use {SHOP_REF}")
        result = example("JobResult")
        result.update(job_id=spec.job_id, raw_capture_refs=[], artifacts=[], rate_limit_pauses=0)
        result["runner_identity"].update(workflow="FAKE-offline", run_id=spec.job_id)
        result["logs_ref"] = f"fake://logs/{spec.job_id}"
        # Terminal cases take precedence over fixture lookup, including unknown IDs.
        for suffix, status in (("__timeout", "TIMEOUT"), ("__blocked", "BLOCKED")):
            if any(s.endswith(suffix) for s in spec.scenario_ids):
                result.update(status=status, error=f"FAKE deterministic {status.lower()}")
                return JobResult.model_validate(result)
        refs = [f"{PREFIX}{scenario}.{variant}.json"
                for scenario in spec.scenario_ids for variant in spec.variants]
        for ref in refs:
            self.fetch_capture(ref)
        result.update(status="OK", raw_capture_refs=refs,
                      rate_limit_pauses=int(spec.kind == "RECORD" and len(spec.scenario_ids) > 9))
        return JobResult.model_validate(result)

    def fetch_capture(self, ref: str) -> RawCapture:
        if not ref.startswith(PREFIX):
            raise LookupError(f"Unknown capture reference: {ref!r}")
        name = ref.removeprefix(PREFIX)
        path = PROOF / "raw" / name
        if "/" in name or "\\" in name or not name.endswith(".json") or not path.is_file():
            raise LookupError(f"Unknown capture reference: {ref!r}")
        return boundary("RawCapture/1", path)
