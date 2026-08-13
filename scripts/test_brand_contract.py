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
STYLE_GUIDE = (
    REPO_ROOT / "plugins/mcp-server/skills/common-skills/artifact-style-guide/SKILL.md"
)
EXAMPLES = REPO_ROOT / "plugins/mcp-server/skills/common-skills/example-artifacts/SKILL.md"
REPORT_GUIDE = (
    REPO_ROOT / "plugins/mcp-server/skills/common-skills/report-creation-guide/SKILL.md"
)
CONTRACT = REPO_ROOT / "plugins/mcp-server/skills/brand-contract.json"
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_brand_contract as bcc  # noqa: E402


class BrandContractTests(unittest.TestCase):
    def test_live_repo_matches_pin(self) -> None:
        drifts = bcc.check_repo()
        self.assertEqual(drifts, [], msg="\n".join(d.format_message() for d in drifts))

    def test_drift_is_plain_data(self) -> None:
        drift = bcc.Drift("skill.md", "DP_TEXT_PRIMARY", "#191815", "#00ff00")

        self.assertNotIsInstance(drift, BaseException)
        self.assertIn("DP_TEXT_PRIMARY", drift.format_message())

    def test_unterminated_dp_string_is_rejected_as_malformed(self) -> None:
        for quote in ("'", '"'):
            with self.subTest(quote=quote):
                text = (
                    f"const DP_TEXT_PRIMARY = {quote}#191815;\n"
                    f"const DP_TEXT_MUTED = {quote}#716e6b{quote};"
                )

                with self.assertRaisesRegex(
                    bcc.ContractError,
                    "unterminated string assignment for DP_TEXT_PRIMARY",
                ):
                    bcc.extract_dp_constants(text)

    def test_deliberate_drift_message_names_file_and_values(self) -> None:
        """Mutate DP_TEXT_PRIMARY in a temp copy; assert exit-1 style message."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            skills = tmp_root / "plugins/mcp-server/skills/common-skills"
            skills.mkdir(parents=True)
            guide_dir = skills / "artifact-style-guide"
            examples_dir = skills / "example-artifacts"
            guide_dir.mkdir()
            examples_dir.mkdir()
            guide_text = STYLE_GUIDE.read_text().replace(
                "const DP_TEXT_PRIMARY = '#191815';",
                "const DP_TEXT_PRIMARY = '#00ff00';",
                1,
            )
            (guide_dir / "SKILL.md").write_text(guide_text)
            shutil.copy(EXAMPLES, examples_dir / "SKILL.md")

            contract = json.loads(CONTRACT.read_text())
            contract["skills_root"] = "plugins/mcp-server/skills/common-skills"
            contract["files"] = {
                name: contract["files"][name]
                for name in (
                    "artifact-style-guide/SKILL.md",
                    "example-artifacts/SKILL.md",
                )
            }
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

    def test_missing_footer_in_one_artifact_is_rejected(self) -> None:
        text = EXAMPLES.read_text()
        mutated = text.replace('<BuiltWithFooter generated="28 Jul 2026" />', "", 1)
        self.assertNotEqual(mutated, text)
        drifts: list[bcc.Drift] = []
        pin = json.loads(CONTRACT.read_text())["files"]["example-artifacts/SKILL.md"]

        bcc.check_examples("example-artifacts/SKILL.md", mutated, pin, drifts)

        self.assertIn("artifact.1.required_component.BuiltWithFooter", [d.key for d in drifts])

    def test_unapproved_hex_in_artifact_code_is_rejected(self) -> None:
        text = EXAMPLES.read_text()
        pin = json.loads(CONTRACT.read_text())["files"]["example-artifacts/SKILL.md"]

        for color in ("#00ff00", "#f00", "#ff000080"):
            with self.subTest(color=color):
                mutated = text.replace("DP_CHART_DELTA.positive", repr(color), 1)
                self.assertNotEqual(mutated, text)
                drifts: list[bcc.Drift] = []

                bcc.check_examples("example-artifacts/SKILL.md", mutated, pin, drifts)

                mismatch = next(d for d in drifts if d.key == "allowed_hex_values")
                self.assertEqual(mismatch.found, [color])

    def test_footer_attribution_must_be_in_footer_component(self) -> None:
        text = STYLE_GUIDE.read_text()
        mutated = text.replace(
            "<span>Built with Drivepoint</span>",
            "<span>Built by Drivepoint</span>",
            1,
        )
        self.assertNotEqual(mutated, text)
        drifts: list[bcc.Drift] = []
        pin = json.loads(CONTRACT.read_text())["files"]["artifact-style-guide/SKILL.md"]

        bcc.check_style_guide("artifact-style-guide/SKILL.md", mutated, pin, drifts)

        self.assertIn("footer_attribution", [d.key for d in drifts])

    def test_inline_font_face_under_another_name_is_rejected(self) -> None:
        text = STYLE_GUIDE.read_text()
        mutated = text.replace(
            "const DP_FONT_STACK = 'ui-sans-serif, system-ui, sans-serif';",
            "const DP_FONT_STACK = 'ui-sans-serif, system-ui, sans-serif';\n"
            "const EmbeddedFont = `@font-face { font-family: Example; }`;",
            1,
        )
        self.assertNotEqual(mutated, text)
        drifts: list[bcc.Drift] = []
        pin = json.loads(CONTRACT.read_text())["files"]["artifact-style-guide/SKILL.md"]

        bcc.check_style_guide("artifact-style-guide/SKILL.md", mutated, pin, drifts)

        mismatch = next(d for d in drifts if d.key == "font_face")
        self.assertEqual(mismatch.found, ["@font-face"])

    def test_font_face_named_only_in_prose_is_allowed(self) -> None:
        text = STYLE_GUIDE.read_text() + "\nNever add an `@font-face` rule.\n"
        drifts: list[bcc.Drift] = []
        pin = json.loads(CONTRACT.read_text())["files"]["artifact-style-guide/SKILL.md"]

        bcc.check_style_guide("artifact-style-guide/SKILL.md", text, pin, drifts)

        self.assertEqual(drifts, [])

    def test_compact_header_color_cannot_be_masked_by_a_decoy(self) -> None:
        text = STYLE_GUIDE.read_text()
        mutated = text.replace(
            "style={{ color: DP_TEXT_PRIMARY }}>{kind}",
            "style={{ color: DP_TEXT_MUTED }}>{kind}",
            1,
        )
        mutated += (
            "\n```jsx\n"
            "<div style={{ color: DP_TEXT_PRIMARY }}>{kind}</div>\n"
            "```\n"
        )
        drifts: list[bcc.Drift] = []
        pin = json.loads(CONTRACT.read_text())["files"]["artifact-style-guide/SKILL.md"]

        bcc.check_style_guide("artifact-style-guide/SKILL.md", mutated, pin, drifts)

        self.assertIn("compact_header.kind_color", [d.key for d in drifts])

    def test_downstream_skill_cannot_restore_sent_doc_header(self) -> None:
        text = REPORT_GUIDE.read_text()
        mutated = text.replace("CompactHeader", "ArtifactHeader").replace(
            "BuiltWithFooter",
            "SignatureFooter",
        )
        drifts: list[bcc.Drift] = []
        pin = json.loads(CONTRACT.read_text())["files"]["report-creation-guide/SKILL.md"]

        bcc.check_terms("report-creation-guide/SKILL.md", mutated, pin, drifts)

        self.assertEqual(
            {d.key for d in drifts},
            {
                "required_term.CompactHeader",
                "required_term.BuiltWithFooter",
                "forbidden_term.ArtifactHeader",
            },
        )

    def test_missing_contract_exits_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "nope.json"
            with self.assertRaises(bcc.ContractError) as ctx:
                bcc.load_contract(missing)
            self.assertIn("missing contract file", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
