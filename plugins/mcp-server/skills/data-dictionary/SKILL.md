---
name: data-dictionary
description: The generic contract for a Drivepoint customer's BigQuery mart - the ecommerce order-level and line-item-level tables, the smartmodel, smartmodel_actuals and smartmodel_actuals_vs_forecast marts, their grain and materialization, the metric taxonomy and domain prefixes, the canonical income statement, balance sheet and cash flow rollups, and the footguns hit every session. Read before any analytical query, when choosing which mart answers a question, when resolving a metric_id, and when a query scans more bytes or fans out to more rows than expected.
---

# Drivepoint Data Dictionary

Generic contract for `{{env_prefix}}_dwh_mart`. Describes the shape every
Drivepoint customer's mart conforms to. Customer-specific values (the actual
`metric_id` inventory, channel set, plan names, currencies) come from
runtime discovery queries — see §"Discovery patterns".

---

## Dataset overview

Dataset: `{{env_prefix}}_dwh_mart` (in the customer's GCP project).

| Table | Grain | Materialization | Use for |
|---|---|---|---|
| `ecommerce_transactions_order_level` | 1 row per (order, transaction_type) | table | Order-level totals, channel comparisons, geo, fees |
| `ecommerce_transactions_line_item_level` | 1 row per (line_item, transaction_type) | table | SKU / product / category analysis |
| `smartmodel` | 1 row per (company, plan, tab, month, metric) | view | Forecasts, multi-plan comparisons, full model |
| `smartmodel_actuals` | 1 row per (company, month, metric) | view | Default for "how did we actually do" |
| `smartmodel_actuals_vs_forecast` | 1 row per (company, forecast plan, month, metric) | table | Budget vs. actual, variance, forecast accuracy. **Row-multiplied by # of forecast plans — always filter by `plan_id` first or queries fan out.** |

Ignore `mart_test_model` — internal pipeline check.

**Materialization matters for cost.** The three table marts above are
unpartitioned and unclustered: date filters help latency but do not reduce
bytes scanned. The two SmartModel views push predicates down to their
underlying physical tables, so `WHERE metric_id = …` /
`WHERE report_month = …` DO reduce work against them.

---

## Table: `ecommerce_transactions_order_level`

Order- and return-grain ecommerce. Source of truth for order-level totals.

| Column | Type | Notes |
|---|---|---|
| `company_id`, `company_name` | STRING | Provenance |
| `source_name`, `source_table` | STRING | Upstream pipeline identifiers |
| `channel` | STRING | Open-ended; varies per customer (Shopify, Amazon, TikTokShop, Drivepoint storefronts, etc.). Discover with `SELECT DISTINCT channel`. |
| `store` | STRING | Store name within a channel |
| `transaction_type` | STRING | `order` \| `return` |
| `order_id`, `order_name` | STRING | Order identifiers |
| `customer_id` | STRING | |
| `segment` | STRING | Customer segment |
| `customer_type` | STRING | `new` \| `returning` |
| `customer_type_model` | STRING | `Month 0` \| `Month 1+` (cohort flag) |
| `days_since_first_purchase` | INT64 | |
| `created_at` | TIMESTAMP | Raw timestamp; cross-channel TZ logic varies — ~24h drift around midnight is possible. |
| `created_date` | DATE | Upstream-truncated with channel-specific TZ logic. Prefer this for daily aggregates. |
| `fulfillment_at` | TIMESTAMP | |
| `fulfillment_date` | DATE | |
| `currency` | STRING | Per-row; can differ across rows for the same customer |
| `tags` | STRING | |
| `order_status` | STRING | |
| `fulfillment_channel` | STRING | |
| `discount_code` | STRING | |
| `app_id`, `app_name` | STRING | Shopify app provenance |
| `payment_gateway` | STRING | |
| `referring_site`, `landing_site` | STRING | |
| `units_sold` | INT64 | |
| `gross_sales` | FLOAT64 | |
| `discounts` | FLOAT64 | Stored as negative |
| `returns` | FLOAT64 | Stored as negative |
| `net_sales` | FLOAT64 | = `gross_sales + discounts + returns` |
| `shipping`, `taxes` | FLOAT64 | |
| `net_revenue` | FLOAT64 | = `net_sales + shipping + taxes` (NOT after-fees) |
| `retail_delivery_fee`, `referral_fee`, `shipping_fee`, `affiliate_ads_commission`, `affiliate_commission`, `affiliate_partner_commission`, `commission_fees`, `fulfillment_fees`, `other_fees` | FLOAT64 | Selling expenses. NULL on channels where they don't apply (e.g. `commission_fees` is Amazon-only; `retail_delivery_fee` and `affiliate_*` are TikTok-only). NULL means "not applicable," not "missing data." Never blanket-`COALESCE(..., 0)` across channels. |
| `total_fees` | FLOAT64 | Sum of the above |
| `adjustments`, `settlement_amount` | FLOAT64 | TikTok-style settlement detail |
| `city`, `province`, `province_code`, `zip`, `country`, `country_code` | STRING | Shipping geo |
| `company` | STRING | Shipping address company field |

---

## Table: `ecommerce_transactions_line_item_level`

One row per line item × transaction type. Use for product-grain analysis.

Same columns as `ecommerce_transactions_order_level`, **plus**:

| Column | Type | Notes |
|---|---|---|
| `line_item_id` | STRING | |
| `product_id` | STRING | |
| `product_category` | STRING | |
| `product_title`, `product_variant_title` | STRING | |
| `sku`, `asin` | STRING | |
| `unit_price` | FLOAT64 | |
| `transaction_date` | DATE | |
| `transaction_created_at` | TIMESTAMP | |
| `discount_type` | STRING | |
| `customer_type_segment` | STRING | `First-Time` \| `Returning` (richer than `customer_type`) |
| `purchased_order`, `purchase_order_segment` | INT64 / STRING | Purchase-order cohort flags |
| `address1`, `address2` | STRING | **PII** — see warning below |
| `integration` | STRING | |

### PII warning

The line-item table exposes `address1`, `address2`, and `zip`. The
order-level table does not. **Never echo raw addresses in responses or
artifact tables.** Aggregate to city, province, or country for any geo
analysis.

### Critical line-item footgun

On `transaction_type = 'return'` rows, every money column EXCEPT `returns`
is zeroed out. To get returns at line-item grain, **use the `returns`
column** (it's `0`, not NULL, on order rows, so `SUM(returns)` across all
rows works without a `transaction_type` filter). For everything else
(gross sales, discounts, fees), filter `transaction_type = 'order'` or use
the order-level table.

---

## Table: `smartmodel`

Long-format three-statement financial model + KPIs. All plans, all months.

Grain: one row per `(company_id, plan_id, tab_name, report_month, metric_id)`.
Currently only `tab_name = 'M - Monthly'` is ingested.

| Column | Type | Notes |
|---|---|---|
| `company_id`, `company_name` | STRING | |
| `plan_id` | STRING | Canonical plan identifier — use this in SQL filters, not `plan_name`. |
| `plan_name` | STRING | Display name (e.g. "2025 Base Case"); editable in source, not guaranteed unique. |
| `tab_name` | STRING | Currently always `'M - Monthly'` |
| `is_from_live_model` | BOOL | **Plan-level**, constant within a plan. Exactly one plan per company is TRUE (the continuously-updated source of truth). |
| `is_actual` | BOOL | **Row-level**, varies by month within a plan. In the live plan, closed months are TRUE and future months are FALSE. In a frozen forecast plan, only months that had already closed at freeze time are TRUE. |
| `report_month` | DATE | First day of month |
| `metric_id` | STRING | Dot-notation path; see metric taxonomy below |
| `metric_name` | STRING | Display name |
| `metric_levels` | ARRAY\<STRING\> | `metric_id` split on `.`. Use `SAFE_OFFSET(i)`. |
| `parent_metric_id`, `parent_metric_name` | STRING | Hierarchy linkage; null if top-level |
| `depth` | INT64 | Visual hierarchy from the sheet |
| `is_leaf` | BOOL | TRUE when no other row in the same (plan, tab, month) claims this as its parent |
| `metric_sort_order` | INT64 | Display ordering within a `(plan_id, tab_name, report_month)`. Stable within a plan, not necessarily comparable across plans. |
| `metric_format` | STRING | `currency` \| `percentage` \| `number` \| **NULL**. NULL exists for rows lacking an upstream cell format. Do not use `= 'currency'` as a hard filter without also accepting NULLs. |
| `metric_value` | FLOAT64 | The value. **Mixes unlike quantities across `metric_id`s — never sum across metrics.** **Sign is metric-dependent and not documented** (`metric_sign` is deferred). Probe `MIN/MAX(metric_value)` for a known closed month before assuming expenses are positive or negative. |
| `metric_sign`, `aggregation_method`, `metric_formula` | STRING | Currently NULL; seed-file mapping planned but not shipped. Do not use. |
| `data_source` | STRING | Provenance |

---

## Table: `smartmodel_actuals`

View over `smartmodel` filtered to `is_from_live_model = TRUE AND is_actual =
TRUE`. Historical actuals only. **Default surface for "how did we actually
do" questions.**

Grain: one row per `(company_id, report_month, metric_id)`.

Same columns as `smartmodel` minus `plan_id`, `plan_name`, `tab_name`,
`is_from_live_model`, `is_actual`.

---

## Table: `smartmodel_actuals_vs_forecast`

Live-plan actuals LEFT JOINed to each forecast plan.

Grain: one row per `(company_id, forecast plan_id, report_month, metric_id)`.

**Row-multiplied by # of forecast plans** — a customer with 5 saved plans
makes this table ~5× the row count of `smartmodel_actuals`. Always filter
by `plan_id` first.

Same columns as `smartmodel_actuals` plus:

| Column | Type | Notes |
|---|---|---|
| `plan_id`, `plan_name` | STRING | Always a forecast plan (never the live plan). Filter by `plan_id`. |
| `plan_data_type` | STRING | `actual` \| `forecast` — the **forecast plan's own** label for that month at freeze time. This does NOT tell you whether the live actuals row exists for that month — use `actual_value IS NOT NULL` for that. |
| `actual_value` | FLOAT64 | From the live plan |
| `forecast_value` | FLOAT64 | From the forecast plan; NULL if the metric/month isn't in that forecast |
| `variance` | FLOAT64 | = `actual_value - forecast_value` |
| `variance_pct` | FLOAT64 | = `SAFE_DIVIDE(variance, forecast_value)`; NULL when forecast = 0 |

---

## Metric taxonomy

Every `metric_id` is a dot-notation path. The **first segment** routes the
metric to its financial domain.

### Domain prefixes

| Prefix | Domain |
|---|---|
| `incomeStatement.*` | Income Statement / P&L |
| `balanceSheet.*` | Balance Sheet |
| `cashFlowStatement.*` | Cash Flow Statement (NOT `cashFlow`) |
| `metrics.*` | Business KPIs |

### Footguns (encounter these every session)

1. **`cashFlowStatement`, not `cashFlow`.** Models guess wrong constantly.
2. **Channel separator is inconsistent.** Both forms appear and refer to the
   same channel:
   - dot: `incomeStatement.grossSales.dtcOnline`
   - underscore: `incomeStatement.payroll_retail`,
     `incomeStatement.operatingIncome_marketplace`

   When filtering by channel, prefer
   `WHERE LOWER(metric_id) LIKE '%dtconline%'`. **When summing channel
   leaves, also require `is_leaf = TRUE`** — substring match alone scoops
   up parent rollups and double-counts.
3. **Casing duplicates can carry different values.** Both
   `incomeStatement.depreciation` and `incomeStatement.Depreciation` may
   exist with **disagreeing `metric_value`s** (both survived upstream
   dedup). When you find them, surface both back to the user — never pick
   one silently.
4. **Channel tokens** (`dtcOnline`, `marketplace`, `retail`, `wholesale`) are
   a convention, not a guarantee. Not every metric has a channel level; not
   every customer uses all four.

### Canonical Income Statement rollups (`incomeStatement.*`)

Most customers have these top-level metrics. Channel variants exist as
suffixes where applicable (`.dtcOnline`, `.marketplace`, `.retail`,
`.wholesale`, or underscore-suffix equivalents).

- `incomeStatement.grossSales` — Gross Sales
- `incomeStatement.discounts` — Discounts
- `incomeStatement.returns` — Returns
- `incomeStatement.netSales` — Net Sales
- `incomeStatement.netRevenue` — Net Revenue (incl. shipping / taxes)
- `incomeStatement.costOfGoodsSold` — COGS
- `incomeStatement.grossProfit` — Gross Profit
- `incomeStatement.contributionProfit` — Contribution Profit
- `incomeStatement.contributionProfitAfterMarketing` — Contribution Profit After Marketing
- `incomeStatement.operatingIncome` — Operating Income
- `incomeStatement.EBITDA` — EBITDA
- `incomeStatement.EBIT` — EBIT
- `incomeStatement.depreciation`, `incomeStatement.amortization`
- `incomeStatement.netIncome` — Net Income

Sub-categories that exist under the P&L (rolled up plus per-channel leaves):
variable costs, marketing spend, payroll, other operating expenses,
merchant fees.

### Canonical Balance Sheet metrics (`balanceSheet.*`)

- `balanceSheet.cash`
- `balanceSheet.accountsReceivable`
- `balanceSheet.inventory.*` (incl. `finishedGoodsInWarehouse`,
  `finishedGoodsInTransit`, `workInProgress`)
- `balanceSheet.accountsPayable`
- `balanceSheet.lineOfCredit`
- Fixed-asset categories
- `balanceSheet.totalAssets`
- `balanceSheet.totalLiabilities`
- Equity components: common stock, retained earnings, paid-in capital
- `balanceSheet.totalEquity`

### Canonical Cash Flow metrics (`cashFlowStatement.*`)

- `cashFlowStatement.netCashProvidedByOperatingActivities`
- `cashFlowStatement.netCashProvidedByInvestingActivities`
- `cashFlowStatement.netCashProvidedByFinancingActivities`
- `cashFlowStatement.capitalExpenditures`
- `cashFlowStatement.beginningOfPeriodCash`
- `cashFlowStatement.endOfPeriodCash`
- Change-in-working-capital components

### Canonical Business KPIs (`metrics.*`)

Margins (`metric_format = 'percentage'`):
- `metrics.grossMarginPercent`
- `metrics.contributionMarginPercent`
- `metrics.EBITDAMarginPercent`
- `metrics.netIncomeMarginPercent`
- `metrics.costOfGoodsSoldPercent`

Growth (`metric_format = 'percentage'`):
- `metrics.grossSalesGrowthPercent`
- `metrics.adSpendGrowthPercent`

Working capital (`metric_format = 'number'`, in days):
- `metrics.daysInventoryOutstanding`
- `metrics.daysPayableOutstanding`
- `metrics.daysSalesOutstanding`
- `metrics.cashConversionCycle`

Order / customer KPIs (channel-suffixed where applicable):
- `metrics.averageOrderValue.<channel>`
- `metrics.blendedPaidCAC.<channel>`
- New / returning / first-time / OTP / subscription order counts

**Margin denominators are customer-configurable.** Verify the formula
behind any `metrics.*MarginPercent` by reading a single closed month and
back-solving against candidate numerator / denominator pairs before
recomputing a YTD / QTD margin from underlying components.

### GL-level detail

`metrics.marketingAssumptionsGl_*` and `metrics.opexAssumptionsGl_*` expose
spend broken out by general-ledger account code (e.g. `6000`, `6020`). **The
mapping from GL code to friendly account name is known but not yet shipped
in this warehouse.** Return raw codes in answers and tell the user the
friendly-name mapping isn't yet exposed.

### Anything not listed above

Use discovery queries. The complete `metric_id` inventory varies by customer
configuration; the lists above are the universal subset.

---

## Discovery patterns

```sql
-- Find a metric by friendly-name keyword
SELECT DISTINCT metric_id, metric_name, metric_format
FROM `{{env_prefix}}_dwh_mart.smartmodel_actuals`
WHERE LOWER(metric_name) LIKE '%<keyword>%'
   OR LOWER(metric_id)   LIKE '%<keyword>%'
ORDER BY metric_id
LIMIT 50
```

```sql
-- Inventory of distinct channels (ecommerce)
SELECT DISTINCT channel
FROM `{{env_prefix}}_dwh_mart.ecommerce_transactions_order_level`
ORDER BY channel
```

```sql
-- Inventory of plans with their coverage window
SELECT plan_id,
       ANY_VALUE(plan_name)          AS plan_name,
       ANY_VALUE(is_from_live_model) AS is_live,
       MIN(report_month)             AS first_month,
       MAX(report_month)             AS last_month
FROM `{{env_prefix}}_dwh_mart.smartmodel`
GROUP BY plan_id
ORDER BY is_live DESC, plan_name
```

```sql
-- Currency inventory (ecommerce)
SELECT DISTINCT currency
FROM `{{env_prefix}}_dwh_mart.ecommerce_transactions_order_level`
WHERE currency IS NOT NULL
```

```sql
-- Last booked month for actuals (use to anchor YTD / MTD / QTD)
SELECT MAX(report_month) AS last_booked_month
FROM `{{env_prefix}}_dwh_mart.smartmodel_actuals`
```
