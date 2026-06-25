---
name: price-change-analysis
description: Model the financial impact of a price change on one or more SKUs — including sales-mix-weighted AOV adjustments, COGS-as-%-of-revenue pass-through, and per-channel handling. Use when a user asks to "raise the price of [product]", "increase prices on [SKU] by X%", "increase SKU prices", "model a price increase", "price change scenario", "drop price on [SKU]", or "what would a [X]% price increase do to margin?" Also triggers on "price cut", "price drop", "discount strategy", "ASP increase", "list price change", "pricing scenario", or "what if we raised prices on [product]".
---

# Price Change Analysis

**Purpose**: Model a price change on a specific SKU or product family with the right math for the model's actual structure — sales-mix-weighted AOV updates for blended models, direct price edits for SKU-level models, and COGS-margin pass-through so the gross-margin impact actually flows through.
**Prerequisite**: The `smartmodel-protocol` skill must be loaded.

---

## When This Skill Activates

- User asks to raise or lower the price of a specific SKU, product, product family, or SKU set
- User asks to increase SKU prices, increase prices on a named product, or test a price increase/decrease
- User asks "what if we increased / decreased price on [product] by X%"
- User asks to model a price-change scenario
- User wants to understand the margin and revenue impact of a pricing decision before committing to it

This skill is more specific than `/create-scenario` for pricing. Load this for any SKU, product, product-family, ASP, AOV, discount, price increase, or price decrease prompt. Fall back to `/create-scenario` only when the user explicitly asks for a broad portfolio scenario with no SKU/product pricing work.

---

## Phase 1 — Define the Price Change

**Step 1.1 — Use model context from the protocol**
Settings, index, and date spine are already loaded by the protocol's auto-orient. From the model context, note: `companyName`, `currency`, the most recently closed Actual month (used as the end of the sales-mix window in Phase 3), the first Forecast period (price changes apply here only), and the channel revenue sheet names.

**Step 1.2 — Capture the price change from the user**
Required: scope and magnitude. For everything else, pick a sensible default, state the assumption, and proceed — the user can redirect.

| Input | Required? | Default if not specified |
|-------|-----------|--------------------------|
| Scope (SKU, product family, or product line) | Yes | — |
| Magnitude (% or absolute) | Yes | — |
| Direction | Derived | Sign of magnitude |
| Effective period | No | First Forecast period in the model |
| Duration | No | Permanent (all Forecast periods from the effective month forward) |
| Channels affected | No | All channels carrying the SKU |

If the affected SKU is not present in the model's product registries on any channel, stop and tell the user — the analysis cannot proceed without identifying the SKU's row(s).

Restate the captured scope (with defaults flagged) before moving on. Example: *"Increasing the list price of [SKU] by 20%, effective [first forecast month], permanent, across all channels carrying the SKU. Let me know if any of these defaults are wrong."*

---

## Phase 2 — Classify the Model's Pricing Structure

This is the critical orientation step. The same prompt produces very different work depending on how the model represents price.

**Step 2.1 — Inspect the channel revenue sheets**
For each channel affected by the price change, call `read_smartmodel_registries` and `read_smartmodel_data_section` on the channel sheet. Look for:
- A **price** or **ASP** Key Driver row per SKU dimension → SKU-level pricing
- An **AOV** Key Driver row per customer-type / segment combination (e.g., OTP first-time, OTP returning, SUB first-time, SUB returning) → blended AOV pricing

**Step 2.2 — Classify the model**

| Type | Structure | Path |
|------|-----------|------|
| **A — SKU-level price drivers** | Each channel has a price/ASP input per SKU | Skip to Phase 5; the price change is a direct edit to the affected SKU's price row |
| **B — Blended AOV at segment level** | Channel sheets have AOV rows by customer-type / segment, no per-SKU price | Run Phases 3–5; AOV must be adjusted by the SKU's revenue share, not the full price-change % |
| **C — Hybrid** | Some channels are Type A, others Type B | Apply Type A path per Type-A channel and Type B path per Type-B channel |

**Step 2.3 — State the classification explicitly to the user**

Before proceeding, output one line:

```
Pricing structure: [Type A / Type B / Type C — explanation]
Plan: [one-sentence summary of which phases will run]
```

Example: *"Pricing structure: Type B — model uses blended AOV by segment on both DTC and Amazon. Plan: compute per-channel sales mix for the affected SKU, derive segment-specific AOV uplifts, update COGS-as-%-of-revenue, then write changes to the effective period."*

---

## Phase 3 — Sales Mix Analysis (Type B/C only)

A blended AOV represents the average revenue per order across all SKUs in that segment. A 20% price hike on a SKU that is 11% of segment **revenue** does **not** raise AOV by 20% — it raises AOV by ~2.2% (11% × 20%). `sales_mix` is always a revenue share, not an order share — the math below assumes that and would be wrong if mix is computed by units or order count.

**Step 3.1 — Locate the product sales-mix R-sheet per channel**
Each channel typically has its own product-level sales R- sheet (e.g., a Shopify product mix sheet, an Amazon product sales sheet). Call `read_r_sheet` on each. The sheet should have product/SKU rows with revenue and the customer-type / segment dimensions aligned to the channel's AOV inputs.

If the relevant R- sheet is empty or missing, stop and tell the user which sheet needs to be populated before the analysis can proceed.

**Step 3.2 — Compute sales mix per segment, per channel**
Use a representative recent window — typically the **last 3 closed months**. If the model has fewer than 3 closed months of data, use what is available and explicitly flag the small sample. State the window before computing.

For each segment that has its own AOV Key Driver (e.g., DTC OTP first-time, DTC OTP returning, DTC SUB first-time, DTC SUB returning, AMZN OTP, AMZN SUB):

```
sales_mix = (gross revenue from affected SKU(s) in segment) / (gross revenue from all SKUs in segment)
```

If the affected SKU is highly seasonal or recently launched and the trailing window does not represent forward expectations, flag this and ask the user whether to use a different window or apply a forward-looking mix assumption.

**Step 3.3 — Derive segment-specific AOV uplift**

For each segment:

```
new_AOV = old_AOV × (1 + sales_mix × price_change_pct)
```

Not `old_AOV × (1 + price_change_pct)` — that assumes every order is the affected SKU and overstates revenue.

**Modeling assumption — volume held constant.** This formula models the price effect only. It assumes order count and within-segment SKU mix remain unchanged after the price change. In reality, a price increase typically reduces volume (price elasticity); a price decrease may lift it. If the user wants to layer a volume response (e.g., *"a 20% hike will reduce DTC orders by 5%"*), apply that as a separate Key Driver edit on the orders/volume row in addition to the AOV change. Surface this assumption to the user before writing — explicitly offer the option to layer a volume response.

**Step 3.4 — Per-channel mix is required**
**Never reuse one channel's sales mix for another.** DTC, Amazon, and Wholesale generally have materially different SKU mixes. Compute each channel's sales mix from its own R- sheet. If a channel's R- sheet is empty, do not substitute another channel's mix — surface the gap to the user.

Output a sales-mix table before proceeding to Phase 4:

```
Channel: [name]   Window: [date range]
| Segment | Affected SKU mix | Old AOV | New AOV | Δ AOV |
| ...     | ...              | ...     | ...     | ...   |
```

---

## Phase 4 — COGS Margin Pass-Through

A price increase raises gross revenue but the unit cost of the SKU has not changed. If the model represents COGS as a fixed **% of revenue** Key Driver, that percentage must come down or the gross margin improvement will not flow through.

**Step 4.1 — Identify the COGS driver structure**

| Structure | Where to find it | Pass-through |
|-----------|-----------------|--------------|
| COGS as % of revenue (per channel) | Product / COGS schedule sheet, % Key Driver row | Must update — Phase 4.2 |
| COGS as $/unit | Per-SKU unit cost driver | Automatic — skip Phase 4 |
| COGS as $ blended / month | Standalone $ driver | Must verify whether to scale with revenue — confirm with user |

**Modeling assumption — COGS is unit-cost-driven.** The pass-through math in Step 4.2 assumes COGS-as-%-of-revenue represents pure product cost (unit cost × units). If a channel's COGS line bundles **revenue-scaling fees** — Amazon referral fees (typically 8–15% of revenue), payment processing, or fulfillment-as-%-of-revenue — those fees rise with revenue and do not benefit from the price hike. Before applying Phase 4.2, inspect the channel's COGS schedule for component rows. If revenue-scaling fees are bundled in, decompose the COGS % into a product-cost portion and a fee portion, apply the pass-through to the product-cost portion only, and leave the fee % unchanged. State the decomposition to the user before writing.

**Step 4.2 — Compute the new COGS % per affected channel**
For each channel with a COGS-%-of-revenue driver, using the sales mix from Phase 3:

```
revenue_uplift_pct  = sales_mix × price_change_pct
new_cogs_pct        = old_cogs_pct / (1 + revenue_uplift_pct)
```

Express the change in basis points (e.g., 21.9% → 21.4% = -50 bps).

State the result before writing:

```
| Channel | Old COGS % of rev | New COGS % of rev | Δ (bps) |
| ...     | ...               | ...               | ...     |
```

If the model has a single blended COGS % across channels rather than per-channel, weight the new percentage by each channel's share of total revenue.

---

## Phase 5 — Apply Changes (Write Phase)

**Step 5.1 — Capture baseline P&L before any write**
Call `read_smartmodel_data_section` on the consolidation sheet (typically `M - Monthly`) and store the **base** values for the next 12 forecast months: total revenue, COGS, gross profit, opex, EBITDA. These are the "before" numbers for the Phase 6 impact table. If a prior skill in the session (e.g., `/margin-analysis`, `/variance-analysis`) already read consolidation, reuse that response — do not re-read.

**Step 5.2 — Verify the effective-period column against the date spine**
Read row 2 of each target sheet directly via `read_smartmodel_date_spine` (or extract from an existing `read_smartmodel_data_section` response on that sheet). For the user's stated effective month, find the column whose row 2 cell contains that exact month-end date. Restate explicitly before any write:

```
User-stated effective period:           [Month Year]
Date in the target column (from row 2): [Month Year]
Column letter:                          [letter]
First Forecast period in the model:     [Month Year, column letter]
```

The user-stated month and the row-2 date in the named column must match exactly. **Never name a column from memory and never infer a column from the month name alone** — the agent has been observed naming the wrong column (e.g., reporting "BN is June" when BL was June). If the user's effective period is earlier than the first Forecast period, stop — price changes apply to Forecast periods only. Any ambiguity (a boundary month, a relative phrase like "next month"), confirm with the user before writing.

**Step 5.3 — Confirm Key Driver markers before every write**
For every target cell, confirm column A is `•⚡ Key Driver`. If column A reads `  ⚡ Key Result`, the cell contains a formula — **do not overwrite it**. Surface this to the user and stop. Overwriting a formula cell with a hardcoded value breaks the model's calculation chain.

**Step 5.4 — Write the AOV updates (Type B/C)**
Use `bulk_write_smartmodel_drivers` with one entry per (sheet, identifier, period). For permanent changes, write to every Forecast column from the effective period forward — do not assume Excel will propagate the change.

**Step 5.5 — Write the COGS % update (if Phase 4 ran)**
Locate the COGS-%-of-revenue Key Driver row(s) on the product / COGS schedule sheet and write the new percentage to the same Forecast columns. If the model uses a single annual % with formula-based propagation, write to the first applicable Forecast column only, then call `read_smartmodel_data_section` on the COGS sheet after the write to confirm the percentage propagated to all expected Forecast columns. If propagation did not happen, fall back to writing each column explicitly.

**Step 5.6 — Confirm bulk writes**
Per protocol Core Rules, batches affecting more than 10 cells require an explicit user confirmation showing the full change list before execution.

---

## Phase 6 — Output and Next Steps

**Step 6.1 — Re-read the consolidation sheet after writes**
Call `read_smartmodel_data_section` on the consolidation sheet to capture the **scenario** values for the same 12 forecast months captured in Step 5.1 — total revenue, COGS, gross profit, opex, EBITDA. Compute deltas in memory by subtracting Step 5.1's base values.

**Step 6.2 — Format the output**

```
# Price Change Analysis: [Scope]
Direction: [+/-]X%   Effective: [Month Year]   Channels: [list]
Pricing structure detected: [Type A / B / C]

## Modeling Assumptions
- Volume held constant — no demand response to the price change. (If a volume response was layered in Phase 3, state it here instead.)
- COGS pass-through: revenue-scaling fees were [excluded from / decomposed within] the new COGS %. (State which.)
- Sales-mix window: [date range used in Phase 3].

## Sales Mix (if Type B/C)
[Table: channel × segment × affected mix × old AOV × new AOV × Δ]

## COGS Margin Pass-Through
[Table: channel × old COGS % × new COGS % × Δ bps]

## Cells Updated
[Table: sheet × identifier × period × old → new]

## Modeled P&L Impact (next 12 forecast months, from Step 5.1 base vs. Step 6.1 scenario)
| Line Item    | Base | Scenario | Δ ($) | Δ (%) |
| Revenue      | ...  | ...      | ...   | ...   |
| COGS         | ...  | ...      | ...   | ...   |
| Gross Profit | ...  | ...      | ...   | ...   |

## Recommended Next Step
The modeled impact above is forward-looking and lives on top of the current forecast. To compare against a frozen baseline, save the live model into a scenario plan first (use `list_plans` to see existing plans), then re-run the price change. Use `/variance-analysis` or `/compare-scenarios` to package the comparison.
```

---

## Guardrails

- **Never write to a Key Result cell.** Confirm column A marker on every target cell before writing. A formula overwritten with a value breaks the model.
- **Never apply a flat price-change % to a blended AOV** — always weight by sales mix from the corresponding R- sheet.
- **Never reuse one channel's sales mix for another.** Compute per channel from per-channel data.
- **Always update COGS-as-%-of-revenue when applicable** — otherwise revenue rises and gross margin % stays flat, masking the actual margin improvement.
- **Verify the effective-period column letter against the date spine before writing.** Do not infer a column from the month name alone — read row 2 of the target sheet and confirm.
- **Do not silently propagate the change beyond the user's stated duration.** A "permanent" change writes to all Forecast columns from the effective period forward; a "temporary" change writes only to the specified months.
- **Forecast periods only.** Never write into Actual columns.
- **If a tool times out mid-analysis**, on resume: restate the scope and the structure classification from Phase 2 before continuing. Do not silently re-derive.

---

## Common Mistakes to Avoid

1. **Treating blended AOV as if a single SKU drives it.** A 20% price hike on a SKU that is 11% of revenue lifts segment AOV by ~2.2%, not 20%. Always weight by sales mix.
2. **Reusing DTC sales mix for Amazon (or vice versa).** Channel SKU mixes differ materially — every channel needs its own mix from its own R- sheet.
3. **Forgetting the COGS pass-through.** Without lowering the COGS-%-of-revenue Key Driver, revenue rises but gross margin % stays flat and the modeled gross profit improvement is wrong.
4. **Overwriting a formula cell.** When the COGS row is a Key Result (computed from product-level inputs), the percentage cannot be edited directly — write to the underlying Key Drivers or surface the gap.
5. **Misreading the date spine.** Verify column letter against row 2 dates before writing — do not assume the first Forecast column is May, June, or any specific month.
6. **Applying the change everywhere.** A price change scoped to one channel must not write to AOV rows on other channels.
7. **Skipping baseline preservation.** If the user asks to compare scenarios, the live model must be saved as a baseline before the change is written, or the comparison has nothing to compare against.

---

## Integration with Other Skills

- **`/margin-analysis`** — run first if you need to validate the COGS structure (per-channel, blended, $/unit) and current margin levels before applying a change
- **`/create-scenario`** — the general scenario framework; price-change-analysis is the specialized path for pricing
- **`/variance-analysis`** — after applying the change, compare scenario P&L against the saved baseline
- **`/compare-scenarios`** — compare multiple price-change scenarios (e.g., +10% vs. +20%) side by side
- **`/cohort-analysis`** — if the price change is expected to affect retention or repurchase, layer cohort-level assumptions before treating sales mix as static
