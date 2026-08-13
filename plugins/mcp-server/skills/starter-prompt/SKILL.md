---
name: starter-prompt
description: The paste-in first-turn message for a brand-new Drivepoint analytics conversation, asking for a lay of the land before any specific question - ecommerce date range, channels and currencies, SmartModel actuals range and per-plan coverage, and data freshness. Use when a user is starting fresh, asks how to begin, or wants an orientation summary of what data is present. This is a user message to paste, not reference material to load into project knowledge.
---

# Drivepoint Analytics — Starter Prompt

Paste the message below as your first turn in a new Project conversation.
It gives the assistant a quick lay of the land before you dig into specific
questions.

Do not upload this file to Project Knowledge — it's a user message, not
reference material.

---

Hi — first time using this. Can you give me a quick lay of the land before
I ask anything specific?

Run small discovery queries to figure out:

- **Ecommerce:** date range, channels, and currencies present
- **SmartModel:** actuals date range, what plans exist (the live plan and
  any frozen forecasts), and each plan's coverage (date range, count of
  actual vs. forecast months)
- **Freshness:** most recent ecommerce day and most recent actual month

Then:

1. Summarize what you found in a short, scannable format.
2. Flag anything worth knowing — stale data, monthly gaps, multiple
   currencies inside a single channel, plans with zero actuals or zero
   forecast months, etc.
3. Suggest 3–5 starting reports tailored to what's actually there. Use
   real plan names, real channels, and real date ranges from your
   discovery — no placeholders. Number them so I can reply with a number.

Text response only for now — we'll build visuals once I pick a report.
