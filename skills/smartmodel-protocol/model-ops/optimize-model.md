---
name: optimize-model
description: Optimize a SmartModel for performance, file size, and formula efficiency. Use when a user says the model is slow, "Excel is lagging", "the file is huge", "calculations take forever", or asks to "speed up the model", "optimize performance", or "reduce file size". Also triggers on "volatile formulas", "calculation mode", "slow spreadsheet", or "model performance".
user-invocable: true
---

# Optimize Model

**Purpose**: Diagnose and resolve SmartModel performance issues — slow calculation, large file size, oversized used ranges, and inefficient formula patterns — while preserving all business logic and data.
**Prerequisite**: The `smartmodel-protocol` skill must be loaded. Run `/clean_model` first — many performance issues are caused by structural cruft that cleaning resolves.

---

## When This Skill Activates

- User reports the model is slow to calculate or respond
- User says Excel is lagging or the file is large
- User asks to speed up the model or reduce file size
- After a large data import that may have expanded the used range
- As a final step in the audit → clean → optimize maintenance chain

---

## Phase 1 — Diagnose

**Step 1.1 — Read workbook map**
Call `read_smartmodel_index` → count templates, sheets, and data volume. Large workbooks with 10+ templates and 48+ months of data are candidates for formula optimization.

**Step 1.2 — Check used ranges for bloat**
Call `get_sheet_summary` on each schedule sheet → note the reported used range dimensions. A sheet that should have data in columns A–AZ but reports a used range extending to column ZZ has phantom column bloat.

Flag sheets where used range is more than 20% wider or taller than the actual data area.

**Step 1.3 — Check for volatile formulas**
Call `read_range` on a sample of formula cells across each sheet. Flag if any cells contain:
- `NOW()` or `TODAY()` — recalculate on every keystroke
- `INDIRECT()` — prevents Excel from optimizing formula dependencies
- `OFFSET()` — volatile; recalculates on every change
- `RAND()` or `RANDBETWEEN()` — recalculates constantly

**Step 1.4 — Check calculation mode**
Call `read_smartmodel_settings` → check if `settings.calculation_mode` is set. If not set or set to Automatic, note this as an optimization opportunity for large models.

---

## Phase 2 — Optimize (with user approval)

Present a prioritized list of optimizations and confirm before applying each category.

### Optimization 1 — Clear phantom rows/columns

Highest impact, safe to apply.

Call `sheet_clear_phantom_rows_columns` on every schedule and report sheet. This removes empty cells that carry formatting, which dramatically reduces file size and Excel's used-range calculation overhead.

Expected impact: Reduces file size 20–60% for models with phantom range bloat.

### Optimization 2 — Replace volatile formulas

Medium impact, requires case-by-case review.

For each volatile formula found in Phase 1:

**`NOW()` / `TODAY()`**: Replace with a reference to the static date in the Settings tab (`settings.modelStartDate` or similar) or a Key Driver cell. Call `insert_formula` with the non-volatile equivalent.

**`INDIRECT()`**: Replace with direct cell references where possible. If the indirect reference is dynamic (e.g., referencing a sheet name from a cell), note this as a structural tradeoff — eliminating it may require a formula redesign.

**`OFFSET()`**: Replace with `INDEX()` which is non-volatile and performs better.

Do not replace volatile formulas that are used intentionally (e.g., a "refresh timestamp" cell using `NOW()`).

### Optimization 3 — Calculation mode

For large models (>8 templates, >36 months) that are slow to respond during editing:

Call `set_calculation_mode` with mode "AutomaticExceptTables" or "Manual" — present the tradeoff to the user:

| Mode | Effect | When to use |
|------|--------|------------|
| Automatic | Recalculates on every change | Default — best for small/medium models |
| AutomaticExceptTables | Skips table recalc | Good middle ground |
| Manual | Only recalculates when F9 is pressed | Best for very large models — user must remember to recalculate |

Confirm with user before changing. If switching to Manual, explain that they need to press F9 or call `calculate` to refresh results.

### Optimization 4 — Consolidate redundant formulas

Low priority, high care required.

If multiple sheets repeat the same complex formula pattern (e.g., each channel sheet independently computes gross margin using the same multi-step formula), suggest consolidating to a helper row or a shared reference. Confirm with user before any formula restructuring — this changes the dependency graph.

### Optimization 5 — Array formula review

If the model uses array formulas (Ctrl+Shift+Enter or `@` dynamic arrays), check if they span unnecessarily large ranges. An array formula over A1:Z10000 when data only covers A1:Z500 recalculates over 20× more cells than needed. Call `insert_formula` to resize to actual data range after confirming with user.

---

## Phase 3 — Verify and Measure

After applying optimizations:
1. Call `sheet_validate` → confirm model structure is intact
2. Call `get_sheet_summary` on previously-bloated sheets → confirm used range has reduced
3. Call `calculate` (full recalculation) → confirm model still calculates correctly
4. Call `read_smartmodel_data_section` on the consolidation sheet → spot-check that key totals are unchanged

---

## Output

```
# Optimization Report — [Company Name]

## Summary
Optimizations applied: [list]
Estimated impact: [file size reduction estimate, formula volatility eliminated]

## Changes Made
- [Sheet]: [What was changed] → [Expected impact]

## Recommended (not yet applied — require user decision)
- [Optimization]: [Tradeoff] — [How to apply if desired]

## Verification
- Model structure: [Pass / Fail]
- Key totals unchanged: [Pass / Fail]
- Used range (before → after): [size comparison]
```

---

## Guardrails

- Never change business logic during optimization — only change how calculations are performed, not what they compute
- Always verify totals are unchanged after any formula substitution
- Confirm with user before switching calculation mode — Manual mode requires the user to know to press F9
- Do not remove formulas to "simplify" — only replace with equivalent non-volatile alternatives

---

## Common Mistakes to Avoid

1. Don't optimize before cleaning — phantom range bloat and formula errors should be fixed first
2. Don't blindly replace INDIRECT — sometimes it's used intentionally for dynamic sheet references; understand the purpose before replacing
3. Don't switch to Manual calculation mode without warning the user — they'll wonder why the model isn't updating
4. Don't optimize a production model without the user having a backup — formula changes are hard to undo
5. Don't report file size reduction without verifying calculations are still correct — a fast wrong model is worse than a slow correct one

---

## Integration with Other Skills

- **`/clean_model`**: Always run clean before optimize — cleaning resolves phantom range issues that most affect performance
- **`/audit_model`**: Audit identifies structural issues that can cause calculation overhead
- **`/summarize_model`**: Re-run after optimization to confirm model state is unchanged
