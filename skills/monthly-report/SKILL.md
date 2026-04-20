---
name: monthly-report
description: Produces the Drivepoint-style monthly narrative — summary highlights, margins, balance sheet, variance vs forecast, cohort retention, and LTV — from a customer's SmartModel workbook. Use when the user asks to draft, write, generate, or put together a "monthly report," "monthly summary," "monthly recap," "monthly review," or "variance report" for a customer — or says "create my monthly review," "do the December numbers for Dirty Labs," or "CPAP's August writeup." The skill returns markdown content in-chat that matches the house format. Do not use this skill for ad-hoc analysis questions that don't require the full monthly deliverable.
---

# Monthly Report

The Drivepoint monthly report is a written deliverable sent to CPG customers summarizing the prior month's P&L, operating metrics, and variance vs forecast. This skill captures the house format, the canonical section order, and the analytical patterns the team uses so any instance of Claude can produce one that reads like the team wrote it.

The output is **markdown content returned in-chat**. Do not save the output to disk, convert it to PDF/docx, or otherwise package it.

**Prerequisite**: The `smartmodel-protocol` skill must be loaded.

---

## When This Skill Activates

- User asks to draft, write, or generate a monthly report, monthly summary, monthly recap, or monthly review
- User says "create my monthly review"
- User asks to "do the [month] numbers for [customer]" or "[customer]'s [month] writeup"
- User asks for a variance report in the context of a full monthly deliverable

This skill produces the **narrative only** — the written commentary that accompanies the standard monthly report. It does not produce standalone variance analyses (use `variance-analysis` for that), nor does it render or package the final deliverable (use `build-report` for that). If the user's request is a one-off analytical question rather than the full monthly narrative, route to the appropriate analytical skill instead.

---

## Before you start

1. **Confirm the reporting month and customer**. These come from the user's prompt or from `settings.modelName` / `settings.companyName` in the Settings tab. If either is ambiguous, ask.
2. **Read the Index tab of the SmartModel** to discover which templates (and therefore which revenue channels) are present. This is what determines the shape of the report — a two-channel customer (e.g., DTC + Wholesale) gets a different table of contents than a five-channel customer.
3. **Read the monthly consolidation sheet** (typically `M - Monthly` or similar — check Index) to pull the headline numbers. Read channel-specific schedule sheets for channel-level commentary. Also pull YTD consolidation data — the report includes a YTD variance section.
4. **Identify the forecast to compare against**. Ask the user which forecast version is the basis for variance analysis ("vs H2 FCST," "vs 2025 Budget," "vs board forecast," etc.) if it's not obvious from the model. Different customers and different months compare against different baselines; getting this wrong is the #1 way the report embarrasses us. If the user doesn't specify, default to the forecast as rolled forward through the last completed month (i.e., the current live forecast) and flag the choice in the post-draft callout.

If the workbook uses the SmartModel v6 protocol, the `smartmodel-protocol` skill should already be loaded with the grammar you need to navigate it. Use it.

If the data is not in a SmartModel workbook, stop and tell the user. This skill assumes SmartModel structure — Index tab, schedule sheets, consolidated monthly sheet. Without that structure, the section-by-section extraction won't work. Point the user toward getting the data into a SmartModel first, or help them manually if they provide the raw numbers in another format.

---

## Report structure

Every monthly report follows this section order. Sections can be omitted if the channel or data isn't present, but the order of what remains does not change.

```
# [Month] [Year] Monthly Summary
Prepared by Drivepoint for [Customer]

## Summary Highlights
  - YoY narrative (channel-by-channel)
  - MoM narrative (channel-by-channel)

## Margins
  - Net Revenue Margin
  - Gross Margin
  - Contribution Margin
  - Contribution Margin After Marketing (CMAM / CPAM)
  - Fixed Opex
  - EBITDA

## Balance Sheet & Cash Flow
  - Cash change MoM with the drivers (operating / investing / financing)

## Variance Analysis vs [Forecast name]
  - Gross Sales by channel
  - Net Revenue & Net Revenue Margin
  - Gross Margin / Gross Profit
  - Variable Expenses (fulfillment, shipping, merchant fees)
  - Contribution Margin
  - Marketing Expenses + CMAM
  - Fixed Opex
  - EBIT / EBITDA

## YTD Variance vs Forecast
  - Same structure as monthly variance, rolled up YTD

## Cohort Retention
  - One section per segment (subscription / non-subscription / by channel)

## LTV - Per Customer
  - Net Sales LTV
  - Contribution Profit LTV
  - Contribution Profit Less CAC
  - Cross-channel LTV if the customer has a cross-channel business
```

If `references/section-guide.md` exists, read it before writing the report. It contains deeper structural guidance — what goes in each section, the standard sentence patterns, the edge cases — and those patterns are what makes the output recognizable as ours.

If `references/example-openings.md` exists, read it as well. It has worked examples of opening paragraphs across different customer archetypes (multi-channel subscription CPG, two-channel durable goods, three-channel with direct mail). Use these as stylistic anchors rather than templates — the cadence, punctuation, and level of nesting matter more than exact wording.

---

## Numbers and formatting conventions

These are non-negotiable because customers read many of these in a row and inconsistency reads as sloppiness.

- **Currency**: round to the nearest thousand (`$1.3M`, `$906K`, `$15K`) — never show pennies. Millions with one decimal (`$2.9M`), thousands as whole numbers (`$125K`).
- **Percentages**: whole numbers (`+81%`, `-23%`) except for margin rates where one decimal helps (`13.4%`, `39.5%`). The one-decimal rule applies to exactly these five: Net Revenue Margin, Gross Margin, Contribution Margin, CMAM, EBITDA Margin. Negative with a leading minus, positive with a leading plus when in a YoY/MoM context (`+$1.3M or +81% YoY`).
- **Variance framing**: always "`[metric] of [value] increased/decreased by +/-[abs delta] or +/-[% delta] [YoY|MoM]`". E.g., "Amazon Net Revenue of $1.6M increased by +$645K or +70% YoY".
- **Favorability language**: for variance vs forecast, say "tracked above/below," "missed," "exceeded," "came in line with." Avoid "beat" outside of the channel-level line.
- **Channel names**: match what the model calls them. If the Index tab says "Marketplace," use "Amazon" only if the customer consistently calls it Amazon; otherwise use "Marketplace."
- **Acronyms**: first mention spells out (`Contribution Margin After Marketing (CMAM)`).

---

## Charts and tables

This skill does not render charts. Charts are handled outside this skill. What this skill does is write the **commentary around the charts** — the prose that frames what the reader is about to look at. If the user asks for charts, remind them charts are not part of this skill's scope, and stick to producing the markdown narrative.

Tables are fair game in markdown when the variance detail warrants them (e.g., order counts, CAC, AOV by segment). Use them in the variance section when the numbers are doing the work; prose alone in the highlights section.

---

## Channel detection

Read the Index tab manifest. Typical template IDs map to channels like:

- `dtc-revenue` → DTC / DTC Online
- `amzn-revenue` → Amazon / Marketplace
- `wholesale-revenue` → Wholesale
- `retail-revenue` → Retail
- `online-retail-revenue` → Online Retail (3P sites other than Amazon — Target+, Walmart+)
- `dm-revenue` → Direct Mail (rare, older accounts)

Some customers segment further (machine vs no-machine, CSR vs online, OTP vs subscription). Look at the schedule sheet structure — subsidiary sheets (e.g., `DTC - OTP`, `DTC - SUB`) mean the channel has segmentation that should show up in the New Customer Mix and cohort sections.

---

## Tone

Factual, direct, and slightly terse — this is not marketing copy. Short sentences. Lead with the number, then the driver. "DTC Net Revenue of $906K decreased by -$137K or -13% MoM" is the cadence. Never editorialize ("disappointing quarter," "strong performance") — customers read these as data, not opinion. If something is genuinely good or bad, the numbers say so.

It's fine, and often desirable, to note a causal chain: "CPAM of $250K decreased by -$124K or -33% MoM" followed by a bulleted "driven by" list. Customers appreciate the mechanics being visible.

---

## After drafting

After drafting, call out to the user any sections where you had to make a judgment call (e.g., "I used the live forecast rolled through March as the variance baseline — let me know if you wanted budget instead") and any data gaps where the model didn't have what was needed.
