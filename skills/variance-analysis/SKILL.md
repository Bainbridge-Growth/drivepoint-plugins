---
name: variance-analysis
description: Analyze performance vs. plan, forecast, or prior period — decomposing variances by driver (price, volume, mix, timing) and flagging material deviations. Use when a user asks to explain variances, compare actuals to plan/forecast, understand what's driving a miss or beat, check mid-month pacing, or asks "why did we miss?" / "what changed?" / "how are we tracking?" Also triggers on "budget vs. actual", "plan vs. actual", "pacing", "mid-month", or "variance report".
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

**Step 1.1 — Use model context from the protocol**
Settings, index, and date spine are already loaded by the protocol's auto-orient. From the model context, note: `companyName`, `currency`, which columns are Actual vs. Forecast, the most recently closed Actual month, and the consolidation sheet name.

**Step 1.2 — Identify comparison basis**
Infer from the user's request: Plan (original budget), Forecast (latest reforecast), Prior Year, or Prior Month.
Default to **Actuals vs. Forecast** for the most recently closed month if not specified.

**Step 1.3 — State the comparison basis explicitly**
Before proceeding to Phase 2, output this line:

```
Comparison: [Month] Actuals vs. [Month] [Plan / Forecast / Prior Month / Prior Year]
```

Rules:
- If the user specifies the basis ("vs. plan", "vs. last year"), use what they asked for.
- If not specified, default to: Actuals for the most recently closed month vs. Forecast/Plan for that same month.
- If the model has no retained plan/forecast column for the closed period (i.e., forecast was overwritten when actuals landed), default to **prior month** or **prior year** — whichever gives a more meaningful baseline — and state the choice: "This model doesn't retain a separate plan for closed months, so I'm comparing [month] actuals to [prior month / prior year] actuals."
- Do not ask the user to choose. Pick the most useful basis, state it, and proceed. The user can redirect if they want something different.

**Hard rule: never start Phase 2 without having stated the comparison basis in plain English.**

---

## Phase 2 — Gather Data

**If a prior skill ran this session** (e.g., `/summarize_model`), reuse settings, index, date spine, and any data already gathered. Do not re-read sheets that were already read.

**Step 2.1 — Read the consolidation sheet (one call)**
Call `read_smartmodel_data_section` on **M - Monthly** (the consolidation sheet). This single call returns the full P&L for the comparison period: total revenue, COGS, gross profit, opex, EBITDA/net income. Extract everything you need from this one response.

**Step 2.2 — Read channel sheets only for driver decomposition**
Only if the consolidation reveals a material revenue or COGS variance that requires channel-level decomposition, call `read_smartmodel_data_section` on the specific channel sheet(s) involved. Do not read every channel sheet upfront.

Use column B identifiers to locate rows. Do not rely on row numbers — they shift between models.

Pull both **Actual** and **Plan/Forecast** columns for the same period. If comparing to Prior Period, pull the preceding month's Actual columns.

For forecast reasonableness (Phase 2.5), also pull the trailing 12 months of Actuals for each major P&L line from the consolidation sheet.

---

## Phase 2.5 — Forecast Reasonableness Scan

**Run this phase only when the comparison involves a forecast period. Skip for actuals-vs-prior-period or actuals-vs-prior-year comparisons.**

For each major P&L line item (revenue by channel, total COGS, total opex), compare the forecasted value against the min and max of the trailing 12 months of Actuals gathered in Phase 2.

Flag if any forecasted line item **exceeds the 12-month actual max by >20%**:
> "The [month] forecast for [line item] ($X) is [Y]% above the highest actual month in the trailing 12 months ($Z in [month]). This is achievable but represents a level the business hasn't sustained before — execution risk is elevated."

Flag if any forecasted line item is **below the 12-month actual min by >20%**:
> "The [month] forecast for [line item] ($X) is [Y]% below the lowest actual month in the trailing 12 months ($Z in [month]). This may reflect a structural change or conservative planning — worth noting before interpreting the variance."

Present flags as a brief **Forecast Notes** section before the variance analysis — not buried in the deep-dives. If no flags are triggered, skip this section entirely.

This does not invalidate the forecast. There may be excellent reasons for ambitious numbers (new channel launch, confirmed PO, seasonal event). The check gives the user historical context to interpret the variance analysis that follows.

---

## Phase 3 — Compute Variances

For each line item:

```
Variance ($) = Actual − Plan
If Plan ≠ 0:
  Variance (%) = (Actual − Plan) / |Plan|
If Plan = 0:
  Variance (%) = N/A
  Report the dollar variance only
```

**Sign convention for revenue and margin lines**: Positive variance = favorable (beat plan). Always label favorability explicitly.

**Sign convention for variable cost lines (COGS, fulfillment, platform fees)**: Evaluate on a **rate basis**, not absolute dollars. A cost that rises in lockstep with revenue is not a variance — it's the business model working.

- If COGS as % of revenue **improved** (went down) vs. comparison period → **Favorable**
- If COGS as % of revenue **worsened** (went up) vs. comparison period → **Unfavorable**
- If COGS % is roughly flat but absolute COGS increased proportionally with revenue → **Neutral** — label as "Volume-driven"

In the summary table, for variable cost lines show both absolute $ and % of revenue for both periods:
```
COGS  |  $753K (31.6% of rev)  |  $1,635K (35.6% of rev)  |  +$882K  |  ⚠️ Unfav (+4.0pp margin pressure)
```

The summary table and deep-dive must tell the same story. If the deep-dive concludes COGS growth is volume-driven, the summary table must not flag it as unfavorable.

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

**COGS variances** — always decompose into these three components before assigning favorability:
| Driver | How to identify | Favorability |
|--------|----------------|-------------|
| Volume effect | More units sold × same cost per unit | Neutral — cost rising with revenue is expected |
| Rate effect | Same units × higher cost per unit | Unfavorable — efficiency declined |
| Mix effect | Shift toward higher/lower cost products or channels | Favorable or unfavorable depending on direction |

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

### Criticality reordering (apply before presenting output)

After computing all variances, reorder the deep-dives by business criticality — not dollar size:

1. 🔴 **Critical** — Cash/liquidity risk: ending cash drops below 2 months of opex, or cash declines >50% period-over-period. Always surfaces as finding #1 regardless of dollar amount.
2. 🔴 **Critical** — Revenue concentration risk: >50% of forecasted revenue depends on a single channel, customer, or event (e.g., one wholesale shipment). Flag in top 2 findings.
3. 🟡 **Material** — Gross margin compression >3 percentage points vs. comparison period. Always top 3 — signals a structural shift, not just timing.
4. 🟡 **Material** — All other material variances, ranked by absolute dollar impact.
5. 🟢 **Watch** — Variances trending toward concern but not yet material.

Add the severity tag (🔴 Critical / 🟡 Material / 🟢 Watch) to each deep-dive heading.

### Narrative output (default)

Present in this order:
1. **Comparison basis**: Restate the comparison (from Step 1.4) so the reader knows what they're looking at
2. **Forecast Notes** (if Phase 2.5 produced flags): Brief reasonableness callouts before the variance table
3. **Headline**: One sentence — did we beat or miss, by how much, and the single biggest driver
4. **Summary table**: Top-level P&L lines with Actual, Plan, Variance $, Variance %, favorability flag (variable cost lines include % of revenue for both periods)
5. **Material variance deep-dives**: Ordered by criticality (🔴 → 🟡 → 🟢), with driver decomposition for each
6. **Channel-level detail**: Variance by channel if multi-channel data is present
7. **Pacing section** (if mid-month): Run rate vs. plan by channel with status flags
8. **Recommended actions**: What should the operator do based on this analysis

### Excel output (if user requests)

Call `create_sheet` with blue tab color, then `write_range` to populate the variance table. Call `format_range` to apply number formatting (currency, percentages). Call `create_chart` (ColumnClustered) for waterfall visualization if the user requests one.

### Formatting rules

See **Output Formatting Standards** in the protocol. Additionally for variance output:
- Always show both $ and % variance for every line item
- Label favorability explicitly on every variance (Favorable / Unfavorable / Neutral)

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
