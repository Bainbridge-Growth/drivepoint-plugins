---
name: margin-analysis
description: Analyze gross margin, contribution margin, and COGS decomposition across channels and products. Use when a user asks about margins, profitability by channel, COGS breakdown, "why are margins declining?", "what's our most profitable channel?", "Amazon vs. DTC profitability", margin bridge, or unit economics. Also triggers on "gross profit", "contribution margin", "blended margin", "margin mix", or "channel profitability".
---

# Margin Analysis

**Purpose**: Decompose and interpret margins for omnichannel CPG brands — where margin structure varies dramatically by channel (DTC vs. Amazon vs. Wholesale) and by product.
**Prerequisite**: The `smartmodel-protocol` skill must be loaded.

---

## When This Skill Activates

- User asks about margins, profitability, or unit economics
- User asks "what's driving our margin?" or "why are margins down?"
- User asks to compare profitability across channels or products
- User asks about COGS, fulfillment costs, or contribution margin
- User wants a margin bridge or waterfall

---

## The Drivepoint Margin Framework

CPG brands operate across channels with fundamentally different margin structures:

| Channel | Typical Gross Margin | Key Cost Drivers | What Makes It Unique |
|---------|---------------------|-----------------|---------------------|
| DTC (Shopify) | 65–80% | COGS, fulfillment, shipping | Highest gross margin, but CAC eats into contribution margin |
| Amazon | 35–55% | COGS, FBA fees, referral fees, advertising | Amazon typically takes 30–40% of revenue in fees |
| Wholesale | 40–55% | COGS, trade spend, freight | Lower gross margin but lower marketing cost |
| TikTok Shop | 50–65% | COGS, platform fees, fulfillment | Fee structure still evolving |
| Subscription | 70–85% | COGS, fulfillment, platform fees | Highest margin due to reduced CAC on recurring orders |

These are benchmarks. Always use the model's actual data.

---

## Phase 1 — Orient

**Step 1.1 — Use model context from the protocol**
Settings, index, and date spine are already loaded by the protocol's auto-orient. From the model context, identify which schedule sheets correspond to which channels (DTC, AMZN, Wholesale, etc.) and the consolidation sheet (M - Monthly). Note the analysis period (most recent closed month, or user-specified).

**Step 1.2 — Read dimension registries**
Call `read_smartmodel_registries` on the channel sheets relevant to the analysis → identify channel dimensions, product dimensions, and measure identifiers for revenue, COGS, and gross margin rows. Only read registries on sheets the user's question involves.

---

## Phase 2 — Gather Data

**If a prior skill ran this session** (e.g., `/summarize-model`, `/variance-analysis`), reuse settings, index, date spine, and any data already gathered. Do not re-read sheets that were already read.

**Step 2.1 — Read the consolidation sheet first (one call)**
Call `read_smartmodel_data_section` on **M - Monthly** → get blended revenue, COGS, gross profit, and EBITDA. This gives you the blended margin picture before drilling into channels.

**Step 2.2 — Read individual channel sheets for channel-level decomposition**
Call `read_smartmodel_data_section` on each channel sheet that the user wants analyzed (DTC, AMZN, Wholesale, etc.). Look for:

| Data Point | Identifier pattern |
|-----------|-------------------|
| Revenue | `revenue`, `net_revenue`, `sales` |
| COGS | `cogs`, `cost_of_goods`, `landed_cost` |
| Gross profit | `gross_profit`, `gross_margin` |
| Fulfillment / platform fees | shipping, FBA fees, platform fees |

Only read channel sheets relevant to the analysis scope. If the user asks about DTC margins, do not read the Wholesale sheet.

**Step 2.3 — Read opex only if contribution margin is needed**
If the user asks about contribution margin (not just gross margin), call `read_smartmodel_data_section` on the Opex sheet for marketing spend by channel.

Pull both the current period and prior period for trend context. Pull plan/forecast columns for the same period for variance context.

---

## Phase 3 — Compute

### Gross Margin
```
Gross Margin ($) = Net Revenue − COGS
Gross Margin (%) = Gross Margin ($) / Net Revenue
```

### Contribution Margin (if data available)
```
Contribution Margin ($) = Gross Margin − Variable Costs
Variable Costs = Marketing Spend + Fulfillment + Platform Fees
Contribution Margin (%) = Contribution Margin ($) / Net Revenue
```

### Blended vs. channel-level
Always compute both:
- **Blended**: Company-wide margin from the consolidation sheet
- **By channel**: Margin per channel from individual schedule sheets

The blended margin is a mix-weighted average. If it changed, it could be because individual channel margins changed OR because the revenue mix shifted.

### Price-Volume-Mix Bridge

When explaining margin changes period over period:
1. **Volume effect**: More volume at same margin = margin $ up, margin % flat
2. **Price effect**: ASP / AOV change flows directly to margin
3. **Cost effect**: Unit COGS change — input costs, supplier, freight
4. **Mix effect**: Channel or product mix shift — often the biggest hidden driver

**Mix effect calculation:**
```
Mix Effect = Σ (Actual Channel Mix % − Prior Period Channel Mix %) × Prior Period Channel Margin %
```

A brand shifting from 60% DTC / 40% Wholesale to 50/50 will see blended margin decline even if each channel's margin is unchanged.

### COGS Waterfall

For product-level COGS decomposition, build a component breakdown:

| Component | Identifier pattern to look for |
|-----------|-------------------------------|
| Raw materials / ingredients | `unit_cost`, `materials`, `ingredients` |
| Manufacturing / co-pack | `manufacturing`, `copacking`, `production` |
| Packaging | `packaging`, `boxes`, `labels` |
| Inbound freight | `freight`, `landed_cost`, `inbound` |
| Duties / tariffs | `duties`, `tariffs`, `customs` |

---

## Phase 4 — Channel Deep Dives

### DTC
- Gross margin: Revenue − product COGS − fulfillment
- Key metric: Contribution margin after CAC — "are we profitable on first order?"
- Watch for: Shipping cost creep, return rate increases, discount depth
- Always split subscription vs. one-time — subscription margin is structurally higher

### Amazon
- Gross margin: Revenue − COGS − Amazon fees (FBA, referral, advertising)
- Key metric: "True margin" after all Amazon costs
- Watch for: ACoS (advertising cost of sale) as % of revenue, FBA fee increases
- Common trap: Revenue looks great but after Amazon takes 35–40%, margin may be thin

### Wholesale
- Gross margin: Revenue − COGS at wholesale price points
- Key metric: Margin after trade spend and slotting fees
- Watch for: Trade spend effectiveness, deduction rates, freight costs
- Common trap: Trade spend buried in different line items — ensure all channel costs are captured

---

## Phase 5 — Output

### Default output (narrative + tables)

1. **Headline**: "Blended gross margin is X% — [up/down Y bps from plan/prior period] driven primarily by [biggest driver]"
2. **Margin summary table**: Channel × Margin % × Margin $ × Period comparison
3. **Mix-adjusted bridge**: Walk from prior period / plan to current margin, quantifying each driver
4. **Channel deep-dives**: Only for channels with material margin movement
5. **Product-level callouts**: Specific SKUs dragging or boosting margin
6. **Recommendations**: Actionable next steps

### Key ratios to always include
- Gross margin % by channel
- COGS as % of revenue by channel
- Blended gross margin % and 3-month trend
- Contribution margin % (if data available)

### Excel output (if requested)

Call `create_sheet` with blue tab, `write_range` for the margin summary and bridge tables, `format_range` for number formatting, and `create_chart` (ColumnClustered waterfall) for visual impact.

---

## Guardrails

- Never write to Actual columns
- Never overwrite Key Driver cells
- If a channel sheet is missing, note it and compute blended margin from available data only — do not fabricate channel splits

---

## Common Mistakes to Avoid

1. Don't analyze blended margin without channel decomposition — a blended number hides the story
2. Don't ignore mix effects — channel mix shift is the #1 hidden margin driver for omnichannel brands
3. Don't conflate gross margin and contribution margin — a channel can have great gross margin and terrible contribution margin after marketing
4. Don't forget Amazon fees — they're not COGS in the traditional sense but they're a real cost of the channel
5. Don't compare DTC margin to wholesale margin without context — they're structurally different businesses

---

## Integration with Other Skills

- **`/variance-analysis`**: Margin variance is a subset — this skill goes deeper
- **`/sku-rationalization`**: Uses margin data to identify SKUs to keep, grow, or cut
- **`/product-cost-analysis`**: Goes deeper on the COGS side specifically
- **`/build-report`**: Package margin analysis into a formatted deliverable
