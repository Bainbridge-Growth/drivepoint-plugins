---
name: sku-rationalization
description: Analyze product portfolio profitability and recommend which SKUs to invest in, maintain, or cut. Use when a user asks about SKU performance, "which products are profitable?", "what should we cut?", "SKU rationalization", "product portfolio analysis", "which SKUs are dragging margin?", or "where should we focus our product investment?" Also triggers on "product mix", "item profitability", "portfolio review", "do we have too many SKUs?", or "which products should we kill?".
---

# SKU Rationalization

**Purpose**: Rank every SKU by revenue and margin contribution, identify the Pareto-driving SKUs, and flag low-contribution or margin-dilutive products for pruning or repositioning.
**Prerequisite**: The `smartmodel-protocol` skill must be loaded.

---

## When This Skill Activates

- User asks which products are profitable or unprofitable
- User wants to simplify the product lineup
- User asks where to focus product investment
- User asks about SKU-level P&L or unit economics
- User wants to see a Pareto breakdown of product contribution

---

## Phase 1 — Orient

**Step 1.1 — Use model context from the protocol**
Settings, index, and date spine are already loaded by the protocol's auto-orient. From the model context, note `companyName`, `currency`, and identify which sheet(s) contain product/SKU dimensions (template IDs like `product`, `dtc-revenue`, `cogs`). Determine the analysis period — default to trailing 3–6 months of Actuals.

**Step 1.2 — Read SKU dimensions**
Call `read_smartmodel_registries` on the product/SKU sheets → extract `dim_` entries to get the full list of SKUs being modeled.

---

## Phase 2 — Gather Data

**If a prior skill ran this session** (e.g., `/margin-analysis`, `/product-cost-analysis`), reuse settings, index, date spine, and any product or channel data already gathered. Do not re-read sheets that were already read.

Call `read_smartmodel_data_section` on product and channel sheets to collect:

| Metric | Identifier pattern | Why it matters |
|--------|-------------------|---------------|
| Units sold | `units`, `orders`, `volume` | Volume contribution |
| Revenue | `revenue`, `net_revenue` | Top-line contribution |
| COGS / unit cost | `cogs`, `unit_cost`, `landed_cost` | Margin structure |
| Gross profit | `gross_profit` | Direct contribution |
| Gross margin % | Derived if not explicit | Margin quality |
| Returns / refunds | `returns`, `refunds` | Net revenue accuracy |
| Marketing spend (if SKU-level) | `marketing_spend`, `ad_spend` | Contribution margin |

If R- sheets are populated, call `read_r_sheet` on the relevant GL or product cost sheet for more granular unit cost data.

---

## Phase 3 — Compute

### Per-SKU metrics

For each SKU dimension:
```
Gross Profit ($) = Revenue − COGS
Gross Margin (%) = Gross Profit / Revenue
Revenue Contribution (%) = SKU Revenue / Total Revenue
Gross Profit Contribution (%) = SKU Gross Profit / Total Gross Profit
```

### Pareto ranking

Sort SKUs by gross profit contribution descending. Identify:
- **Top tier** (typically top 20% of SKUs generating 80% of gross profit)
- **Mid tier** (next 30% of SKUs generating next 15% of gross profit)
- **Tail** (bottom 50% of SKUs generating last 5% of gross profit)

### Rationalization flags

Flag a SKU for review if it meets ANY of:
- Gross margin % is more than 15 percentage points below the portfolio average
- Revenue contribution is <1% of total revenue (low volume)
- Gross profit contribution is negative (actively margin-dilutive)
- Revenue is declining >20% period-over-period with no recovery trend

### Growth flags

Flag a SKU as a growth candidate if:
- Gross margin % is above portfolio average AND revenue contribution is growing
- Gross profit per unit is high but volume is low (under-invested)

---

## Phase 4 — Output

### Default output

1. **Headline**: "Your top [N] SKUs generate [X]% of gross profit. [M] SKUs are flagged for rationalization."
2. **Ranked SKU table**:

```
| SKU | Revenue | Rev Contrib % | Gross Profit | GP Margin % | GP Contrib % | Flag |
|-----|---------|---------------|-------------|-------------|--------------|------|
```

3. **Pareto commentary**: Which SKUs make up the 80/20 and why
4. **Rationalization candidates**: Table of flagged SKUs with specific reason for each flag
5. **Growth candidates**: Table of high-potential SKUs with investment rationale
6. **Recommendations**: Prioritized actions (cut, maintain, invest, reprice, reposition)

### Excel output (if requested)

Call `create_sheet` with blue tab. Call `write_range` for the ranked SKU table. Call `format_range` for number formatting. Call `conditional_format_range` to color-code margin tiers (green = above average, yellow = mid, red = below threshold). Call `create_chart` (Bar chart showing revenue vs. gross profit contribution — Pareto visualization).

---

## Guardrails

- Never write to Actual columns
- Never delete SKU dimensions from the model — only report findings, do not restructure
- If SKU-level COGS data is not available in the model, note this and compute revenue-only ranking — clearly label the limitation
- Confirm with user before writing any output to the workbook

---

## Common Mistakes to Avoid

1. Don't rationalize based on revenue alone — a high-revenue, low-margin SKU may be worse than a low-revenue, high-margin one
2. Don't ignore return rates — a SKU with high gross sales but high returns may have lower net contribution than it appears
3. Don't recommend cutting a SKU without checking if it's a strategic product (new launch, hero product, relationship driver for a retailer)
4. Don't use a single month of data for rationalization decisions — use trailing 3–6 months minimum
5. Don't conflate volume decline with poor performance — some SKUs are intentionally being phased out

---

## Integration with Other Skills

- **`/margin-analysis`**: Use to understand the COGS structure behind SKU margins
- **`/product-cost-analysis`**: Go deeper on unit economics for flagged SKUs
- **`/variance-analysis`**: Check if SKU performance is a variance from plan or structural
- **`/build-report`**: Package rationalization findings for a leadership or board presentation
