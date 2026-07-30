#!/usr/bin/env python3
"""Compare customer-facing skill brand values against the pinned contract.

Exit codes:
  0 — all values match the pin
  1 — one or more values drifted (message is a fix instruction for a coding agent)
  2 — contract or skill file missing/malformed
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = REPO_ROOT / "plugins/mcp-server/skills/brand-contract.json"

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
            depth = 0
            j = i
            while j < len(text):
                if text[j] == "[":
                    depth += 1
                elif text[j] == "]":
                    depth -= 1
                    if depth == 0:
                        j += 1
                        break
                j += 1
            raw = text[i:j]
            consts[name] = [a or b for a, b in re.findall(r"'([^']+)'|\"([^\"]+)\"", raw)]
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


def parse_font_face(css: str) -> dict[str, str]:
    mime_m = re.search(r"data:([^;]+);", css)
    fam_m = re.search(r"font-family:'([^']+)'", css)
    if not mime_m or not fam_m:
        raise ContractError("DP_FONT_FACE_CSS missing data: mime or font-family")
    return {
        "family": fam_m.group(1),
        "mime": mime_m.group(1),
        "sha256": hashlib.sha256(css.encode()).hexdigest(),
    }


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
    font_css = found.pop("DP_FONT_FACE_CSS", None)
    if font_css is None:
        drifts.append(Drift(rel, "DP_FONT_FACE_CSS", "<present>", "<missing>"))
    else:
        ff_found = parse_font_face(font_css)
        ff_pin = pin.get("font_face") or {}
        for k in ("family", "mime", "sha256"):
            if ff_pin.get(k) != ff_found.get(k):
                drifts.append(Drift(rel, f"font_face.{k}", ff_pin.get(k), ff_found.get(k)))

    for name, expected in expected_consts.items():
        if name not in found:
            drifts.append(Drift(rel, name, expected, "<missing>"))
        elif found[name] != expected:
            drifts.append(Drift(rel, name, expected, found[name]))
    for name in found:
        if name not in expected_consts:
            drifts.append(Drift(rel, name, "<not in pin>", found[name]))

    attr = pin.get("footer_attribution")
    if attr and attr not in text:
        drifts.append(Drift(rel, "footer_attribution", attr, "<missing>"))

    ch = pin.get("compact_header") or {}
    kind_m = re.search(r"style=\{\{\s*color:\s*(DP_TEXT_\w+)\s*\}\}>\{kind\}", text)
    period_m = re.search(r"style=\{\{\s*color:\s*(DP_TEXT_\w+)\s*\}\}>\{period\}", text)
    kind_found = kind_m.group(1) if kind_m else "<missing>"
    period_found = period_m.group(1) if period_m else "<missing>"
    if ch.get("kind_color") != kind_found:
        drifts.append(Drift(rel, "compact_header.kind_color", ch.get("kind_color"), kind_found))
    if ch.get("period_color") != period_found:
        drifts.append(Drift(rel, "compact_header.period_color", ch.get("period_color"), period_found))

    for key in ("status_positive", "status_negative"):
        expected = pin.get(key)
        if expected and expected not in text:
            drifts.append(Drift(rel, key, expected, "<missing>"))


def check_examples(rel: str, text: str, pin: dict[str, Any], drifts: list[Drift]) -> None:
    for name in pin.get("required_components") or []:
        if name not in text:
            drifts.append(Drift(rel, f"required_component.{name}", name, "<missing>"))

    for key in ("status_positive", "status_negative", "ink", "muted"):
        expected = pin.get(key)
        if expected and expected not in text:
            drifts.append(Drift(rel, key, expected, "<missing>"))

    if pin.get("forbid_dp_redeclarations"):
        redecs = re.findall(r"^const (DP_[A-Z0-9_]+)\s*=", text, re.M)
        if redecs:
            drifts.append(
                Drift(
                    rel,
                    "forbid_dp_redeclarations",
                    "no const DP_* in this file",
                    f"found {redecs}",
                )
            )


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
