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
| `smartmodel_wweekly` | 1 row per (company, plan, tab, week, metric) | view | Weekly counterpart to `smartmodel`. **Only for customers with a `W - Weekly` tab — empty otherwise.** |
| `smartmodel_wweekly_actuals` | 1 row per (company, week, metric) | view | Weekly counterpart to `smartmodel_actuals`. Same per-customer caveat. |
| `smartmodel_wweekly_actuals_vs_forecast` | 1 row per (company, forecast plan, week, metric) | table | Weekly counterpart to `smartmodel_actuals_vs_forecast`. Same per-customer caveat + **row-multiplied by # of forecast plans**. |

| `financials_general_ledger` | 1 row per (company, account, class, dimension, period) | table | Full GL with Drivepoint mapping fields. Source of truth for period-level accounting detail. |
| `financials_income_statement` | 1 row per (company, account, class, dimension, period) | table | P&L filtered from the GL (`financial_statement = 'income_statement'`). Primary value: `period_net_change`. |
| `financials_balance_sheet` | 1 row per (company, account, class, dimension, period) | table | Balance sheet filtered from the GL (`financial_statement = 'balance_sheet'`). Primary value: `period_ending_balance`. |
| `financials_chart_of_accounts` | 1 row per (company, account) | table | Account dimension table. No period dimension. Hierarchy, class, type, sub-type. |
| `financials_mapping_coverage` | 1 row per (company, financial_statement) | table | Mapping audit. Account-count and value-weighted coverage rates. |
| `financials_invoices` | 1 row per invoice | table | QuickBooks AR invoice headers with aging. **QB customers only.** |
| `financials_invoice_lines` | 1 row per (invoice, line) | table | QB invoice line items with parsed account-number family and revenue-line flag. **QB customers only.** |
| `financials_bills` | 1 row per bill | table | QB AP bills with vendor name and aging. **QB customers only.** |
| `financials_payments` | 1 row per payment | table | QB payment records. **QB customers only.** |
| `financials_purchases` | 1 row per purchase | table | QB purchase transactions with vendor name. **QB customers only.** |
| `financials_journal_entries` | 1 row per journal entry | table | QB manual journal entries with nested line items. **QB customers only.** |
| `financials_vendors` | 1 row per vendor | table | QB vendor master. **QB customers only.** |
| `financials_items` | 1 row per item | table | QB item/product master. **QB customers only.** |
| `financials_transactions` | 1 row per transaction line | table | Transaction-level drill-down with Drivepoint mappings. **QB customers only.** |

Ignore `mart_test_model` — internal pipeline check.

**Weekly is per-tenant optional.** The `W - Weekly` worksheet exists only for
some customers, so the three `smartmodel_wweekly*` views return rows only for
those tenants and are **empty (but still queryable) for everyone else**. Only
reach for them on explicitly week-level or intra-month questions; default to
the monthly tables otherwise. See §"Weekly SmartModel" below.

**Financials marts (fourth domain).** Fourteen `financials_*` tables in this same
dataset expose the ERP general ledger, Drivepoint mapping status, and
QuickBooks sub-ledger detail. The GL tables (`financials_general_ledger`,
`financials_income_statement`, `financials_balance_sheet`,
`financials_chart_of_accounts`, `financials_mapping_coverage`) are populated for
every customer with a financial data connection. The ten QuickBooks-specific
tables (`financials_invoices`, `financials_invoice_lines`, `financials_bills`,
`financials_payments`, `financials_purchases`, `financials_journal_entries`,
`financials_vendors`, `financials_items`, `financials_transactions`) exist for
every tenant but are **empty for non-QB customers** (NetSuite, Xero, etc.).
Full schema in the "Financials domain" section at the bottom of this document.

**Retail marts (third domain).** Brands with a retail data feed (Alloy / Muffin)
also have ten `retail_*` marts in this same dataset — POS sell-through,
inventory/distribution snapshots, and shipments, at retailer and store grain,
weekly and monthly. They are empty for brands with no retail feed. Full schema
in the "Retail domain" section at the bottom of this document.

**Materialization matters for cost.** The table-materialized marts above
(both ecommerce tables and the two `*_actuals_vs_forecast` tables) are
unpartitioned and unclustered: date filters help latency but do not reduce
bytes scanned. The SmartModel views (monthly and weekly) push predicates down
to their underlying physical tables, so `WHERE metric_id = …` /
`WHERE report_month = …` (or `report_week`) DO reduce work against them.

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
Only `tab_name = 'M - Monthly'` is ingested here. The separate `W - Weekly`
worksheet — when a customer has one — lands in the `smartmodel_wweekly*` views,
not this table (see §"Weekly SmartModel").

| Column | Type | Notes |
|---|---|---|
| `company_id`, `company_name` | STRING | |
| `plan_id` | STRING | Canonical plan identifier — use this in SQL filters, not `plan_name`. |
| `plan_name` | STRING | Display name (e.g. "2025 Base Case"); editable in source, not guaranteed unique. |
| `tab_name` | STRING | Always `'M - Monthly'` in this table (weekly lives in `smartmodel_wweekly*`) |
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

## Weekly SmartModel (`W - Weekly`)

Some customers maintain a `W - Weekly` worksheet alongside the monthly model.
When they do, it is synced to three views that **mirror the monthly SmartModel
tables one-for-one**, keyed on the week instead of the month:

| Weekly view | Mirrors | Materialization |
|---|---|---|
| `smartmodel_wweekly` | `smartmodel` | view |
| `smartmodel_wweekly_actuals` | `smartmodel_actuals` | view |
| `smartmodel_wweekly_actuals_vs_forecast` | `smartmodel_actuals_vs_forecast` | table |

**Only difference from their monthly counterparts:**

- `report_week` (DATE, the **beginning-of-week / week-starting** date) replaces
  `report_month`. There is no `report_month` column on the weekly views.
- `tab_name` is `'W - Weekly'` (on `smartmodel_wweekly`).

Everything else is identical: same column names, same `is_from_live_model` /
`is_actual` semantics, same `metric_id` taxonomy and footguns, same
`smartmodel_wweekly_actuals` = live-model actual rows, same
`smartmodel_wweekly_actuals_vs_forecast` row-multiplication by forecast plan
(**always filter by `plan_id` first**).

**When to use them:**

- Only for **explicitly week-level or intra-month** questions ("last 8 weeks
  of net sales," "which week did we cross X"). For everything monthly, use the
  monthly tables — they exist for every customer and are the default surface.
- These views **compile for every tenant but return zero rows** when the
  customer has no `W - Weekly` tab. A weekly query coming back empty usually
  means the customer doesn't have the tab, not that the metric is missing —
  fall back to the monthly tables and say so.
- Weekly actuals extend only as far as the customer keeps the weekly tab
  current; anchor with `SELECT MAX(report_week) FROM smartmodel_wweekly_actuals`
  the same way you anchor the monthly grain with `MAX(report_month)`.

```sql
-- Does this customer have weekly SmartModel data?
SELECT COUNT(*) AS weekly_rows,
       MAX(report_week) AS last_week
FROM `{{env_prefix}}_dwh_mart.smartmodel_wweekly_actuals`
```

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

---

## Retail domain

A third mart family (alongside ecommerce and SmartModel), present for brands
with a retail data connection (Alloy and/or Muffin). Same dataset,
`{{env_prefix}}_dwh_mart`. Covers point-of-sale sell-through, on-shelf
inventory/distribution, and shipments into the retail channel — the
physical-retail counterpart to the ecommerce tables.

**Only populated for brands with a retail feed.** dbt builds all ten tables for
every tenant, but they are empty for brands with no Alloy/Muffin connection.
Even within a retail brand a table can be empty when that brand lacks that
source's grain (see footgun 2). Probe with a `COUNT(*)` and
`SELECT DISTINCT source_name` before assuming a retail table has data.

### Tables

Three families × {retailer, location} grain × {week, month} period. The weekly
tables are the primary surface.

| Table | Grain | Use for |
|---|---|---|
| `retail_pos_sales_retailer_week` | source × retailer × product × week (Sat week-ending) | Sell-through by retailer/week. Muffin + Alloy. |
| `retail_pos_sales_location_week` | source × retailer × location × product × week | Store-level sell-through. **Muffin only.** |
| `retail_pos_sales_retailer_month` | source × retailer × product × calendar month | Monthly sell-through by retailer. Muffin + Alloy. |
| `retail_pos_sales_location_month` | source × retailer × location × product × month | Store-level monthly sell-through. **Muffin only.** |
| `retail_inventory_snapshot_retailer_week` | source × retailer × product × week | On-hand + distribution/OOS by retailer/week. Muffin + Alloy. |
| `retail_inventory_snapshot_location_week` | source × retailer × location × product × week | Store-level on-hand + in-stock. **Muffin only.** |
| `retail_inventory_snapshot_retailer_month` | source × retailer × product × month | Monthly on-hand + distribution. Muffin + Alloy. |
| `retail_inventory_snapshot_location_month` | source × retailer × location × product × month | Store-level monthly on-hand. **Muffin only.** |
| `retail_shipments_week` | source × shipment_type × ship_from × ship_to × product × week | Shipments into retail (distributor→store + inbound receipts). |
| `retail_shipments_month` | source × shipment_type × ship_from × ship_to × product × month | Monthly shipments. |

Each table's uniqueness key IS its grain — exact column tuples in "Grain keys"
below. `alloy_sales_by_product_and_partner` also lives in this dataset; it is a
legacy Alloy rollup superseded by `retail_pos_sales_retailer_*` — prefer the
retail marts.

### Cost & materialization (differs from the other two domains)

Unlike the ecommerce and SmartModel marts, the **weekly** retail tables ARE
partitioned (by `retail_week_ending_date`, DAY) and clustered (by
`source_name, retailer_id`). So `WHERE retail_week_ending_date >= …` and
`WHERE source_name = …` / `retailer_id = …` genuinely reduce bytes scanned —
use them. The **monthly** tables are not partitioned or clustered; filter for
latency but it will not cut bytes.

### Shared columns (every retail mart)

| Column | Type | Notes |
|---|---|---|
| `company_id`, `company_name` | STRING | Provenance |
| `source_name` | STRING | `muffin` \| `alloy` — the retail feed the row came from. See footgun 1. |
| `source_table`, `data_source` | STRING | Upstream identifiers |
| `source_reporting_grain` | STRING | `day` \| `week` \| `month` — granularity of the source row before rollup |
| `retailer_id`, `retailer_name`, `parent_retailer` | STRING | Retailer / banner. `parent_retailer` groups banners (e.g. all Walmart formats). |
| `reporting_channel` | STRING | Retail reporting channel |
| `product_id`, `retailer_product_id`, `product_name`, `upc`, `gtin_14`, `sku` | STRING | Product identity. `sku` is absent on the location-grain tables. |
| `retail_week_ending_date` *(week)* / `retail_month_end_date` *(month)* | DATE | Period end. Week-ending is always a Saturday; month-end is always `LAST_DAY`. |
| `source_updated_at`, `latest_source_date`, `data_complete_through_date` | TIMESTAMP / DATE | Freshness. Use `data_complete_through_date` — not `MAX(retail_week_ending_date)` — to state "data through". |
| `days_observed` | INT64 | Distinct source dates rolled into this period bucket |
| `nrf_fiscal_year`, `nrf_quarter`, `nrf_period` | INT64 | Conformed NRF 4-5-4 calendar (week and month tables) |
| `calendar_year`, `calendar_month`, `calendar_quarter` | INT64 | Gregorian calendar dims |
| `walmart_*`, `iso_*`, `walmart_week_alignable` | — | **Week tables only.** Walmart (Sat-Fri) and ISO week conformance. Absent on month tables — months do not align to retail-week boundaries. |

Location-grain tables additionally carry store descriptors: `location_id`,
`location_name`, `location_type`, `location_status_source`, `address`, `city`,
`state`, `postal_code`, `country`, `latitude`, `longitude`.

### POS-sales measures (`retail_pos_sales_*`)

Additive sell-through. Retailer grain carries the full set: `units_sold`,
`units_sold_gross`, `pos_scan_units`, `gross_sales`, `net_sales`; regular /
promo / clearance splits (`{regular,promo,clearance}_{units,sales}`); returns
(`returns_units`, `returns_sales`, `returns_cost_dollars`); margin / COGS
(`gross_margin_dollars` + regular/promo/clearance variants, `cogs_net_dollars`,
`cogs_gross_dollars`, `cogs_from_sales_dollars`, and regular/promo/clearance
COGS). All additive within the table's grain.

`forecast_*` columns (`forecast_inbound_ordered_units`,
`forecast_inbound_received_units`, `forecast_sales_units_net`,
`forecast_store_sales_units_net`) are **Alloy-native forecasts** — keep them
segregated, never sum them into the actuals measures.

Location tables carry a thinner measure set (`units_sold`, `pos_scan_units`,
`gross_sales`, `net_sales`, `regular_units`); the promo/clearance/COGS/forecast
splits are retailer-grain only.

### Inventory-snapshot measures (`retail_inventory_snapshot_*`)

Snapshot (point-in-time, **NOT additive over time**). `inventory_as_of_date` is
the day the snapshot was actually picked (≤ the period end).

Retailer grain carries the rich set: `on_hand_units`, `on_hand_dollars`,
`on_hand_cost_dollars`, `regular_on_hand_*`; pipeline `on_order_*`,
`in_transit_*`; distribution / OOS store counts `stores_carrying`,
`stores_in_stock`, `stores_carrying_target`, `stores_in_stock_target`,
`stores_observed`, `stores_oos`, `stores_below_presmin`, `stores_selling`,
`stores_active`; `presentation_units`, `presentation_minimum_units`; and
`source_in_stock_pct`. `days_observed` counts snapshot dates in the period.

Location grain is intentionally thin: `on_hand_units`, `was_in_stock` (BOOL),
`days_observed`, `days_in_stock`.

- **`on_hand_*` and `stores_*` are point-in-time — never SUM across periods.**
  Take the latest, or average deliberately. They ARE additive across products /
  retailers within one period.
- **`source_in_stock_pct` is an Alloy-native ratio for traceability only —
  never SUM or AVG it** across weeks, retailers, or products. Recompute in-stock
  rate as `stores_in_stock / stores_carrying` when you need an aggregate.

### Shipments measures (`retail_shipments_*`)

`shipment_type` splits the table into `distributor_to_store` (Muffin) and
`inbound_received` (Alloy) — different physical flows; filter to one before
analysis. Ship nodes: `ship_from_id`, `ship_to_id` plus `ship_to_*` location
descriptors. Measures (additive): `ordered_units`, `ordered_cases`,
`shipped_units`, `shipped_cases`, `shipped_gross_dollars`, `shipped_net_dollars`,
`received_units`, `received_dollars`, `received_cost_dollars`.

### Retail footguns

1. **`source_name` is `muffin` or `alloy`, and they are different lenses.**
   Muffin = store-level POS / distributor detail (has `location_id`); Alloy =
   retailer-level syndicated data (no store grain) plus forecasts, pipeline, and
   distribution / OOS. A retailer-grain table can hold BOTH sources for the same
   retailer/week — **filter by `source_name` (or aggregate deliberately) so you
   do not double-count sell-through across the two feeds.**
2. **Source × grain coverage.** Location-grain tables are **Muffin-only** (Alloy
   has no store column) and are empty for an Alloy-only brand. Retailer-grain
   tables carry both. `forecast_*`, `stores_*`, `on_order_*`, `in_transit_*`, and
   `source_in_stock_pct` are Alloy-native — NULL / absent on Muffin rows.
3. **`walmart_week_alignable`** is TRUE only for day-sourced (Muffin) rows.
   Alloy weekly rows are Saturday-boundary snapshots that cannot be re-bucketed
   into Walmart Sat-Fri weeks (FALSE). Only roll into Walmart fiscal weeks where
   this flag is TRUE.
4. **Week vs month are separate tables, not a rollup you do yourself.** The month
   tables are calendar-month grouped (Alloy month rows are its native monthly
   feed, NOT re-bucketed from weeks). Query the month table rather than SUMming
   weeks across the muffin/alloy seam.
5. **State "data through" from `data_complete_through_date`**, not the max period
   date — a partially-loaded latest week/month is still present in the table.
6. **Snapshots vs flows.** POS sales and shipments are additive flows; inventory
   is a snapshot — never SUM inventory over time.

### Grain keys (uniqueness tuple per table)

- `retail_pos_sales_retailer_{week,month}`: `source_name, company_id, retailer_id, product_id, retail_{week_ending,month_end}_date`
- `retail_pos_sales_location_{week,month}`: the above **+ `location_id`**
- `retail_inventory_snapshot_retailer_{week,month}`: `source_name, company_id, retailer_id, product_id, retail_{…}_date`
- `retail_inventory_snapshot_location_{week,month}`: the above **+ `location_id`**
- `retail_shipments_{week,month}`: `source_name, company_id, shipment_type, retailer_id, ship_from_id, ship_to_id, product_id, retail_{…}_date`

### Retail discovery patterns

```sql
-- Which retail sources / retailers does this brand have, and how fresh?
SELECT source_name, retailer_id, retailer_name,
       COUNT(*)                        AS rows,
       MAX(data_complete_through_date) AS data_through
FROM `{{env_prefix}}_dwh_mart.retail_pos_sales_retailer_week`
GROUP BY 1, 2, 3
ORDER BY 1, 2
```

```sql
-- Weekly sell-through for one retailer (partition + cluster pruned)
SELECT retail_week_ending_date,
       SUM(units_sold)  AS units,
       SUM(gross_sales) AS gross_sales
FROM `{{env_prefix}}_dwh_mart.retail_pos_sales_retailer_week`
WHERE source_name = 'muffin'                    -- pick one feed; avoid double-counting alloy
  AND retailer_id = '<retailer_id>'
  AND retail_week_ending_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 26 WEEK)
GROUP BY 1
ORDER BY 1
```

```sql
-- Latest on-shelf distribution / OOS by retailer (snapshot — take the latest week)
SELECT retailer_id, retailer_name,
       SUM(stores_carrying) AS stores_carrying,
       SUM(stores_in_stock) AS stores_in_stock,
       SAFE_DIVIDE(SUM(stores_in_stock), SUM(stores_carrying)) AS in_stock_rate
FROM `{{env_prefix}}_dwh_mart.retail_inventory_snapshot_retailer_week`
WHERE source_name = 'alloy'
  AND retail_week_ending_date = (
    SELECT MAX(retail_week_ending_date)
    FROM `{{env_prefix}}_dwh_mart.retail_inventory_snapshot_retailer_week`
    WHERE source_name = 'alloy')
GROUP BY 1, 2
ORDER BY in_stock_rate
```

---

## Financials domain

A fourth mart family exposing ERP general-ledger data and QuickBooks
sub-ledger detail. Same dataset, `{{env_prefix}}_dwh_mart`. All fourteen
tables exist for every tenant. The five GL tables are populated for any
customer with a financial data connection (QuickBooks, NetSuite, Xero). The
nine QuickBooks-specific tables are **empty (but queryable) for non-QB
customers**.

### GL tables (always populated)

Five tables built from the Drivepoint financial mapping pipeline.

| Table | Grain | Use for |
|---|---|---|
| `financials_general_ledger` | (company, account, class, dimension1, period) | Full GL with Drivepoint v2 mapping fields. Every GL line carries its category, sign adjustment, and mapping status. |
| `financials_income_statement` | (company, account, class, dimension1, period) | P&L only. Pre-filtered to `financial_statement = 'income_statement'`. Primary value: `period_net_change`. |
| `financials_balance_sheet` | (company, account, class, dimension1, period) | Balance sheet only. Pre-filtered to `financial_statement = 'balance_sheet'`. Primary value: `period_ending_balance`. |
| `financials_chart_of_accounts` | (company, account) | Account dimension. No period axis. Use for lookups, hierarchy navigation, filtering. |
| `financials_mapping_coverage` | (company, financial_statement) | Mapping audit. Account-count coverage and value-weighted coverage rates (0 to 1). |

### QuickBooks sub-ledger tables (QB customers only)

Nine tables sourced from QuickBooks via Airbyte. Deduplicated to the latest
extract per entity ID.

| Table | Grain | Use for |
|---|---|---|
| `financials_invoices` | 1 row per invoice | AR invoice headers with aging (is_open, days_past_due). |
| `financials_invoice_lines` | (invoice, line) | Invoice line items with parsed account_number, account_number_family, and is_revenue_line flag. |
| `financials_bills` | 1 row per bill | AP bills with vendor name and aging. |
| `financials_payments` | 1 row per payment | Payment records with customer and method. |
| `financials_purchases` | 1 row per purchase | Purchase transactions with vendor name, payment_type. |
| `financials_journal_entries` | 1 row per journal entry | Manual journal entries with nested line_items JSON. |
| `financials_vendors` | 1 row per vendor | Vendor master with name, balance, 1099 status. |
| `financials_items` | 1 row per item | Item/product master with income/expense/asset account links. |
| `financials_transactions` | 1 row per transaction line | Transaction-level drill-down joined to Drivepoint mappings. |

### Table: `financials_general_ledger`

The core financials table. LEFT JOINs the canonical GL to the v2 financial
mapping output so every GL line carries its Drivepoint category, sign
adjustment, and mapping status.

| Column | Type | Notes |
|---|---|---|
| `company_id`, `company_name` | STRING | Provenance |
| `account_id` | STRING | GL account identifier from the ERP |
| `account_name` | STRING | GL account name |
| `account_number` | STRING | GL account number |
| `full_account_name` | STRING | Full account name including parent path |
| `fully_qualified_name` | STRING | Fully qualified account name from the ERP |
| `parent_account_name` | STRING | Immediate parent account name |
| `category_account_name` | STRING | Category-level parent |
| `grand_parent_account_name` | STRING | Top-level parent |
| `account_class` | STRING | Asset, Liability, Equity, Revenue, or Expense |
| `account_type` | STRING | Type within class (e.g., Cost of Goods Sold, Other Current Asset) |
| `account_sub_type` | STRING | Sub-type |
| `account_transaction_type` | STRING | Credit or Debit |
| `financial_statement` | STRING | `income_statement` \| `balance_sheet` |
| `is_sub_account` | BOOL | Whether this is a sub-account |
| `period_first_day`, `period_last_day` | DATE | Accounting period boundaries |
| `period_net_change` | FLOAT64 | Net change during the period (raw ERP sign) |
| `period_beginning_balance` | FLOAT64 | Balance at period open |
| `period_ending_balance` | FLOAT64 | Balance at period close |
| `class` | STRING | QuickBooks class or NetSuite classification |
| `dimension1`, `dimension2`, `dimension3` | STRING | Custom dimensions (department, location, etc.) |
| `currency` | STRING | Transaction currency |
| `channel`, `vertical`, `stores` | STRING | Tags if present |
| `drivepoint_category_id` | STRING | Drivepoint v2 category ID. NULL if unmapped. |
| `drivepoint_category_name` | STRING | Human-readable Drivepoint category name. NULL if unmapped. |
| `drivepoint_type` | STRING | Category type (e.g., revenue, cogs, opex). NULL if unmapped. |
| `drivepoint_statement_type` | STRING | `income_statement` \| `balance_sheet`. NULL if unmapped. |
| `sign_convention` | STRING | `Revenue`, `Expense`, or `BalanceSheet`. NULL if unmapped. |
| `is_mapped` | BOOL | Whether this GL line has a Drivepoint v2 mapping |

### Table: `financials_income_statement`

Filtered subset of `financials_general_ledger` where
`financial_statement = 'income_statement'`. Same columns except
`financial_statement`, `account_transaction_type`, `is_sub_account`,
`period_beginning_balance`, `period_ending_balance` are dropped. Primary
value column is `period_net_change`.

### Table: `financials_balance_sheet`

Filtered subset of `financials_general_ledger` where
`financial_statement = 'balance_sheet'`. Same column set as
`financials_income_statement`. Primary value columns are
`period_ending_balance` and `period_beginning_balance` (both present here);
`period_net_change` is also available.

### Table: `financials_chart_of_accounts`

Account dimension table. One row per (company, account). No period axis.
Picks the latest period's metadata via `ROW_NUMBER() OVER (PARTITION BY
company_id, account_id ORDER BY period_last_day DESC)`.

Same account-descriptor columns as the general ledger (`account_id`,
`account_name`, `account_number`, `full_account_name`,
`fully_qualified_name`, `parent_account_name`, `category_account_name`,
`grand_parent_account_name`, `account_class`, `account_type`,
`account_sub_type`, `account_transaction_type`, `financial_statement`,
`is_sub_account`, `currency`).

### Table: `financials_mapping_coverage`

Mapping audit aggregated by company and financial statement.

| Column | Type | Notes |
|---|---|---|
| `company_id`, `company_name` | STRING | Provenance |
| `financial_statement` | STRING | `income_statement` \| `balance_sheet` |
| `total_account_periods`, `mapped_account_periods`, `unmapped_account_periods` | INT64 | Account-period counts |
| `mapping_coverage_rate` | FLOAT64 | Fraction of account-periods mapped (0 to 1) |
| `total_accounts`, `mapped_accounts`, `unmapped_accounts` | INT64 | Distinct account counts |
| `total_absolute_value`, `mapped_absolute_value`, `unmapped_absolute_value` | FLOAT64 | Value-weighted amounts |
| `value_coverage_rate` | FLOAT64 | Fraction of absolute value covered by mapped accounts (0 to 1). More meaningful than account count for assessing completeness. |

### Table: `financials_invoices`

QuickBooks AR invoice headers with computed aging fields.

| Column | Type | Notes |
|---|---|---|
| `invoice_id` | STRING | QuickBooks invoice ID |
| `transaction_date`, `due_date` | DATE | Invoice and due dates |
| `total_amount`, `balance`, `deposit` | FLOAT64 | Amounts |
| `doc_number` | STRING | Invoice document number |
| `customer_id`, `customer_name` | STRING | Customer |
| `currency` | STRING | Invoice currency |
| `exchange_rate` | FLOAT64 | FX rate |
| `home_total_amount` | FLOAT64 | Amount in home currency |
| `sales_term_id`, `sales_term_name` | STRING | Payment terms |
| `email_status`, `print_status` | STRING | Send status |
| `memo` | STRING | Private note |
| `is_open` | BOOL | TRUE when balance > 0 |
| `days_past_due` | INT64 | Days past due. NULL if not overdue or fully paid. |

### Table: `financials_invoice_lines`

Invoice line items. Explodes each invoice's Line JSON into one row per
economic line (sales items, discounts, allowances). SubTotal lines are
excluded so line amounts foot to the invoice total.

| Column | Type | Notes |
|---|---|---|
| `invoice_id` | STRING | Joins to `financials_invoices` |
| `doc_number` | STRING | Invoice document number |
| `transaction_date` | DATE | Invoice date |
| `customer_id`, `customer_name` | STRING | Customer (denormalized from header) |
| `currency` | STRING | Invoice currency |
| `line_id` | STRING | Line ID within the invoice |
| `line_num` | INT64 | Line sequence |
| `detail_type` | STRING | e.g. SalesItemLineDetail, DescriptionOnly |
| `item_id`, `item_name` | STRING | Product/item |
| `account_id`, `account_name` | STRING | GL account the line posts to (colon-separated hierarchy) |
| `tax_code` | STRING | e.g. TAX, NON |
| `quantity` | FLOAT64 | Units vary by item (cases vs eaches) |
| `unit_price` | FLOAT64 | Line unit price |
| `amount` | FLOAT64 | Line amount, signed as booked |
| `account_number` | STRING | Parsed from the leading alphanumeric prefix of `account_name` (e.g. `41310N`) |
| `account_number_family` | STRING | First digit of `account_number`. Groups into families: 4 = revenue, 5 = COGS, 6-9 = expenses, 1-3 = balance sheet. |
| `is_revenue_line` | BOOL | TRUE when the line posts to a 41xxx sales account |

### Table: `financials_bills`

QuickBooks AP bills with vendor name and computed aging fields.

| Column | Type | Notes |
|---|---|---|
| `bill_id` | STRING | QuickBooks bill ID |
| `transaction_date`, `due_date` | DATE | Bill and due dates |
| `total_amount`, `balance` | FLOAT64 | Amounts |
| `doc_number` | STRING | Bill document number |
| `vendor_id`, `vendor_name`, `vendor_company_name` | STRING | Vendor (name resolved via vendor master) |
| `ap_account_id`, `ap_account_name` | STRING | AP posting account |
| `department_id`, `department_name` | STRING | Department |
| `sales_term_id`, `sales_term_name` | STRING | Payment terms |
| `currency` | STRING | Bill currency |
| `exchange_rate` | FLOAT64 | FX rate |
| `memo` | STRING | Private note |
| `is_open` | BOOL | TRUE when balance > 0 |
| `days_past_due` | INT64 | Days past due. NULL if not overdue or fully paid. |

### Table: `financials_payments`

QuickBooks payment records.

| Column | Type | Notes |
|---|---|---|
| `payment_id` | STRING | QuickBooks payment ID |
| `transaction_date` | DATE | Payment date |
| `total_amount`, `unapplied_amount` | FLOAT64 | Amount and unapplied portion |
| `payment_ref_number` | STRING | Reference/check number |
| `customer_id`, `customer_name` | STRING | Customer |
| `payment_method_id`, `payment_method_name` | STRING | Method (e.g. Check, ACH, Credit Card) |
| `ar_account_id`, `ar_account_name` | STRING | AR account |
| `deposit_account_id`, `deposit_account_name` | STRING | Deposit-to account |
| `currency` | STRING | Payment currency |
| `exchange_rate` | FLOAT64 | FX rate |
| `memo` | STRING | Memo |

### Table: `financials_purchases`

QuickBooks purchase transactions with vendor name.

| Column | Type | Notes |
|---|---|---|
| `purchase_id` | STRING | QuickBooks purchase ID |
| `transaction_date` | DATE | Transaction date |
| `total_amount` | FLOAT64 | Amount |
| `doc_number` | STRING | Reference number |
| `payment_type` | STRING | Cash, Check, or CreditCard |
| `is_credit` | BOOL | TRUE if this is a credit transaction |
| `entity_id`, `entity_name` | STRING | Vendor/payee (name resolved via vendor master when entity_type = Vendor) |
| `entity_type` | STRING | Vendor, Employee, or Customer |
| `account_id`, `account_name` | STRING | GL account |
| `currency` | STRING | Transaction currency |
| `exchange_rate` | FLOAT64 | FX rate |
| `memo` | STRING | Memo |

### Table: `financials_journal_entries`

QuickBooks manual journal entries.

| Column | Type | Notes |
|---|---|---|
| `journal_entry_id` | STRING | QuickBooks journal entry ID |
| `transaction_date` | DATE | Entry date |
| `doc_number` | STRING | Document number |
| `is_adjustment` | BOOL | Whether this is an adjustment entry |
| `currency` | STRING | Entry currency |
| `exchange_rate` | FLOAT64 | FX rate |
| `memo` | STRING | Memo |
| `line_items` | JSON | Nested array of debit/credit lines. Parse with `JSON_EXTRACT_ARRAY`. |

### Table: `financials_vendors`

QuickBooks vendor master.

| Column | Type | Notes |
|---|---|---|
| `vendor_id` | STRING | QuickBooks vendor ID |
| `display_name` | STRING | Display name |
| `company_name` | STRING | Company name |
| `given_name`, `family_name` | STRING | Contact name |
| `print_on_check_name` | STRING | Check print name |
| `is_active` | BOOL | Active status |
| `balance` | FLOAT64 | Outstanding balance |
| `is_1099` | BOOL | 1099 contractor flag |
| `account_number` | STRING | Vendor account number |
| `tax_identifier` | STRING | Tax ID |
| `currency` | STRING | Default currency |
| `email`, `phone` | STRING | Contact info |

### Table: `financials_items`

QuickBooks item/product master.

| Column | Type | Notes |
|---|---|---|
| `item_id` | STRING | QuickBooks item ID |
| `item_name` | STRING | Item name |
| `fully_qualified_name` | STRING | Full hierarchy name |
| `item_type` | STRING | Service, Inventory, NonInventory, Group, Category, Bundle, Fixed Asset |
| `is_active` | BOOL | Active status |
| `unit_price` | FLOAT64 | Sales price |
| `purchase_cost` | FLOAT64 | Purchase cost |
| `description`, `purchase_description` | STRING | Sales / purchase descriptions |
| `is_taxable` | BOOL | Taxable flag |
| `tracks_quantity` | BOOL | Whether inventory is tracked |
| `quantity_on_hand` | FLOAT64 | Current inventory on hand |
| `inventory_start_date` | DATE | When inventory tracking started |
| `income_account_id`, `income_account_name` | STRING | Revenue posting account |
| `expense_account_id`, `expense_account_name` | STRING | Expense posting account |
| `asset_account_id`, `asset_account_name` | STRING | Inventory asset account |

### Table: `financials_transactions`

Transaction-level drill-down for QuickBooks customers. Joins raw transactions
to Drivepoint mappings so each line carries its category and mapping status.

| Column | Type | Notes |
|---|---|---|
| `account_name`, `account_id` | STRING | GL account |
| `amount` | FLOAT64 | Transaction amount (raw ERP sign) |
| `transaction_date` | DATE | Transaction date |
| `entity_name`, `entity_id` | STRING | Vendor, customer, or employee |
| `transaction_type` | STRING | Invoice, Bill, Journal Entry, etc. |
| `transaction_type_id` | STRING | QB type code |
| `memo` | STRING | Transaction memo |
| `split_account`, `split_account_id` | STRING | Contra/split account |
| `department`, `department_id` | STRING | Department |
| `doc_number` | STRING | Document number |
| `is_posting` | BOOL | Whether the transaction posts to the GL |
| `currency` | STRING | Transaction currency |
| `period_start`, `period_end` | DATE | Period boundaries used for mapping join |
| `company_id` | STRING | From the mapping join. NULL if unmapped. |
| `drivepoint_category_id`, `drivepoint_category_name` | STRING | Drivepoint category. NULL if unmapped. |
| `drivepoint_type`, `drivepoint_statement_type` | STRING | Category metadata. NULL if unmapped. |
| `sign_convention` | STRING | Revenue, Expense, or BalanceSheet. NULL if unmapped. |
| `is_mapped` | BOOL | Whether this transaction's account has a Drivepoint mapping |

### Financials grain keys (uniqueness tuple per table)

- `financials_general_ledger`: `company_id, account_id, class, dimension1, period_last_day`
- `financials_income_statement`: `company_id, account_id, class, dimension1, period_last_day`
- `financials_balance_sheet`: `company_id, account_id, class, dimension1, period_last_day`
- `financials_chart_of_accounts`: `company_id, account_id`
- `financials_mapping_coverage`: `company_id, financial_statement`
- `financials_invoices`: `invoice_id`
- `financials_invoice_lines`: `invoice_id, line_id`
- `financials_bills`: `bill_id`
- `financials_payments`: `payment_id`
- `financials_purchases`: `purchase_id`
- `financials_journal_entries`: `journal_entry_id`
- `financials_vendors`: `vendor_id`
- `financials_items`: `item_id`
- `financials_transactions`: no single unique key (transaction lines can repeat across splits)

### Financials footguns

1. **QB tables are empty stubs for non-QB customers.** The tables exist for
   every tenant (no runtime errors), but return zero rows for NetSuite, Xero,
   etc. Probe with a `COUNT(*)` before building analysis on them. The GL tables
   (`financials_general_ledger` through `financials_mapping_coverage`) are
   always populated.
2. **`class` and `dimension1` can be empty strings, not NULL.** The GL grain
   includes these columns, so two rows for the same account/period with
   different class values are distinct. Use `COALESCE(class, '')` or filter
   with `class = ''` when looking for unclassified entries.
3. **`period_net_change` sign follows the ERP.** Revenue accounts typically
   carry negative net change (credit normal); expenses are positive (debit
   normal). Use `sign_convention` from the Drivepoint mapping to normalize:
   Revenue lines should be flipped; Expense and BalanceSheet lines keep their
   raw sign.
4. **`is_mapped` is the mapping-quality signal.** Unmapped GL lines
   (`is_mapped = FALSE`) have NULL for all `drivepoint_*` columns. Use
   `financials_mapping_coverage` to assess how complete the mapping is before
   building Drivepoint-category rollups.
5. **Invoice line `quantity` units vary.** Cases vs eaches depends on the item
   configuration. Do not sum quantities across items without normalizing.
6. **`account_number_family` on invoice lines is a single character.** Use it
   for broad classification (4 = revenue, 5 = COGS), not exact account
   matching.

### Financials discovery patterns

```sql
-- Does this customer have financials data? Check GL row count and date range.
SELECT company_id,
       company_name,
       COUNT(*)            AS gl_rows,
       MIN(period_last_day) AS earliest_period,
       MAX(period_last_day) AS latest_period,
       COUNTIF(is_mapped)   AS mapped_rows,
       COUNTIF(NOT is_mapped) AS unmapped_rows
FROM `{{env_prefix}}_dwh_mart.financials_general_ledger`
GROUP BY 1, 2
```

```sql
-- Does this customer have QuickBooks sub-ledger data?
SELECT
  (SELECT COUNT(*) FROM `{{env_prefix}}_dwh_mart.financials_invoices`) AS invoices,
  (SELECT COUNT(*) FROM `{{env_prefix}}_dwh_mart.financials_bills`) AS bills,
  (SELECT COUNT(*) FROM `{{env_prefix}}_dwh_mart.financials_payments`) AS payments,
  (SELECT COUNT(*) FROM `{{env_prefix}}_dwh_mart.financials_vendors`) AS vendors,
  (SELECT COUNT(*) FROM `{{env_prefix}}_dwh_mart.financials_items`) AS items,
  (SELECT COUNT(*) FROM `{{env_prefix}}_dwh_mart.financials_transactions`) AS transactions
```

```sql
-- Mapping coverage summary
SELECT company_name,
       financial_statement,
       mapped_accounts,
       total_accounts,
       ROUND(mapping_coverage_rate, 3)  AS acct_coverage,
       ROUND(value_coverage_rate, 3)    AS value_coverage
FROM `{{env_prefix}}_dwh_mart.financials_mapping_coverage`
ORDER BY company_name, financial_statement
```

```sql
-- Income statement by Drivepoint category for a given period
SELECT drivepoint_category_name,
       drivepoint_type,
       SUM(period_net_change) AS net_change
FROM `{{env_prefix}}_dwh_mart.financials_income_statement`
WHERE is_mapped
  AND period_last_day = '2025-12-31'
GROUP BY 1, 2
ORDER BY drivepoint_type, drivepoint_category_name
```

```sql
-- Open AR invoices with aging
SELECT invoice_id, doc_number, customer_name,
       transaction_date, due_date, total_amount, balance, days_past_due
FROM `{{env_prefix}}_dwh_mart.financials_invoices`
WHERE is_open
ORDER BY days_past_due DESC
```

```sql
-- Revenue by product from invoice lines
SELECT item_name,
       SUM(quantity)  AS total_qty,
       SUM(amount)    AS total_revenue
FROM `{{env_prefix}}_dwh_mart.financials_invoice_lines`
WHERE is_revenue_line
GROUP BY 1
ORDER BY total_revenue DESC
```

```sql
-- AP aging by vendor
SELECT vendor_name,
       COUNT(*) AS open_bills,
       SUM(balance) AS total_outstanding,
       MAX(days_past_due) AS max_days_past_due
FROM `{{env_prefix}}_dwh_mart.financials_bills`
WHERE is_open
GROUP BY 1
ORDER BY total_outstanding DESC
```
