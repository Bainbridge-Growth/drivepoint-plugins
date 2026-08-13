# Scenario Planning — SmartModel Key Drivers

How to answer any "what if…?" / "what should I change to hit X?" question
against a customer's SmartModel plan using the plan-scenario tools. Runs on
the same Raptor path the Drivepoint webapp's **Preview Scenario** button
uses; the workbook file is never modified.

Applies to every ask that boils down to _edit some Key Drivers and see what
happens to Key Results_ — cash extensions, margin plays, opex cuts,
working-capital sweeps, ad-spend / CAC reshaping, wholesale door expansion.

For visual style of any charts you produce from the recalculated output,
follow `artifact-style-guide.md` and `report-creation-guide.md`. This skill
governs the analysis loop only.

---

## Operating defaults (read first)

These override anything below if they conflict.

1. **Always preview — never ask for permission to run.** When the user asks a
   "what if…?" / scenario question, run `preview_plan_scenario` and return the
   result. Do not ask "should I run a scenario / preview this?" — just do it.
   The only thing you may confirm is a genuine ambiguity that changes the
   numbers (sign convention on a negative baseline, or which lever to move
   when the user named none). Never gate the preview itself behind a question.
2. **Say "model", not "plan".** In all user-facing prose call these workbooks
   **models** ("your live model", "this model"). Tool names and schema fields
   (`planId`, `list_company_plans`) keep their names — only your prose changes.
3. **Assume the live model — silently.** The live model is the plan whose
   `isLive` flag is true in `list_company_plans` (it matches the company's
   `liveSharepointPlanId`). Default to it silently: do NOT announce that you
   found or identified the live model, and do NOT explain your resolution
   logic. Never resolve a model by name alone. Only surface a choice if there
   is a real, unresolved ambiguity (e.g. no plan is flagged `isLive`).
4. **The output is always an artifact.** Every completed scenario ships as a
   React artifact built to the spec in Phase 5 and `artifact-style-guide.md`
   — never a bare text summary or a markdown table, unless the user explicitly
   asks for text only.
5. **Be explicit about drivers you skip.** Never silently drop a driver
   because its Forecast values are NA/NaN. Tell the user, in prose, which rows
   you used and which you skipped and why, and invite a correction (see Phase
   3).

---

## How the tool works (read this first)

`preview_plan_scenario` takes **high-level rules, not per-period numbers.**
You describe each Key Driver change once — a `value`, a `change_type`, and an
`interval_type` — plus a single `start_date`/`end_date` window. The server
pulls that driver's current Forecast values, expands your rule across the
window, recalculates through Raptor, and hands back everything you need:

- **`baseline`** — the current (pre-change) values of the Key Results you
  asked for. _This is your before-series; you never compute it or run a
  separate call to get it._
- **`scenario`** — the recalculated values of those Key Results after your
  rules. _This is your after-series._
- **`appliedChanges`** — the exact per-period `before`/`after` the server
  wrote for each driver. _This is your driver-change table; you never
  recompute it._
- **`skipped`** / **`missing`** — rules or metrics that were dropped (no-op,
  null/NaN, unknown id). _Always read these and surface anything relevant._

You do **not** hand-compute month-by-month values, and you do **not** run a
no-op baseline. One `preview_plan_scenario` call = one scenario, before and
after, in a single response.

### Rule anatomy

Each entry in `rules` is `{tab, id, value, change_type, interval_type}`:

- **`interval_type: "percent"`** — `value` is a percentage change. `10` is
  +10%, `-15` is −15%. Works on any driver regardless of its `dataType`.
  **This is the common case** ("increase AOV 10%", "cut blended CAC 15%").
- **`interval_type: "absolute"`** — `value` is added in the driver's native
  units. Dollars for `currency_*` (`value: 5` → +$5). Decimal points for
  `percent_*` (`value: 0.05` → +5 percentage points). Days for `days_*`.
- **`interval_type: "setTo"`** — `value` replaces the cell outright. Native
  units; decimal for `percent_*` drivers (`0.2` → set to 20%).
- **`change_type: "fromCurrent"`** — base is each month's own current value.
  Use this almost always.
- **`change_type: "fromPrevious"`** — base is the previous month's value; use
  for compounding ramps ("grow 3% month over month").

So "increase AOV by 10% across the forecast" is **one** rule:
`{tab, id, value: 10, change_type: "fromCurrent", interval_type: "percent"}`.

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
  _make the deficit N% smaller_ or _cut the monthly burn by N%_? If it
  matters, confirm with the user in one sentence before running.
- **Time horizon** (which Forecast months matter — this becomes your
  `start_date`/`end_date` window: quarter, half, calendar year, plan-end).
- **Lever preference.** Cash can be moved by cutting opex, improving
  margins, tightening working capital, or reshaping ad spend / CAC —
  each requires touching a very different driver set. If the user hasn't
  said which lever, ask once before pulling values.

Do not proceed until you can name the target metric, the horizon, and one
lever category to test.

### Phase 1 — Discover the plan

1. `list_company_plans` — pick the right `planId`. Default silently to the plan
   whose `isLive` flag is true (it matches the company's `liveSharepointPlanId`).
   Do NOT announce that you found or picked the live model, and never resolve by
   name alone. Only ask the user if no plan is flagged `isLive`, or there is a
   genuine, unresolved ambiguity (see Operating defaults #3).
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

| Lever category                 | Tabs to include                                                               |
| ------------------------------ | ----------------------------------------------------------------------------- |
| Opex cuts                      | `Opex`, `M - Monthly` (for Key Results)                                       |
| Working capital                | `Control Panel - Master`, `M - Monthly`                                       |
| DTC ad spend / CAC / AOV       | `Control Panel - Master`, relevant `DTC - *` / `AMZN - *` tabs, `M - Monthly` |
| Wholesale expansion            | `Wholesale`, `M - Monthly`                                                    |
| Margin (pricing, product cost) | `Control Panel - Master`, per-segment tabs, `M - Monthly`                     |

Then pick the specific `{tab, id}` tuples that could plausibly move the
goal metric. Do not pass every driver into the next call — narrow first.
Present the shortlist to the user if the ambiguity is real (e.g. "these
five opex lines are the biggest movers — should I zero them all or a
subset?").

### Phase 3 — Sanity-check the drivers you'll move (no baseline call)

Call `get_plan_key_driver_values` for the shortlisted drivers, batched in a
single call. You need this to:

- **Confirm the driver is usable** — skip drivers whose Forecast values are
  `null` or `NaN` (common in dev / copy plans). **Never skip silently.** Tell
  the user which rows you moved and which you left alone and why, and invite a
  correction. Make the user aware, e.g.: "You only have one populated Ad Spend
  row which is Facebook. There's others but they contain NA so I won't touch
  them. If you believe that's a mistake please correct me." This is required
  whenever a plausible driver is dropped for NA/NaN values — do not bury it.
- **Read `dataType` so you pick the right `interval_type`.** A "10%
  increase" is `interval_type: "percent", value: 10` on _any_ driver. An
  absolute +5-point bump on a `percent_*` driver is
  `interval_type: "absolute", value: 0.05`. A "$5 higher AOV" on a
  `currency_*` driver is `interval_type: "absolute", value: 5`.
- **Ground your magnitude in reality** — know roughly where the driver sits
  before proposing a change, and to explain the before/after in prose.

You do **not** transcribe these per-period values into the next call, and
you do **not** run a no-op baseline — `preview_plan_scenario` returns the
Key-Result `baseline` for you.

### Phase 4 — Design and run the scenario (one call, batched rules)

`preview_plan_scenario` with **one rule per driver** and a single
`start_date`/`end_date` window. One scenario = one tool call. Splitting a
scenario across multiple calls compounds cost and makes diffing impossible.

Rules for `rules`:

- One entry per driver: `{tab, id, value, change_type, interval_type}`. See
  **Rule anatomy** above.
- Do **not** send per-period values — the server expands your rule across
  every Forecast month in `[start_date, end_date]`.
- `start_date` / `end_date` are `YYYY-MM` and should sit inside the Forecast
  horizon. Actuals that fall in the window are ignored (only Forecast is
  editable).
- For a "% change", use `interval_type: "percent"` with the **whole-number
  percent** (`10`, not `0.10`). Reserve decimals for `absolute` / `setTo`
  on percent-typed drivers.
- Never invent ids. Every `{tab, id}` must come verbatim from Phase 2.

Rules for `results`:

- Include every Key Result you plan to chart or reference in prose (Cash,
  EBITDA, Net Revenue, Gross Margin components, whatever the target is).
- Keep the list tight — every metric adds a Raptor lookup, and every metric
  you list gets both a `baseline` and a `scenario` series back.

After the call, **read `skipped` and `missing`.** If a driver you meant to
move shows up there, your rule was a no-op (percent/absolute value 0), the
current values were null/NaN, or the `{tab, id}` was wrong — fix it and
rerun. Do not claim a change that landed in `skipped`/`missing`.

### Phase 5 — Compare, iterate, render as a chart artifact

Compare the returned `scenario` against `baseline` (both come from the same
call), Forecast periods only. Compute:

- **Absolute delta** at the horizon end month (the user's "by when").
- **Percent delta** at the horizon end month — using the correct sign
  convention for negative baselines (Phase 0).
- **Trajectory** across the horizon window if the metric is a stock
  (Cash, Inventory) — the shape matters, not just the endpoint.

The driver-change table comes straight from `appliedChanges` — no
recomputation.

If the scenario misses the target:

- Iterate on **magnitude** (raise the rule's `value`) before switching
  lever categories.
- Iterate on **timing** (cash is cumulative — extending the window earlier
  compounds further). Widening `start_date` back a month often does more
  than a bigger `value` in the horizon month alone.
- Only widen the lever category once you've established the current one
  can't reach the target. Say so explicitly.

---

## Visualization — match the Drivepoint webapp

> **The visualization is not a generic chart. It reproduces the
> Drivepoint "Scenario Preview / Scenario Details" experience the webapp
> ships.** The reference design lives in Figma (`DVPT-Experiments`, the
> "FI feedback on index screens, preview and results" board, node
> `8019-297`). An AI client building this artifact should reproduce that
> layout, not invent its own. Below is that layout in enough detail to
> build it without opening Figma; open the Figma frame only when you need
> exact pixel/token values.

Every completed scenario ships as a **React/Recharts artifact**
(`application/vnd.ant.react`) unless the user explicitly asked for text
only. **`artifact-style-guide.md` governs every visual token** — brand
colors, `CompactHeader` / `BuiltWithFooter`, card surfaces, fonts, and
number formatting. Do not invent your own colors, marks, or surfaces here. The
Figma reference above informs only the scenario-specific *layout* (the two
screens below) and *series roles* (which line is baseline vs. scenario);
everything you draw pulls its style from the artifact style guide.

### Which of the two layouts to build

The reference board contains **two distinct screens**. Pick based on how
many scenarios you are presenting:

1. **Single-scenario preview** (one scenario vs. baseline) — build the
   compact layout: `CompactHeader` → KPI card row → two-series line chart
   → driver-change table → source line + `BuiltWithFooter`. This is the
   common case for "what if we cut opex by X?"
2. **Multi-scenario comparison** (2+ candidate scenarios, e.g. a
   Drivepoint-Intelligence-style set of proposals) — same compact chrome,
   fuller body: `CompactHeader` → proposals summary → comparison chart →
   **Scenario Details** table with per-scenario rows and controls. This
   is the case for "give me a few scenarios to hit breakeven." Run one
   `preview_plan_scenario` call per candidate scenario (each with its own
   `rules`), then compare their `scenario` series.

Do not mix them. If unsure, default to the single-scenario preview.

### Shared chrome (both layouts)

**1. Compact header.** Render `CompactHeader` from
`artifact-style-guide.md` § "Customer-built compact header" as the first
child — no lockup or logomark in the header.

- `kind` — e.g. "Scenario comparison" or "Scenario preview".
- `period` — horizon window (e.g. "JUN–SEP 2026").
- `title` — the experiment / scenario name (e.g. "Ad Spend and CAC ·
  03/15/2025" or "`<KeyResult>` · Scenario Preview").
- `subtitle` — the plan name, currency, and — in one phrase — the levers
  you moved ("Opex cuts: 5 lines, Jun–Sep 2026").
- In the multi-scenario layout only, add a "Drivepoint Intelligence"
  wordmark with a small **BETA** pill (Drivepoint yellow `#FFDE6A` fill /
  `#191815` text) below the header, above the proposals block.

**2. Source + Built with footer.** Source line:
`Source: plan '<planName>' · Raptor preview (workbook not modified)`.
Close with `BuiltWithFooter`. Keep the source line — it warns the user
the change is not persisted.

**3. Formatting.** Every number is formatted per its metric's `dataType`
(currency in the _plan's_ currency, not hardcoded USD; percent to one
decimal; days to zero decimals). Color deltas with
`DP_CHART_DELTA.positive` (better) / `DP_CHART_DELTA.negative` (worse)
**and** a `↑`/`↓` glyph — never color alone. For negative baselines use the
less-negative-is-better convention consistently.

### Series roles (from the chart palette)

`artifact-style-guide.md` § "Color tokens" is the palette. Do not add new
hexes — map each scenario series onto the existing tokens:

- **Baseline series line:** `DP_CHART_DELTA.forecast` (`#cbd5e1`),
  `strokeWidth={2}`, `dot={false}`.
- **Scenario / primary series line:** `DP_CHART_SERIES[0]`,
  `strokeWidth={2}`, `dot={false}`.
- **Second comparison series (two scenarios on one small chart):**
  `DP_CHART_SERIES[1]`.
- **Target / "winning" region highlight** (scatter view): the favorable
  token — border `#2f7d54`, fill `rgba(47,125,84,0.08)`.

Grid, axes, cards, page background, fonts, and spacing are **not**
redefined here — use them exactly as `artifact-style-guide.md` specifies
(grid `#ecebe9` `strokeDasharray="3 3"`, axis text `#716e6b`, cards
`border border-[#ecebe9] rounded-lg shadow-sm` on `bg-[#fefefe]`).

### Layout A — single-scenario preview (compact)

This is the default output for every single-scenario "what if…?". Build it top
to bottom exactly in this order. The Drivepoint logo sits top-right via
`CompactHeader` (shared chrome).

> **Everything below is a structure spec, not literal copy.** The example
> wording ("Facebook Ad Spend", "EBITDA", "$4K", "20%") is illustrative — every
> label, sentence, and number is derived from the actual driver you moved and
> the actual target Key Result. Never hardcode "EBITDA" or "Facebook Ad Spend";
> substitute the real `metricFriendlyName`s and values from the tool response.

1. **Header lockup** (shared chrome above). The `CompactHeader` `title` is the
   **plain-English impact statement** — what the change did to the target Key
   Result, in one line, with real numbers, composed from `{driver} {direction}
{magnitude} {verb} {targetMetric} by {formatted delta}`. Example shape (not
   literal):

   > "A 20% increase in Facebook Ad Spend increases EBITDA by $4K"

   Build it from the driver moved + the target metric's delta at the horizon
   end (direction word + formatted amount). The `subtitle` carries the model
   name, horizon window, currency, and lever phrase.

2. **Exec summary** — a 2–3 line text block directly under the header saying
   what changed and the headline result (the "so what"). Muted slate
   (`text-slate-600`), `text-sm`. This is prose, not a restatement of the tiles.
3. **Three tiles** — 3 cards across (`sm:grid-cols-3`), each a bordered white
   card with a small uppercase label and a large value. The labels are dynamic
   — use the real driver and Key Result names, not the example words:
   - **Input** — the driver change you applied (e.g. "Facebook Ad Spend +20%",
     or the before → after value), formatted per the driver's `dataType`.
   - **`<Target metric>` Output** — the target Key Result's scenario value at
     the horizon end, labeled with that metric's real `metricFriendlyName`
     ("EBITDA" in the example is just one possible target).
   - **`<Target metric>` Change** — the delta vs. baseline: absolute **and**
     percent, both signed, with `↑`/`↓` and the emerald/red rule above.
4. **Baseline-vs-scenario `LineChart`** — the primary trend,
   `ResponsiveContainer width="100%" height={360}`. Baseline + scenario,
   Forecast periods only, aligned monthly:

   ```jsx
   <LineChart data={rows}>
     <CartesianGrid strokeDasharray="3 3" stroke="#ecebe9" />
     <XAxis dataKey="date" stroke="#716e6b" />
     <YAxis stroke="#716e6b" tickFormatter={fmt} />
     <Tooltip formatter={fmt} />
     <Legend formatter={(value) => <span style={{ color: '#191815' }}>{value}</span>} />
     <Line
       dataKey="baseline"
       name="Baseline"
       stroke={DP_CHART_DELTA.forecast}
       strokeWidth={2}
       dot={false}
     />
     <Line
       dataKey="scenario"
       name="Scenario"
       stroke={DP_CHART_SERIES[0]}
       strokeWidth={2}
       dot={false}
     />
   </LineChart>
   ```

   Build `rows` by inner-joining the tool's `baseline` and `scenario`
   result series on `date`, over the Forecast periods in your horizon
   window (both live in the single `preview_plan_scenario` response):

   ```jsx
   // result = the preview_plan_scenario response
   const baseVals = result.baseline[tab].find((m) => m.id === metricId).values;
   const scenVals = result.scenario[tab].find((m) => m.id === metricId).values;

   const byDate = {};
   for (const v of baseVals) {
     if (v.type === "Forecast")
       byDate[v.date] = { date: v.date, baseline: v.value };
   }
   for (const v of scenVals) {
     if (v.type === "Forecast")
       (byDate[v.date] ??= { date: v.date }).scenario = v.value;
   }
   const rows = Object.values(byDate)
     .filter((r) => r.date >= startDate && r.date <= endDate)
     .sort((a, b) => a.date.localeCompare(b.date));
   ```

   **Make the change visible.** A common failure is a chart where "nothing
   looks like it changed" because the two lines are visually identical against
   a tall, zero-anchored axis. Do NOT force the Y axis to start at 0. Compute a
   focused domain around the two series so the gap between baseline and scenario
   is legible:

   ```jsx
   const vals = rows
     .flatMap((r) => [r.baseline, r.scenario])
     .filter((n) => n != null);
   const lo = Math.min(...vals),
     hi = Math.max(...vals);
   const pad = (hi - lo) * 0.15 || Math.abs(hi) * 0.05 || 1;
   // <YAxis domain={[lo - pad, hi + pad]} ... />
   ```

   If the two series are still nearly indistinguishable at this zoom (a very
   small relative delta), add a companion **delta series** (scenario − baseline)
   as a second small chart or a secondary axis so the movement is unmistakable,
   and say in prose that the effect is small.

5. **Driver-change table** — the edits that produced the scenario, built
   directly from `appliedChanges`. One row per driver; columns: metric name
   (`metricFriendlyName`), months edited (compact range from the entry's
   `values` dates, "Jun–Sep 2026"), before / after (from each entry's
   `values`, formatted per that driver's own `dataType`), monthly delta.
   Do not recompute these — they are the exact values the server sent to
   Raptor.
6. **Additional Key Results chart** — only if the user cares about more
   than one output (e.g. Cash _and_ EBITDA): one more `LineChart` per
   metric, using the same `baseline`/`scenario` join. Never stack
   different currencies or dimensionally different metrics on one axis —
   one chart per metric.
7. **Recommendation** — a 2–3 sentence closing block (bordered card or
   muted callout) giving your judgment: is this the highest-leverage move to
   hit the user's goal, or would another lever/scenario do more? Name the
   concrete alternative(s) worth running next (e.g. "cutting blended CAC 10%
   moves EBITDA ~3x more than this ad-spend bump — want me to run it?"). Base
   this on the magnitudes you actually observed, not generic advice.
8. **Source footer** (shared chrome).

### Layout B — multi-scenario comparison (full)

Reproduces the "N Scenario Proposals" + "Scenario Details" screens. In
order:

1. **Compact header** with the **Drivepoint Intelligence · BETA** wordmark.
2. **Proposals summary** — a short "`N` Scenario Proposals" heading and a
   one-line rationale sentence ("I've identified `N` scenarios that best
   optimize `<lever>` based on the following trends and criteria.").
   Optionally a responsive grid of small "trend" cards (one per basis:
   Short-Term Growth, Medium-Term, Seasonality, Benchmarks, …), each a
   titled mini `LineChart` (`DP_CHART_SERIES[0]` vs. `DP_CHART_SERIES[1]`,
   `dot={false}`, no legend, tiny axes). Only include the trend cards you
   actually have data for — do not fabricate bases.
3. **Comparison chart** — one chart comparing the candidate scenarios
   across the horizon:
   - Default: a multi-line `LineChart`, one line per scenario's `scenario`
     series, over the Forecast horizon (share one `baseline` line).
   - Give line comparisons a data-derived padded Y-axis domain. Do not
     default to zero when every series occupies a narrow high-value band;
     that hides the differences this view exists to compare.
   - When the user cares about the scenario's position in a tradeoff
     space (e.g. CAC vs. Ad Spend), use a `ScatterChart` with a
     translucent **green target region** marking the desirable zone
     (tokens above) and a tooltip showing the scenario's key coordinates.
4. **Scenario Details table** — the centerpiece. A bordered white card
   titled "Scenario Details" with the subtitle "Analyze scenario impact
   month by month on output variable." It has:
   - **Controls row** (right-aligned): a "Show relative variance" toggle,
     a **Date Range** picker (reflecting the horizon), and an **Output
     Variable** selector (the Key Result being compared, e.g. EBITDA).
     In a static artifact these are real, working React controls:
     the toggle switches the table between absolute values and
     variance-vs-baseline; the Output Variable `<select>` re-renders the
     table against whichever Key Result the user picks when more than one
     Key Result is present (include every Key Result you pulled in
     `results`). Use a read-only Output Variable label when exactly one
     Key Result is present. The Date Range can be a read-only label if you
     only have one horizon.
   - **Table**: a leading checkbox + scenario-name column, then one column
     per month across the horizon (Month 1 … Month N, labeled with the
     actual `YYYY-MM`). One row per scenario. Values formatted per the
     output variable's `dataType`.
   - **Row annotations**: mark the recommended row with a small subtitle
     under its name — "Drivepoint Intelligence Winner" — and a secondary
     candidate with "Secondary Pick". Select (checkbox) the winner by
     default. Do not invent a winner; base it on the delta-vs-target you
     computed in Phase 5, and say in prose why it won.
   - **Relative-variance mode**: when the toggle is on, show each cell as
     the signed delta vs. baseline (favorable/unfavorable color + arrow),
     not the raw value.
5. **Source footer** (shared chrome).

### Choosing a non-default chart type

Only when the shape argues for it:

- **Diverging bar** — per-period variance (scenario − baseline) when
  "which months moved" matters more than the trajectory.
- **Grouped bar** — comparing multiple scenarios side by side against
  baseline for a single horizon month.
- **`ComposedChart` with two Y axes** — driver movement and result
  movement together (e.g. ad-spend line + gross-margin line). Use
  sparingly; it's dense.

### Interactivity rules for the React artifact

The webapp screens are interactive; the artifact should be too, within
what static data allows.

- All state is React state (`useState`) — **never** `localStorage` /
  `sessionStorage` (unsupported in artifacts).
- Toggles and selectors recompute from the `data` you already have in
  memory; they must not attempt any tool or network call.
- Do **not** wire the "SAVE TO CURRENT PLAN" / "RUN EXPERIMENT" buttons to
  anything. If you render them (optional, for visual fidelity), they are
  inert and you must keep the source-footer caveat that the workbook is
  not modified. Committing a scenario requires the Drivepoint webapp — say
  so if the user asks.
- Do not call the Anthropic API or any MCP server from inside the artifact
  for this skill — the scenario data is computed by Raptor before the
  artifact is built and passed in as static props/data.

### Prose that ships with the artifact

Keep it short — the chart is the answer.

- **One-sentence headline.** What changed, what it delivered against the
  target. e.g. "Cutting five discretionary opex lines Jun–Sep 2026
  narrows the Sep cash deficit by 10.9% ($412K)."
- **A caveat when it applies.** Cutting sales-broker commissions or
  marketing-contractor lines to zero can starve the revenue driving the
  P&L — flag second-order effects the model can't compute. If cash is
  deeply negative and only marginally improved, say so — do not package a
  rounding-error win as a solution. Surface going-concern signals (deep
  negative cash, sub-quarter runway) as a **separate flag above the
  artifact**, not buried under the win.
- **Anything in `skipped` / `missing`** that affected the answer (a driver
  you meant to move but couldn't, because it was NaN or a no-op).

Do not narrate the tool calls or the phases in the reply. The user sees
the answer, not the workflow.

---

## Anti-patterns from real sessions

Things that go wrong when the loop is not followed. Do not do these.

1. **Fabricating driver ids.** Ids like `opex_ga_line_item_1` don't
   exist unless Phase 2 returned them. Every id in `rules` / `results`
   must be copied verbatim from a prior tool response. Fabricated ids
   land in `missing`; the scenario appears to run but that driver never
   moved.
2. **Splitting a scenario across calls.** Sending one driver's rule, then
   another driver's rule in a second call. Assemble **all** driver rules
   into a single `preview_plan_scenario` call so baseline and scenario are
   internally consistent and diffable.
3. **Fabricating a before-series.** The `baseline` is returned to you —
   never eyeball, hand-type, or approximate "before" numbers. If you need
   before/after, it's already in the response.
4. **Ignoring NaN drivers.** A NaN driver can't be expanded — the server
   skips those periods and lists the driver in `skipped`. Drop it from the
   scenario and surface it to the user rather than pretending it moved.
5. **Sign-flip on negative baselines.** "Improve cash by 10%" against a
   -$3.8M baseline means -$3.42M (less negative), not -$4.18M. Confirm
   the interpretation before running, and use it consistently in the
   presentation.
6. **Percent-vs-decimal confusion.** A "% change" is
   `interval_type: "percent"` with a **whole number** — "increase 10%" is
   `value: 10`, "cut 10%" is `value: -10`. Passing `0.10` for "10%" is a
   0.1% change. Decimals are only for `absolute` / `setTo` on `percent_*`
   drivers (e.g. `absolute` `0.05` = +5 percentage points).
7. **Windowing onto Actuals.** Pick `start_date` / `end_date` inside the
   Forecast horizon. Actuals that fall in the window are booked and are
   ignored — they won't error, but they also won't move.
8. **Multi-plan variance in one scenario.** Only one `planId` per
   scenario. If the user asks to compare two plans, that's a different
   analysis — not a scenario preview.
9. **Reading tab names loosely.** `M - Monthly` (with spaces) is not the
   same as `M-Monthly`. Copy tab names verbatim from `get_valid_plan_tabs`.
10. **Treating scenario output as final numbers.** The workbook is not
    modified. If the user wants the scenario committed, that requires the
    Drivepoint webapp — say so explicitly.
11. **Inventing the visualization layout.** The Scenario Preview /
    Scenario Details design is fixed (Figma `8019-297`). Build Layout A or
    Layout B as specified above — do not substitute a bare chart or a
    text table when the artifact is expected.
12. **Fabricating a "winner" or trend bases.** Only annotate a
    Drivepoint-Intelligence winner / secondary pick, or render a trend
    card, for scenarios and bases you actually computed. No placeholder
    proposals.
13. **Wiring artifact buttons to actions.** SAVE / RUN buttons are inert;
    toggles and selectors recompute from in-memory data only. No tool,
    network, or storage calls from inside the artifact.
14. **Ignoring `skipped` / `missing`.** If a rule silently did nothing it
    is reported there. Read it every time; never claim a change that was
    skipped or dropped.

---

## Tool reference (quick)

| Phase | Tool                                | Purpose                                                                                         |
| ----- | ----------------------------------- | ----------------------------------------------------------------------------------------------- |
| 0     | (no tool — frame the goal in prose) | Confirm target metric, horizon, lever, sign convention.                                         |
| 1     | `list_company_plans`                | Pick `planId`.                                                                                  |
| 1     | `get_valid_plan_tabs`               | Get the roll-forward tab names for the plan.                                                    |
| 2     | `list_plan_key_drivers_and_results` | Metadata for editable drivers and read-only results on chosen tabs.                             |
| 3     | `get_plan_key_driver_values`        | Sanity-check drivers (NaN / dataType / rough magnitude) — not transcribed.                      |
| 4     | `preview_plan_scenario` (rules)     | Expand your rules across the window → Raptor; returns `baseline`, `scenario`, `appliedChanges`. |

All tools above are read-only from the model's perspective — nothing in the
scenario-preview loop mutates the workbook.

---

## Editing a model (write tools)

Separate from the read-only preview loop, three tools **modify the live model
workbook** on SharePoint. Use them only when the user explicitly asks to change
the model (add a line item, mark a row as a driver/result) — never as part of a
"what if…?" preview.

- `search_plan_row` — read-only. Find the row number for a label / id on a tab
  (matches column C friendly name and/or column B id and/or column A marker).
  Always run this first to get the exact `rowNumber`.
- `add_plan_row` — inserts a **blank row at `rowNumber` first** (existing rows
  shift down), then writes `cells` (keyed by column letter: A = marker, B =
  durable id, C = friendly name, K onward = the monthly spine). Requires
  `confirm: true`; without it you get a preview.
- `mark_key_driver_or_result` — marks a row as a Key Driver or Key Result. The
  marker is always written to **column A** (that is the single set/enable
  action — there is no separate step); a durable id is generated into column B
  if missing. Requires `confirm: true`.

Workflow: `search_plan_row` → (optional) `add_plan_row` → `mark_key_driver_or_result`.

Rules for write tools:

- These **modify the workbook** (unlike preview). Show the user what you will
  change and get their go-ahead, then call with `confirm: true`.
- After marking a row, its `{tab, id}` becomes usable by
  `list_plan_key_drivers_and_results` and the preview loop.
- Copy `tab` verbatim from `get_valid_plan_tabs`; use the `rowNumber` from
  `search_plan_row` — never guess a row.

| Tool                        | Modifies workbook? | Purpose                                                                     |
| --------------------------- | ------------------ | --------------------------------------------------------------------------- |
| `search_plan_row`           | No                 | Locate a row by label / id / marker.                                        |
| `add_plan_row`              | Yes (confirm)      | Insert a blank row above `rowNumber`, then write values.                    |
| `mark_key_driver_or_result` | Yes (confirm)      | Write the Key Driver / Key Result marker into column A (+ durable id in B). |

---

## Presentation defaults

- Lead with the answer, not the process. One sentence: what changed, what
  it delivered against the target.
- Every driver number is formatted per its `dataType` (currency with the
  plan's currency, percent to one decimal, days to zero decimals).
- Every result number keeps the model's currency and shows the horizon
  month explicitly.
- Include the model name (from `list_company_plans`) and last-booked-month
  context in the source-context line at the top, per
  `report-creation-guide.md` § "Source-context line".
- If the scenario reveals a going-concern issue (deeply negative cash,
  runway shorter than a quarter), surface that as a separate flag —
  don't bury it under the optimization result.
