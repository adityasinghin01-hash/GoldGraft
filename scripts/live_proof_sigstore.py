"""Runner-only smoke test. Writes one synthetic proof entry to the public log."""

import argparse

from goldgraft_contracts.registry import validate

from pieces.proof.certificate import certificate_payload
from pieces.proof.sigstore import sign_payload, verify_bundle

from .demo_proof import read


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workflow-identity", required=True)
    parser.add_argument("--workflow-sha", required=True)
    args = parser.parse_args()

    raw = read("certificate/valid.json")
    raw["runner_identity"]["sha"] = args.workflow_sha
    certificate = validate("Certificate/1", raw)
    certificate.signature, certificate.rekor_entry = sign_payload(certificate_payload(certificate))
    pins = {"workflow_identity": args.workflow_identity, "workflow_sha": args.workflow_sha}
    if not verify_bundle(certificate, certificate_payload(certificate), **pins):
        raise SystemExit("Live Cosign signature or Rekor verification failed")
    certificate.cost.tokens += 1
    if verify_bundle(certificate, certificate_payload(certificate), **pins):
        raise SystemExit("Live verification accepted a tampered certificate")
    print("SYNTHETIC payload, real Sigstore signature: verified; tampered payload: rejected")


if __name__ == "__main__":
    main()
