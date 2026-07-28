# Report Creation Guide

How to construct a multi-section report. A report is a structured
deliverable that answers a recurring business question (monthly review,
sales deep-dive, P&L summary, cohort health, AvF) — not a one-shot
visualization.

For single-chart output, see `artifact-style-guide.md`. For visual tokens,
chart-type selection, and number formatting, follow the artifact style
guide as well — this file extends it, it does not replace it.

---

## When the answer is a report

A report is warranted when **any** of these is true:

- The user asks for a "review," "dashboard," "summary," "monthly," "deep
  dive," "deck," "overview," or names a recurring artifact ("the sales
  report," "the P&L," "the cohort report").
- The question requires ≥3 distinct views to answer responsibly
  (e.g. a KPI strip + a trend + a breakdown).
- The user names a time window without a specific question ("how did we do
  in March," "Q1 review," "last month").
- A previous answer is being expanded ("now break that down by channel and
  show the trend") — the cumulative output now has report shape; promote it.

A single-question ask with one dimension is **not** a report. Return text +
SQL, or one artifact. Don't pad a small question into a long deliverable.

---

## Anatomy

A report has these sections, in this order. Every section is optional
except title and source-context line — include a section only when the
data justifies it.

1. **Title + lockup** — render via the `ArtifactHeader` component (see
   `artifact-style-guide.md` § "Brand lockup"). Title is
   `<noun> · <period>` — e.g. "Monthly Business Review · Mar 2026", "DTC
   Sales · Last 12 Months". The complete Drivepoint lockup anchors the
   top-left, with an optional customer co-brand and meta line beside it.
   The title and source-context line sit below the header hairline.
2. **Source-context line** — one sentence with the date range, plan name
   (if SmartModel data is used), channel / segment filter, currency, and
   the last booked month if any actuals are involved. Same content as the
   subtitle requirement in `system-prompt.md` §"Response style", just
   surfaced once at the top of the report instead of per-answer.
3. **TL;DR** — at most two lines. State the headline number and the single
   most material movement. Omit if nothing is materially different from
   the prior period. Do not write a TL;DR that says "performance was
   mixed."
4. **KPI strip** — 3–5 cards across. Each card: label, value, period
   sub-label, and (only if comparison is unambiguous) a delta vs. prior
   period. See §"Comparisons" before adding a delta.
5. **Primary trend** — one chart, the most-asked-about series over the
   report's period. Usually monthly. Area for a single series, line for
   2–4 series, stacked bar for composition over time.
6. **Breakdowns** — one chart per dimension that materially changes the
   story (channel, segment, customer type, product category, geo). One
   dimension per chart — do not pre-pivot two dimensions into one.
7. **Supporting table** — the underlying numbers for the breakdowns,
   right-aligned, `tabular-nums`, sortable rows. Include the totals row.
8. **Variance** — if a plan is in scope, one variance view (vs. forecast
   for the same plan, same period). See §"Comparisons".
9. **Footnotes** — source mart(s), last booked month for SmartModel data,
   any caveats the user should know (currency mix, casing duplicates,
   missing forecast months).

Section ordering is fixed; section presence is not. A pure sales report
will not have variance or balance-sheet sections. A pure P&L report will
not have a SKU breakdown.

---

## Source-mart routing

This is the most consequential decision in a report. Pick the wrong mart
and the numbers will be wrong or unanswerable. Default rules:

### Always ecommerce (`ecommerce_transactions_order_level` / `_line_item_level`)

- Orders, units sold, AOV
- Gross sales / discounts / returns / net sales **at daily or
  sub-monthly granularity**
- Shipping, taxes, channel fees, settlement detail
- Customer type (`new` / `returning`), customer-type segment
  (`First-Time` / `Returning`), cohort flags (`customer_type_model`,
  `days_since_first_purchase`, `purchased_order`)
- SKU, product, product category, ASIN, variant
- Geographic breakouts (`country`, `province_code`, `city`)
- Discount-code performance
- Returns analysis at SKU / channel / month grain
- Payment gateway, fulfillment channel, app provenance, referring / landing
  site
- Any "what happened this week" or "yesterday vs. last week" question —
  SmartModel does not have daily grain

### Always SmartModel (`smartmodel_actuals`, `smartmodel`, `smartmodel_actuals_vs_forecast`)

- Full P&L lines: COGS, gross profit, contribution profit, contribution
  profit after marketing, operating income, EBITDA, EBIT, net income
- Margins: gross margin %, contribution margin %, EBITDA margin %, net
  income margin % — and never sum these across months; recompute from
  numerator / denominator (see `system-prompt.md` aggregation rules and
  `sample-queries.md` §11)
- Balance sheet: cash, AR, AP, inventory (incl. in-warehouse / in-transit /
  WIP), line of credit, equity, total assets / liabilities
- Cash flow statement (note: prefix is `cashFlowStatement`, not
  `cashFlow`)
- Working capital days: DIO, DPO, DSO, cash conversion cycle — never sum;
  use the latest value or recompute
- Marketing spend, payroll, opex — aggregate only (GL-level codes are
  available under `metrics.marketingAssumptionsGl_*` and
  `metrics.opexAssumptionsGl_*`; friendly-name mapping is not yet shipped,
  so return raw codes and say so)
- Forecast vs. actual, variance, forecast accuracy — only here
- Multi-plan / scenario comparisons — only here
- Forward-looking projections — only here
- Anything that needs to tie to the customer's stated three-statement model

### Overlap zone — both marts can answer; choose by context

Gross sales, net sales, net revenue, and channel mix exist in both marts.
Pick by these tiebreakers in order:

1. **Granularity needed.** Daily / weekly / sub-monthly → ecommerce.
   Monthly with no need to split further → either; default to SmartModel
   if the report also contains P&L lines, so all numbers come from one
   source.
2. **Sub-channel detail needed.** If the report breaks revenue by SKU,
   product, customer type, geo, or discount code → ecommerce. SmartModel
   only carries the channel-level rollups.
3. **Tie-to-model required.** If the user has cited a number from the
   SmartModel UI in the same conversation, or the report includes P&L
   rollups → SmartModel, so the revenue line ties to gross profit and
   below.
4. **Recency.** SmartModel actuals end at the last booked month;
   ecommerce extends to the current day. If the report needs the latest
   week, use ecommerce and clearly mark that those days post-date the
   last close.

Never show the **same metric** sourced from both marts side-by-side in one
report. Pick one and use it everywhere in that report.

### Never available — say so and stop

`system-prompt.md` §"What you do not have" already enumerates this; the
short list: raw source systems, ad-platform spend at row grain, the GL →
account-name dictionary, inventory ops, 3PL data, anything from `prep` /
`core` dbt layers. Do not invent a section that depends on these.

---

## Section choice by data shape

Same rules as `artifact-style-guide.md` §"Chart-type selection", applied to
report sections. The non-obvious calls:

| Section purpose | Default chart |
|---|---|
| Revenue / sales over time, ≤4 series | Line |
| Revenue / sales over time, composition (subscription × customer type, channel × segment) | **Stacked bar** by month |
| Channel ranking for the report period | Horizontal bar, sorted descending |
| Cohort economics / retention | Triangle table with conditional shading + per-cohort line overlay |
| P&L summary | Side-by-side table (months as columns, metrics as rows), recomputed margins below |
| Variance vs. plan | Diverging bar (actual − forecast, signed) or two-column table with `variance` and `variance_pct` |
| Working-capital days | Latest-value KPI card; if trended, line with the actual value labels at each point |
| Balance-sheet snapshot | Two-column table (last month vs. prior comparable) — not a chart |
| Top-N SKUs / products | Horizontal bar, sorted descending, with units and net sales |
| Geographic | Table sorted by net sales descending. Never a map — the mart has no shape data. |

Always pair color with sign or label — never use color as the only encoder.

---

## Period defaults

Anchor every report's period before building it. **The anchor always
comes from a query**, never from the model's internal sense of "today"
(see `system-prompt.md` Hard rule §9). A wrong year in the anchor
corrupts every number in the report.

- **Default period for a "monthly review":** the last fully closed month.
  Compute it as `MAX(report_month) FROM smartmodel_actuals` (or
  `DATE_SUB(DATE_TRUNC(MAX(created_date), MONTH), INTERVAL 1 MONTH)` if
  no SmartModel data is in scope).
- **Default period for a "trend report":** trailing 12 months ending at
  the last closed month.
- **Default period for "QTD" / "YTD":** the open quarter / year, ending at
  the last booked month. **State the last booked month explicitly in the
  source-context line.** Period-to-date figures from SmartModel are only
  current through that boundary.
- **Default period for "this week" / "last 7 days":** ecommerce only, using
  `created_date`. Flag in the footer that these days may post-date the
  last SmartModel close.
- **Default period for a cohort report:** cohort months from
  `(last closed month - 12)` to the last closed month; intervals-since-
  first-purchase out to whatever horizon the cohort size still supports.

When the user names a period that resolves ambiguously ("last month" on
the 3rd of the month), choose the last fully closed calendar month and
state the resolution in the source-context line.

---

## Comparisons

A delta or variance only goes in the report if the comparison is
unambiguous and defensible.

- **vs. prior period (MoM / WoW):** safe for additive metrics (sales,
  orders, units, P&L dollar lines) and for a single-period percentage
  compared directly to the adjacent single-period percentage. Never
  construct a multi-period percentage by summing or averaging monthly
  percents — recompute from numerator / denominator totals.
- **vs. prior year (YoY):** safe for the same metric and same calendar
  span. Flag if the prior-year period had a known anomaly (channel not
  yet launched, currency change).
- **vs. plan (variance):** only when a plan is in scope and the variance
  comes from `smartmodel_actuals_vs_forecast` for a single `plan_id`. State
  the plan name. Do not show variance against multiple plans in one chart.
- **vs. budget / target:** if the customer's plan name implies budget
  (`*Base Case*`, `*Budget*`, `*Plan*`), say so; do not assume.

Format deltas as both absolute and percent. Use `SAFE_DIVIDE`. Render
percent deltas to one decimal. Render dollar deltas with the currency
code.

If a comparison's denominator is zero or NULL, **omit the delta from the
KPI card** — do not render "∞%" or "—%".

---

## Commentary

Default to no commentary. Charts and tables stand on their own. Add a
prose line **only when the statement is verifiable from the same data
already in the report**, and the inference is direct, not speculative.

Acceptable:

- "Net sales fell 24% MoM; DTC subscription contributed −18 of those 24
  points." (Both numbers visible in the breakdown.)
- "Gross margin declined from 41.2% to 36.8%, recomputed from gross
  profit ÷ net revenue for both months." (Recompute is shown.)

Not acceptable:

- "Performance was mixed." (Empty.)
- "The decline was likely driven by paid-media efficiency." (Speculation
  unless ad-spend efficiency is in the report and the link is computed.)
- "We recommend reducing promotional intensity." (Recommendation, not
  observation.)
- "Returns are within normal range." ("Normal" is undefined.)

When in doubt, omit the line. A clean chart with no commentary is better
than a chart with a wrong inference under it.

---

## Pre-publish cross-checks

Before rendering the report, verify each of these. If any fails, fix it
before showing the report — do not ship with a caveat.

1. **One mart per metric.** No metric appears sourced from two different
   marts in the same report.
2. **One currency per chart.** If multiple currencies are present, split
   into one chart per currency, or aggregate by currency. Never combine.
3. **One plan per variance chart.** All variance numbers in a single chart
   come from the same `plan_id`.
4. **Channel leaves don't double-count parents.** When summing
   channel-suffixed SmartModel rows, `is_leaf = TRUE` is in the filter.
5. **Percentages aren't summed.** Every margin / growth percent shown over
   multiple months is either the period's own row or recomputed from
   numerator / denominator totals — never `AVG` and never `SUM` of monthly
   percents.
6. **Last booked month is stated** if any actuals are in scope.
7. **No raw addresses.** Geographic sections aggregate to city / province /
   country.
8. **Casing duplicates surfaced.** If discovery turned up
   `incomeStatement.depreciation` AND `incomeStatement.Depreciation` with
   different values, both are shown in the footnote; neither is silently
   chosen.
9. **Numbers tie.** If the report has both a KPI strip total and a
   breakdown, the breakdown sums to the KPI value (within rounding).
   Reconcile or remove one.
10. **Brand lockup is present.** The report's first child renders the
    `ArtifactHeader` component with the complete Drivepoint lockup on the
    left.

---

## Multi-currency, multi-channel, multi-plan at report scale

Discipline that is easy to lose at report scale:

- **Currency:** if more than one currency appears, the report has either
  (a) one chart per currency stacked vertically, or (b) one chart with a
  currency facet. The source-context line lists every currency present.
- **Channel:** the source-context line names either "all channels" or the
  specific channels filtered to. If the report's primary trend is
  channel-agnostic but a breakdown is channel-specific, that is fine —
  but state it.
- **Plan:** at most one plan in scope per report. If the user asks to
  compare plans, that is a separate report shape (multi-plan variance),
  not a default monthly review.

---

## File handoff

Reports render as React artifacts following `artifact-style-guide.md` and
the templates in `example-artifacts.md`. A long report can be a single
artifact with multiple sections stacked vertically. Use the layout-pattern
rules (card grid for KPIs, chart container at 360px height, sticky-header
tables, source footer) at every section, not just the top.

If the report contains commentary, render commentary as plain prose
between sections — not inside chart tooltips, not as chart annotations.
