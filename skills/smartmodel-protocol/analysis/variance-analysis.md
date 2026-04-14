---
name: variance-analysis
description: Analyze performance vs. plan, forecast, or prior period — decomposing variances by driver (price, volume, mix, timing) and flagging material deviations. Use when a user asks to explain variances, compare actuals to plan/forecast, understand what's driving a miss or beat, check mid-month pacing, or asks "why did we miss?" / "what changed?" / "how are we tracking?" Also triggers on "budget vs. actual", "plan vs. actual", "pacing", "mid-month", or "variance report".
user-invocable: true
---

# Variance Analysis

**Purpose**: Structured, driver-based variance analysis — full-period (actuals vs. plan/forecast) and mid-month pacing. Covers revenue, COGS, gross margin, and opex.
**Prerequisite**: The `smartmodel-protocol` skill must be loaded.

---

## When This Skill Activates

- User asks to compare actuals vs. plan, budget, forecast, or prior period
- User asks "why did we miss/beat?"
- User asks "how are we pacing?" or "where are we mid-month?"
- User asks for a variance report or bridge analysis
- User opens a SmartModel and asks about performance

---

## Phase 1 — Orient

**Step 1.1 — Read model identity**
Call `read_smartmodel_settings` → capture `settings.companyName`, `settings.currency`, `settings.modelStartDate`.

**Step 1.2 — Establish time context**
Call `read_smartmodel_date_spine` on the consolidation sheet (M - Monthly) or primary schedule sheet.
- Identify which columns are "Actual" vs. "Forecast" from Row 3
- Determine the most recently closed Actual month
- Determine the comparison period (user-specified or default to most recent closed month)

**Step 1.3 — Identify comparison basis**
Ask or infer: Plan (original budget), Forecast (latest reforecast), Prior Year, or Prior Month.
Default to **Actuals vs. Forecast** for the most recently closed month if not specified.

---

## Phase 2 — Gather Data

Call `read_smartmodel_data_section` on the relevant sheets for the comparison period:

| Data Point | Sheet | Section |
|-----------|-------|---------|
| Total revenue | M - Monthly (consolidation) | Revenue section |
| Revenue by channel | DTC, AMZN, Wholesale sheets | Revenue rows |
| COGS | Product sheet or consolidation | COGS section |
| Gross margin | Derived: Revenue − COGS | — |
| Opex | Opex sheet | All sections |
| Net income / EBITDA | Consolidation | Bottom of P&L |

Use column B identifiers to locate rows. Do not rely on row numbers — they shift between models.

Pull both **Actual** and **Plan/Forecast** columns for the same period. If comparing to Prior Period, pull the preceding month's Actual columns.

---

## Phase 3 — Compute Variances

For each line item:

```
Variance ($) = Actual − Plan
Variance (%) = (Actual − Plan) / |Plan|
```

**Sign convention**: Positive = favorable for revenue/margin lines. Positive = unfavorable for expense lines. Always label favorability explicitly.

### Materiality threshold

Flag a variance as material if it meets ANY of:
- Absolute dollar variance > 5% of total revenue for the period
- Percentage variance > ±10% of the plan line item
- Line item is in the top 3 largest absolute variances

Report only on material variances. Do not list every line item.

### Driver decomposition for material variances

**Revenue variances:**
| Driver | How to identify |
|--------|----------------|
| Volume | Units / orders vs. plan — check order count rows in channel sheets |
| Price / AOV | Average order value or price per unit vs. plan |
| Mix | Channel mix shift — e.g., more wholesale (lower margin) vs. DTC |
| Timing | Revenue recognized earlier/later than planned (wholesale ship dates, subscription renewals) |
| New vs. existing | Split by acquisition vs. returning if cohort data available |

**COGS variances:**
| Driver | How to identify |
|--------|----------------|
| Input cost | Raw material or unit cost changes vs. plan |
| Volume | More/fewer units sold |
| Freight / fulfillment | Shipping cost per order vs. plan |
| Product mix | Higher vs. lower margin SKU mix shift |

**Opex variances:**
| Driver | How to identify |
|--------|----------------|
| Headcount | Payroll sheet — hires/departures vs. plan |
| Marketing spend | Actual vs. planned budget by channel |
| Timing | Spend pulled forward or pushed back |
| One-time items | Non-recurring costs not in plan |

---

## Phase 4 — Mid-Month Pacing Mode

When the user asks about pacing (current month not yet closed):

1. Call `get_todays_date` to get today's date, days elapsed in month, and days in month
2. **Compute run rate**: `(Actuals to date / Days elapsed) × Days in month`
3. Compare run rate to plan for the full month
4. Flag channels or line items pacing below plan

**Pacing thresholds:**
- On track: run rate within ±5% of plan
- Watch: run rate 5–15% below plan
- At risk: run rate >15% below plan

For DTC with daily data: use actual daily revenue.
For wholesale with lumpy shipments: caveat that pacing may not be linear — check against scheduled ship dates if available in the model.

---

## Phase 5 — Output

### Narrative output (default)

Present in this order:
1. **Headline**: One sentence — did we beat or miss, by how much, and the single biggest driver
2. **Summary table**: Top-level P&L lines with Actual, Plan, Variance $, Variance %, favorability flag
3. **Material variance deep-dives**: Driver decomposition for each material line
4. **Channel-level detail**: Variance by channel if multi-channel data is present
5. **Pacing section** (if mid-month): Run rate vs. plan by channel with status flags
6. **Watch items**: Variances not yet material but trending toward concern
7. **Recommended actions**: What should the operator do based on this analysis

### Excel output (if user requests)

Call `create_sheet` with blue tab color, then `write_range` to populate the variance table. Call `format_range` to apply number formatting (currency, percentages). Call `create_chart` (ColumnClustered) for waterfall visualization if the user requests one.

### Formatting rules

- Use currency from `settings.currency` (default USD)
- Round to thousands for companies >$10M revenue; round to dollars for smaller
- Always show both $ and % variance
- Never present raw data without interpretation — every number needs a "so what"

---

## Guardrails

- Never write to Actual columns
- Never overwrite Key Driver cells without explicit user confirmation
- If the plan/forecast column is empty for a period, note this and skip the variance computation for that line — do not assume the plan is $0

---

## Common Mistakes to Avoid

1. Don't compare Actuals to Actuals and call it variance analysis — variance requires a plan or forecast as baseline
2. Don't ignore timing — a wholesale shipment arriving Week 1 vs. Week 5 can swing a month without anything changing
3. Don't treat all variances as equal — a $50K miss on $5M revenue is noise; a $50K miss on $200K marketing is a 25% overspend
4. Don't forget to check if the plan itself was reasonable — if it was sandbagged or stretch, the variance is misleading
5. Don't present 30 line items — focus on the 3–5 that explain 80%+ of the total variance

---

## Integration with Other Skills

- **`/summarize_model`**: Run first if not yet oriented to the model
- **`/margin_analysis`**: Go deeper on gross margin variances
- **`/build_report`**: Package the variance analysis into a formatted report
- **`/interrogate_model`**: If the user asks follow-up questions about specific variances
