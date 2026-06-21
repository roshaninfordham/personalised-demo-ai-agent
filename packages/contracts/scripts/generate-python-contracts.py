from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

CONTRACTS_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = CONTRACTS_ROOT / "schemas"
OUT_DIR = CONTRACTS_ROOT / "generated" / "python" / "live_demo_contracts"
BASE_HEADER = "# Generated from packages/contracts/schemas. Do not edit manually.\n"
NOQA_HEADER = BASE_HEADER + "# ruff: noqa: E501, F401, RUF100\n\n"
PLAIN_HEADER = BASE_HEADER + "\n"
INIT_HEADER = "# Generated from packages/contracts/schemas. Do not edit manually.\n\n"

FILE_NAME_MAP = {
    "browser-action.schema.json": "browser_action.py",
    "compiled-recipe.schema.json": "compiled_recipe.py",
    "common.schema.json": "common.py",
    "demo-graph.schema.json": "demo_graph.py",
    "demo-recipe.schema.json": "demo_recipe.py",
    "demo-session.schema.json": "demo_session.py",
    "event.schema.json": "event.py",
    "generated-route.schema.json": "generated_route.py",
    "knowledge-retrieval.schema.json": "knowledge_retrieval.py",
    "lead-summary.schema.json": "lead_summary.py",
    "learner-job.schema.json": "learner_job.py",
    "product-learning.schema.json": "product_learning.py",
    "recipe-match.schema.json": "recipe_match.py",
    "recipe-progress.schema.json": "recipe_progress.py",
    "recipe-validation.schema.json": "recipe_validation.py",
    "screen-state.schema.json": "screen_state.py",
    "transcript.schema.json": "transcript.py",
}

COMMON_TYPES = {
    "BoundingBox",
    "DemoPhase",
    "IsoDateTimeString",
    "JsonValue",
    "Metadata",
    "PolicyDecision",
    "ProviderName",
    "RiskLevel",
    "SessionStatus",
    "TraceId",
    "UuidString",
}


def load_schema(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        parsed = json.load(file)

    if not isinstance(parsed, dict):
        raise TypeError(f"{path} must contain a JSON object")

    return parsed


def ref_name(ref: str) -> str:
    name = ref.rsplit("/", maxsplit=1)[-1]
    if not name:
        raise ValueError(f"Invalid $ref: {ref}")
    return name


def enum_member(value: str) -> str:
    member = re.sub(r"[^0-9A-Za-z]+", "_", value).strip("_").upper()
    if not member:
        member = "VALUE"
    if member[0].isdigit():
        member = f"VALUE_{member}"
    return member


def python_type(schema: dict[str, Any]) -> str:
    ref = schema.get("$ref")
    if isinstance(ref, str):
        return ref_name(ref)

    one_of = schema.get("oneOf")
    if isinstance(one_of, list):
        return " | ".join(python_type(item) for item in one_of if isinstance(item, dict))

    any_of = schema.get("anyOf")
    if isinstance(any_of, list):
        return " | ".join(python_type(item) for item in any_of if isinstance(item, dict))

    enum = schema.get("enum")
    if isinstance(enum, list):
        values = ", ".join(json.dumps(item) for item in enum if isinstance(item, str))
        return f"Literal[{values}]"

    schema_type = schema.get("type")
    if isinstance(schema_type, list):
        return " | ".join(
            python_type({**schema, "type": item}) for item in schema_type if isinstance(item, str)
        )
    if schema_type == "string":
        return "str"
    if schema_type == "integer":
        return "int"
    if schema_type == "number":
        return "float"
    if schema_type == "boolean":
        return "bool"
    if schema_type == "null":
        return "None"
    if schema_type == "array":
        items = schema.get("items")
        if not isinstance(items, dict):
            raise TypeError("Array schemas must define object items")
        return f"list[{python_type(items)}]"
    if schema_type == "object":
        additional_properties = schema.get("additionalProperties")
        if isinstance(additional_properties, dict):
            return f"dict[str, {python_type(additional_properties)}]"
        if additional_properties is True:
            return "dict[str, JsonValue]"
        return "dict[str, JsonValue]"

    raise ValueError(f"Unsupported schema type: {schema}")


def field_default(schema: dict[str, Any], required: bool) -> str:
    if "default" in schema:
        default = schema["default"]
        if default == []:
            return " = Field(default_factory=list)"
        if default == {}:
            return " = Field(default_factory=dict)"
        if isinstance(default, bool):
            return f" = {default}"
        return f" = {json.dumps(default)}"

    if required:
        return ""

    return " = None"


def render_definition(name: str, schema: dict[str, Any]) -> str:
    enum = schema.get("enum")
    if isinstance(enum, list):
        lines = [f"class {name}(StrEnum):"]
        for value in enum:
            if not isinstance(value, str):
                raise TypeError(f"Enum {name} contains non-string value")
            lines.append(f"    {enum_member(value)} = {json.dumps(value)}")
        return "\n".join(lines) + "\n"

    if schema.get("type") != "object" or not isinstance(schema.get("properties"), dict):
        return f"type {name} = {python_type(schema)}\n"

    required = set(schema.get("required", []))
    properties = schema["properties"]
    lines = [
        f"class {name}(BaseModel):",
        '    model_config = ConfigDict(extra="forbid")',
        "",
    ]

    for property_name, property_schema in properties.items():
        if not isinstance(property_schema, dict):
            raise TypeError(f"Property {property_name} in {name} must be an object")
        is_required = property_name in required
        property_type = python_type(property_schema)
        if not is_required and "default" not in property_schema:
            property_type = f"{property_type} | None"
        lines.append(
            f"    {property_name}: {property_type}{field_default(property_schema, is_required)}"
        )

    if len(lines) == 3:
        lines.append("    pass")

    return "\n".join(lines) + "\n"


def uses_field(schema: Any) -> bool:
    if isinstance(schema, dict):
        if schema.get("default") in ([], {}):
            return True
        return any(uses_field(value) for value in schema.values())
    if isinstance(schema, list):
        return any(uses_field(item) for item in schema)
    return False


def uses_literal(schema: Any) -> bool:
    if isinstance(schema, dict):
        if isinstance(schema.get("enum"), list):
            return True
        return any(uses_literal(value) for value in schema.values())
    if isinstance(schema, list):
        return any(uses_literal(item) for item in schema)
    return False


def render_file(schema_file_name: str, schema: dict[str, Any]) -> str:
    defs = schema.get("$defs")
    if not isinstance(defs, dict):
        title = schema.get("title")
        if not isinstance(title, str):
            raise TypeError(f"{schema_file_name} must define $defs or string title")
        defs = {title: schema}

    pydantic_imports = ["BaseModel", "ConfigDict"]
    if uses_field(schema):
        pydantic_imports.append("Field")

    imports = [
        "from __future__ import annotations",
        "",
        "from enum import StrEnum",
    ]
    if uses_literal(schema):
        imports.extend(["from typing import Literal", ""])
    else:
        imports.append("")
    imports.append(f"from pydantic import {', '.join(pydantic_imports)}")

    if schema_file_name != "common.schema.json":
        imports.extend(
            [
                "",
                "from live_demo_contracts.common import (",
                *[f"    {type_name}," for type_name in sorted(COMMON_TYPES)],
                ")",
            ]
        )

    body = "\n\n".join(
        render_definition(name, definition)
        for name, definition in defs.items()
        if isinstance(definition, dict)
    )

    header = NOQA_HEADER
    separator = "\n\n\n" if schema_file_name != "common.schema.json" else "\n\n"
    return header + "\n".join(imports) + separator + body


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "__init__.py").write_text(
        INIT_HEADER + '"""Generated Python contracts for the live demo agent platform."""\n',
        encoding="utf-8",
    )

    for schema_path in sorted(SCHEMA_DIR.glob("*.schema.json")):
        output_file_name = FILE_NAME_MAP.get(schema_path.name)
        if output_file_name is None:
            raise ValueError(f"No Python output mapping for {schema_path.name}")
        schema = load_schema(schema_path)
        (OUT_DIR / output_file_name).write_text(
            render_file(schema_path.name, schema),
            encoding="utf-8",
        )

    print(f"Generated Python contracts in {OUT_DIR}")


if __name__ == "__main__":
    main()
