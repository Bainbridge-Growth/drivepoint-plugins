---
name: product-cost-analysis
description: Decompose COGS into component-level unit economics — materials, manufacturing, packaging, freight, duties. Use when a user asks about product costs, unit economics, COGS breakdown, "what does it cost to make this?", "where are our costs going?", "landed cost per unit", or "cost per unit by SKU". Also triggers on "bill of materials", "unit cost", "COGS decomposition", "landed cost", or "cost structure".
---

# Product Cost Analysis

**Purpose**: Break down COGS into its component parts — per-unit and in aggregate — to identify cost drivers, track cost trends, and surface savings opportunities.
**Prerequisite**: The `smartmodel-protocol` skill must be loaded.

---

## When This Skill Activates

- User asks about product costs, unit economics, or cost structure
- User wants to understand what's driving COGS up or down
- User asks for a landed cost breakdown by SKU
- User wants to find cost reduction opportunities
- User is evaluating a new supplier or manufacturing change

---

## Phase 1 — Orient

**Step 1.1 — Read model identity**
Call `read_smartmodel_settings` → capture `settings.companyName`, `settings.currency`.

**Step 1.2 — Locate product/COGS data**
Call `read_smartmodel_index` → identify the product sheet, COGS schedule, or any sheet with template IDs related to product or cost.

**Step 1.3 — Read product dimensions**
Call `read_smartmodel_registries` on the product sheet → extract `dim_` entries to get SKU list and `measure_` entries to understand what cost components are tracked.

**Step 1.4 — Read time context**
Call `read_smartmodel_date_spine` → determine analysis period. Use trailing 3–6 months of Actuals for cost analysis. Note any periods where costs appear to have stepped up or down.

---

## Phase 2 — Gather Data

Call `read_smartmodel_data_section` on the product/COGS sheet:

| Cost Component | Identifier pattern | What it represents |
|---------------|-------------------|-------------------|
| Unit cost / COGS | `unit_cost`, `cogs_per_unit` | Total landed cost per unit |
| Raw materials | `materials`, `ingredients`, `raw_cost` | Core input cost |
| Manufacturing / co-pack | `manufacturing`, `copacking`, `production_cost` | Labor + facility cost |
| Packaging | `packaging`, `cartons`, `labels` | Primary and secondary packaging |
| Inbound freight | `inbound_freight`, `freight`, `shipping_in` | Cost to get goods to warehouse |
| Duties / tariffs | `duties`, `tariffs`, `customs` | Import taxes (critical for tariff-impacted brands) |
| Fulfillment / outbound | `fulfillment`, `3pl`, `pick_pack` | Cost to fulfill orders (often on channel sheets) |

If R- sheets contain GL data, call `read_r_sheet` on the COGS GL categories for actual cost breakdowns.

Also gather units sold from channel sheets via `read_smartmodel_data_section` — needed to compute per-unit costs from total cost rows.

---

## Phase 3 — Compute

### Per-unit cost waterfall

For each SKU:
```
Landed Cost per Unit = Raw Materials + Manufacturing + Packaging + Inbound Freight + Duties
Gross Cost per Order = Landed Cost per Unit × Units per Order
Total Fulfillment Cost per Order = Fulfillment Cost per Order (from channel data)
Total Variable Cost per Order = Gross Cost per Order + Total Fulfillment Cost per Order
```

### Cost as % of revenue

```
COGS % = Total COGS / Net Revenue
Each component % = Component Cost / Net Revenue
```

### Cost trend analysis

Compare current period vs. prior periods:
```
Cost Change ($) = Current Period Unit Cost − Prior Period Unit Cost
Cost Change (%) = Cost Change ($) / Prior Period Unit Cost
```

Flag if any component has increased >10% period-over-period.

### Blended vs. SKU-level

Always compute both:
- **Blended**: Portfolio-average unit cost and COGS %
- **By SKU**: Cost structure for each product (some SKUs may have dramatically different cost profiles)

---

## Phase 4 — Output

### Default output

1. **Headline**: "Blended landed cost per unit is $[X], representing [Y]% of net revenue. [Biggest cost component] is the primary driver at [Z]%."
2. **Cost waterfall table** (per unit):

```
| Component | $ per Unit | % of Revenue | % of Total COGS |
|-----------|-----------|-------------|-----------------|
| Raw materials | | | |
| Manufacturing | | | |
| Packaging | | | |
| Inbound freight | | | |
| Duties | | | |
| Landed cost total | | | |
| Fulfillment | | | |
| Total variable cost | | | |
```

3. **SKU-level comparison**: Side-by-side cost structure for each SKU
4. **Cost trend**: Period-over-period change by component with flags on step-changes
5. **Tariff exposure**: If duties are >5% of COGS, highlight tariff risk and note which inputs are affected
6. **Recommendations**: Specific cost reduction opportunities (supplier renegotiation, packaging simplification, freight consolidation)

### Excel output (if requested)

Call `create_sheet` with blue tab. Call `write_range` for the waterfall table and SKU comparison. Call `format_range` for number formatting. Call `create_chart` (ColumnStacked) for a per-unit cost waterfall by component.

---

## Guardrails

- Never write to Actual columns
- If unit-level cost data isn't available (only total COGS without unit counts), compute per-unit costs by dividing total COGS by units sold from channel data — clearly note this is derived, not model-declared
- Do not guess cost components that aren't in the model — report what's available and flag what's missing

---

## Common Mistakes to Avoid

1. Don't ignore fulfillment — for DTC brands, fulfillment can be 10–20% of revenue and must be in the unit economics picture
2. Don't use total COGS without units sold — always convert to per-unit for meaningful comparison
3. Don't ignore tariff exposure — for brands sourcing from China or overseas, duties can be a significant and volatile cost component
4. Don't compare cost % across channels without noting that revenue prices differ — DTC price vs. wholesale price vs. Amazon price produce different cost % even on the same product
5. Don't analyze point-in-time costs without trend — cost creep is the most common issue and requires period comparison to detect

---

## Integration with Other Skills

- **`/margin_analysis`**: This skill feeds the COGS side of margin analysis
- **`/sku_rationalization`**: Use per-SKU cost data to rank products by true profitability
- **`/variance_analysis`**: Check cost variances against plan
- **`/build_report`**: Package cost analysis for leadership or investor review
