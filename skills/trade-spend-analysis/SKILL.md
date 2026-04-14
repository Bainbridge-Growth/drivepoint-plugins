---
name: trade-spend-analysis
description: Analyze retail trade spend — promotional effectiveness, deduction rates, accrual vs. actual, and retailer-level P&L. Use when a user asks about trade spend, "are our promotions working?", "what's our deduction rate?", "retailer profitability", "trade spend as % of revenue", or "promo ROI". Also triggers on "trade promotion", "retail deductions", "scan backs", "MCBs", "slotting fees", or "wholesale P&L".
---

# Trade Spend Analysis

**Purpose**: Analyze trade promotion spend for wholesale/retail channels — decomposing spend by type, measuring promotional ROI, tracking accrual vs. actual, and building a retailer-level P&L.
**Prerequisite**: The `smartmodel-protocol` skill must be loaded.

---

## When This Skill Activates

- User asks about trade spend, promotions, or retail deductions
- User wants to know if their promotions are generating ROI
- User asks about retailer-level profitability (Walmart P&L, Target P&L, etc.)
- User wants to reconcile trade spend accruals vs. actual deductions
- User is planning next season's promotional calendar

---

## Phase 1 — Orient

**Step 1.1 — Read model identity**
Call `read_smartmodel_settings` → capture `settings.companyName`, `settings.currency`.

**Step 1.2 — Locate trade spend and wholesale data**
Call `read_smartmodel_index` → identify the wholesale schedule sheet and any trade spend or deductions sections. Trade spend may live on the wholesale revenue sheet, a dedicated trade sheet, or the opex sheet.

**Step 1.3 — Read wholesale structure**
Call `read_smartmodel_registries` on the wholesale sheet → identify retailer dimensions (Walmart, Target, Whole Foods, etc.) and trade spend measure identifiers.

**Step 1.4 — Read time context**
Call `read_smartmodel_date_spine` → determine analysis period. Trade spend analysis typically covers a promotion period (event-based) or rolling 3–6 months.

---

## Phase 2 — Gather Data

**If a prior skill ran this session** (e.g., `/margin_analysis`, `/variance_analysis`), reuse settings, index, date spine, and any wholesale data already gathered. Do not re-read sheets that were already read.

Call `read_smartmodel_data_section` on wholesale and trade spend sheets:

| Metric | Identifier pattern | What it represents |
|--------|-------------------|-------------------|
| Gross wholesale revenue | `gross_revenue`, `gross_sales` | Revenue before trade deductions |
| Trade spend total | `trade_spend`, `total_trade` | All promotional investment |
| — Scan backs / OIs | `scan_backs`, `oi`, `off_invoice` | Per-unit promotional discount |
| — MCBs / billbacks | `mcb`, `billback`, `performance_fund` | Retroactive deductions |
| — Slotting fees | `slotting`, `slotting_fee` | New item placement fees |
| — Ad fees | `ad_fee`, `coop_advertising` | Retailer co-op advertising |
| Net wholesale revenue | `net_revenue`, `net_sales` | Gross minus all trade |
| Shipped units | `units_shipped`, `units_sold` | Volume through each retailer |
| Velocity / consumption | `velocity`, `consumption` | Sell-through rate at retail |

If R- sheets contain retailer POS data, call `read_r_sheet` for consumption vs. shipment comparison.

---

## Phase 3 — Compute

### Trade spend rate

```
Trade Rate = Total Trade Spend / Gross Wholesale Revenue
Net Revenue Realization = Net Wholesale Revenue / Gross Wholesale Revenue
```

CPG benchmarks for trade rate:
| Retailer Type | Typical Trade Rate |
|--------------|-------------------|
| Mass (Walmart, Target) | 25–35% |
| Natural/Specialty (Whole Foods, Sprouts) | 15–25% |
| Club (Costco) | 10–20% |
| Drug (CVS, Walgreens) | 20–30% |

### Trade spend by type

Break down trade spend into its components and show each as % of gross revenue:
```
Scan Back Rate = Scan Backs / Gross Revenue
MCB Rate = MCBs / Gross Revenue
Slotting Rate = Slotting Fees / Gross Revenue
Ad Fee Rate = Ad Fees / Gross Revenue
```

### Promotional lift analysis

For periods with identifiable promotions (price reductions, TPRs):
```
Baseline Velocity = Average weekly velocity in non-promoted weeks
Promoted Velocity = Average weekly velocity in promoted weeks
Lift = (Promoted Velocity − Baseline Velocity) / Baseline Velocity
Incremental Units = (Promoted Velocity − Baseline Velocity) × Promo Weeks
Promo Revenue = Promoted Price × Promo Units Sold
Trade Cost = Scan Back per Unit × Total Promo Units
Promo ROI = (Incremental Gross Profit − Trade Cost) / Trade Cost
```

### Accrual vs. actual reconciliation

```
Trade Accrual (in model) = Forecast trade spend rate × Revenue
Trade Actual (from deductions) = Actual deductions received
Variance = Accrual − Actual
```

Flag if actual deductions are running significantly above or below accrual — this creates working capital surprises.

### Retailer-level P&L

For each retailer dimension:
```
Gross Revenue
− Trade Spend
= Net Revenue
− COGS
= Gross Profit
− Freight to retailer
= Net Contribution
Net Contribution Margin % = Net Contribution / Gross Revenue
```

---

## Phase 4 — Output

### Default output

1. **Headline**: "Trade spend is running at [X]% of gross wholesale revenue. [Retailer] is the most profitable channel at [Y]% net contribution margin; [Retailer] is the least profitable at [Z]%."
2. **Trade rate summary**:

```
| Retailer | Gross Rev | Trade Spend | Trade Rate | Net Rev | Net Margin |
|----------|-----------|-------------|-----------|---------|-----------|
```

3. **Trade spend waterfall**: Breakdown by type (scan backs, MCBs, slotting, ad fees)
4. **Accrual vs. actual**: Variance table with flag if >10% off accrual
5. **Promo effectiveness**: For identifiable promotions — lift, incremental units, ROI
6. **Retailer P&L**: Net contribution by retailer, ranked best to worst
7. **Recommendations**: Which retailers to invest more, which to restructure trade terms, which promotions to continue or cut

### Excel output (if requested)

Call `create_sheet` with blue tab. Call `write_range` for the retailer P&L table and trade spend waterfall. Call `format_range` for number and currency formatting. Call `create_chart` (ColumnClustered) comparing gross vs. net revenue by retailer.

---

## Guardrails

- Never write to Actual columns
- Trade spend is often the most complex and least consistently structured section of wholesale models — if identifiers don't match expected patterns, read the section headers and ask the user to confirm which rows represent which trade type before computing
- Accrual vs. actual reconciliation requires both model data and actual deduction data — if only one is available, note the limitation

---

## Common Mistakes to Avoid

1. Don't report gross wholesale revenue without netting trade — it's a misleading number that overstates actual revenue
2. Don't ignore slotting fees in new retailer economics — they're a one-time cost that can make the first year unprofitable even if ongoing economics are good
3. Don't compare trade rates across retailers without noting the structural differences (mass vs. natural vs. club have fundamentally different trade structures)
4. Don't analyze promotional ROI using shipment data alone — if the retailer builds inventory during a promotion without increased sell-through, the lift is illusory
5. Don't assume accruals are accurate — many brands consistently over- or under-accrue; the actual deduction history is the ground truth

---

## Integration with Other Skills

- **`/margin_analysis`**: Trade spend is a major driver of wholesale channel margin
- **`/variance_analysis`**: Check if trade spend is running above or below plan
- **`/sku_rationalization`**: Trade spend ROI by SKU informs which products are worth promotional investment
- **`/build_report`**: Include retailer P&L in board or investor reports for wholesale-heavy brands
