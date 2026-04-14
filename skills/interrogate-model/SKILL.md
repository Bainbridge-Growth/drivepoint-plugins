---
name: interrogate-model
description: Answer ad-hoc questions about model data by tracing numbers back through formula dependencies and driver chains. Use when a user asks a specific question about their model — "where does that number come from?", "why is revenue $X?", "what's driving that line?", "explain this formula", or any specific data question. Also triggers on "trace this", "explain that number", "walk me through this", or "what's behind that figure?".
---

# Interrogate Model

**Purpose**: Answer specific questions about model data by reading the relevant sections, tracing formula dependencies, and following the Key Driver → Key Result chain to explain where any number comes from.
**Prerequisite**: The `smartmodel-protocol` skill must be loaded.

---

## When This Skill Activates

- User asks about a specific number in the model
- User wants to understand why a figure is what it is
- User asks "where does that number come from?"
- User wants to trace a result back to its inputs
- User asks a question that requires reading and interpreting model data

---

## Phase 1 — Understand the Question

Before reading any data, clarify:
1. **What number?** — Which line item, metric, or cell is the user asking about?
2. **Which period?** — Which month, quarter, or time range?
3. **What type of answer?** — "What is X?" (lookup), "Why is X that value?" (trace), "How does X flow into Y?" (dependency trace)

If the question is ambiguous, ask for clarification rather than guessing. A wrong trace wastes more time than a quick question.

---

## Phase 2 — Orient to the Relevant Sheet

**Step 2.1 — Read model map (if not already loaded)**
Call `read_smartmodel_index` → identify which template and sheet owns the metric the user is asking about.

**Step 2.2 — Read the sheet metadata**
Call `read_smartmodel_sheet_metadata` on the relevant sheet → get the template name, structure overview, and section layout.

**Step 2.3 — Read time context**
Call `read_smartmodel_date_spine` on the relevant sheet → confirm which column corresponds to the period the user is asking about.

---

## Phase 3 — Find and Read the Data

**Step 3.1 — Locate the row by identifier**
Call `read_smartmodel_data_section` on the relevant section of the sheet. Use column B identifiers to locate the specific row — do not rely on row numbers.

**Step 3.2 — Read the cell value and formula**
Call `read_range` on the specific cell(s) → get:
- The current value
- The formula (if it's a Key Result row)
- The column A marker (Key Driver vs. Key Result)

**Step 3.3 — Trace dependencies (for Key Result rows)**

If the row is a Key Result (formula-driven):
1. Read the formula to identify which cells it references
2. Call `read_range` on each referenced cell to get their values and formulas
3. Follow the chain: Key Result → references Key Driver(s) + other Key Results → repeat until you reach the leaf Key Driver inputs

Map the dependency tree:
```
[Key Result] ← formula referencing:
  ├── [Key Driver A]: [current value]
  ├── [Key Driver B]: [current value]
  └── [Key Result C] ← formula referencing:
        ├── [Key Driver D]: [current value]
        └── [Key Driver E]: [current value]
```

**Step 3.4 — Cross-sheet traces**

If the formula references another sheet (e.g., consolidation references channel sheet):
1. Call `read_smartmodel_sheet_metadata` on the source sheet
2. Call `read_range` on the referenced cells in the source sheet
3. Repeat the dependency trace on the source sheet

---

## Phase 4 — Explain the Answer

Structure the answer at two levels:

### Short answer (always lead with this)
One sentence: "[Metric] is [value] for [period] because [single biggest driver]."

### Full trace (show the work)
Walk through the dependency chain in plain language:
- "Revenue of $1.2M in March comes from the DTC sheet, which is the sum of three channels..."
- "DTC revenue = Orders (2,400) × AOV ($83). Orders are a Key Driver — the user entered 2,400 for March. AOV is also a Key Driver — currently set to $83."
- "This flows into the M - Monthly consolidation via the formula in cell [ref], which sums DTC + Amazon + Wholesale revenue."

### If the answer requires cross-period context
Pull 2–3 months of data to show the trend, not just the point-in-time value.

### If the answer reveals a data gap
If tracing leads to an empty R- sheet or a Key Driver with no value:
- Note what's missing
- Explain what would need to be populated for the number to be non-zero
- Suggest how to populate it

---

## Guardrails

- This skill reads only — it never writes to the workbook
- If a formula is too complex to trace fully (e.g., deeply nested SUMIFS, INDEX/MATCH chains), read the formula and explain its logic in plain English rather than tracing every cell reference
- If the user's question references a cell or metric that doesn't exist in the model, say so directly rather than guessing at a related metric

---

## Common Mistakes to Avoid

1. Don't just report the number — explain where it comes from. A lookup without a trace doesn't help the user understand the model.
2. Don't assume the user knows what "Key Driver" means — explain in plain language ("this is an input you control" vs. "this is calculated automatically")
3. Don't trace every single cell in a complex formula — summarize the logic and highlight the key inputs
4. Don't skip cross-sheet traces — the most interesting dependency chains span multiple templates
5. Don't answer without reading the data first — guessing at model values based on general knowledge is a critical error

---

## Integration with Other Skills

- **`/summarize_model`**: Run first to get the workbook map before interrogating specific cells
- **`/variance_analysis`**: Use when the user's question is "why did X change vs. plan?"
- **`/audit_model`**: If tracing reveals formula errors or broken references
- **`/build_report`**: If the user wants to document the findings from interrogation
