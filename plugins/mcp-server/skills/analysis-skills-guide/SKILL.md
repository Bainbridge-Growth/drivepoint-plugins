---
name: analysis-skills-guide
description: Analytical method for Drivepoint data questions - how to frame the question, enumerate hypotheses, and keep the reasoning defensible before and while writing SQL. Use when an ask is vague or causal ("why is X down?"), or when a move needs decomposing via mix/rate/volume, a variance bridge, a funnel, statement linkage, or cohort triangulation. Also covers choosing the right denominator, sanity checks before believing a number, reading absence in the data, reconciling two paths that disagree, deciding when to drill or stop, and communicating uncertainty. Sits above sample-queries (execution) and below report-creation-guide (presentation).
---

# Analysis Skills Guide

How to think through an analytical question before writing SQL, and how to
keep your reasoning honest as you go. Sits above `sample-queries.md` (the
execution layer) and below `report-creation-guide.md` (the presentation
layer).

`system-prompt.md` defines the rules and footguns you must never violate.
This file defines the **habits** that produce a defensible answer.

---

## The opening move

Before any query runs, do three things in this order:

1. **Reframe the question into something concrete and answerable.** "How
   are we doing?" is not a question; "What were net sales in the last
   closed month vs. the same month last year, by channel?" is. If the
   user's ask is vague, restate the version you intend to answer and
   proceed under that framing — make the restatement visible so the user
   can correct it.
2. **Enumerate candidate hypotheses.** When the question is causal ("why
   is X down?"), write the 3–5 plausible drivers in your head before you
   query. This shapes which discovery is worth running. A query you can't
   tie back to one of those hypotheses is probably a fishing trip.
3. **Choose the smallest discovery that differentiates.** Pick the cheapest
   query that can rule out hypotheses or narrow the metric IDs / channels
   / plans in play. `sample-queries.md` §1–3 are the canonical starting
   probes. Resist the urge to write the "real" query first.

The cost of a 30-second discovery is always less than the cost of a
confidently-wrong answer.

---

## Decomposition frameworks

When an aggregate has moved or surprises, pick the decomposition that
matches the question shape. Use one — do not chain them speculatively.

### Mix / rate / volume — for any aggregate dollar move

A change in a `SUM(metric)` over time decomposes into:

- **Volume:** did the count of underlying units (orders, customers, SKUs
  sold) change?
- **Rate:** did the per-unit value (AOV, unit price, margin per order)
  change?
- **Mix:** did the *composition* across a dimension (channel, segment,
  product category) shift toward higher- or lower-value buckets?

Run all three at the same grain (usually monthly) and identify which
dominates. A move is rarely all three equally — if it looks like it is,
double-check that you're not double-counting (parent + child rollups).

### Variance bridge — for actual vs. plan

When actuals miss a plan, decompose the gap in this order:

1. By P&L line (revenue, COGS, marketing, opex) — which line drives the
   variance?
2. Within the dominant line, by channel — which channel drives it?
3. Within the channel, by mix vs. rate (as above).

Stop when the residual is small relative to the headline variance. Do not
attribute variance to a driver you have not separately computed.

### Funnel — for new-customer / acquisition questions

The full acquisition funnel is sessions → conversion rate → orders → AOV
→ return rate. The ecommerce mart carries the post-conversion steps —
orders, AOV, return rate, and the new vs. returning flag on each order.
**Sessions and conversion rate are not in this warehouse** (see
`system-prompt.md` §"What you do not have"); they live upstream. When a
question depends on the pre-purchase steps, state the boundary and stop
there — do not infer conversion rate from order counts alone.

### Statement linkage — for cash and working-capital questions

Cash moves trace through the three statements:

- Operating cash = net income ± non-cash items ± change in working capital
- Working capital change = ΔAR + ΔInventory − ΔAP (signs depend on the
  customer's convention — verify with one closed month)
- Investing / financing flows are separate

If the user asks "why did cash move," check the three components above in
order before reaching for narrative.

### Cohort triangulation — for retention / LTV / unit-economics questions

Period-level metrics (monthly net sales, monthly orders) blur cohorts.
Same monthly revenue can come from a thriving acquisition flywheel or a
shrinking returning base — they are different businesses. When the
question is about customer health, switch to cohort view: rows are
acquisition month, columns are months-since-acquisition. The ecommerce
mart's `customer_type_model`, `days_since_first_purchase`, and
`customer_type_segment` columns support this directly.

---

## Choosing the right denominator

The single most common analyst error is dividing by the wrong base.
Discipline before computing any ratio:

- **Margin percent:** the SmartModel KPI rows
  (`metrics.grossMarginPercent`, etc.) use a customer-configured
  denominator. Verify it for a single closed month before recomputing for
  any other period. See `sample-queries.md` §11.
- **Growth percent:** state the base period explicitly. "20% growth" is
  ambiguous between MoM, YoY, and trailing-12 vs. prior-trailing-12. Pick
  one and label it.
- **Share / mix percent:** the denominator is the total of the same metric
  for the same scope (period, currency, channel filter). Don't compute
  channel share from net sales using one period's numerator and a
  different period's denominator.
- **Per-customer / per-order metrics:** the count in the denominator must
  match the metric in the numerator. AOV = net sales / **order count**,
  not net sales / customer count. Per-customer revenue uses distinct
  customers in the period.
- **Returns rate:** numerator is the absolute value of `returns`; the
  denominator is `gross_sales`, not `net_sales` (net already includes
  returns — dividing into net double-counts).

If the right denominator is ambiguous, **compute both candidates and show
them.** Don't pick silently.

---

## Sanity checks before believing a number

Run these against any headline number before reporting it. Each is cheap.

1. **Order of magnitude.** Does the number sit within the customer's
   plausible range? If the customer's last 12 months of revenue averaged
   $1M / month, a $50M month is a unit error, a date-range bug, or a
   currency mix-up — not a result.
2. **Sign.** Is the sign consistent with the metric's known convention?
   `discounts` and `returns` are negative; expense lines may be either
   (SmartModel `metric_sign` is not yet populated — verify via min/max for
   a closed month). A positive returns figure is almost certainly a sign
   flip somewhere.
3. **Scale across time.** Does the metric jump by ≥2× between adjacent
   months without a known reason? Likely causes, in order: (a) channel
   launched or paused, (b) plan freeze boundary crossed, (c) date-range
   off-by-one, (d) currency mix changed, (e) actual one-time event.
4. **Freshness.** Is the period you're computing inside the last booked
   month? If the period extends beyond `MAX(report_month)`, the tail
   months are incomplete and the aggregate is misleading.
5. **Reconcile to a known total.** When you compute a number that should
   tie to a SmartModel rollup (e.g. ecommerce net sales by channel ↔
   `incomeStatement.netSales` channel leaves), check it ties. Some drift
   from timing and definitional differences is expected; divergence
   beyond that needs investigation before publishing.

---

## Reading absence

A missing value is information. Treat each of these as a finding to
surface, not a gap to silently fill:

- **NULL `metric_value`:** the upstream cell was empty. Different from
  zero. Report as null in the answer.
- **NULL channel-specific fee column** (`commission_fees`,
  `retail_delivery_fee`, `affiliate_*`): "not applicable to this channel,"
  not "fee was zero." See `system-prompt.md` ecommerce footguns.
- **Missing months in actuals:** check `MAX(report_month)` to confirm the
  close boundary. If a month is missing *inside* the closed range, the
  customer's model has a gap — flag it.
- **A channel that appears, then disappears:** launch or sunset event,
  not a data bug — but worth naming.
- **A metric that exists in forecast plans but not in actuals:** the
  customer has modeled something they don't track in live. Report exactly
  that — don't synthesize an actual.
- **Casing duplicates with disagreeing values:** when discovery returns
  both `incomeStatement.depreciation` and `incomeStatement.Depreciation`
  with different `metric_value`s, both are real. Surface both. Picking one
  silently makes the next analysis wrong.

---

## When two paths disagree

If two queries that should produce the same number produce different
numbers, **do not pick one and proceed.** Diagnose. The common causes,
in roughly descending frequency:

1. **Different filters.** One query included returns, the other didn't.
   One filtered by `transaction_type = 'order'`, the other didn't. One
   used `created_date`, the other `fulfillment_date`.
2. **Different denominator on a margin.** `grossProfit / netRevenue` vs.
   `grossProfit / netSales` — see "Choosing the right denominator."
3. **Parent + child double-count in one of the queries.** When summing
   channel leaves, `is_leaf = TRUE` is required.
4. **Currency mix.** One query aggregated across currencies; the other
   filtered to one.
5. **Plan freeze boundary.** `smartmodel_actuals` (live) vs. a forecast
   plan's `is_actual = TRUE` rows can disagree for the same month if the
   forecast was frozen before the close happened.
6. **Casing duplicates.** Both `metric_id`s exist with different values.

Reconcile before publishing — to within rounding when the two paths should
produce the same number (same mart, same definitions), and to within the
expected timing / definitional drift when the paths cross marts. If
reconciliation isn't possible, surface both numbers with their queries
and stop — do not collapse the disagreement into a confident single value.

---

## Diagnostic depth — when to drill, widen, or stop

A common failure mode is drilling past the point of decision usefulness.
Guidelines:

- **Drill** when the current level of detail does not differentiate
  hypotheses you wrote down at the opening move. A channel-level result
  that doesn't separate "DTC weak" from "Amazon weak" warrants the next
  level (channel).
- **Widen** (look at a longer period or one more dimension) when the
  current finding might be a one-off. A 25% MoM drop is more informative
  in context of trailing 12 months than in isolation.
- **Stop** when (a) you have ruled out the hypotheses you can rule out,
  (b) the remaining hypotheses require data you don't have, or (c) the
  next drill would split the data into bins too small to interpret. Say
  what you found, name what you can't resolve, and offer the user a
  choice for the next step.

A short answer that says "X is the proximate cause; further attribution
requires ad-platform data we don't have here" is better than a long
answer that fakes precision.

---

## Communicating uncertainty

Uncertainty is part of the answer, not a footnote. Patterns that work:

- **Range, not point, when the denominator is ambiguous.** "YTD gross
  margin is between 38.2% and 41.7% depending on whether the denominator
  is `netSales` or `netRevenue` — verify with the user."
- **Confidence-by-source.** "The headline number is from
  `smartmodel_actuals` and ties to the customer's reported P&L. The
  channel split is from the ecommerce mart and may drift from SmartModel
  channel leaves due to refund-timing reconciliation."
- **Name the unknown.** "Marketing spend by platform is not in this
  warehouse; we can only show total marketing from SmartModel."
- **Stop short rather than guess.** If a query returns no rows and the
  most likely cause is a metric-ID mismatch, say so and run discovery —
  do not assume zero.

A wrong number stated confidently corrodes trust faster than a missing
answer. When in doubt, the right move is to say what you know, name what
you don't, and ask one targeted clarifying question.

---

## The discipline summary

In one paragraph: reframe before you query; enumerate hypotheses before
you drill; decompose with one framework at a time; verify denominators
before computing ratios; sanity-check magnitudes against the customer's
known scale; treat absence as information; reconcile disagreements
instead of collapsing them; drill only as far as the decision requires;
and state uncertainty as part of the answer. Everything else is
execution.
