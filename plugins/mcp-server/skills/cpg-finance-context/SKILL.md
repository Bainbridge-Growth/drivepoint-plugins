---
name: cpg-finance-context
description: CPG finance vocabulary-and-concepts bridge for Drivepoint SmartModel / analytics data. Use whenever a user names a financial metric, line item, ratio, margin, or business concept (e.g. "net sales", "revenue", "gross margin", "contribution margin", "CAC", "LTV", "payback", "EBITDA", "weeks of supply", "DTC vs wholesale") so you map their wording to the model's actual line and NEVER report a metric as missing when the model carries it under another name. Translates user language to canonical metric_ids, explains CPG finance (gross-to-net, contribution-margin tiers, trade spend/deductions, channel economics, working capital), and disambiguates the terms most often confused (net sales vs net revenue, margin denominators, blended vs paid CAC). Triggers on finance-vocabulary questions, "where is X in my model", "what's our [metric]", or any metric the model does not literally label.
---

# CPG Finance Context

The vocabulary-and-concepts bridge between how a **CPG operator talks** and how a
**SmartModel is structured**. Load this whenever the user names a financial metric,
line item, ratio, or business concept. Its job is to stop the assistant from ever
saying "that metric isn't in your model" when the model has the same thing under a
different name.

This skill is **concept knowledge**, not data. The live numbers, exact `metric_id`
inventory, column names, and query idioms are in `data-dictionary` and
`sample-queries` — always confirm a term against the actual model before quoting a
number. If anything here conflicts with `data-dictionary` for a specific customer,
the customer's real model wins; use the discovery queries below to check.

---

## Why this exists (the failure we are fixing)

A user asked for **"net sales"** for a period. The model labels that line
**"net revenue,"** so the assistant searched for `incomeStatement.netSales`, didn't
find the exact string, and reported it as missing — then stopped. The user was left
stranded by a pure vocabulary gap, not a data gap.

That is the canonical failure. An analyst who knew the model would have said: *"This
model surfaces that as Net Revenue — here's the number — and note Net Revenue here =
Net Sales + shipping + taxes, so if you specifically want product-only net sales,
that's a different line."* **Bridge, explain, deliver. Never strand.**

---

## The cardinal rule — never strand the user

When the user names a metric that is **not a literal match** for a `metric_id` or
column, do NOT report it missing and stop. Run this procedure:

1. **Recognize the concept.** Map what they said to the underlying finance concept
   using the Vocabulary Bridge below. "Net sales," "top line," "revenue," "what we
   actually booked" are all pointing at the revenue family — figure out which rung.
2. **Map to candidate canonical term(s).** Get the likely `metric_id` / column and
   note any alternates (e.g. `netSales` *and* `netRevenue`; gross-margin on `netSales`
   *vs* `netRevenue`).
3. **Confirm it exists in THIS model — discover, don't assume.** Run the keyword
   discovery query (see "Confirming a term"). Customer models vary: not every line
   exists for every customer, and labels drift. Never invent a `metric_id`.
4. **If the literal term is absent, name the closest line and explain the difference.**
   "There's no `netSales` line in this model; the top line it carries is `netRevenue`.
   They differ by shipping + taxes. Here's net revenue; I can approximate net sales as
   netRevenue − shipping − taxes if those lines exist — want that?"
5. **Deliver the number with the definitional caveat**, and state which line you used.
   Always say *"interpreting 'X' as the model's 'Y' line"* so the user can correct you.

Two standing sub-rules:

- **Denominator ambiguity → compute and show both.** "Margin," "CAC," "LTV," and
  "revenue" are the four words most often silently mis-mapped. Margins can be struck on
  `netSales` *or* `netRevenue`, and the model's choice is **customer-configurable** —
  verify by back-solving one closed month (see `analysis-skills-guide` → "Choosing the
  right denominator"). If you can't verify, present the range and name the assumption.
- **Some asks are computed concepts, not rows.** "Payback," "LTV:CAC," "weeks of
  supply," "true active customers," "monthly-trial cohort" usually have **no single
  line** in the model. Don't call them missing — say what *is* available (the inputs,
  or the grain that exists) and offer to compute the concept from those inputs, or point
  to the analysis skill that does (`cohort-analysis`, `inventory-analysis`, etc.).
- **Watch for duplicate lines — surface both, never pick silently.** The same rollup can
  appear twice: under different **casing** (`incomeStatement.depreciation` vs `.Depreciation`)
  or under a parallel **company-namespace prefix** (e.g. `incomeStatement.netRevenue` vs
  `incomeStatement.mudWtr.netRevenue`), often with **slightly different values** (~1%).
  Discovery returns both. The plain `incomeStatement.*` namespace is usually the one the
  `metrics.*` KPI rows tie to — confirm by back-solving a margin (gross profit ÷ net revenue
  should equal `metrics.grossMarginPercent`). Report the verified base value and name the twin
  rather than averaging or guessing.

### Worked example — "net sales" (the real case)

> **User:** "What were net sales last month vs. budget?"
>
> **Good response:** "This model doesn't carry a line literally called *net sales* —
> its top revenue line is **Net Revenue** (`incomeStatement.netRevenue`). In Drivepoint,
> Net Revenue = Net Sales + shipping + taxes, where Net Sales = Gross Sales − discounts −
> returns. So:
> - **Net Revenue, [month]:** USD X (actual) vs USD Y (budget) → variance Z
> - If you specifically mean *product-only net sales* (ex-shipping/tax), this model
>   [does / does not] break out `netSales` separately — [here it is / I can derive it as
>   netRevenue − shipping − taxes].
>
> Which definition do you want me to track from here on?"

The wrong response — *"I couldn't find net sales in the income statement"* — is the bug
this skill exists to prevent.

---

## Vocabulary Bridge — what users say → what the model calls it

`metric_id`s below are the **canonical top-level rollups** that exist for most
customers (per `data-dictionary`). Sub-lines (specific opex/marketing/fulfillment
accounts), channel leaves, and KPI denominators **vary by customer — discover them,
don't hardcode them.** Channel suffixes appear as both `.dtcOnline` and `_dtcOnline`;
match with `LOWER(metric_id) LIKE '%dtconline%'`.

### Revenue & the gross-to-net stack

| User says | Model concept → `metric_id` | Notes / how to confirm |
|---|---|---|
| gross sales, gross revenue, top-line (loosely), GMV, "the sticker number" | Gross Sales → `incomeStatement.grossSales` | Before discounts/returns/shipping. Largest, least meaningful number. |
| discounts, promos, markdowns | Discounts → `incomeStatement.discounts` | Contra-revenue; stored **negative** in the ecommerce mart. |
| returns, refunds, RMAs | Returns → `incomeStatement.returns` | Contra-revenue; stored negative. |
| **net sales**, product revenue, "net we kept on product" | Net Sales → `incomeStatement.netSales` | = Gross Sales − discounts − returns. **May not exist for every customer** — if absent, see Net Revenue. The #1 confusion (see worked example). |
| **net revenue**, revenue, total revenue, "the top line," "what we booked" | Net Revenue → `incomeStatement.netRevenue` | = Net Sales + shipping + taxes. For many customers this is the **headline top line**, and the line a user calling for "net sales" actually wants. **NOT after platform fees.** |
| revenue after fees, net proceeds, settlement, "what hit the bank" | Net Revenue − fees (derive) | No standard rollup — compute `netRevenue − total_fees` on the ecommerce mart, or discover a customer line. |
| "sales" (bare, no qualifier) | Ambiguous — gross / net sales / net revenue | Don't guess. Default to **net revenue** for "revenue," but state the assumption and offer the alternatives. |
| trade spend, deductions, allowances, chargebacks (retailer), slotting, scan-downs, off-invoice, billbacks, MCBs, free fills, co-op | Contra-revenue between gross and net (often inside discounts/returns rollups or customer opex) | CPG-specific; **reduces net sales, not a marketing expense** (see Primer §3). Discover where this customer books it — varies. |

### Profitability ladder & margins

| User says | Model concept → `metric_id` | Notes |
|---|---|---|
| COGS, cost of goods, product cost, landed cost, cost of sales, "Cox" (misheard) | Cost of Goods Sold → `incomeStatement.costOfGoodsSold` | CPG COGS = product + packaging + inbound freight + duties/tariffs. Excludes outbound shipping & marketing. |
| gross profit, GP | Gross Profit → `incomeStatement.grossProfit` | = Net Revenue (or Net Sales) − COGS. Same as **CM1** in DTC parlance. |
| gross margin, GM%, margin (often) | Gross Margin % → `metrics.grossMarginPercent` | **Denominator is customer-configurable** (`netRevenue` vs `netSales`). Verify before recomputing. Never average a % across months. |
| contribution profit, contribution margin $, CM, "variable margin" | Contribution Profit → `incomeStatement.contributionProfit` | Gross profit − variable costs (fulfillment, shipping, processing, marketplace fees). Roughly **CM2**. Ask *which* variable costs if it matters. |
| contribution after marketing, CPAM, "contribution less ad spend," true contribution | Contribution Profit After Marketing → `incomeStatement.contributionProfitAfterMarketing` | CM after variable marketing. Roughly **CM3**. The DTC "are we profitable on acquisition" line. |
| contribution margin % | Contribution Margin % → `metrics.contributionMarginPercent` | Denominator customer-configurable; verify. |
| operating income, operating profit, EBIT | Operating Income → `incomeStatement.operatingIncome` / `incomeStatement.EBIT` | After fixed opex, before interest/tax. |
| EBITDA | EBITDA → `incomeStatement.EBITDA` | Operating earnings before D&A. Valuation basis in CPG M&A. |
| adjusted EBITDA, normalized EBITDA, "add-backs" | Usually **not a stored line** | Derive: EBITDA + one-time/discretionary add-backs. Say what's in EBITDA and that add-backs aren't modeled unless a line exists. |
| D&A | `incomeStatement.depreciation`, `incomeStatement.amortization` | Casing/namespace duplicates can carry different values — surface both, never pick silently (see the duplicate-lines sub-rule under the cardinal rule). |
| net income, net profit, bottom line, earnings, PAT | Net Income → `incomeStatement.netIncome` | After everything. |
| net margin, net income margin | `metrics.netIncomeMarginPercent` | — |
| COGS %, gross margin's cost side | `metrics.costOfGoodsSoldPercent` | — |
| marketing, ad spend, media, total marketing | Marketing rollup under `incomeStatement.*` (varies) | Discover the customer's line; may split direct ads vs agency vs other. GL-level marketing sits under `metrics.marketingAssumptionsGl_*` (raw GL codes, not yet name-mapped). |
| fulfillment, 3PL, pick/pack, shipping cost, merchant/processing fees | Variable-cost lines under `incomeStatement.*` (varies) | The brand's outbound cost — distinct from shipping *income* (which is in net revenue). Discover the customer's line. |
| payroll, G&A, opex, overhead | Opex rollups under `incomeStatement.*` (varies) | GL-level opex under `metrics.opexAssumptionsGl_*` (raw GL codes). |

### Unit economics & marketing efficiency

| User says | Model concept → `metric_id` | Notes |
|---|---|---|
| AOV, average order value, average basket/ticket | `metrics.averageOrderValue.<channel>` | Channel-suffixed. |
| CAC, acquisition cost, cost per acquisition, "blended CAC" | `metrics.blendedPaidCAC.<channel>` (blended-paid) | **Clarify which CAC:** blended (all spend ÷ all new) vs paid vs new-customer (nCAC) vs fully-loaded. Also clarify **scope and denominator**: the model's "blended" CAC is usually **channel-scoped** (e.g. `.dtcOnline`, blended across that channel's campaigns — *not* an all-company figure), and often comes per-order *and* per-customer (`.dtcOnline` vs `.dtcOnline.customers`). There may be **no all-channel CAC** — say so rather than implying a company-wide blended CAC exists. A `metrics.fullyLoadedCAC.<channel>` variant may also exist. |
| payback, CAC payback, months to recover CAC | Computed concept — **not a row** | Derive from nCAC ÷ (CM per order × purchase frequency). Offer to compute; don't call it missing. |
| LTV, lifetime value, CLV/CLTV | Computed concept — usually **not a row** | Clarify revenue-LTV vs **margin-LTV** (use margin-LTV for any CAC comparison). Point to `cohort-analysis`. |
| LTV:CAC | Computed ratio | Only meaningful if both margin-based & CAC is nCAC/loaded. Target ~3:1. |
| MER, blended ROAS | Total revenue ÷ total marketing | Business-wide efficiency. |
| ROAS | Channel revenue ÷ channel ad spend | Tactical, per-channel; not a profit metric. |
| aMER, acquisition MER, new-customer efficiency | New-customer revenue ÷ total marketing | — |
| retention, repeat rate, returning %, "two-plus / three-plus," recurring customers | Cohort retention / repeat metrics | Overloaded term. **State the grain that exists** (cohort-level retention, order counts) — by-SKU retention prediction generally does **not** exist. See `cohort-analysis`. |
| subscription vs OTP, subscribe-and-save, one-time | Order-type splits (`metrics.*` order counts) | Subscription LTV typically far higher. |
| new vs returning customers | New/returning order counts (`metrics.*`); ecommerce `customer_type` | — |

### Working capital, inventory & the balance sheet / cash flow

| User says | Model concept → `metric_id` | Notes |
|---|---|---|
| cash, cash balance, ending cash, cash position | `balanceSheet.cash` (balance) / `cashFlowStatement.endOfPeriodCash` (flow) | "Cash" (balance) ≠ "cash flow" (statement). |
| AR, receivables | `balanceSheet.accountsReceivable` | Near-zero for pure DTC; large for wholesale (net terms). |
| inventory, stock on hand, FG, in-transit, WIP | `balanceSheet.inventory.*` | Sub-levels (finished goods in warehouse / in transit / WIP) vary by customer — discover. |
| AP, payables | `balanceSheet.accountsPayable` | — |
| line of credit, revolver, debt | `balanceSheet.lineOfCredit` | — |
| total assets / liabilities / equity | `balanceSheet.totalAssets` / `.totalLiabilities` / `.totalEquity` | Equity components: common stock, paid-in capital, retained earnings. |
| operating / investing / financing cash flow, OCF | `cashFlowStatement.netCashProvidedBy{Operating,Investing,Financing}Activities` | Prefix is **`cashFlowStatement`, not `cashFlow`** — models guess wrong constantly. |
| CapEx, capital expenditures | `cashFlowStatement.capitalExpenditures` | — |
| beginning / ending cash, runway | `cashFlowStatement.beginningOfPeriodCash` / `.endOfPeriodCash` | Runway = ending cash ÷ avg monthly burn (derive). |
| DIO / DSO / DPO | `metrics.daysInventoryOutstanding` / `.daysSalesOutstanding` / `.daysPayableOutstanding` | "Days" metrics — **never sum across months**; use latest or recompute. |
| cash conversion cycle, CCC, cash cycle | `metrics.cashConversionCycle` | = DIO + DSO − DPO. Can be negative (good). |
| inventory turns, sell-through, weeks of supply, GMROI | Mostly **derived** | Turns = COGS ÷ avg inventory. Weeks of supply / GMROI usually not stored — compute or see `inventory-analysis`. |

### Channels & spoken shorthand

| User says | Model concept | Notes |
|---|---|---|
| DTC, D2C, DDC, direct-to-consumer, own site, Shopify, ecommerce | DTC Online channel → `*.dtcOnline` / `*_dtcOnline` | All the same channel. Normalize the spelling drift; surface the model's canonical label. |
| Amazon, marketplace, 1P, 3P, Seller/Vendor Central | Marketplace channel → `*.marketplace` | **1P books wholesale revenue; 3P books retail revenue gross of fees** (Primer §4) — don't conflate. |
| wholesale, retail, B2B, distributor, retailer | Wholesale / Retail channel → `*.wholesale` / `*.retail` | Revenue booked at **sell-in** (wholesale price), not sell-through. |
| TikTok Shop, social commerce, live shopping | Often under marketplace/DTC (varies) | Books retail revenue gross of platform + creator fees. |
| "P&L", "P&O" (misheard), income statement | `incomeStatement.*` | — |
| GL, general ledger | R-GL import / `*AssumptionsGl_*` | GL code → friendly name mapping not yet shipped; return raw codes. |
| budget, plan, forecast, "the plan" | A `plan_id` (not the live model) | Use `plan_id` in SQL; `plan_name` for display. See `data-dictionary`. |

---

## CPG Finance Primer (the part that lets you reason like a CPG analyst)

Use this to *explain* concepts, sanity-check magnitudes, and disambiguate. Benchmark
ranges are directional operator rules of thumb, not standards — present as guidance.

### 1. Gross-to-net revenue waterfall

```
Gross sales
  − discounts / promos / markdowns          (contra-revenue)
  − returns / refunds                        (contra-revenue)
  − trade spend / allowances / chargebacks   (contra-revenue; CPG retail)
= Net sales                                  ← classic CPG top line
  + shipping income + taxes billed           (Drivepoint folds these in)
= Net revenue                                ← Drivepoint's headline top line
```

Total gross-to-net deductions commonly run **30–40% of gross** for retail CPG, leaving
net ~60–70%. **Net Sales vs Net Revenue is the load-bearing distinction** for this skill:
Net Sales is product-only; Net Revenue adds shipping + taxes. Neither is "after fees."

### 2. Profitability ladder (and the CM levels operators use)

```
Net revenue
  − landed COGS (product + packaging + inbound freight + duties/tariffs)
= Gross profit  = CM1
  − variable fulfillment (outbound shipping, 3PL pick/pack, payment processing,
    returns processing, marketplace/referral fees)
= CM2  (after fulfillment — max you can spend on CAC and still break even on order 1)
  − variable marketing / acquisition (paid media, affiliate/CPA)
= CM3  ≈ contribution profit after marketing — funds fixed cost + profit
  − fixed opex (payroll, rent, software, fixed marketing, D&A)
= Operating income / EBIT
  + D&A → EBITDA  ;  + one-time/discretionary add-backs → Adjusted EBITDA
  − interest − taxes
= Net income
```

Drivepoint's `grossProfit` ≈ CM1, `contributionProfit` ≈ CM2, `contributionProfitAfterMarketing`
≈ CM3 — but the exact variable-cost set is customer-configurable, so confirm before
asserting what a tier nets out. **"Margin" is ambiguous** — clarify gross vs contribution
(which tier) vs EBITDA vs net, and which denominator.

### 3. Trade spend & retailer deductions (CPG-specific, easy to misclassify)

Under ASC 606, money paid/credited to a *customer* (retailer/distributor) is presumed
**contra-revenue** — it reduces net sales, it is **not** marketing/opex and **not** COGS.

| Item | What it is | P&L placement |
|---|---|---|
| Off-invoice (OI) | Per-case discount netted on the invoice at buy-in | Contra-revenue |
| Scan-down / scanback | $/unit reimbursed on POS-scanned units (sell-through) | Contra-revenue |
| Billback / MCB | After-the-fact claim; MCB = distributor charges back a promo discount | Contra-revenue |
| Slotting / listing / free fills | Pay-to-play for new-item shelf placement | Contra-revenue |
| Spoils / swell allowance | Standing % for unsaleable goods | Usually contra-revenue |
| Co-op advertising / MDF | Funding retailer's advertising of the brand | **Opex** *iff* a distinct service at fair value; else contra-revenue |
| Shortages / OTIF fines / compliance chargebacks | Operational penalties (retailer/wholesaler) | Reduce net cash in practice; keep in a separate bucket from funded promos |
| MAP (minimum advertised price) | A pricing **policy** | **No P&L line at all** — not a deduction |

Booking trade spend below the line overstates both revenue and gross margin. Accrue it
monthly (retailers bill 60–90 days late) and true up.

### 4. Channel economics — what "revenue" means by channel

The price point at which revenue is booked changes by channel:

| Channel | Who sells to consumer | Revenue booked = | ~ vs shelf |
|---|---|---|---|
| DTC (own Shopify) | Brand | Full retail price (net of discounts/returns; + shipping income) | 100% |
| Amazon 1P / Vendor Central | Amazon (bought wholesale) | **Wholesale PO price** (gross-to-net of co-op/allowances) | 40–60% |
| Amazon 3P / Seller Central | Brand | **Full retail price, gross of fees** | 100% |
| Wholesale / retail | Retailer | **Sell-in (wholesale) price** (gross-to-net of trade spend) | 40–50% |
| TikTok Shop / marketplace | Brand | Full retail price, gross of platform + creator fees | 100% |

- **Sell-in = revenue** (units shipped to the trade, at wholesale price, on control transfer).
  **Sell-through / depletions = a demand signal, not a second revenue event.**
- **1P/wholesale book the low (wholesale) number; DTC/3P/TikTok book the high (retail)
  number**, then channel costs (referral ~15% Amazon, ~6% + creator ~13% TikTok, FBA,
  processing) come out below. Conflating 1P and 3P is the classic channel error.
- **Contra-revenue vs opex:** in wholesale/1P, trade spend & allowances are genuinely
  contra-revenue (ASC 606). In marketplace (3P/TikTok), the brand is usually the
  *principal* (controls goods) → fees are **selling opex** and top line = consumer GMV;
  a "net of fees" view is a defensible management presentation that changes top-line and
  gross-margin % but not net income. Flag which view a number uses.

### 5. Retail margin math (wholesale ⇄ shelf)

Frequent confusion, especially for brands selling into retail:

- **Markup vs margin** (same dollar profit, different base): `Margin% = Markup% ÷ (1 + Markup%)`;
  `Markup% = Margin% ÷ (1 − Margin%)`. So 50% markup = 33.3% margin. Applying a markup when
  you meant a margin underprices the product.
- **Set price** from a target: `Price = Cost ÷ (1 − Margin%)` or `Price = Cost × (1 + Markup%)`.
- **Keystone** = 2× cost = 100% markup = 50% margin (the classic retail default).
- **MSRP / list / RRP** = suggested shelf price (a benchmark). **MAP** = the lowest
  *advertised* price (a policy, not a transaction price). **Net / invoice price** = what the
  brand actually receives.
- **Backing wholesale out of a shelf price** (margins stack on each tier's selling price):
  `Wholesale = MSRP × (1 − retailer_margin) × (1 − distributor_margin)`. E.g. MSRP $8.00,
  retailer 40%, distributor 20% → retailer pays $4.80 → brand's net wholesale = $3.84.
  Direct-to-retailer (no distributor): `Wholesale = MSRP × (1 − retailer_margin)`.

A retailer's **required margin** (~30–50%, specialty up to 50%+) is a gatekeeping number:
if the brand's wholesale price doesn't leave the retailer that margin at the target shelf
price, the item won't be carried.

### 6. Unit economics & working capital (quick reference)

- **Keep the basis consistent:** margin-based throughout, new-customer CAC throughout,
  when chaining AOV → CM/order → CAC payback → LTV → LTV:CAC.
- **CPG is working-capital-intensive:** cash goes out for inventory long before sales
  come back (and later still for wholesale net terms). CCC = DIO + DSO − DPO is the core
  liquidity metric; growth makes it worse, so a profitable brand can still run out of cash.
- **Homonyms to watch:** "chargeback" = consumer card dispute in DTC, but a vendor
  compliance penalty in Amazon 1P / a promo deduction (MCB) in wholesale. "Referral fee"
  = marketplace commission. "Net revenue" includes shipping income in DTC but means
  gross-minus-full-deduction-stack in wholesale.

---

## Confirming a term exists in THIS model (discovery)

Always confirm before quoting a number — labels and line sets vary by customer.

```sql
-- Find a metric by friendly-name keyword (run before saying "not found")
SELECT DISTINCT metric_id, metric_name, metric_format
FROM `production_dwh_mart.smartmodel_actuals`
WHERE LOWER(metric_name) LIKE '%<keyword>%'
   OR LOWER(metric_id)   LIKE '%<keyword>%'
ORDER BY metric_id
LIMIT 50
```

Try the concept *and* its aliases: searching `%net%` surfaces both `netSales` and
`netRevenue`; `%margin%` surfaces the KPI rows so you can read the denominator. To verify
a margin's denominator, read one closed month and back-solve (see `analysis-skills-guide`).
If discovery returns nothing for every alias, *then* tell the user the concept isn't in
the model — and name the closest thing that is.

---

## Related skills

- `data-dictionary` — the authoritative `metric_id` taxonomy, column names, and the
  netSales/netRevenue/fee definitions. This skill maps vocabulary *to* it.
- `sample-queries` — discovery and metric-pull query templates.
- `analysis-skills-guide` — denominator discipline, decomposition, sanity checks.
- `margin-analysis`, `cohort-analysis`, `inventory-analysis`, `variance-analysis` —
  the analyses that compute the derived concepts (LTV, payback, weeks of supply, etc.).

---

## Maintaining this skill

This is a living glossary. When a new vocabulary gap shows up on a customer call or in
support, add the alias to the Vocabulary Bridge with the canonical term and the "how to
confirm" note. Keep `metric_id`s here limited to the **canonical rollups** that
`data-dictionary` guarantees; everything customer-specific stays a "discover it" pointer
so this file never goes stale against a single customer's model.
