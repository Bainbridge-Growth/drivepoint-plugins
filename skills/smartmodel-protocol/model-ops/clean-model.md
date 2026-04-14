---
name: clean-model
description: Fix structural issues, repair broken formulas, standardize formatting, and remove cruft from a SmartModel workbook. Use when a user asks to "clean up", "fix", "repair", or "tidy" their model, or after an audit reveals issues. Also triggers on "broken formulas", "fix the model", "standardize formatting", "remove errors", or "clean this up".
user-invocable: true
---

# Clean Model

**Purpose**: Systematically repair and standardize a SmartModel — fixing structural issues found by `/audit_model`, removing clutter, restoring protocol compliance, and preparing the model for reliable analysis or external sharing.
**Prerequisite**: The `smartmodel-protocol` skill must be loaded. Run `/audit_model` first to identify what needs fixing — this skill fixes issues, not discovers them.

---

## When This Skill Activates

- After `/audit_model` identifies specific issues
- User explicitly asks to clean, fix, or repair the model
- User reports specific broken elements (errors, wrong colors, broken references)
- Before sharing a model with investors or external parties
- After a roll-forward or major import that may have introduced structural issues

---

## Phase 1 — Establish Scope

**Step 1.1 — Load audit findings (if available)**
If `/audit_model` was already run this session, use those findings as the work list. If not, call `sheet_validate` and `sheet_error_find` to establish a baseline.

**Step 1.2 — Confirm with user before destructive operations**
Before any operation that deletes content or rewrites formulas, state what you're about to do and get explicit user confirmation. Examples:
- "I'm going to delete 3 orphan sheets: [names]. Confirm?"
- "I'm going to replace hardcoded values in Key Result rows with formulas. Confirm?"

Never batch all destructive operations without individual confirmations.

---

## Phase 2 — Fix Critical Errors (Priority 1)

### 2.1 — Formula errors

Call `sheet_error_find` to get the full list of errors by location. For each error:

**#REF! errors**: Call `read_range` on the cell → read the broken formula → identify what it should reference → call `insert_formula` with the corrected formula.

**#DIV/0! errors**: Wrap in IFERROR or fix the denominator. Use `insert_formula` to rewrite the cell.

**#NAME? errors**: Fix misspelled function names or named ranges via `insert_formula`.

**Circular references**: Identify the loop by reading the formula chain via `read_range`. Restructure the calculation to break the cycle. Requires user confirmation before changing formula logic.

### 2.2 — Broken cross-sheet references

If formulas reference renamed or deleted sheets, call `read_range` to identify the broken reference and `insert_formula` to point to the correct sheet/cell.

---

## Phase 3 — Restore Protocol Structure (Priority 2)

### 3.1 — Hardcoded Key Result cells

Call `read_smartmodel_data_section` to find Key Result rows (column A = `  ⚡ Key Result`) with hardcoded values instead of formulas. Preserve protocol-accurate leading spaces when matching markers (and do the same for Key Driver markers, e.g. `  → Key Driver`, wherever those are checked). For each:
- Ask the user: "Row [id] is a Key Result but has hardcoded value [X]. What formula should it use?"
- Call `insert_formula` with the correct formula after confirmation.

### 3.2 — Missing metadata

Call `read_smartmodel_sheet_metadata` on each schedule sheet. For sheets missing `metadata___template_id`:
- Propose a template ID based on the sheet name and content
- Confirm with user, then call `write_range` to populate the metadata block.

### 3.3 — Tab colors

Call `get_sheet_names` to list all tabs. For any tab with incorrect color:
- Schedule sheets (not yellow): call `format_range` to apply yellow tab color `#FFD966`
- Report sheets (not blue): call `format_range` to apply blue tab color `#4472C4`

### 3.4 — Settings gaps

Call `read_smartmodel_settings`. For any required field that is blank:
- Ask the user for the correct value
- Call `write_range` to populate the Settings tab.

---

## Phase 4 — Standardize Formatting (Priority 3)

### 4.1 — Column B monospace

Call `format_range` on column B of each schedule sheet to apply Menlo font, size 10, black.

### 4.2 — Column widths

Call `resize_columns` to set column A = 4, column B = 40 on all schedule sheets.

### 4.3 — Number formats

Call `format_range` to apply:
- Currency format to revenue, cost, and profit rows
- Percentage format to margin and rate rows
- Date format `mmm-yy` to Row 2 on all schedule sheets

### 4.4 — Key Driver input cell styling

Call `format_range` to apply light gray background and blue-ish text to forecast-period cells in Key Driver rows.

---

## Phase 5 — Remove Cruft (Priority 4)

### 5.1 — Phantom rows/columns

Call `sheet_clear_phantom_rows_columns` on each sheet to remove empty formatting that bloats the used range.

### 5.2 — Orphan sheets (with confirmation)

For any sheet not referenced by any template in the Index manifest:
- Present a list of orphan sheets to the user
- Ask: "These sheets are not referenced by any template. Delete them?"
- Call `delete_sheet` only after explicit confirmation for each sheet.

---

## Phase 6 — Verify

After completing all fixes:
1. Call `sheet_validate` → confirm no structural errors remain
2. Call `sheet_error_find` → confirm no formula errors remain
3. Call `read_smartmodel_data_section` on the consolidation sheet → spot-check key totals are calculating correctly

---

## Output

```
# Model Cleaning Report — [Company Name]

## Summary
[N] issues fixed | [M] remaining (require user input)

## Critical Fixes Applied
- [Sheet] [Row/Cell]: [What was wrong] → [What was fixed]

## Structural Repairs
- [Description of each structural fix]

## Formatting Standardized
- [Summary: N cells reformatted, M columns resized]

## Removed
- [What was removed and why]

## Still Requires Attention
- [Items that need user input before they can be fixed]

## Verification
- Formula errors: [count remaining, or "None"]
- Protocol compliance: [Pass / Fail with details]
- Consolidation tie: [Pass / Fail]
```

---

## Guardrails

- Never delete Key Driver values (user data) — only fix formulas and structure
- Never change business logic — fix broken formulas to restore intended logic; do not redesign calculations
- Always confirm before destructive operations (sheet deletion, formula rewrites)
- Log every change — maintain the cleaning report throughout the operation
- If unsure what a formula should be, ask the user rather than guessing

---

## Common Mistakes to Avoid

1. Don't clean without an audit first — fixing visible issues while missing hidden ones leaves the model in an inconsistent state
2. Don't batch all destructive operations — confirm each one individually to avoid unrecoverable mistakes
3. Don't "clean" by hiding problems — an IFERROR that returns blank instead of 0 may hide a real formula error
4. Don't reformat without checking if the formatting is intentional — some non-standard formatting may be deliberate
5. Don't run clean on a model that hasn't been backed up — remind the user to save a copy before proceeding

---

## Integration with Other Skills

- **`/audit_model`**: Always run audit first to identify what needs cleaning
- **`/optimize_model`**: After cleaning, optimize for performance and efficiency
- **`/summarize_model`**: Re-run summary after cleaning to confirm model state
