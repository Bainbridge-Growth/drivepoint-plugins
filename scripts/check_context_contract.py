#!/usr/bin/env python3
"""Check that the context templates satisfy the context contract.

Company and personal context files (profile, guidance, context/<topic>.md,
skills/<name>/SKILL.md) are validated by webapp-server on every write_context
call against plugins/mcp-server/context-templates/context-contract.json. The
templates in that folder are what new companies, Neo's "New file" button, and
the drivepoint-customers importer start from, so they must pass the same
contract. This check fails CI when a template drifts from it.

`validate_file` is the reusable entry point: pass `template=False` to validate
a saved file, where date placeholders are not allowed.

Exit codes:
  0 — every template satisfies the contract
  1 — one or more templates violate the contract
  2 — contract file or templates root missing/malformed
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_ROOT = REPO_ROOT / "plugins/mcp-server/context-templates"
DEFAULT_CONTRACT = TEMPLATES_ROOT / "context-contract.json"

ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
FIELD_RE = re.compile(r"^([a-z_]+):\s*(.*)$")


class ContractError(Exception):
    """Malformed or missing contract / templates input (exit 2)."""


@dataclass
class Violation:
    file: str
    message: str

    def format_message(self) -> str:
        return f"CONTEXT CONTRACT VIOLATION in {self.file}\n  {self.message}"


def load_contract(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ContractError(f"missing contract file: {path}")
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise ContractError(f"malformed contract JSON ({path}): {e}") from e
    for key in ("frontmatter", "kinds", "description", "skill_name", "body_max_chars"):
        if key not in data:
            raise ContractError(f"contract missing required key '{key}': {path}")
    return data


def kind_for(rel: str) -> str:
    return "skill" if rel.endswith("/SKILL.md") or rel == "SKILL.md" else "context"


def parse_frontmatter(text: str) -> tuple[dict[str, str] | None, str, str | None]:
    """Returns (fields, body, error). Frontmatter is flat `key: value` lines between --- fences."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None, text, "file must start with a --- frontmatter fence"
    try:
        end = next(i for i in range(1, len(lines)) if lines[i].strip() == "---")
    except StopIteration:
        return None, text, "frontmatter is missing its closing --- fence"
    fields: dict[str, str] = {}
    for number, line in enumerate(lines[1:end], start=2):
        if not line.strip():
            continue
        match = FIELD_RE.match(line)
        if not match:
            return None, text, f"line {number}: frontmatter must be flat `key: value` lines"
        key, value = match.group(1), match.group(2).strip()
        if key in fields:
            return None, text, f"line {number}: duplicate frontmatter key `{key}`"
        fields[key] = value
    body = "\n".join(lines[end + 1:])
    return fields, body, None


def body_limit(contract: dict[str, Any], rel: str, kind: str) -> int:
    limits = contract["body_max_chars"]
    by_file = limits.get("by_file", {})
    name = rel.rsplit("/", 1)[-1]
    if kind == "context" and name in by_file:
        return int(by_file[name])
    return int(limits[kind])


def validate_file(rel: str, text: str, contract: dict[str, Any], template: bool = False) -> list[Violation]:
    kind = kind_for(rel)
    fields, body, error = parse_frontmatter(text)
    if error:
        return [Violation(rel, error)]
    assert fields is not None
    violations: list[Violation] = []
    spec = contract["kinds"][kind]
    allowed = set(spec["required"]) | set(spec.get("optional", []))
    for key in spec["required"]:
        if not fields.get(key):
            violations.append(Violation(rel, f"missing required {kind} field `{key}`"))
    for key in fields:
        if key not in allowed:
            violations.append(Violation(rel, f"unknown {kind} field `{key}` (allowed: {', '.join(sorted(allowed))})"))

    description = fields.get("description", "")
    rule = contract["description"]
    if description and not description.startswith(rule["prefix"]):
        violations.append(Violation(rel, f"description must start with \"{rule['prefix']}\""))
    if len(description) > int(rule["max_chars"]):
        violations.append(Violation(rel, f"description is {len(description)} characters; the limit is {rule['max_chars']}"))

    placeholder = contract["frontmatter"].get("template_date_placeholder", "YYYY-MM-DD")
    for key in contract["frontmatter"].get("date_fields", []):
        value = fields.get(key)
        if not value:
            continue
        if template and value == placeholder:
            continue
        if not ISO_DATE_RE.match(value):
            violations.append(Violation(rel, f"`{key}` must be an ISO date (YYYY-MM-DD), got `{value}`"))

    if kind == "skill":
        name = fields.get("name", "")
        is_placeholder = template and "<" in name
        if name and not is_placeholder and not re.match(contract["skill_name"]["pattern"], name):
            violations.append(Violation(rel, f"skill name `{name}` must match {contract['skill_name']['pattern']}"))

    limit = body_limit(contract, rel, kind)
    if len(body) > limit:
        violations.append(Violation(rel, f"body is {len(body)} characters; the limit for this file is {limit}"))
    return violations


def run(contract_path: Path = DEFAULT_CONTRACT, templates_root: Path = TEMPLATES_ROOT) -> int:
    try:
        contract = load_contract(contract_path)
    except ContractError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if not templates_root.is_dir():
        print(f"error: templates root not found: {templates_root}", file=sys.stderr)
        return 2

    files = sorted(path for path in templates_root.glob("**/*.md") if path.name != "README.md")
    if not files:
        print(f"error: no templates under {templates_root}", file=sys.stderr)
        return 2

    violations: list[Violation] = []
    for path in files:
        rel = str(path.relative_to(templates_root))
        violations.extend(validate_file(rel, path.read_text(), contract, template=True))

    if violations:
        for violation in violations:
            print(violation.format_message())
            print()
        print(f"{len(violations)} violation(s) across {len({v.file for v in violations})} template(s).")
        return 1

    print(f"OK: {len(files)} template(s) satisfy the context contract.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
