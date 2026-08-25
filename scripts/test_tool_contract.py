#!/usr/bin/env python3
"""Unit tests for check_tool_contract. Run: python3 scripts/test_tool_contract.py -v"""

from __future__ import annotations

import unittest

import check_tool_contract as c

VERBS = {"get", "list", "save", "read", "run", "import", "preview", "publish", "search", "add", "mark"}
KNOWN = {"save_product_mappings", "run_query", "get_plan"}


class ToolShapeTests(unittest.TestCase):
    def test_verb_prefixed_snake_case_is_tool_shaped(self):
        self.assertTrue(c.is_tool_shaped("save_product_mappings", VERBS))
        self.assertTrue(c.is_tool_shaped("run_query", VERBS))

    def test_non_verb_prefix_is_not_tool_shaped(self):
        # metric ids / column names that merely contain underscores must not trip the check
        self.assertFalse(c.is_tool_shaped("net_sales", VERBS))
        self.assertFalse(c.is_tool_shaped("r_gl_replace", VERBS))


class ScanTests(unittest.TestCase):
    def test_known_reference_passes(self):
        text = "First call `run_query`, then `save_product_mappings`."
        self.assertEqual(c.scan_skill("s.md", text, VERBS, KNOWN), [])

    def test_stale_reference_is_flagged(self):
        text = "Then call `save_product_mappings_to_firebase` once."
        dead = c.scan_skill("s.md", text, VERBS, KNOWN)
        self.assertEqual(len(dead), 1)
        self.assertEqual(dead[0].token, "save_product_mappings_to_firebase")

    def test_line_number_is_reported(self):
        text = "line one\nline two\n`publish_to_nowhere` on line three"
        dead = c.scan_skill("s.md", text, VERBS, KNOWN)
        self.assertEqual(len(dead), 1)
        self.assertEqual(dead[0].line, 3)

    def test_allowlisted_non_tool_token_passes(self):
        text = "the `get_data_from_warehouse` sentinel is client-side"
        known = KNOWN | {"get_data_from_warehouse"}
        self.assertEqual(c.scan_skill("s.md", text, VERBS, known), [])

    def test_unbackticked_token_is_ignored(self):
        text = "save_product_mappings_to_firebase without backticks is prose"
        self.assertEqual(c.scan_skill("s.md", text, VERBS, KNOWN), [])


class IntegrationTests(unittest.TestCase):
    def test_repo_skills_satisfy_the_pin(self):
        # The real skills in this repo must pass against the committed pin.
        self.assertEqual(c.run(), 0)


if __name__ == "__main__":
    unittest.main()
