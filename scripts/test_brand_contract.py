#!/usr/bin/env python3
"""Unit tests for check_brand_contract — includes a deliberate-drift fixture."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_brand_contract as bcc  # noqa: E402


class BrandContractTests(unittest.TestCase):
    def test_live_repo_matches_pin(self) -> None:
        drifts = bcc.check_repo()
        self.assertEqual(drifts, [], msg="\n".join(d.format_message() for d in drifts))

    def test_deliberate_drift_message_names_file_and_values(self) -> None:
        """Mutate DP_TEXT_PRIMARY in a temp copy; assert exit-1 style message."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            skills = tmp_root / "plugins/mcp-server/skills/common-skills"
            skills.mkdir(parents=True)
            src_guide = (
                REPO_ROOT
                / "plugins/mcp-server/skills/common-skills/artifact-style-guide/SKILL.md"
            )
            src_examples = (
                REPO_ROOT
                / "plugins/mcp-server/skills/common-skills/example-artifacts/SKILL.md"
            )
            guide_dir = skills / "artifact-style-guide"
            examples_dir = skills / "example-artifacts"
            guide_dir.mkdir()
            examples_dir.mkdir()
            guide_text = src_guide.read_text().replace(
                "const DP_TEXT_PRIMARY = '#191815';",
                "const DP_TEXT_PRIMARY = '#00ff00';",
                1,
            )
            (guide_dir / "SKILL.md").write_text(guide_text)
            shutil.copy(src_examples, examples_dir / "SKILL.md")

            contract_src = REPO_ROOT / "plugins/mcp-server/skills/brand-contract.json"
            contract = json.loads(contract_src.read_text())
            # Point skills_root at the temp tree (relative to tmp_root).
            contract["skills_root"] = "plugins/mcp-server/skills/common-skills"
            contract_path = tmp_root / "brand-contract.json"
            contract_path.write_text(json.dumps(contract, indent=2))

            drifts = bcc.check_repo(contract_path=contract_path, repo_root=tmp_root)
            self.assertTrue(drifts, "expected at least one drift")
            primary = next(d for d in drifts if d.key == "DP_TEXT_PRIMARY")
            msg = primary.format_message()
            self.assertIn("artifact-style-guide/SKILL.md", msg)
            self.assertIn("#191815", msg)
            self.assertIn("#00ff00", msg)
            self.assertIn("brand-contract.json", msg)
            self.assertIn("pin edits are brand decisions", msg)
            self.assertEqual(
                [d.key for d in drifts],
                ["DP_TEXT_PRIMARY"],
                msg="deliberate fixture should only drift the mutated constant",
            )
    def test_missing_contract_exits_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "nope.json"
            with self.assertRaises(bcc.ContractError) as ctx:
                bcc.load_contract(missing)
            self.assertIn("missing contract file", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
