---
name: monthly-report
description: Produces the Drivepoint-style monthly summary report for a CPG customer from their SmartModel workbook. Use whenever the user asks to draft, write, generate, or put together a "monthly report," "monthly summary," "monthly recap," or "monthly writeup" for a customer — or asks something like "do the [month] numbers for [customer]" or "[customer]'s [month] writeup." The skill returns markdown content in-chat that matches the house format (summary highlights → margins → balance sheet → variance → cohort retention → LTV). Do not use this skill for ad-hoc analysis questions that don't require the full monthly deliverable.
---

# Monthly Report

The Drivepoint monthly report is a written deliverable sent to CPG customers summarizing the prior month's P&L, operating metrics, and variance vs forecast. This skill captures the house format, the canonical section order, and the analytical patterns the team uses so any instance of Claude can produce one that reads like the team wrote it.

The output is **markdown content returned in-chat**. Do not create files or modify the workbook. If the user wants an Excel version of the report, offer to run `/build-report` afterward — but that's a separate, optional step.

## Before you start

1. **Confirm the reporting month and customer.** Customer name is readable from `settings.companyName`. Reporting month defaults to the most recently closed Actual period — infer it from the date spine on the consolidation sheet. Only ask the user if genuinely ambiguous.
2. **Read the Index tab** to discover which templates (and therefore which channels) are present. This determines the shape of the report — a two-channel customer gets a different table of contents than a five-channel customer.
3. **Read the monthly consolidation sheet** (typically `M - Monthly` — check Index) for headline numbers. Read channel-specific schedule sheets for channel-level commentary.

If the workbook uses SmartModel v6 protocol, the `smartmodel-protocol` skill should already be loaded. Use it.

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
  - Cash change MoM with drivers (operating / investing / financing)

## Variance Analysis
  - Run /variance-analysis and incorporate the output here

## Customer Retention Cohorts
  - One section per segment (subscription / non-subscription / by channel)

## LTV - Per Customer
  - Net Sales LTV
  - Contribution Profit LTV
  - Contribution Profit Less CAC
  - Cross-channel LTV if applicable
```

## Summary Highlights

Two subsections: YoY and MoM. Both follow the same shape — a headline sentence with the total, then a bulleted breakdown by channel. Sub-bullets call out the drivers (orders, ad spend, CAC, AOV) for each channel.

Indentation depth matches business importance. Channels with acquisition mechanics (DTC, Amazon) get the most sub-bullets. Channels where the story is simpler (Wholesale, Retail) get one line each.

**Sentence patterns:**
- `"[metric] was relatively flat MoM"` — for deltas under ~2%
- `"contracted by"` / `"expanded by"` — for margin metrics
- `"driven by"` — the causal connector after stating a delta

**YoY shape:**
```
[Month] [Year] Net Revenue of $X.XM increased/decreased by +/-$[delta] or +/-[%] YoY
● [Channel 1] Net Revenue of $XM increased by +$XK or +X% YoY
  ○ [Channel 1] ad spend of $XK increased by +$XK or +X% YoY
  ○ [Relevant ratio] increased to X% from X% prior year period
● [Channel 2] Net Revenue of $XK increased by +$XK or +X% YoY
  ○ Total orders of XK increased by +XK or +X% YoY
  ○ New customer orders X.XK were relatively flat YoY
    ■ Ad Spend of $XK increased by +$XK or +X% YoY
    ■ CAC of $X increased by +$X or X% YoY
  ○ Returning customer orders XK vs XK prior year
● [Channel 3] Net Revenue of $XK increased by +$XK YoY
```

Mirror the same structure for MoM, adding commentary that YoY won't surface — e.g., first-time vs returning customer mix shifts, AOV movements within the month.

## Margins

Written as flowing prose with bullets for specific drivers. Follow the P&L waterfall order. Each margin gets 2–4 lines.

Use these transition phrases — they carry the logic between margins and appear in nearly every report:
- **"Due to the above..."** — after variable expenses
- **"As a result..."** — after marketing
- **"Therefore..."** — leading into EBITDA

**Shape:**
```
Net Revenue Margin of X% increased/decreased MoM
● [Channel] Net Revenue margin rose to X% after [driver]

Gross Margin contracted to X% [context]
● COGS % of Gross Sales was X% vs X% the prior month
● Gross Profit of $X.XM contracted by -$XK or -X% MoM

Contribution Margin contracted to X% from X%, mostly on [driver] coupled with [secondary driver]
● Variable Expenses totaled $X.XM and represented X% of Net Revenue
  ○ Shipping: $XK or X% of Net Revenue
  ○ Fulfillment: X% of Net Revenue, flat MoM
  ○ Merchant Fees: X% of Net Revenue, flat MoM
Due to the above, Contribution Profit of $XK decreased by -$XK or -X% MoM

Contribution Profit After Marketing (CPAM) declined to X% from X%
● Total marketing expenses of $XK decreased by -$XK or -X% MoM
  ○ Direct ad spend of $XK (-$XK MoM)
  ○ Other marketing of $XK decreased from $XK MoM
  ○ Agency costs of $XK increased from $XK MoM
As a result, CPAM of $XK decreased by -$XK or -X% MoM

Fixed expenses totaled $XK, increased by +$XK or +X% MoM

Therefore, EBITDA declined to -$XK or -X% of Net Revenue from -$XK or X% the prior month
● YTD EBITDA [context]
```

## Balance Sheet & Cash Flow

Short section. Read the balance sheet and cash flow rows from the consolidation sheet (`M - Monthly`). One lead sentence with ending cash and MoM change, then a nested bullet list of the three cash flow categories. Always annotate each line with `(use of cash)` or `(source of cash)`.

```
Cash at the end of [Month] of $X.XM decreased/increased by $XK MoM
● $XK of cash used by operations
  ○ $XK operating loss (use of cash)
  ○ Offset by $XK lower working capital needs (source of cash)
    ■ $XK increase in AR (use of cash)
    ■ $XK decrease in AP (use of cash)
    ■ $XK decrease in net inventory (source of cash)
    ■ $XK increase in other current liabilities (source of cash)
● $XK cash used for financing (decrease in long term debt)
● $XK cash used by investing activities (use of cash)
```

## Variance Analysis

Load the `/variance-analysis` skill and follow its workflow for this section. That skill handles comparison basis selection, data gathering, driver decomposition, and output formatting. Incorporate its output directly here. The section headline must name the forecast baseline exactly — include a clarifying parenthetical if there's any ambiguity about which plan version is being compared against.

## Customer Retention Cohorts

Load the `/cohort-analysis` skill and follow its workflow to produce the retention curves and LTV data for this customer. That skill handles data discovery, retention curve computation, and LTV buildup. Incorporate its retention curve output directly into this section — one table per segment (DTC Subscription, DTC Non-Subscription, Amazon Subscription, Amazon Non-Subscription where present).

Under each table: 1–2 bullets on which cohorts are outperforming and which direction the trend is moving. No more.

## LTV - Per Customer

Reuse the LTV output already produced by `/cohort-analysis` above — no need to reload the skill. Include the per-segment LTV tables: Net Sales, Contribution Profit, and Contribution Profit Less CAC. If the customer has a cross-channel business, include the Cross Channel LTV tables after the single-channel tables.

## Numbers and formatting conventions

Non-negotiable — inconsistency reads as sloppiness.

- **Currency**: round to the nearest thousand (`$1.3M`, `$906K`, `$15K`). Millions with one decimal, thousands as whole numbers. Never show pennies.
- **Percentages**: whole numbers (`+81%`, `-23%`) except margin rates where one decimal helps (`13.4%`, `39.5%`). Negative with leading minus, positive with leading plus in YoY/MoM context.
- **Variance framing**: always `"[metric] of [value] increased/decreased by +/-[abs delta] or +/-[% delta] [YoY|MoM]"`.
- **Channel names**: match what the model calls them exactly.
- **Acronyms**: spell out on first mention (`Contribution Margin After Marketing (CMAM)`).
- **Bullet depth**: stop at 3 levels (●, ○, ■). If you need deeper nesting, the logic is too tangled — rework the paragraph.

## Tone

Factual, direct, slightly terse. Short sentences. Lead with the number, then the driver. Never editorialize — "disappointing" and "strong" are opinions; the numbers say what they say. It's fine to name a causal chain; customers appreciate the mechanics being visible.

## Handoff

Return the markdown in-chat. After drafting, flag any sections where you made a judgment call and any data gaps — keep this brief.

Then offer the user an Excel version: "If you'd like this as a rendered report tab in the workbook, I can run `/build-report` to create a formula-driven Excel version." Wait for the user to confirm before invoking it — some customers want markdown only.
