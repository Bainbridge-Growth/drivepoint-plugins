---
name: cohort-analysis
description: Analyze customer retention curves and lifetime value (LTV) in a single consolidated pass. Use when a user asks about cohort retention, LTV, CAC payback period, "how long do customers stay?", "what's our LTV?", "are we retaining customers?", "LTV:CAC ratio", or "cohort performance". Also triggers on "retention analysis", "customer lifetime value", "churn", or "repeat purchase rate".
---

# Cohort Analysis

**Purpose**: Compute retention curves and LTV from cohort data in a single consolidated pass — one analysis that answers both "how long do customers stay?" and "how much are they worth?"
**Prerequisite**: The `smartmodel-protocol` skill must be loaded.

---

## When This Skill Activates

- User asks about customer retention or churn
- User asks about LTV, CAC payback, or LTV:CAC ratio
- User asks how long customers typically stay or what their repeat purchase rate is
- User wants to understand cohort-level performance trends

---

## Phase 1 — Orient and Locate Cohort Data

**Step 1.1 — Read model identity**
Call `read_smartmodel_settings` → capture `settings.companyName`, `settings.currency`, `settings.historicalStartDate`.

**Step 1.2 — Locate cohort data source**
Call `read_smartmodel_index` → look for:
- R- sheets prefixed with cohort, retention, subscriber, or customer data
- Schedule sheets with dimension registries listing cohort months or customer acquisition periods

**Step 1.3 — Check R- sheet population**
Call `read_r_sheet` on any relevant R- sheets → check if cohort data is populated (rows beyond headers). If empty, note this and ask if the user can provide cohort data or if it needs to be derived from order-level data in another R- sheet.

**Step 1.4 — Read time context**
Call `read_smartmodel_date_spine` → determine how many cohort months are available. Cohort analysis needs a minimum of 6 months of data for meaningful curves; 12+ months preferred.

---

## Phase 2 — Gather Data

Depending on what's available in the model:

**Path A — Cohort sheet exists**
Call `read_smartmodel_data_section` on the cohort/subscription sheet. Look for:
- Active subscribers or customers by cohort month (rows = cohort, columns = months since acquisition)
- Revenue by cohort month
- CAC by cohort

**Path B — Derive from order data**
Call `read_r_sheet` on the orders R- sheet → extract customer IDs, acquisition dates, and order dates. Group by acquisition month to form cohorts. This requires in-prompt computation — note the approach to the user.

**Path C — No cohort data available**
If neither path yields data, report: "Cohort analysis requires order-level or cohort-level data. Available R- sheets are [list]. To proceed, please populate the [sheet name] with cohort data or connect an order history data source." Stop and provide guidance.

---

## Phase 3 — Compute

### Retention curves

For each acquisition cohort (month M0):
```
Retention Rate at Month N = Active Customers in Month N / Customers Acquired in Month M0
```

Compute for each cohort month (M1, M2, M3, ..., M12+).

### Blended retention rates

Average retention across all cohorts at each cohort month to produce a blended retention curve:
```
Blended Retention at Month N = Average(Cohort Retention at Month N) across all cohorts with N months of data
```

### LTV (cumulative revenue per acquired customer)

```
Monthly Revenue per Customer (Month N) = Cohort Revenue in Month N / Customers Acquired in M0
Cumulative LTV at Month N = Sum of Monthly Revenue per Customer from M0 to MN
```

### CAC payback period

```
CAC Payback (months) = CAC / (Average Monthly Revenue per Customer × Gross Margin %)
```

Find the cohort month N where Cumulative LTV × Gross Margin % = CAC.

### LTV:CAC ratio (at 12 months and 24 months)

```
LTV:CAC (12-month) = Cumulative LTV at M12 × Gross Margin % / CAC
```

Benchmarks for CPG DTC:
- LTV:CAC < 1x: Unprofitable acquisition, unsustainable
- LTV:CAC 1–2x: Marginal, needs improvement
- LTV:CAC 2–3x: Healthy
- LTV:CAC > 3x: Strong — scale acquisition

---

## Phase 4 — Output

### Default output

1. **Headline**: "Customers acquired in [period] have [X]% 12-month retention and [Y] LTV:CAC ratio."
2. **Retention curve table**: Cohorts as rows, months 1–12+ as columns, retention % in each cell
3. **Blended retention curve**: Single row showing average retention at each month
4. **LTV buildup**: Cumulative LTV by cohort month with CAC payback month highlighted
5. **CAC payback**: "Average cohort pays back CAC in [N] months"
6. **LTV:CAC summary**: At 12 months and 24 months vs. benchmark
7. **Cohort trend**: Are newer cohorts retaining better or worse than older cohorts?
8. **Recommendations**: Specific actions based on where the retention curve drops most sharply

### Excel output (if requested)

Call `create_sheet` with blue tab. Call `write_range` for the cohort retention grid and LTV buildup table. Call `conditional_format_range` with a color scale (green = high retention, red = low retention) on the cohort grid to create a heatmap-style view. Call `create_chart` (Line chart) for the blended retention curve.

---

## Guardrails

- Never write to Actual columns
- If fewer than 6 cohort months of data are available, note the limitation and caveat the retention curve — curves with <6 data points are unreliable
- Do not fabricate retention assumptions — if data is missing, report what's available and ask for the rest
- Confirm with user before writing output to the workbook

---

## Common Mistakes to Avoid

1. Don't report LTV without anchoring it to a gross margin assumption — gross LTV is misleading
2. Don't compare LTV:CAC across channels without noting that CAC and retention differ structurally by channel (DTC vs. Amazon vs. subscription)
3. Don't average cohort retention if cohort sizes are wildly different — weight by cohort size
4. Don't use a single cohort to represent the business — blended curves across multiple cohorts are more reliable
5. Don't ignore cohort trend direction — stable 30% retention is different from declining from 40% to 30%

---

## Integration with Other Skills

- **`/margin_analysis`**: LTV:CAC requires gross margin — run margin analysis first
- **`/marketing_efficiency_analysis`**: CAC is the other half of the LTV:CAC equation
- **`/variance_analysis`**: Check if retention changes are a recent variance from historical trend
- **`/build_report`**: Package cohort analysis for an investor or board presentation
