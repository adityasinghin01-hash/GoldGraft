"""Export v2 metadata from Python contracts; no guessed handlers or API stand-in."""

import re

from .api_routes import PLAN5_ROUTES
from .registry import PLAN5_REGISTRY


def add_plan5(spec: dict) -> None:
    components = spec.setdefault("components", {})
    schemas = components.setdefault("schemas", {})
    for key, model in sorted(PLAN5_REGISTRY.items()):
        schema = model.model_json_schema(
            by_alias=True, ref_template="#/components/schemas/P5_{model}"
        )
        for name, definition in schema.pop("$defs", {}).items():
            name = "P5_" + name
            if name in schemas and schemas[name] != definition:
                raise ValueError(f"conflicting OpenAPI definition: {name}")
            schemas[name] = definition
        component_name = "P5_" + model.__name__
        if component_name in schemas and schemas[component_name] != schema:
            raise ValueError(f"conflicting OpenAPI model: {key}")
        schemas[component_name] = schema
    components["securitySchemes"] = {
        "caseSession": {"type": "apiKey", "in": "cookie", "name": "__Host-goldgraft-session"},
        "draftCapability": {"type": "apiKey", "in": "cookie", "name": "__Host-goldgraft-draft"},
        "serviceIdentity": {
            "type": "http",
            "scheme": "bearer",
            "description": "Authenticated collector identity; never a browser credential",
        },
    }
    security = {
        "session": [{"caseSession": []}],
        "draft": [{"draftCapability": []}],
        "session_and_draft": [{"caseSession": [], "draftCapability": []}],
        "service": [{"serviceIdentity": []}],
        "public_projection": [],
    }
    for route in PLAN5_ROUTES:
        response_refs = [{"$ref": "#/components/schemas/P5_" + m.__name__} for m in route.response]
        response_schema = response_refs[0] if len(response_refs) == 1 else {"oneOf": response_refs}
        operation = {
            "operationId": route.name,
            "summary": route.name.replace("_", " "),
            "security": security[route.auth],
            "x-implementation-status": "contract_only",
            "x-evidence-class": "schema_contract",
            "x-recheck-current-authority": True,
            "responses": {
                str(route.success_status): {
                    "description": (
                        "Committed receipt or current authorised projection; "
                        "synthetic examples are not real evidence"
                    ),
                    "content": {
                        "text/event-stream" if route.sse else "application/json": {
                            "schema": response_schema
                        }
                    },
                }
            },
            "parameters": [],
        }
        for name in re.findall(r"{([^}]+)}", route.path):
            operation["parameters"].append(
                {
                    "name": name,
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string", "minLength": 1, "maxLength": 256},
                }
            )
        for name in route.query:
            schema = {"type": "string", "minLength": 1, "maxLength": 256}
            if name in {"limit", "after"}:
                schema = {"type": "integer", "minimum": 1 if name == "limit" else 0}
                if name == "limit":
                    schema["maximum"] = 50
            operation["parameters"].append(
                {"name": name, "in": "query", "required": False, "schema": schema}
            )
        if route.sse:
            operation["parameters"].append(
                {
                    "name": "Last-Event-ID",
                    "in": "header",
                    "required": False,
                    "schema": {"type": "string", "pattern": r"^\d+$"},
                }
            )
            operation["x-sse-event"] = "case"
            operation["x-payload-projection"] = "authorised_case_projection_only"
        for name, needed in [
            ("Idempotency-Key", route.needs_idempotency_key),
            ("X-CSRF-Token", route.csrf),
        ]:
            if needed:
                operation["parameters"].append(
                    {
                        "name": name,
                        "in": "header",
                        "required": True,
                        "schema": {"type": "string", "minLength": 1, "maxLength": 256},
                    }
                )
        if route.request:
            schema = {"$ref": "#/components/schemas/P5_" + route.request.__name__}
            media = {"schema": schema}
            if route.request_media == "multipart/form-data":
                media = {
                    "schema": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["metadata", "data"],
                        "properties": {
                            "metadata": schema,
                            "data": {"type": "string", "format": "binary", "maxLength": 4194304},
                        },
                    },
                    "encoding": {"metadata": {"contentType": "application/json"}},
                }
            operation["requestBody"] = {"required": True, "content": {route.request_media: media}}
        for code in [400, 401, 403, 404, 409, 410, 412, 422, 429, 503]:
            operation["responses"][str(code)] = {
                "description": (
                    "Typed bounded problem; unknown submission reconciles original identity"
                ),
                "content": {
                    "application/problem+json": {
                        "schema": {"$ref": "#/components/schemas/P5_P5Problem"}
                    }
                },
            }
        if route.auth in {"draft", "session_and_draft"}:
            operation["x-draft-capability"] = (
                "HttpOnly Secure scoped cookie; bound continuation, CSRF, rate/size/TTL; "
                "URL alone grants no access"
            )
            if route.name == "create_draft":
                operation["x-cookie-issuance"] = (
                    "Bootstrap cookie issued by this bounded anonymous request; "
                    "existing cookie is not required"
                )
                operation["security"] = []
        spec["paths"].setdefault(route.path, {})[route.method.lower()] = operation
