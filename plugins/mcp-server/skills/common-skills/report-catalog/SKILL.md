# Drivepoint report gallery

The live catalog of stock reports in the Neo app. Use it when a question
matches a gallery card, when the user asks what reports exist, and when you
link them to a stock report. Read it before you build from a card.

Source: Firestore collection `reportCatalog`, seed version **9**, 23 published
cards. The page is the Neo report gallery:

`{{app_base_url}}/neo/<company_id>/reports/gallery`

Page copy: start from a Drivepoint template or from scratch. Build saves a
company copy and opens it in Drivepoint chat.

This is not the older Reports hub. Do not link
`/<company_id>/reports/bundle/<bundle_id>`, do not invent a bundle id, and do
not treat `report_bundles` as this list. Cohort, benchmark, channel-sales, and
Cin7 purchase-order bundles are not gallery cards.

**Resolving `<company_id>`:** every mart row carries `company_id`. Pull it
from the latest query result, or run
``SELECT DISTINCT company_id FROM `{{env_prefix}}_dwh_mart.smartmodel_actuals` LIMIT 1``
once and reuse it. Name a card by its display name. Do not recite a catalog
id to the user.

---

## Two build paths

Build does different work depending on whether the card has a saved-report
definition. Both paths end in `saved-reports-guide` and `save_report`. A
gallery report is a structured definition (header, controls, blocks, queries).
Do not save a React artifact as the report. `report-creation-guide` is only
for a one-off artifact the user will not save.

### Structured template (20 cards)

The card's `template` is already a saved-report definition. Build copies it
into a live company report (change summary: "Report was created from the
report gallery.") and opens chat with **Check {name} against our data**.

In that thread the report is already built:

1. Load `saved-reports-guide`. Call `get_report` on the saved report id and
   `preview_report` the saved query unchanged.
2. Drop or change a block, series, column, or control only when this
   customer's data for it is missing, and say what you changed.
3. Do not invent a new layout and do not rebuild the report from scratch.
4. Show the change and wait. After the user agrees, call `save_report` with
   that report id.

If the user asks for one of these cards outside a gallery thread, send them
to the gallery and have them press Build. That copies the template. Do not
re-author the layout in chat.

### Prompt-only card (3 cards)

These cards have no `template`: **Inventory health**, **Demand forecast
review**, and **Landed cost monitor**. Build saves a company draft and opens
chat with the card's brief plus instructions to load `saved-reports-guide`,
preview every query, show the draft, and wait. When the user approves, call
`save_report` with that draft id so the draft goes live in Reports.

Author the definition to the report conventions already in this conversation:
controls live in `report.controls`, a date axis uses presets `last_12_months`,
`year_to_date`, `this_month`, `last_month`, and `last_quarter` with default
`last_12_months`, then KPIs, then a chart, then a table. Title Case. No em
dashes.

**Start from scratch** is the same path with no catalog card: a company draft
and a brief the user wrote. Load `saved-reports-guide`, preview, then
`save_report` with the draft id after they approve.

---

## How the gallery is organized

Sections, in order: Finance, Planning, Sales, Marketing, Operations,
Cross-functional. Filter chips are All, Finance, Planning, Sales, Marketing,
and Operations. Cross-functional has no chip of its own. It shows under All.

Archive removes a card from the gallery and leaves existing company copies.
If a name below is missing from the page, it was archived or edited. Do not
offer a card that is not in this list.

A company copy, once saved, opens at
`{{app_base_url}}/neo/<company_id>/reports/<report_id>`.
The stock-card link is always the gallery URL above. Cards are not
individually addressable.

---

## Cards

Kind `structured` has a template. Kind `prompt-only` does not.

| Name | Section | Kind | Covers | Intent |
|---|---|---|---|---|
| Balance Sheet | Finance | structured | Balance-sheet lines over closed months. Financial model. | "balance sheet", "assets and liabilities" |
| Balance Sheet Variance | Finance | structured | Balance sheet actuals compared with a selected plan. | "balance sheet vs plan", "balance sheet variance" |
| Cash and liquidity watch | Finance | structured | Monthly cash, working capital, and cash conversion. QuickBooks. | "cash", "liquidity", "working capital", "runway" |
| Cash Flow Statement | Finance | structured | Operating, investing, and financing cash flow. | "cash flow", "cash flow statement" |
| Key Metrics | Finance | structured | Headline financial and operating metrics. | "key metrics", "headline metrics", "kpi summary" |
| Key Metrics Variance | Finance | structured | Key-metric actuals compared with a selected plan. | "kpi vs plan", "key metrics variance" |
| Margins | Finance | structured | Stored margin percentages from the model. Do not recompute them. | "margins", "gross margin", "contribution margin" |
| Monthly plan variance | Finance | structured | Actual vs plan for revenue, profit, operating expenses, EBITDA, and cash. QuickBooks. | "plan variance", "actual vs plan", "budget vs actual" |
| Profit and Loss Statement | Finance | structured | Closed-month profit and loss from SmartModel actuals. | "p&l", "pnl", "income statement", "profit and loss" |
| Profit and Loss Variance | Finance | structured | Profit and loss actuals compared with a selected plan. | "p&l variance", "profit variance vs plan" |
| Demand forecast review | Planning | prompt-only | Forecast error and bias versus actuals, seasonality, and promotions, by SKU and channel. Shopify, Amazon. | "forecast accuracy", "forecast bias", "demand forecast" |
| Inventory health | Planning | prompt-only | On-hand, on-order, weeks of supply, stockout, and excess by SKU, channel, and node. Cin7, Amazon, Shopify. | "inventory health", "weeks of supply", "stockout", "excess inventory" |
| Retail account performance | Sales | structured | Sell-through, promotional sales, and retailer inventory by account and week. Muffin. | "retail account", "sell-through by retailer", "retailer inventory" |
| Wholesale Variance | Sales | structured | Wholesale results compared with a selected plan. Model and wholesale activity. | "wholesale vs plan", "wholesale variance" |
| DTC Marketing and CAC | Marketing | structured | Direct-to-consumer marketing cost and cost to acquire. Financial model. | "cac", "customer acquisition cost", "dtc marketing" |
| Marketing efficiency | Marketing | structured | Ad spend, net sales, CAC, MER, and revenue per spend dollar by channel. Meta, Shopify, Amazon. | "mer", "marketing efficiency", "roas", "ad spend" |
| Inventory Balances Trends | Operations | structured | How inventory balances move over time in the financial model. | "inventory balance trend", "inventory over time" |
| Landed cost monitor | Operations | prompt-only | Landed cost versus standard, and the margin impact, by SKU. NetSuite. | "landed cost", "standard cost", "duties", "freight cost" |
| Average Order Value Trends | Cross-functional | structured | How direct-to-consumer average order value moves over time. | "aov", "average order value" |
| Cash Conversion Cycle Trends | Cross-functional | structured | Days inventory, sales, and payables outstanding, and the cash conversion cycle. | "cash conversion cycle", "dio", "dso", "dpo" |
| Financial Margins Trends | Cross-functional | structured | How margins move over time. | "margin trend", "margins over time" |
| Sales By Channel Trends | Cross-functional | structured | How sales move over time by channel. | "sales by channel", "channel trend" |
| Weekly business performance | Cross-functional | structured | Weekly ecommerce orders, sales, and fees. Shopify, Amazon. | "weekly performance", "weekly sales", "orders this week" |

### Prompt-only briefs

Use these when the thread was opened from that card, or when the user asks
you to build that card and no template was copied.

- **Inventory health.** Create an inventory health report by SKU, channel, and
  node. Include on-hand, on-order, weeks of supply, sell-through, aged
  inventory, stockout risk, and excess risk. Recommend reorders, transfers,
  markdowns, or purchase-order changes.
- **Demand forecast review.** Create a demand forecast review by SKU and
  channel. Compare the current forecast with actual sales, seasonality,
  promotions, launches, and retailer forecasts. Show forecast error and bias,
  recommend overrides, and explain material changes.
- **Landed cost monitor.** Create a landed cost report by SKU. Show material,
  manufacturing, packaging, freight, duty, tariff, and total landed cost
  versus standard and prior period. Quantify margin impact and recommend
  standard-cost or sourcing actions.

---

## Matching rules

1. Match on intent, not on a column name. "How did profit compare to plan?"
   is **Profit and Loss Variance**, not the whole Finance section.
2. Match only when the question maps cleanly to one card. A generic "how's
   the business?" gets no gallery link.
3. When two cards fit, pick the more specific one. A wholesale plan question
   is **Wholesale Variance**, not **Monthly plan variance**.
4. Skip a card whose required source is absent. Retail account performance
   needs Muffin. Marketing efficiency needs ad and storefront data. Inventory
   health needs inventory data (Cin7, Amazon, or Shopify). Landed cost needs
   NetSuite. Finance statement cards need the SmartModel. If the mart has no
   rows for that source, do not offer the card.
5. **Inventory health** (operational, prompt-only) and **Inventory Balances
   Trends** (model balances, structured) are different reports. Do not
   substitute one for the other.
6. These are not gallery cards. Answer the question without a gallery link:
   cohort and LTV, peer benchmarks, a TikTok-only or Amazon-only sales
   bundle, Cin7 purchase orders, and a single combined "financial statements"
   or "business trends" bundle. Point a financial-statement question at the
   one matching card (Profit and Loss Statement, Balance Sheet, or Cash Flow
   Statement).

After answering, when one card is a clean match, add one line:

`Also in the report gallery: [Card name]({{app_base_url}}/neo/<company_id>/reports/gallery)`

In an artifact, set `REPORT_LINK` to that card name and the same gallery URL.
Set it to null when no card matches. Do not add a generic Reports link on
every answer.
