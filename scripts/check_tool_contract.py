#!/usr/bin/env python3
"""Check that MCP tool identifiers named in skills exist in the tool registry.

Skills (common-skills/**/SKILL.md) name tools in their workflow steps, e.g.
`save_product_mappings`. When a tool is renamed in the webapp-server MCP
registry, a skill that still names the old identifier silently points the model
at a tool that no longer exists. This check fails CI on that drift.

It scans for backticked, tool-shaped identifiers (snake_case whose first segment
is a known tool verb prefix) and flags any that are not in the pinned
`valid_tools` list and not in the `allow_non_tool` escape hatch.

Exit codes:
  0 — every tool-shaped reference resolves to a known tool
  1 — one or more skills reference an unknown tool identifier (message is a fix
      instruction for a coding agent)
  2 — pin file or skills root missing/malformed
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PIN = REPO_ROOT / "plugins/mcp-server/skills/tool-names.json"

# A backticked snake_case identifier: `foo_bar`, `foo_bar_baz`.
BACKTICKED_TOKEN_RE = re.compile(r"`([a-z][a-z0-9]*(?:_[a-z0-9]+)+)`")

REMEDY = (
    "this identifier is tool-shaped but is not a registered MCP tool. Either it is "
    "a stale reference to a renamed/removed tool (update the skill to the current "
    "tool name), or it is a real tool that was just added/renamed (add it to "
    "valid_tools in plugins/mcp-server/skills/tool-names.json IN THE SAME CHANGE as "
    "the webapp-server registry edit), or it is a non-tool token that merely shares a "
    "tool verb prefix (add it to allow_non_tool). Do not add a name to valid_tools "
    "unless the webapp-server MCP server actually registers it."
)


class ContractError(Exception):
    """Malformed or missing pin / skills input (exit 2)."""


@dataclass
class DeadRef:
    """A skill reference to an unknown tool identifier (collected into exit 1)."""

    file: str
    token: str
    line: int

    def format_message(self) -> str:
        return (
            f"UNKNOWN TOOL REFERENCE in {self.file}:{self.line}\n"
            f"  token: `{self.token}`\n"
            f"  remedy: {REMEDY}"
        )


def load_pin(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ContractError(f"missing pin file: {path}")
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise ContractError(f"malformed pin JSON ({path}): {e}") from e
    for key in ("skills_root", "tool_verb_prefixes", "valid_tools"):
        if key not in data:
            raise ContractError(f"pin missing required key '{key}': {path}")
    return data


def is_tool_shaped(token: str, verb_prefixes: set[str]) -> bool:
    return token.split("_", 1)[0] in verb_prefixes


def scan_skill(
    rel: str,
    text: str,
    verb_prefixes: set[str],
    known: set[str],
) -> list[DeadRef]:
    dead: list[DeadRef] = []
    for match in BACKTICKED_TOKEN_RE.finditer(text):
        token = match.group(1)
        if not is_tool_shaped(token, verb_prefixes):
            continue
        if token in known:
            continue
        line = text.count("\n", 0, match.start()) + 1
        dead.append(DeadRef(rel, token, line))
    return dead


def run(pin_path: Path = DEFAULT_PIN) -> int:
    try:
        pin = load_pin(pin_path)
    except ContractError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    skills_root = REPO_ROOT / pin["skills_root"]
    if not skills_root.is_dir():
        print(f"error: skills_root not found: {skills_root}", file=sys.stderr)
        return 2

    verb_prefixes = set(pin["tool_verb_prefixes"])
    known = set(pin["valid_tools"]) | set(pin.get("allow_non_tool", []))

    skill_files = sorted(skills_root.glob("**/SKILL.md"))
    if not skill_files:
        print(f"error: no SKILL.md files under {skills_root}", file=sys.stderr)
        return 2

    dead: list[DeadRef] = []
    for path in skill_files:
        rel = str(path.relative_to(REPO_ROOT))
        dead.extend(scan_skill(rel, path.read_text(), verb_prefixes, known))

    if dead:
        for ref in dead:
            print(ref.format_message())
            print()
        print(f"{len(dead)} unknown tool reference(s) across {len({d.file for d in dead})} skill(s).")
        return 1

    print(f"OK: {len(skill_files)} skill(s) scanned, all tool references resolve.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
