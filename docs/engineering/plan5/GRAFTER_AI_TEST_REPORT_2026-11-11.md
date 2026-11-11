# Grafter — real-model test, 11 November 2026

**ACCEPTED MODEL COMPONENT SCOPE.** Actual guarded runtime and component gateway, original synthetic
MIT cases and scripted tool/control/collector counterparts. Model/profile routing
is fixed before dispatch; no infrastructure or live-shop qualification.

| Measure | Result |
|---|---|
| Final sample | **24/29 passed**; rounds g0, g1, g2, g3 |
| Output acceptance | 17/29 produced accepted artifacts |
| Audit | 24/29 clean: receipts, rescore, output use, reopen |
| Hostile preflight | 3/3 held, $0, zero model calls |
| Free replay | 11/11 (not a model-quality score) |
| Profiles | haiku8, sonnet |
| Turns | 1–3 per run |
| Latency | 7.91s median; 8.98s max |
| Role spend | $0.096823 of $1.60; all rounds |
| Project spend | $2.691255 of $10; no unresolved turns/reservations |
| Checks | 101–104: 873 tests; lint/format/diff clean |
| scored | 17/21 correct |
| model_hold | 7/8 correct |

| Capability | Evidence |
|---|---|
| Bounded patch | 1–2 files; exact replacements and untouched file preservation |
| Repair lineage | Repair rounds 1 and 2 require fresh independent failure |
| Collector inspection | Observed wrong-tree/missing-snapshot faults; independent review remains mandatory |
| Snapshot output | ChangeList/2 snapshot refs; null branch and commit |

| Fix | Reason |
|---|---|
| Private inline | CandidatePatch map validated and staged task-scoped; no public record change |
| Provider schemas | Closed path keys and snapshot-only output projection after free schema rejections |
| Metadata review | Model label and grounded summary may vary; lineage/digests remain exact |
| Installed operation | Every target plan operation checked against installed symbols |
| Typed hold | Missing snapshot becomes MISSING_EVIDENCE instead of KeyError |
| Hidden control | Collector fault switch removed from provider presentation; real receipt remains visible |
| Read routing | Haiku four-file overflow twice; Sonnet also failed, tuning stopped |

Failed final runs (held, not hidden): `ag-grafter-gr-4-files-g0`, `ag-grafter-gr-wrong-tree-g0`, `ag-grafter-gr-2-files-g1`, `ag-grafter-gr-repair1-g1`, `ag-grafter-gr-repair2-g2`.

Decisions: case labels were fixed before paid runs; no post-result relabelling.
Independent labels are excluded from model context. Artifact output inspection and
read-only reopen are evidence of synthetic consumer use, not teammate service acceptance.

Limits: Four-file shape failed on both profiles (native call count), unqualified and not repeated after failed pilot; g0 retains that failure, g1–g3 cover the seven previously pilot-passing cases (29 final runs total). Hard safety never accepts wrong artifacts; model hold quality is reported independently. No general migration, actual container/CAS/collector/payment qualification, APIMatic, deployment or live writes. Preflight p1 eight cases and p2 one case were $0 provider schema rejections; p3/p4 retain development evidence and all spend. Labels unchanged.

Evidence: `~/reports/goldgraft-all-agents-20261111/grafter/` (cases, dry runs,
series log and audit); run artifacts at `~/reports/goldgraft-model-gateway-20261111/live/ag-grafter-*`.
