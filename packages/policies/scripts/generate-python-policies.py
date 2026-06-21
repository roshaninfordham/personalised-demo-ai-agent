"""Generate Python constants from policy rule JSON."""

from __future__ import annotations

import json
import pprint
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULE_DIR = ROOT / "rules"
OUT_DIR = ROOT / "generated" / "python" / "live_demo_policies"
HEADER = '"""Generated from packages/policies/rules. Do not edit manually."""\n\n'

MODULES = {
    "action_safety_rules.json": "action_safety_rules.py",
    "rbac_permissions.json": "rbac_permissions.py",
    "redaction_rules.json": "redaction_rules.py",
    "recipe_policy_defaults.json": "recipe_policy_defaults.py",
    "audit_action_catalog.json": "audit_action_catalog.py",
}


def constant_name(file_name: str) -> str:
    return Path(file_name).stem.upper()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    exports: list[str] = []
    for rule_file, module_file in MODULES.items():
        data = json.loads((RULE_DIR / rule_file).read_text(encoding="utf-8"))
        name = constant_name(rule_file)
        exports.append(name)
        content = HEADER + f"{name} = {pprint.pformat(data, sort_dicts=True, width=88)}\n"
        (OUT_DIR / module_file).write_text(content, encoding="utf-8")
    imports = "\n".join(
        f"from live_demo_policies.{Path(module).stem} import {constant_name(rule)}"
        for rule, module in sorted(MODULES.items(), key=lambda item: item[1])
    )
    export_lines = "\n".join(f'    "{name}",' for name in sorted(exports))
    (OUT_DIR / "__init__.py").write_text(
        HEADER + imports + "\n\n__all__ = [\n" + export_lines + "\n]\n",
        encoding="utf-8",
    )
    (OUT_DIR / "types.py").write_text(
        HEADER
        + "from typing import Any\n\n"
        + "JsonObject = dict[str, Any]\n",
        encoding="utf-8",
    )
    print(f"Generated Python policies in {OUT_DIR}")


if __name__ == "__main__":
    main()
