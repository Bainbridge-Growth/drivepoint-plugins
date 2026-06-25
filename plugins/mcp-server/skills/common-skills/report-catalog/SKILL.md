# Drivepoint Stock Report Catalog

Stock report bundles that ship to every Drivepoint customer. Use this
catalog to link back to the canonical reporting experience when an answer
matches a known bundle's intent.

Source: Firestore collection `report_bundles` (filtered to
`status = "active"`, `available_to_all = true`, and excluding customer-
specific bundles and Omni workspace tiles).

---

## URL templates

App URLs are tenant-prefixed. The tenant segment is the `company_id`
column from the data warehouse — same identifier in both systems.

- **Bundle (group of related reports):**
  `https://app.drivepoint.io/<company_id>/reports/bundle/<bundle_id>`
- **Reports hub (fallback when no bundle matches):**
  `https://app.drivepoint.io/<company_id>/reports`

**Resolving `<company_id>`:** every row of every mart table carries
`company_id`. Pull it from your most recent query result, or run
``SELECT DISTINCT company_id FROM `{{env_prefix}}_dwh_mart.smartmodel_actuals` LIMIT 1``
once at session start and reuse for the rest of the session.

> **If the production app URL is not `app.drivepoint.io`**, update the
> host in every row of the table below. The path templates are stable.

---

## Bundles

Listed in display-order from the source (`order` field).

| Bundle ID | Display name | Covers | Intent keywords |
|---|---|---|---|
| `dtc_sales_bundle` | DTC Sales | Shopify / direct-to-consumer channel sales metrics; monthly department reviews | "dtc sales", "shopify sales", "direct-to-consumer revenue", "dtc channel performance", "online sales", "ecommerce sales" |
| `amazon_sales` | Amazon Sales | Amazon marketplace sales metrics; monthly Marketing & Sales reviews | "amazon sales", "amazon revenue", "marketplace sales", "amazon orders", "amazon performance" |
| `tiktokshop_sales` | TikTok Shop Sales | TikTok Shop sales performance | "tiktok sales", "tiktok shop revenue", "tiktok performance", "tiktok orders" |
| `cohortanalysis_bundle` | DTC Cohort & LTV Analysis | Cohort and LTV performance across custom dimensions over time (Shopify) | "dtc cohort", "dtc ltv", "customer lifetime value", "shopify cohort", "retention", "repeat purchase rate", "lifetime value by cohort", "ltv by dimension" |
| `amazon_cohortanalysis_bundle` | Amazon Cohort & LTV Analysis | Cohort and LTV performance for the Amazon channel | "amazon cohort", "amazon ltv", "amazon retention", "marketplace ltv", "amazon customer lifetime", "amazon ltv by dimension" |
| `tiktokshop_cohorts` | TikTok Shop Cohort & LTV Analysis | Cohort and LTV performance for TikTok Shop | "tiktok cohort", "tiktok ltv", "tiktok retention", "tiktok customer lifetime" |
| `finance_bundle` | Financial Statements | Core financial statements for board / accounting / investor reviews | "p&l", "pnl", "income statement", "balance sheet", "cash flow", "financial statements", "financials" |
| `monthly_bundle` | Business Trends | Monthly trend reports for board meetings, investor updates, all-hands | "monthly trends", "business overview", "board metrics", "executive summary", "monthly performance", "business trends" |
| `variance_bundle` | Variance Reviews | Actuals vs. plan; quarterly / annual / monthly reviews | "actuals vs forecast", "variance", "budget vs actual", "plan vs actual", "forecast accuracy", "variance analysis", "actuals vs plan" |
| `wholesale_bundle` | Wholesale & Retail | Distribution / wholesale / retail / POS performance | "wholesale", "retail", "b2b sales", "distribution", "pos scan", "shipment velocity", "retail performance" |
| `benchmarks_bundle` | Benchmarks | P&L and Cohorted Financials benchmarks; identify strengths and weaknesses | "benchmarks", "peer comparison", "industry benchmarks", "kpi comparison", "benchmark analysis" |
| `inventory_starter_bundle` | Inventory Trends | Inventory performance over time | "inventory", "stock levels", "inventory trends", "inventory performance" |
| `cin7_omni_bundle` | Cin7 Omni | Sales and PO trends across channels (Cin7 customers) | "cin7", "purchase orders", "po trends", "product sales by channel", "cin7 sales" |

---

## Matching rules

1. Match on **intent**, not on column name. "How much did we make on TikTok last month?" → `tiktokshop_sales`.
2. Match only when the user's question maps cleanly to a bundle's coverage. If the question is generic ("how's the business?") or doesn't map to one specific bundle, **don't force a link** — silence is better than a noisy hub link on every response.
3. When two bundles plausibly fit (e.g. an Amazon question with cohort context), pick the more specific one (`amazon_cohortanalysis_bundle` over `amazon_sales`).
4. **Customer access varies.** Bundles are LaunchDarkly-gated per customer (`bundle.<id>.enabled`). A link that 404s means this customer doesn't have access to that bundle — that's expected behavior, not an error worth catching on the Claude side. If the user reports a dead link repeatedly, suggest they check with their Drivepoint admin.
5. **Source-dependency hints.** Some bundles only make sense if the customer has the underlying data source:
   - DTC / Shopify bundles → Shopify data
   - Amazon bundles → Amazon data
   - TikTok bundles → TikTok Shop data
   - Cin7 bundle → Cin7 integration
   - Wholesale → wholesale data (Muffin Data integration in many cases)
   - Benchmarks / Variance / Monthly / Finance → SmartModel
   If you're producing analysis for a customer who clearly doesn't have a source (e.g. you queried `ecommerce_transactions_order_level` and found zero Amazon rows), don't link to an Amazon-specific bundle.

---

## Inner reports

Each bundle contains 1–7 individual Dazzler reports (linkable at
`/<company_id>/dazzler/report/<dazzler_report_id>`). Their UUIDs are in
the bundle's `reports` array in Firestore, but their human-readable names
live in the separate `dazzler` Firestore collection and aren't covered by
this catalog. Linking at the bundle level is sufficient for v1; if you
want sub-report precision, ask the operator to export the `dazzler`
collection and amend this file.

---

## Excluded from this catalog

- **Inactive bundles** (e.g. `tiktokshop_all`).
- **Customer-specific custom bundles** (`*_custom_dashboards`, `moshlife_custom_reports`, etc.) — these are unique to one customer and shouldn't be linked to from a generic system prompt.
- **Omni workspace tiles** (`omni_bundle_my_documents`, `omni_bundle_shared_with_me`, `omni_bundle_team_documents`) — these are navigation surfaces inside the Omni workspace, not analytical reports.
- **The 8 stock landing pages** (Reports hub, Dazzler Studio, Plans, etc.) — only the Reports hub is referenced here as the fallback.
