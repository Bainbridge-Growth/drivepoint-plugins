---
name: compare-scenarios
description: Compare two or more scenarios or plans side by side, highlighting key financial differences and trade-offs. Use when a user asks to "compare scenarios", "which scenario is better?", "show me the options side by side", "what's the difference between plan A and B?", or after creating scenarios with /create-scenario. Also triggers on "plan comparison", "compare plans", "budget vs latest forecast", or "plan A vs plan B".
---

# Compare Scenarios

**Purpose**: Load two or more scenarios or plans, present a side-by-side delta analysis, and articulate the trade-offs to support a clear decision.
**Prerequisite**: The `smartmodel-protocol` skill must be loaded.

---

## When This Skill Activates

- User has created 2+ scenarios and wants to compare
- User asks "which option is better?" or "show me the options side by side"
- User needs to present options to leadership or a board for a decision
- User asks for a decision matrix or trade-off analysis between named plans

---

## Phase 1 — Identify Scenarios to Compare

**Step 1.1 — Check for existing plans**
Call `list_plans` → get the list of available plans/scenarios. Present to the user if multiple options exist and let them confirm which to compare.

**Step 1.2 — Load comparison plans (if multi-plan)**
If comparing named plans from the server: call `import_plans` with the selected `planIds` to load the comparison plan data into the current session.

**Step 1.3 — Check for in-model scenarios**
If comparing scenarios created via `/create-scenario` within the current workbook: call `get_sheet_names` → identify any blue scenario tabs. Call `read_range` on each scenario tab to get the assumption sets and P&L impact tables.

**Step 1.4 — Confirm comparison basis**
Always include the **base case** as the reference point. Confirm with user:
- Base case: [current model / base plan]
- Scenario A: [name]
- Scenario B: [name] (if 3-way comparison)
- Comparison period: [specific months / full forecast / specific quarter]

---

## Phase 2 — Gather Data

**If `/create-scenario` ran this session**, reuse the base case data and scenario assumptions already gathered. Do not re-read sheets that were already read.

**Step 2.1 — Read base case**
Call `read_smartmodel_date_spine` → confirm the comparison period.
Call `read_smartmodel_data_section` on the consolidation sheet (M - Monthly) → extract P&L line items for the comparison period from the base case.

**Step 2.2 — Read scenario data**
For each scenario:
- If it's an in-model scenario tab: call `read_range` on the scenario tab's P&L impact table
- If it's a loaded comparison plan: call `read_smartmodel_data_section` on the consolidation sheet for that plan's data
- If it's a side-by-side tab from `/create-scenario`: call `read_range` on the scenario columns

**Step 2.3 — Extract assumption differences**
For each scenario, document which Key Drivers differ from the base case — this is the "what's different" table that makes comparisons interpretable.

---

## Phase 3 — Compute Deltas

For each line item across all scenarios:

```
Delta vs. Base ($) = Scenario Value − Base Case Value
Delta vs. Base (%) = (Scenario Value − Base Case Value) / |Base Case Value|, only when |Base Case Value| is not near 0
If Base Case Value = 0 (or extremely close to 0), show Delta vs. Base (%) as N/A and use Delta vs. Base ($) only
```

For 3-way comparison, also compute:
```
Scenario A vs. Scenario B ($) = Scenario A Value − Scenario B Value
```

Flag material differences (>5% of revenue or >±10% on the specific line item).

---

## Phase 4 — Build the Comparison

### Side-by-side P&L

```
| Line Item     | Base Case | Scenario A | Scenario B | A vs. Base | B vs. Base | A vs. B |
|--------------|-----------|-----------|-----------|------------|------------|---------|
| Revenue      |           |           |           |            |            |         |
| COGS         |           |           |           |            |            |         |
| Gross Profit |           |           |           |            |            |         |
| Gross Margin%|           |           |           |            |            |         |
| Opex         |           |           |           |            |            |         |
| EBITDA       |           |           |           |            |            |         |
| EBITDA Margin%|          |           |           |            |            |         |
```

### Assumption differences table

```
| Assumption | Base Case | Scenario A | Scenario B |
|-----------|-----------|-----------|-----------|
| [driver]  |           |           |           |
```

### Risk and confidence assessment

For each scenario:
- **Execution risk**: How hard is this to pull off? (Low / Medium / High)
- **Assumption sensitivity**: Which assumption, if wrong by 20%, changes the recommendation?
- **Time to impact**: When do the financial effects materialize?
- **Reversibility**: Can we undo this if it doesn't work?

---

## Phase 5 — Output

### Default output (narrative + tables)

1. **Headline**: State the key trade-off in one sentence. "Scenario A generates $200K more revenue but requires $80K additional marketing spend. Scenario B is lower-risk with $100K incremental revenue and no additional spend."

2. **Side-by-side P&L table** (as above)

3. **Assumption differences table**

4. **Key trade-offs** — articulate in plain language what the decision is really about:
   - "If optimizing for growth: Scenario A"
   - "If optimizing for profitability: Scenario B"
   - "If optimizing for cash: [assessment]"
   - "If de-risking: [assessment]"

5. **Risk assessment table** by scenario

6. **Recommendation** (if asked): State which scenario and why. If not asked, frame the decision clearly without choosing for the user.

### Excel output (if requested)

Call `create_sheet` with blue tab (e.g., "Scenario Comparison"). Call `write_range` for the side-by-side P&L and assumption tables. Call `format_range` for number and currency formatting — use bold for the delta columns to make differences visually prominent. Call `create_chart` (ColumnClustered) for a visual comparison of EBITDA by scenario.

---

## Guardrails

- Never write to Actual columns or overwrite Key Drivers in the base model
- Always include the base case as a reference — a comparison without a baseline is not a comparison
- If fewer than 2 scenarios can be identified, ask the user to specify scenarios or create them via `/create-scenario` first
- Confirm with user before writing any output tab to the workbook

---

## Common Mistakes to Avoid

1. Don't compare without a base case — everything is relative to a reference point
2. Don't just show numbers — articulate the trade-off in plain language; the decision-maker needs the "so what"
3. Don't ignore execution difficulty — a financially superior scenario that's impossible to execute is not better
4. Don't present more than 3–4 scenarios at once — decision fatigue makes comparisons useless beyond that
5. Don't conflate "higher revenue" with "better scenario" — higher revenue with worse margins and more cash burn may be the inferior choice

---

## Integration with Other Skills

- **`/create-scenario`**: Create the scenarios first, then compare
- **`/build-report`**: Package the comparison into a board-ready format
- **`/interrogate-model`**: If user asks follow-up questions about specific scenario details
- **`/variance-analysis`**: Compare scenario assumptions to actual performance after the fact
