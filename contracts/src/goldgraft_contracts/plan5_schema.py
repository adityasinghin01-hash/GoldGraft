"""JSON Schema projections of conditional wire forms; relational checks remain Python."""

from copy import deepcopy


def decorate(schema: dict, name: str, collection_limit: int) -> dict:
    properties = schema.get("properties", {})
    for field in properties.values():
        if field.get("type") == "array":
            field.setdefault("maxItems", collection_limit)
        if field.get("type") == "object":
            field.setdefault("maxProperties", collection_limit)

    def nonnull(key):
        field = deepcopy(properties[key])
        if "anyOf" in field:
            field = next(x for x in field["anyOf"] if x.get("type") != "null")
        return field

    def array(key, **limits):
        return {**deepcopy(properties[key]), **limits}

    def branch(tag, tag_value, **fields):
        discriminator = {"const": tag_value} if isinstance(tag_value, str) else {"enum": tag_value}
        return {"properties": {tag: {**properties[tag], **discriminator}, **fields}}

    null = {"type": "null"}
    if name in {"CertificateClaims", "CertificateV2"}:
        schema["oneOf"] = []
        for route in ["git", ["local_folder", "cloud_files", "host_export"]]:
            for signer in ["github_actions", "trusted_service"]:
                form = branch(
                    "source_route",
                    route,
                    git_source=nonnull("git_source") if route == "git" else null,
                )
                form["properties"].update(
                    branch(
                        "signer_kind",
                        signer,
                        workflow_identity=nonnull("workflow_identity")
                        if signer == "github_actions"
                        else null,
                        workflow_sha=nonnull("workflow_sha")
                        if signer == "github_actions"
                        else null,
                    )["properties"]
                )
                schema["oneOf"].append(form)
    elif name == "ModelTurnResult":
        schema["oneOf"] = [
            branch(
                "kind",
                "tool_calls",
                calls=array("calls", minItems=1),
                final_artifact_ref=null,
                issue=null,
            ),
            branch(
                "kind",
                "final",
                calls=array("calls", maxItems=0),
                final_artifact_ref=nonnull("final_artifact_ref"),
                issue=null,
            ),
            branch(
                "kind",
                "blocked",
                calls=array("calls", maxItems=0),
                final_artifact_ref=null,
                issue=nonnull("issue"),
            ),
        ]
    elif name == "AgentResult":
        schema["oneOf"] = [
            branch(
                "outcome", "completed", output_refs=array("output_refs", minItems=1), issue=null
            ),
            branch("outcome", ["blocked", "failed", "unknown"], issue=nonnull("issue")),
        ]
    elif name == "ChangeListV2":
        changes = properties["changes"]

        def change_items(commit):
            return {
                **deepcopy(changes),
                "items": {
                    "allOf": [deepcopy(changes["items"]), {"properties": {"commit": commit}}]
                },
            }

        schema["oneOf"] = [
            branch("provenance", "snapshot", branch=null, changes=change_items(null)),
            branch(
                "provenance",
                "git",
                branch=nonnull("branch"),
                changes={**change_items({"type": "string"}), "minItems": 1},
            ),
        ]
    elif name == "WorkStatus":
        schema["oneOf"] = [
            branch(
                "state",
                ["submitting", "held", "unknown", "cancellation_pending", "cancelled", "failed"],
            ),
            branch("state", ["accepted", "queued", "provisioning"], work_id=nonnull("work_id")),
            branch(
                "state",
                "operation_started",
                work_id=nonnull("work_id"),
                generation=nonnull("generation"),
                evidence_refs=array("evidence_refs", minItems=1),
            ),
            branch(
                "state",
                "stopped",
                work_id=nonnull("work_id"),
                evidence_refs=array("evidence_refs", minItems=1),
            ),
        ]
    elif name == "DeliveryDecision":
        schema["oneOf"] = [
            branch(
                "kind",
                "request",
                operation=nonnull("operation"),
                input_refs=array("input_refs", minItems=1),
            ),
            branch(
                "kind",
                ["wait", "hold", "incident", "complete"],
                operation=null,
                slot_id=null,
                existing_effect_ref=null,
            ),
        ]
        schema["allOf"] = [
            {
                "if": {
                    "properties": {
                        "operation": {
                            "enum": [
                                "publish_artifact",
                                "publish_source",
                                "merge_protected",
                                "apply_configuration",
                                "deploy_exact",
                                "preserve_state",
                                "finalise",
                                "run_exit",
                                "revoke_exit_evidence",
                            ]
                        }
                    }
                },
                "then": {"properties": {"slot_id": nonnull("slot_id")}},
            },
            {
                "if": {"properties": {"operation": {"const": "reconcile_effect"}}},
                "then": {
                    "properties": {
                        "slot_id": null,
                        "existing_effect_ref": nonnull("existing_effect_ref"),
                    }
                },
            },
        ]
    elif name == "ManifestEntry":
        schema["oneOf"] = [
            branch("file_type", "file", sha256=nonnull("sha256")),
            branch("file_type", "directory", sha256=null, bytes={"const": 0}),
        ]
    elif name == "ConfigurationEntry":
        schema["oneOf"] = [
            branch("kind", "public_value", value=nonnull("value"), secret_ref=null),
            branch("kind", "secret_reference", value=null, secret_ref=nonnull("secret_ref")),
        ]
    elif name == "UploadSession":
        schema["oneOf"] = [
            branch("state", "finalised", finalised_snapshot_ref=nonnull("finalised_snapshot_ref")),
            branch(
                "state",
                ["pending", "receiving", "cancelled", "expired"],
                finalised_snapshot_ref=null,
            ),
        ]
    return schema
