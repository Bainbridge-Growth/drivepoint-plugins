---
name: create-scenario
description: Create a named what-if scenario by adjusting Key Driver assumptions and computing the resulting financial impact. Use when a user asks to "model a scenario", "what if we...", "create a scenario", "model the impact of...", "what happens if we launch X", "what if we raise prices", or any hypothetical business question. Also triggers on "what-if", "scenario planning", "stress test", "model a new assumption", "what if CAC goes up 10%", "what if tariffs hit", "what levers extend runway", or "what if we miss Q2 by 10%".
---

# Create Scenario

**Purpose**: Create a named scenario by locating the relevant Key Driver inputs in the model, adjusting them per the user's hypothesis, and reporting the downstream P&L impact.
**Prerequisite**: The `smartmodel-protocol` skill must be loaded.

---

## When This Skill Activates

- User asks "what if...?" about any business variable
- User wants to model a new product launch, price change, new channel, or growth scenario
- User asks to stress test or sensitivity-test assumptions
- User wants to see the financial impact of a specific decision before committing to it

---

## Common Scenario Types for CPG Brands

| Scenario | Key Drivers to adjust | Sheets affected |
|----------|----------------------|----------------|
| Price increase / decrease (SKU-level) | ASP / AOV inputs | Channel revenue sheets — **use `/price-change-analysis` instead**; it handles sales-mix-weighted AOV math and COGS pass-through |
| New product launch | Add dimension, set revenue + COGS assumptions | Product, channel sheets |
| New retail partner | Add dimension to wholesale sheet, set volume + pricing | Wholesale sheet |
| Marketing spend change | Marketing budget inputs | Opex sheet |
| Demand shock (up/down) | Volume / order inputs | Channel sheets |
| COGS increase (e.g. tariff) | Unit cost inputs | Product sheet |
| Hiring plan change | Headcount and salary inputs | Payroll sheet |
| Subscription mix shift | OTP vs. SUB mix inputs | DTC sheet |

---

## Phase 1 — Define the Scenario

Capture from the user:
1. **Scenario name** — descriptive label (e.g., "10% Price Increase July 2025", "Sephora Launch Jan 2026")
2. **What's changing** — which variables / assumptions
3. **By how much** — absolute or percentage change
4. **Starting when** — which period the change begins
5. **Duration** — temporary (specific months) or permanent (all forecast periods)

If the user is vague ("what if we grow faster?"), ask for specifics. Scenarios require concrete numbers to be useful.

---

## Phase 2 — Orient and Locate Assumptions

**Step 2.1 — Use model context from the protocol**
Settings, index, and date spine are already loaded by the protocol's auto-orient. From the model context, identify which sheets contain the relevant Key Drivers and which columns correspond to the scenario start period and duration.

**Step 2.2 — Find the Key Driver rows**
Call `read_smartmodel_data_section` on each affected sheet. For each variable being changed:
1. Locate the Key Driver row (column A = `•⚡ Key Driver`)
2. Note the current value for the affected periods from the data section response — do not make a separate `read_range` call for data already returned
3. Identify downstream Key Result rows that reference this driver

**Document the base case** before changing anything:
```
Driver: [column B identifier]
Sheet: [sheet name]
Periods affected: [month list]
Current values: [list of current values by period]
```

---

## Phase 3 — Choose Implementation Approach

Present the options to the user and confirm before proceeding:

**Approach A — Side-by-side (recommended)**
Create a scenario summary section (new blue tab) showing Base Case | Scenario | Delta. The base model stays intact; scenario values are computed via formulas referencing base + adjustment factor. Safe and reversible.

**Approach B — Direct edit**
Modify Key Driver cells in the existing model for the affected periods via `bulk_write_smartmodel_drivers`. Excel propagates changes through Key Results automatically. ⚠️ This overwrites the base case — document original values first.

**Approach C — New scenario plan**
If the model supports multiple named plans (check via `list_plans`), create a new plan as the scenario vehicle.

Default recommendation: **Approach A** unless the user explicitly wants to replace the current forecast.

---

## Phase 4 — Implement

### For Approach A (side-by-side tab)

1. Call `create_sheet` with a descriptive name (e.g., "Scenario - Price Increase") and blue tab color
2. Call `write_range` to set up the comparison framework:

   ```
   | Period | Base | Scenario | Delta $ | Delta % |
   ```
3. For each affected driver, call `insert_formula` to populate:
   - Base column: reference the source Key Driver cell
   - Scenario column: reference the same cell + adjustment (e.g., `=DTC!K45 * 1.10` for 10% increase)
4. For each affected Key Result, call `insert_formula` to compute the scenario output using scenario driver values

### For Approach B (direct edit)

Document all original values first via `read_range`. Then:

Call `bulk_write_smartmodel_drivers` with:
```json
[
  { "sheetName": "[sheet]", "identifier": "[column B id]", "period": "[YYYY-MM-DD]", "value": [new value] },
  ...
]
```

Call this with `confirm: true` for batches >10 changes.

### After any approach — open the result

For Approach A: call `activate_sheet` with the new scenario tab name.
For Approach B: call `activate_sheet` with the modified source sheet name so the user sees the updated drivers.

---

## Phase 5 — Compute and Present Impact

After implementing, call `read_smartmodel_data_section` on the consolidation sheet → read the updated totals.

Trace the full P&L impact:
1. Revenue impact (top-line change)
2. COGS impact (if volume or product mix changed)
3. Gross margin impact ($ and % change)
4. Opex impact (if scenario requires additional spend)
5. EBITDA / net income impact
6. Cash impact (if the model tracks cash)

### Output structure

```
# Scenario: [Scenario Name]
Created: [today's date]
Periods affected: [list]

## Assumptions Changed
| Assumption | Base Case | Scenario | Change |
|-----------|-----------|----------|--------|
| [driver id] | [current value] | [new value] | [+/- amount or %] |

## P&L Impact
| Line Item | Base Case | Scenario | Delta ($) | Delta (%) |
|----------|-----------|----------|-----------|-----------|
| Revenue | | | | |
| COGS | | | | |
| Gross Profit | | | | |
| Opex | | | | |
| EBITDA | | | | |

## Key Insight
[One paragraph: What does this scenario tell us? Is it worth pursuing?]

## Risks / Sensitivities
[What assumptions is this scenario most sensitive to? What could cause the outcome to differ?]
```

---

## Guardrails

- Never adjust Key Result cells — only change Key Drivers. Results must update via formulas.
- Always document original values before a direct edit (Approach B) — store them in the scenario tab
- Never overwrite Actual period columns — scenario changes apply to Forecast periods only
- Confirm with user before any write operation

---

## Common Mistakes to Avoid

1. Don't adjust Key Result cells — only Key Drivers. Overwriting a formula with a value breaks the model's calculation chain.
2. Don't forget second-order effects — a price increase may reduce volume; a new channel needs marketing spend
3. Don't overwrite the base case without documenting it first
4. Don't create a scenario without concrete assumptions — "grow 20%" is not a scenario; "increase DTC orders by 20% starting July" is
5. Don't ignore the sign convention — a COGS increase is unfavorable even though the number goes up

---

## Integration with Other Skills

- **`/price-change-analysis`**: For SKU-level price changes, use the price-change skill instead — it handles sales-mix-weighted AOV updates and COGS-as-%-of-revenue pass-through that this general skill does not
- **`/compare-scenarios`**: After creating multiple scenarios, compare them side by side
- **`/summarize-model`**: Orient to model structure before creating scenarios
- **`/build-report`**: Package scenario analysis into a board-ready presentation
