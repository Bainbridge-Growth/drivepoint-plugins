# Scenario Planning — SmartModel Key Drivers

How to answer any "what if…?" / "what should I change to hit X?" question
against a customer's SmartModel plan using the plan-scenario tools. Runs on
the same Raptor path the Drivepoint webapp's **Preview Scenario** button
uses; the workbook file is never modified.

Applies to every ask that boils down to *edit some Key Drivers and see what
happens to Key Results* — cash extensions, margin plays, opex cuts,
working-capital sweeps, ad-spend / CAC reshaping, wholesale door expansion.

For visual style of any charts you produce from the recalculated output,
follow `artifact-style-guide.md` and `report-creation-guide.md`. This skill
governs the analysis loop only.

---

## When to use this skill

Any request that combines a **goal metric** (Cash, EBITDA, Net Revenue,
Gross Margin, Runway, DIO, …), a **direction / magnitude** ("improve by
10%", "get to breakeven", "extend runway to 18 months"), and a **time
horizon** ("next quarter", "by year-end", "FY 2027") is a scenario-planning
task. Also:

- "What should I change to hit …?"
- "Model a scenario where …"
- "What if we cut …?"
- "How much do I need to raise CAC / cut opex / add doors to …?"
- "Show me the P&L impact of …"

If the user only wants to inspect current values without simulating a
change, this is not a scenario task — use the read tools directly.

---

## The five-phase loop

Every scenario answer follows these phases, in order. Skipping a phase is
how you produce wrong numbers.

### Phase 0 — Frame the goal

Before any tool call, restate the ask to yourself:

- **Target metric** (which Key Result — e.g. `balanceSheet.cash`).
- **Direction & magnitude** (+10%, –$500k, breakeven, ratio).
- **Sign convention.** If the baseline is negative (overdraft, EBITDA
  loss, negative FCF), "improve by N%" is ambiguous — does the user mean
  *make the deficit N% smaller* or *cut the monthly burn by N%*? If it
  matters, confirm with the user in one sentence before running.
- **Time horizon** (which Forecast months matter — pick the tab's date
  spine window: quarter, half, calendar year, plan-end).
- **Lever preference.** Cash can be moved by cutting opex, improving
  margins, tightening working capital, or reshaping ad spend / CAC —
  each requires touching a very different driver set. If the user hasn't
  said which lever, ask once before pulling values.

Do not proceed until you can name the target metric, the horizon, and one
lever category to test.

### Phase 1 — Discover the plan

1. `list_company_plans` — pick the right `planId`. Prefer plans whose
   `state` is `active`. If multiple plans exist, name the one you chose
   in your reply.
2. `get_valid_plan_tabs` — returns the roll-forward tabs (the only tabs
   that carry Key Drivers / Key Results). Copy tab names verbatim,
   case-sensitive.

Standard tab shape you'll see in most CPG plans:

- `Control Panel - Master` — top-level DTC drivers (Blended CAC, AOV,
  channel mix, working-capital days).
- `DTC - OTP`, `DTC - SUB`, `AMZN - OTP`, `AMZN - SUB` — per-segment
  drivers (AOV, % Discounts, orders adjustments).
- `Wholesale` — doors, SKUs/door, units/SKU per retailer.
- `Opex` — line-item G&A / Contractors / Legal / R&D drivers.
- `M - Monthly` — where the P&L / balance-sheet **Key Results** live
  (Cash, EBITDA, Net Revenue, Gross Profit, Inventory, …). Almost every
  scenario's `results` array will target this tab.

### Phase 2 — Enumerate drivers and results (metadata only)

`list_plan_key_drivers_and_results` with the tabs you actually need for
the lever category the user picked. Do not scan every tab.

Typical tab selections:

| Lever category                | Tabs to include                                                                 |
| ----------------------------- | ------------------------------------------------------------------------------- |
| Opex cuts                     | `Opex`, `M - Monthly` (for Key Results)                                         |
| Working capital               | `Control Panel - Master`, `M - Monthly`                                         |
| DTC ad spend / CAC / AOV      | `Control Panel - Master`, relevant `DTC - *` / `AMZN - *` tabs, `M - Monthly`  |
| Wholesale expansion           | `Wholesale`, `M - Monthly`                                                      |
| Margin (pricing, product cost)| `Control Panel - Master`, per-segment tabs, `M - Monthly`                       |

Then pick the specific `{tab, id}` tuples that could plausibly move the
goal metric. Do not pass every driver into the next call — narrow first.
Present the shortlist to the user if the ambiguity is real (e.g. "these
five opex lines are the biggest movers — should I zero them all or a
subset?").

### Phase 3 — Pull baseline

Two things you need before proposing changes:

1. **Current values of the drivers you're considering** — via
   `get_plan_key_driver_values` with the shortlisted tuples, batched in a
   single call. Read the Forecast entries; that's what you'll edit.
   - Skip drivers whose values are `null` or `NaN` (common in dev / copy
     plans). Note them in your reply so the user knows they're excluded.
   - Use `dataType` to interpret magnitudes: `percent_*` values are
     decimals (0.15 = 15%), `currency_*` are dollars, `days_*` are day
     counts. "Cut by 10%" on a percent driver means subtract 0.10, not 10.
2. **Baseline of the target Key Result(s)** — via `preview_plan_scenario`
   with a **no-op change** (edit any one Forecast cell to its existing
   value from step 1) and the Key Results you're targeting in `results`.
   The returned `data` for those results is your baseline time series.

Do not eyeball the baseline. If the user needs before/after numbers, you
need a baseline preview run.

### Phase 4 — Design and run the scenario (one call, batched)

`preview_plan_scenario` with **every driver × every period** in a single
`changes` array. One scenario = one tool call. Splitting a scenario across
multiple calls compounds cost and makes diffing impossible.

Rules for `changes`:

- One entry per driver. Its `values` array holds every period you edit
  for that driver.
- `date` is YYYY-MM and must exactly match a Forecast period on that
  tab's date spine. Copy dates from the Forecast entries you saw in
  `get_plan_key_driver_values` — dates that don't match are silently
  ignored by Raptor.
- `value` is a literal cell value. Percent drivers take decimals.
- Never invent ids. Every `{tab, id}` must come verbatim from Phase 2.
- Only edit `Forecast` periods. Actuals are booked and locked.

Rules for `results`:

- Include every Key Result you plan to chart or reference in prose (Cash,
  EBITDA, Net Revenue, Gross Margin components, whatever the target is).
- Optionally include the edited drivers so you can confirm Raptor applied
  the change (their values in `data` should reflect your edits).
- Keep the list tight — every metric adds a Raptor lookup.

### Phase 5 — Compare, iterate, render as a chart artifact

Compare the scenario `data` against the baseline `data` from Phase 3,
Forecast periods only. Compute:

- **Absolute delta** at the horizon end month (the user's "by when").
- **Percent delta** at the horizon end month — using the correct sign
  convention for negative baselines (Phase 0).
- **Trajectory** across the horizon window if the metric is a stock
  (Cash, Inventory) — the shape matters, not just the endpoint.

If the scenario misses the target:

- Iterate on **magnitude** (deeper cuts, larger changes) before switching
  lever categories.
- Iterate on **timing** (cash is cumulative — cutting earlier compounds
  further). Extending an opex cut back one month often does more than a
  bigger cut in the horizon month alone.
- Only widen the lever category once you've established the current one
  can't reach the target. Say so explicitly.

#### Render as a React artifact, not a text table

The webapp's Preview Scenario UI is a chart. Match that. Every completed
scenario ships as a React/Recharts artifact
(`application/vnd.ant.react`) unless the user explicitly asked for text
only. Follow `artifact-style-guide.md` for tokens, layout, and the
`ArtifactHeader` lockup.

Default artifact shape:

1. **`ArtifactHeader`** — title is `<KeyResult> · Scenario Preview`,
   subtitle is the plan name, horizon window, currency, and (in one
   phrase) the levers you moved (e.g. "Opex cuts: 5 lines,
   Jun–Sep 2026").
2. **KPI card row** (3 cards across, `sm:grid-cols-3`):
   - Baseline at horizon end (formatted per `dataType` of the metric)
   - Scenario at horizon end (same formatting)
   - Delta — absolute value AND percent, both signed, with `↑`/`↓` and
     `text-emerald-600` / `text-red-600` per the artifact-style-guide
     rule ("never color alone"). For negative baselines, use the
     less-negative-is-better sign convention consistently.
3. **Two-series LineChart** — the primary trend, `ResponsiveContainer
   width="100%" height={360}`. One line for baseline, one for scenario,
   Forecast periods only, aligned monthly:

   ```jsx
   <LineChart data={rows}>
     <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
     <XAxis dataKey="date" stroke="#64748b" />
     <YAxis stroke="#64748b" tickFormatter={fmt} />
     <Tooltip formatter={fmt} />
     <Legend />
     <Line dataKey="baseline" name="Baseline" stroke="#cbd5e1" strokeWidth={2} dot={false} />
     <Line dataKey="scenario" name="Scenario" stroke="#5b8dd8" strokeWidth={2} dot={false} />
   </LineChart>
   ```

   `rows` is `[{date: '2026-07', baseline, scenario}, …]` built by
   inner-joining the baseline and scenario `data[tab][metric].values`
   on `date` where `type === 'Forecast'` and the date falls in the
   horizon window.

4. **Driver-change table** — the edits that produced the scenario. One
   row per driver, columns: metric name (`metricFriendlyName`), months
   edited (compact range like "Jun–Sep 2026"), before / after values
   (formatted per each driver's own `dataType`), monthly delta.
5. **Additional Key Results chart** — if the user cares about more than
   one output (e.g. Cash *and* EBITDA), add one more LineChart per
   metric. Do NOT stack multiple currencies or dimensionally different
   metrics on a single axis; use one chart per metric.
6. **Source footer** — `Source: plan '<planName>' · Raptor preview
   (workbook not modified)`. Keep this literal — it warns the user the
   change is not persisted.

Choose a different chart type only when the shape argues for it:

- **Diverging bar** — per-period variance (scenario − baseline) when the
  user cares more about "which months moved" than the trajectory.
- **Grouped bar** — comparing multiple scenarios side by side against
  baseline for the same horizon month.
- **`ComposedChart` with two Y axes** — showing driver movement and
  result movement together (e.g. ad spend line + gross-margin line). Use
  sparingly; it's dense.

Every number in the artifact is formatted per its metric's `dataType`.
Currency picks up the plan's currency, not a hardcoded `'USD'`.

#### Prose that ships with the artifact

Keep it short — the chart is the answer.

- **One-sentence headline.** What changed, what it delivered against the
  target. e.g. "Cutting five discretionary opex lines Jun–Sep 2026
  narrows the Sep cash deficit by 10.9% ($412K)."
- **A caveat when it applies.** Cutting sales-broker commissions or
  marketing-contractor lines to zero can starve the revenue driving the
  P&L — flag second-order effects the model can't compute. If cash is
  deeply negative and only marginally improved, say so — do not package
  a rounding-error win as a solution. Surface going-concern signals
  (deep negative cash, sub-quarter runway) as a separate flag above the
  artifact, not buried under the win.

Do not narrate the tool calls or the phases in the reply. The user sees
the answer, not the workflow.

---

## Anti-patterns from real sessions

Things that go wrong when the loop is not followed. Do not do these.

1. **Fabricating driver ids.** Ids like `opex_ga_line_item_1` don't
   exist unless Phase 2 returned them. Every id in `changes` / `results`
   must be copied verbatim from a prior tool response. Fabricated ids
   are silently ignored; the scenario appears to run but nothing changes.
2. **One tiny change instead of the full batch.** Sending a single edit
   like `[{tab: "Opex", id: "…", values: [{date: "2026-07", value: 39.99}]}]`
   when you intended to zero five drivers across four months. Always
   assemble the full `changes` array in one call.
3. **Skipping the baseline.** Running the scenario and asking the user to
   trust that "before" was worse. Always run a baseline preview first (or
   diff against Phase-3 driver values for driver-only comparisons).
4. **Ignoring NaN drivers.** A single NaN in a driver's Forecast can
   propagate through Raptor and produce garbage across every metric in
   `data`. If Phase 3 shows NaN, drop that driver from the scenario and
   surface it to the user.
5. **Sign-flip on negative baselines.** "Improve cash by 10%" against a
   -$3.8M baseline means -$3.42M (less negative), not -$4.18M. Confirm
   the interpretation before running, and use it consistently in the
   presentation.
6. **Percent-vs-decimal confusion.** Percent drivers (dataType
   `percent_*`) store decimals. "15%" is `0.15`, not `15`. "Cut by 10%"
   is a `-0.10` delta, not `-10`.
7. **Editing Actuals.** Only Forecast periods can be changed. Actuals in
   `changes` are ignored — do not include them.
8. **Multi-plan variance in one scenario.** Only one `planId` per
   scenario. If the user asks to compare two plans, that's a different
   analysis — not a scenario preview.
9. **Reading tab names loosely.** `M - Monthly` (with spaces) is not the
   same as `M-Monthly`. Copy tab names verbatim from `get_valid_plan_tabs`.
10. **Treating scenario output as final numbers.** The workbook is not
    modified. If the user wants the scenario committed, that requires the
    Drivepoint webapp — say so explicitly.

---

## Tool reference (quick)

| Phase | Tool                                    | Purpose                                                                 |
| ----- | --------------------------------------- | ----------------------------------------------------------------------- |
| 0     | (no tool — frame the goal in prose)     | Confirm target metric, horizon, lever, sign convention.                 |
| 1     | `list_company_plans`                    | Pick `planId`.                                                          |
| 1     | `get_valid_plan_tabs`                   | Get the roll-forward tab names for the plan.                            |
| 2     | `list_plan_key_drivers_and_results`     | Metadata for editable drivers and read-only results on chosen tabs.     |
| 3     | `get_plan_key_driver_values`            | Per-period values for the shortlisted drivers (batched).                |
| 3     | `preview_plan_scenario` (no-op)         | Baseline `data` for the target Key Results.                             |
| 4     | `preview_plan_scenario` (scenario)      | Recalculated `data` after your batched changes.                         |

All tools are read-only from the plan's perspective — nothing here mutates
the SmartModel workbook.

---

## Presentation defaults

- Lead with the answer, not the process. One sentence: what changed, what
  it delivered against the target.
- Every driver number is formatted per its `dataType` (currency with the
  plan's currency, percent to one decimal, days to zero decimals).
- Every result number keeps the plan's currency and shows the horizon
  month explicitly.
- Include the plan name (from `list_company_plans`) and last-booked-month
  context in the source-context line at the top, per
  `report-creation-guide.md` § "Source-context line".
- If the scenario reveals a going-concern issue (deeply negative cash,
  runway shorter than a quarter), surface that as a separate flag —
  don't bury it under the optimization result.
