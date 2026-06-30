# Sample Queries

12 battle-tested SQL patterns covering the most common questions a CPG
finance person asks. Every literal is a `<placeholder>` — replace before
running. Every example assumes `{{env_prefix}}_dwh_mart` is the active dataset.

Use these as templates. Adapt; don't fabricate from scratch.

---

## 1. Discovery: find a metric by keyword

**User asks:** "Do we have a metric for marketing efficiency / contribution
profit / [anything you don't already know the ID for]?"

```sql
SELECT DISTINCT metric_id, metric_name, metric_format
FROM `{{env_prefix}}_dwh_mart.smartmodel_actuals`
WHERE LOWER(metric_name) LIKE '%<keyword>%'
   OR LOWER(metric_id)   LIKE '%<keyword>%'
ORDER BY metric_id
LIMIT 50
```

**Notes:** Always run this before guessing a `metric_id`. Show the user what
you found and let them pick. If the metric exists only in forecast plans
(not actuals), repeat against `smartmodel` instead.

---

## 2. Discovery: list channels and currencies

```sql
SELECT channel,
       currency,
       COUNT(*)            AS row_count,
       MIN(created_date)   AS first_date,
       MAX(created_date)   AS last_date
FROM `{{env_prefix}}_dwh_mart.ecommerce_transactions_order_level`
WHERE transaction_type = 'order'
GROUP BY 1, 2
ORDER BY channel, currency
```

**Notes:** Currency varies by channel. Any aggregation across channels must
respect currency or filter to one.

---

## 3. Discovery: list plans

```sql
SELECT plan_id,
       ANY_VALUE(plan_name)          AS plan_name,
       ANY_VALUE(is_from_live_model) AS is_live,
       MIN(report_month)             AS first_month,
       MAX(report_month)             AS last_month,
       COUNTIF(is_actual)            AS actual_months,
       COUNTIF(NOT is_actual)        AS forecast_months
FROM `{{env_prefix}}_dwh_mart.smartmodel`
GROUP BY plan_id
ORDER BY is_live DESC, plan_name
```

**Notes:** Exactly one plan should have `is_from_live_model = TRUE` — that's
the live plan. Everything else is a frozen forecast. **Use `plan_id` in
SQL filters; `plan_name` is editable and not guaranteed unique.**

---

## 4. Monthly net sales by channel (last N months)

```sql
SELECT channel,
       DATE_TRUNC(created_date, MONTH)   AS month,
       currency,
       SUM(net_sales)                    AS net_sales,
       COUNT(DISTINCT order_id)          AS orders,
       SUM(units_sold)                   AS units
FROM `{{env_prefix}}_dwh_mart.ecommerce_transactions_order_level`
WHERE transaction_type = 'order'
  AND created_date >= DATE_SUB(CURRENT_DATE(), INTERVAL <N> MONTH)
GROUP BY 1, 2, 3
ORDER BY 2 DESC, 1
```

**Notes:** Use `net_sales`, not `net_revenue`. `net_revenue` adds shipping
and taxes — usually not what "revenue" means in conversation. Filter
`transaction_type = 'order'` to exclude returns from the order count.

---

## 5. Top N products by net sales (line-item grain)

```sql
SELECT product_id,
       product_title,
       sku,
       channel,
       SUM(units_sold)   AS units,
       SUM(net_sales)    AS net_sales
FROM `{{env_prefix}}_dwh_mart.ecommerce_transactions_line_item_level`
WHERE transaction_type = 'order'
  AND created_date BETWEEN DATE '<start>' AND DATE '<end>'
  -- optional: AND channel = '<channel>'
GROUP BY 1, 2, 3, 4
ORDER BY net_sales DESC
LIMIT <N>
```

**Notes:** Must filter `transaction_type = 'order'` — on return rows every
money column except `returns` is zero. Always include a date range; this is
the largest table.

---

## 6. Returns rate by channel and month

```sql
WITH monthly AS (
  SELECT channel,
         DATE_TRUNC(created_date, MONTH)                      AS month,
         currency,
         SUM(IF(transaction_type = 'order',  gross_sales, 0)) AS gross_sales,
         SUM(IF(transaction_type = 'return', returns,     0)) AS returns
  FROM `{{env_prefix}}_dwh_mart.ecommerce_transactions_order_level`
  WHERE created_date >= DATE_SUB(CURRENT_DATE(), INTERVAL <N> MONTH)
  GROUP BY 1, 2, 3
)
SELECT channel, month, currency, gross_sales, returns,
       SAFE_DIVIDE(-returns, gross_sales) AS returns_rate
FROM monthly
ORDER BY 2 DESC, 1
```

**Notes:** `returns` is stored as a negative — flip the sign for the rate.
Use `SAFE_DIVIDE` to avoid divide-by-zero on months with no sales.

---

## 7. Customer-type breakdown (new vs. returning) by month

```sql
SELECT DATE_TRUNC(created_date, MONTH)        AS month,
       channel,
       customer_type,
       currency,
       COUNT(DISTINCT order_id)               AS orders,
       SUM(net_sales)                         AS net_sales,
       SAFE_DIVIDE(SUM(net_sales),
                   COUNT(DISTINCT order_id))  AS aov
FROM `{{env_prefix}}_dwh_mart.ecommerce_transactions_order_level`
WHERE transaction_type = 'order'
  AND created_date >= DATE '<start>'
GROUP BY 1, 2, 3, 4
ORDER BY 1 DESC, 2, 3
```

---

## 8. Geographic top states / countries by net sales

```sql
SELECT country, province_code,
       currency,
       SUM(net_sales)                AS net_sales,
       COUNT(DISTINCT order_id)      AS orders
FROM `{{env_prefix}}_dwh_mart.ecommerce_transactions_order_level`
WHERE transaction_type = 'order'
  AND created_date BETWEEN DATE '<start>' AND DATE '<end>'
GROUP BY 1, 2, 3
ORDER BY net_sales DESC
LIMIT <N>
```

**Notes:** Use `country` / `province_code` only. Never echo raw addresses
(`address1`, `address2`, `zip`) from the line-item table.

---

## 9. Discount-code effectiveness

```sql
SELECT discount_code,
       channel,
       currency,
       COUNT(DISTINCT order_id)   AS orders,
       SUM(gross_sales)           AS gross_sales,
       SUM(discounts)             AS discounts,
       SUM(net_sales)             AS net_sales,
       SAFE_DIVIDE(-SUM(discounts), SUM(gross_sales)) AS effective_discount_rate
FROM `{{env_prefix}}_dwh_mart.ecommerce_transactions_order_level`
WHERE transaction_type = 'order'
  AND created_date BETWEEN DATE '<start>' AND DATE '<end>'
  AND discount_code IS NOT NULL
GROUP BY 1, 2, 3
ORDER BY net_sales DESC
LIMIT 50
```

---

## 10. Monthly P&L summary (key live-actual rollups)

```sql
SELECT report_month,
       metric_id,
       metric_name,
       metric_format,
       metric_sort_order,
       metric_value
FROM `{{env_prefix}}_dwh_mart.smartmodel_actuals`
WHERE metric_id IN (
        'incomeStatement.grossSales',
        'incomeStatement.netSales',
        'incomeStatement.netRevenue',
        'incomeStatement.costOfGoodsSold',
        'incomeStatement.grossProfit',
        'incomeStatement.contributionProfit',
        'incomeStatement.operatingIncome',
        'incomeStatement.EBITDA',
        'incomeStatement.netIncome'
      )
  AND report_month BETWEEN DATE '<start>' AND DATE '<end>'
ORDER BY report_month, metric_sort_order
```

**Notes:** Each row is a single metric × month. Pivot in code, not in SQL,
to render side-by-side columns. If a metric is absent from the result,
this customer's SmartModel may not break out that line item — run
discovery (§1) to confirm before reporting a "missing" line.

---

## 11. YTD margin (recomputed, never summed)

**User asks:** "What's our YTD gross margin?"

**Before running:** verify which denominator the SmartModel uses. Look up
the KPI row for a single closed month and back-solve from candidates:

```sql
-- One-month verification — back-solve numerator / denominator
SELECT metric_id, metric_value
FROM `{{env_prefix}}_dwh_mart.smartmodel_actuals`
WHERE report_month = DATE '<recent_closed_month>'
  AND metric_id IN (
    'metrics.grossMarginPercent',
    'incomeStatement.grossProfit',
    'incomeStatement.netRevenue',
    'incomeStatement.netSales'
  )
```

Compute `grossProfit / netRevenue` and `grossProfit / netSales` and check
which matches `metrics.grossMarginPercent`. Use that pair.

Then for YTD:

```sql
-- Replace <numerator_metric_id> and <denominator_metric_id> with the
-- pair you verified above.
WITH ytd AS (
  SELECT metric_id, SUM(metric_value) AS v
  FROM `{{env_prefix}}_dwh_mart.smartmodel_actuals`
  WHERE metric_id IN ('<numerator_metric_id>',
                      '<denominator_metric_id>')
    AND report_month BETWEEN DATE '<ytd_start>' AND DATE '<ytd_end>'
  GROUP BY 1
)
SELECT SAFE_DIVIDE(
         MAX(IF(metric_id = '<numerator_metric_id>',   v, NULL)),
         MAX(IF(metric_id = '<denominator_metric_id>', v, NULL))
       ) AS ytd_margin
FROM ytd
```

**Notes:** Never sum `metrics.grossMarginPercent` (or any percentage metric)
across months — percentages aren't additive. Always recompute from
numerator / denominator totals. Surface `MAX(report_month)` for the same
filter so the user knows the YTD boundary you're closed through.

---

## 12. Actuals vs. forecast for a single metric and plan

```sql
SELECT report_month,
       metric_name,
       actual_value,
       forecast_value,
       variance,
       variance_pct
FROM `{{env_prefix}}_dwh_mart.smartmodel_actuals_vs_forecast`
WHERE metric_id = '<metric_id>'
  AND plan_id   = '<plan_id>'         -- resolved via discovery §3
  AND report_month BETWEEN DATE '<start>' AND DATE '<end>'
ORDER BY report_month
```

**Notes:** Always filter by `plan_id`, not `plan_name` — names are editable
and not guaranteed unique. This table is row-multiplied by the number of
forecast plans, so the `plan_id` filter is also a cost optimization. A
NULL `forecast_value` means that metric/month wasn't in the forecast plan,
not that the forecast was zero. `variance_pct` is NULL when forecast was
zero (via `SAFE_DIVIDE`). `plan_data_type` is the forecast plan's
self-label at freeze time — use `actual_value IS NOT NULL` if you need to
know whether the live model has booked an actual for that month.
