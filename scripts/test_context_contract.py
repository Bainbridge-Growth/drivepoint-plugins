#!/usr/bin/env python3
"""Unit tests for check_context_contract. Run: python3 scripts/test_context_contract.py -v"""

from __future__ import annotations

import unittest

import check_context_contract as c

CONTRACT = c.load_contract(c.DEFAULT_CONTRACT)

CONTEXT = """---
title: Metrics
description: Use when computing a metric.
owner: jt@example.com
updated: 2026-11-03
source: kickoff call
---

# Metrics
- Net revenue = net sales + shipping.
"""

SKILL = """---
name: company:headcount-check
description: Use when asked to check headcount against plan.
owner: jt@example.com
updated: 2026-11-03
---

# Headcount check
"""


class FrontmatterTests(unittest.TestCase):
    def test_valid_context_file_passes(self):
        self.assertEqual(c.validate_file("context/metrics.md", CONTEXT, CONTRACT), [])

    def test_valid_skill_passes(self):
        self.assertEqual(c.validate_file("skills/headcount-check/SKILL.md", SKILL, CONTRACT), [])

    def test_missing_fence_is_flagged(self):
        violations = c.validate_file("context/metrics.md", "# Metrics", CONTRACT)
        self.assertEqual(len(violations), 1)
        self.assertIn("frontmatter fence", violations[0].message)

    def test_nested_frontmatter_is_flagged(self):
        text = CONTEXT.replace("source: kickoff call", "source:\n  - kickoff call")
        violations = c.validate_file("context/metrics.md", text, CONTRACT)
        self.assertTrue(any("flat" in v.message for v in violations))

    def test_missing_required_field_is_flagged(self):
        text = CONTEXT.replace("source: kickoff call\n", "")
        violations = c.validate_file("context/metrics.md", text, CONTRACT)
        self.assertEqual([v.message for v in violations], ["missing required context field `source`"])

    def test_unknown_field_is_flagged(self):
        text = CONTEXT.replace("source: kickoff call", "source: kickoff call\ntags: finance")
        violations = c.validate_file("context/metrics.md", text, CONTRACT)
        self.assertTrue(any("unknown context field `tags`" in v.message for v in violations))


class DescriptionTests(unittest.TestCase):
    def test_description_must_start_with_use_when(self):
        text = CONTEXT.replace("Use when computing a metric.", "Metric definitions.")
        violations = c.validate_file("context/metrics.md", text, CONTRACT)
        self.assertTrue(any("must start with" in v.message for v in violations))

    def test_long_description_is_flagged(self):
        text = CONTEXT.replace("Use when computing a metric.", "Use when " + "x" * 200)
        violations = c.validate_file("context/metrics.md", text, CONTRACT)
        self.assertTrue(any("description is" in v.message for v in violations))


class DateTests(unittest.TestCase):
    def test_placeholder_date_allowed_only_in_templates(self):
        text = CONTEXT.replace("2026-11-03", "YYYY-MM-DD")
        self.assertEqual(c.validate_file("context/metrics.md", text, CONTRACT, template=True), [])
        violations = c.validate_file("context/metrics.md", text, CONTRACT)
        self.assertTrue(any("ISO date" in v.message for v in violations))


class SkillNameTests(unittest.TestCase):
    def test_unprefixed_skill_name_is_flagged(self):
        text = SKILL.replace("company:headcount-check", "headcount-check")
        violations = c.validate_file("skills/headcount-check/SKILL.md", text, CONTRACT)
        self.assertTrue(any("skill name" in v.message for v in violations))

    def test_personal_prefix_passes(self):
        text = SKILL.replace("company:headcount-check", "me:weekly-dtc")
        self.assertEqual(c.validate_file("skills/weekly-dtc/SKILL.md", text, CONTRACT), [])


class SizeTests(unittest.TestCase):
    def test_profile_has_the_pinned_limit(self):
        text = CONTEXT + "x" * 2100
        violations = c.validate_file("profile.md", text, CONTRACT)
        self.assertTrue(any("limit for this file is 2000" in v.message for v in violations))
        self.assertEqual(c.validate_file("context/metrics.md", text, CONTRACT), [])

    def test_context_file_limit(self):
        text = CONTEXT + "x" * 8100
        violations = c.validate_file("context/metrics.md", text, CONTRACT)
        self.assertTrue(any("limit for this file is 8000" in v.message for v in violations))


class IntegrationTests(unittest.TestCase):
    def test_repo_templates_satisfy_the_contract(self):
        self.assertEqual(c.run(), 0)


if __name__ == "__main__":
    unittest.main()
