#!/usr/bin/env python3
"""Compare customer-facing skill brand values against the pinned contract.

Exit codes:
  0 — all values match the pin
  1 — one or more values drifted (message is a fix instruction for a coding agent)
  2 — contract or skill file missing/malformed
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = REPO_ROOT / "plugins/mcp-server/skills/brand-contract.json"
CSS_HEX_RE = re.compile(
    r"(?<![0-9A-Fa-f])#(?:[0-9A-Fa-f]{8}|[0-9A-Fa-f]{6}|"
    r"[0-9A-Fa-f]{4}|[0-9A-Fa-f]{3})(?![0-9A-Fa-f])"
)

REMEDY = (
    "restore this value from brand-contract.json. Only update the pin itself if your "
    "ticket explicitly changes brand values — pin edits are brand decisions, not fixes."
)


class ContractError(Exception):
    """Malformed or missing contract / skill input (exit 2)."""


class Drift(Exception):
    """A single brand-value mismatch (collected into exit 1)."""

    def __init__(self, file: str, key: str, expected: Any, found: Any):
        self.file = file
        self.key = key
        self.expected = expected
        self.found = found

    def format_message(self) -> str:
        return (
            f"BRAND CONTRACT DRIFT in {self.file}\n"
            f"  value: {self.key}\n"
            f"  expected: {self.expected!r}\n"
            f"  found:    {self.found!r}\n"
            f"  remedy: {REMEDY}"
        )


def extract_balanced(text: str, start: int, opening: str, closing: str) -> str:
    depth = 0
    quote: str | None = None
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in "\"'":
            quote = char
        elif char == opening:
            depth += 1
        elif char == closing:
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    raise ContractError(f"unterminated {opening}{closing} assignment")


def extract_dp_constants(text: str) -> dict[str, Any]:
    consts: dict[str, Any] = {}
    for m in re.finditer(r"^const (DP_[A-Z0-9_]+)\s*=\s*", text, re.M):
        name = m.group(1)
        start = m.end()
        rest = text[start:].lstrip()
        if not rest:
            raise ContractError(f"empty assignment for {name}")
        if rest.startswith("["):
            i = text.find("[", start)
            raw = extract_balanced(text, i, "[", "]")
            consts[name] = [a or b for a, b in re.findall(r"'([^']+)'|\"([^\"]+)\"", raw)]
        elif rest.startswith("{"):
            i = text.find("{", start)
            raw = extract_balanced(text, i, "{", "}")
            pairs = re.findall(
                r"(?:'([^']+)'|\"([^\"]+)\")\s*:\s*(?:'([^']*)'|\"([^\"]*)\")",
                raw,
            )
            consts[name] = {
                single or double: single_value or double_value
                for single, double, single_value, double_value in pairs
            }
        elif rest[0] in "\"'":
            q = rest[0]
            k = 1
            while k < len(rest):
                if rest[k] == q and rest[k - 1] != "\\":
                    break
                k += 1
            consts[name] = rest[1:k]
        else:
            m2 = re.match(r"(\d+)", rest)
            if not m2:
                raise ContractError(f"unparseable assignment for {name}")
            consts[name] = int(m2.group(1))
    return consts


def extract_fenced_code(text: str, languages: set[str]) -> list[str]:
    pattern = re.compile(
        r"^```(?P<language>[\w+-]+)[ \t]*\r?\n(?P<body>.*?)^```[ \t]*$",
        re.M | re.S,
    )
    return [
        match.group("body")
        for match in pattern.finditer(text)
        if match.group("language") in languages
    ]


def extract_component(code_blocks: list[str], name: str) -> str | None:
    pattern = re.compile(
        rf"^const {re.escape(name)}\b(?P<body>.*?)(?=^const [A-Z]\w*\b|\Z)",
        re.M | re.S,
    )
    for code in code_blocks:
        match = pattern.search(code)
        if match:
            return match.group(0)
    return None


def load_contract(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ContractError(f"missing contract file: {path}")
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise ContractError(f"malformed contract JSON ({path}): {e}") from e
    if not isinstance(data, dict) or "files" not in data or "skills_root" not in data:
        raise ContractError(f"contract missing required keys (files, skills_root): {path}")
    return data


def check_style_guide(rel: str, text: str, pin: dict[str, Any], drifts: list[Drift]) -> None:
    found = extract_dp_constants(text)
    expected_consts = pin.get("dp_constants") or {}
    code_blocks = extract_fenced_code(text, {"js", "jsx"})
    executable_code = "\n".join(code_blocks)
    font_css = found.pop("DP_FONT_FACE_CSS", None)
    if pin.get("forbid_font_face"):
        font_face_sources = []
        if font_css is not None:
            font_face_sources.append("DP_FONT_FACE_CSS")
        if re.search(r"@font-face\b", executable_code, re.I):
            font_face_sources.append("@font-face")
        if font_face_sources:
            drifts.append(Drift(rel, "font_face", "<absent>", font_face_sources))
    elif font_css is None:
        drifts.append(Drift(rel, "DP_FONT_FACE_CSS", "<present>", "<missing>"))

    for name, expected in expected_consts.items():
        if name not in found:
            drifts.append(Drift(rel, name, expected, "<missing>"))
        elif found[name] != expected:
            drifts.append(Drift(rel, name, expected, found[name]))
    for name in found:
        if name not in expected_consts:
            drifts.append(Drift(rel, name, "<not in pin>", found[name]))

    for name in pin.get("required_components") or []:
        if extract_component(code_blocks, name) is None:
            drifts.append(Drift(rel, f"required_component.{name}", name, "<missing>"))

    attr = pin.get("footer_attribution")
    footer = extract_component(code_blocks, "BuiltWithFooter")
    if attr and (footer is None or f"<span>{attr}</span>" not in footer):
        drifts.append(Drift(rel, "footer_attribution", attr, "<missing from BuiltWithFooter>"))

    ch = pin.get("compact_header") or {}
    compact_header = extract_component(code_blocks, "CompactHeader") or ""
    kind_m = re.search(
        r"style=\{\{\s*color:\s*(DP_TEXT_\w+)\s*\}\}>\{kind\}",
        compact_header,
    )
    period_m = re.search(
        r"style=\{\{\s*color:\s*(DP_TEXT_\w+)\s*\}\}>\{period\}",
        compact_header,
    )
    kind_found = kind_m.group(1) if kind_m else "<missing>"
    period_found = period_m.group(1) if period_m else "<missing>"
    if ch.get("kind_color") != kind_found:
        drifts.append(Drift(rel, "compact_header.kind_color", ch.get("kind_color"), kind_found))
    if ch.get("period_color") != period_found:
        drifts.append(Drift(rel, "compact_header.period_color", ch.get("period_color"), period_found))


def check_examples(rel: str, text: str, pin: dict[str, Any], drifts: list[Drift]) -> None:
    code_blocks = extract_fenced_code(text, {"jsx"})
    if not code_blocks:
        drifts.append(Drift(rel, "artifact_code_blocks", "at least one JSX block", "<missing>"))

    for index, code in enumerate(code_blocks, start=1):
        for name in pin.get("required_components") or []:
            if not re.search(rf"<{re.escape(name)}(?:\s|/?>)", code):
                drifts.append(
                    Drift(
                        rel,
                        f"artifact.{index}.required_component.{name}",
                        f"<{name} ...>",
                        "<missing>",
                    )
                )

    allowed_hex = {value.lower() for value in pin.get("allowed_hex_values") or []}
    used_hex = {
        value.lower()
        for code in code_blocks
        for value in CSS_HEX_RE.findall(code)
    }
    unapproved_hex = sorted(used_hex - allowed_hex)
    if unapproved_hex:
        drifts.append(
            Drift(
                rel,
                "allowed_hex_values",
                sorted(allowed_hex),
                unapproved_hex,
            )
        )

    if pin.get("forbid_dp_redeclarations"):
        redecs = [
            name
            for code in code_blocks
            for name in re.findall(r"^const (DP_[A-Z0-9_]+)\s*=", code, re.M)
        ]
        if redecs:
            drifts.append(
                Drift(
                    rel,
                    "forbid_dp_redeclarations",
                    "no const DP_* in this file",
                    f"found {redecs}",
                )
            )


def check_terms(rel: str, text: str, pin: dict[str, Any], drifts: list[Drift]) -> None:
    for term in pin.get("required_terms") or []:
        if term not in text:
            drifts.append(Drift(rel, f"required_term.{term}", term, "<missing>"))
    for term in pin.get("forbidden_terms") or []:
        if term in text:
            drifts.append(Drift(rel, f"forbidden_term.{term}", "<absent>", term))


def check_repo(contract_path: Path = DEFAULT_CONTRACT, repo_root: Path = REPO_ROOT) -> list[Drift]:
    contract = load_contract(contract_path)
    skills_root = repo_root / contract["skills_root"]
    if not skills_root.is_dir():
        raise ContractError(f"skills_root not found: {skills_root}")

    drifts: list[Drift] = []
    files = contract["files"]
    if not isinstance(files, dict) or not files:
        raise ContractError("contract.files must be a non-empty object")

    for rel, pin in files.items():
        path = skills_root / rel
        if not path.is_file():
            raise ContractError(f"missing skill file: {path}")
        text = path.read_text()
        if rel.endswith("artifact-style-guide/SKILL.md"):
            check_style_guide(rel, text, pin, drifts)
        elif rel.endswith("example-artifacts/SKILL.md"):
            check_examples(rel, text, pin, drifts)
        elif "required_terms" in pin or "forbidden_terms" in pin:
            check_terms(rel, text, pin, drifts)
        else:
            raise ContractError(f"no checker registered for {rel}")
    return drifts


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    contract_path = Path(argv[0]) if argv else DEFAULT_CONTRACT
    try:
        drifts = check_repo(contract_path=contract_path)
    except ContractError as e:
        print(f"BRAND CONTRACT ERROR: {e}", file=sys.stderr)
        return 2

    if drifts:
        for d in drifts:
            print(d.format_message(), file=sys.stderr)
            print(file=sys.stderr)
        print(f"{len(drifts)} brand-contract mismatch(es).", file=sys.stderr)
        return 1

    print("brand-contract: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
