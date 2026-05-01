---
name: qa-financials
description: Tie out a customer's raw GL export against the R-GL tab in their SmartModel, line by line, for a specified period. Use when a user asks to "QA the financials," "QA the GL," "QA R-GL," "QA the import," "tie out the GL," "reconcile GL," "check the NetSuite import," "verify the import for [month]," or says "[Customer] sent me their financial export — can you QA it." Compares external source data (typically a NetSuite-Drivepoint Income Statement or Balance Sheet) to the imported data on R-GL after roll-forward. Read-only — produces a markdown tie-out report in chat.
---

# QA Financials

**Purpose**: Compare external GL data (from the customer's accounting system) against the R-GL tab in the SmartModel for a target period, flag mismatches by severity, and surface the specific accounts and amounts that need investigation. Run after roll-forward, before drafting the monthly report.
**Prerequisite**: The `smartmodel-protocol` skill must be loaded.

---

## When This Skill Activates

- User asks to QA, tie out, reconcile, or verify the GL / financials / import for a given month
- User pastes a financial export and asks Claude to check it against the model
- User says "QA RGL tab [month]" or "[Customer] sent me their export"
- Run before drafting the monthly report so the underlying numbers are trusted

This skill compares **external source** to **imported model data**. It is not the same as `/audit-model`, which checks structural and protocol integrity of the workbook itself. The two are complementary.

---

## Phase 1 — Orient

Settings, index, and date spine are already loaded by the protocol's auto-orient. From the model context, note: `companyName`, `currency`, the most recently closed Actual month, and the R-GL sheet name from the Index manifest (typically `R - GL`).

**Confirm the target period** from the user's request. Default to the most recently closed Actual month if unspecified.

**State the comparison explicitly** before proceeding:

```
QA: [Customer] [Month Year] — source export vs. R-GL after roll-forward
```

If R-GL doesn't exist in the Index, stop and tell the user — this skill requires a GL-level import to compare against.

---

## Phase 2 — Acquire the Source Export

Resolve input in this order — file is the dominant case (the user typically drag-drops the export from their accounting team):

1. **Attached file** — if the user's message references a file the host environment has surfaced (drag-drop in Claude.ai, attachment, etc.), read it directly.
2. **File path** — if the user provides a path (e.g., `~/Downloads/Arbor_GL_March2026.csv`), use the `Read` tool.
3. **Pasted block** — if the user pasted tabular GL content directly in chat, parse from text.
4. **Ask once** — if none of the above resolve: "Drop the GL export, paste it here, or give me a path to the file."

### Parser — NetSuite-Drivepoint format (primary path)

**Detect by header**: the first 5 rows contain `Drivepoint Income Statement` or `Drivepoint Balance Sheet`. Either triggers the Drivepoint parser; route by which one was found.

**Common parsing rules (both report types):**
- **Skip the header banner** (company name, report title, date range, "Options: …", blank rows) until the row beginning with `Financial Row`
- **Locate the target period column** by matching the date row against the requested month (e.g., "Mar 2026")
- **Anchor on rollup rows**: rows beginning with `Total - <number> - <name>` are the account-level totals. Use these directly — do not sum the detail rows beneath them
- **Currency parsing**: strip `"`, `$`, `,`. Treat `($X)` as `-X`. Empty cells = `0`

**If Drivepoint Income Statement** (the dominant case — full line-level tie-out):
- Capture major subtotals for roll-up sanity: `Total - Income`, `Total - Cost Of Sales`, `Gross Profit`, `Total - Expense`, `Net Ordinary Income`, `Total - Other Expense`, `Net Other Income`, `Net Income`
- Proceed to Phase 4 (full tie-out, both roll-up and line-level)

**If Drivepoint Balance Sheet** (roll-up only — see why below):
- Capture only the major subtotals: `Total Assets`, `Total Liabilities & Equity`
- Proceed to Phase 4.1 (roll-up sanity), then skip line-level
- Tell the user why: the Drivepoint BS export defaults to "Activity Only" (period flow) while R-GL stores closing balances, so line-level comparison is unreliable. Recommend re-exporting with closing balances if line-level BS QA is needed.

### Parser — fallback (non-NetSuite source)

If the header doesn't match the Drivepoint template, ask: "This doesn't look like a NetSuite-Drivepoint export. Paste a simple two-column table — account ID or name, then value for [month] — or tell me what accounting system this came from." Do not attempt to auto-parse arbitrary formats.

---

## Phase 3 — Read R-GL

Call `read_smartmodel_data_section` on the R-GL sheet for the target period column. Use the column **header labels** to locate fields — do not hardcode column letters, since position can vary across customers and protocol versions:

- `Financial Statement Helper` — section (`Income Statement` / `Balance Sheet`)
- `Financial Account Name` — account name
- `Financial Account Number` — account number (the canonical match key; may be blank for some accounts like `Net Income`, `Inventory Asset`, or legacy `(deleted)` accounts)
- `Drivepoint Account Category` — used for downstream consolidation, not for tie-out
- The date column matching the target period (e.g., `Mar-26`) — the value to compare

`read_smartmodel_data_section` already strips the metadata block (rows 9–15 per protocol). No additional row filtering needed beyond skipping rows with no account name and no number.

---

## Phase 4 — Tie Out

### 4.1 — Roll-up sanity (run this first)

Tie out the major totals before touching line-level detail. If totals don't tie, line-level findings are diagnostic only.

**Tie to the consolidation sheet, not to a re-summed R-GL.** The model already aggregates R-GL accounts into consolidated P&L lines via the `Drivepoint Account Category` mapping; that aggregation lives on `M - Monthly` (or whichever consolidation sheet the Index identifies). Reinventing the rollup math here risks bucketing accounts differently than the model does, which produces phantom mismatches.

Call `read_smartmodel_data_section` on the consolidation sheet for the target period column.

**For an Income Statement export**, compare:

| Source line (from export) | Model line (on consolidation sheet) |
|---------------------------|-------------------------------------|
| `Total - Income` | Net Revenue (or Gross Sales − Discounts/Returns, per the model's convention) |
| `Total - Cost Of Sales` | Total COGS |
| `Gross Profit` | Gross Profit |
| `Net Ordinary Income` | Operating Income / EBITDA, per the model |
| `Net Income` | Net Income |

**For a Balance Sheet export**, compare:

| Source line (from export) | Model line (on consolidation sheet) |
|---------------------------|-------------------------------------|
| `Total Assets` | Total Assets |
| `Total Liabilities & Equity` | Total Liabilities & Equity |

Also verify the source's own internal balance: `Total Assets` should equal `Total Liabilities & Equity` for the period. If not, that's a source-side data integrity issue (NetSuite shouldn't export an unbalanced BS) — flag as FAIL and surface before the model comparison.

The model's exact line names vary by customer — match by position in the statement structure, not by exact string. If the consolidation sheet doesn't carry one of these lines, note it and skip that row rather than fabricating a comparison.

**If a major roll-up is off by more than tolerance**: flag as FAIL in Critical Issues, surface the specific line that broke. For IS, continue to the line-level step (4.2) to help diagnose where the gap originated; for BS, stop here — line-level BS tie-out is out of scope for this skill.

### 4.2 — Account-level tie-out

For each `Total - <number> - <name>` row in the source:

1. **Match key**: account number first. If number is absent on either side, fall back to account name (case-insensitive, trimmed).
2. **Compute delta**: `delta = source_value − rgl_value`
3. **Sign check**: if source and R-GL have opposite signs (and both non-zero), flag as FAIL regardless of magnitude — this is a real bug, not a tolerance issue
4. **Apply tolerance and categorize** per 4.3

Capture unmatched accounts on either side:
- **Source has, R-GL missing** → likely a new account that wasn't picked up by the import. WARNING.
- **R-GL has, source missing** → likely an account that was zeroed out or removed. WARNING if the R-GL value is non-zero; INFO otherwise.

**Special-case accounts** (treat as expected-zero, flag if non-zero):
- Account names containing `(deleted)`, `(DON'T USE)`, `DO NOT USE` → WARNING with note "stale account showing activity; investigate"
- `Uncategorized Income`, `Uncategorized Expense`, `Reconciliation Discrepancies` → WARNING with note "NetSuite catch-all account; should be cleared before close"

**Worked example (Income Statement)** — one tie-out line, end-to-end:
- Source row `Total - 41010 - Discounts` for Mar-26 = `($45,231.20)` → parsed value `-45,231.20`
- R-GL row matched on `Financial Account Number = 41010` for Mar-26 = `-45,180.00`
- delta = `-45,231.20 − (-45,180.00) = -51.20`
- Source `Total - Income` for Mar-26 = $1.8M → tolerance = `max($100, 0.1% × $1.8M)` = `$1,800`
- |delta| = `$51.20` ≤ tolerance → **PASS** (within rounding noise)

### 4.3 — Tolerance and severity

Tolerance differs by report type:

- **Income Statement** (per line, used in 4.1 roll-up and 4.2 line-level): `max($100, 0.1% × source Total - Income for the period)`
- **Balance Sheet** (roll-up only, used in 4.1): `max($100, 0.05% × source Total Assets for the period)` — tighter rate because BS roll-up sits at the top of the structure; if Total Assets disagrees by more than ~5bp, something material is off

| Condition | Severity |
|-----------|----------|
| \|delta\| ≤ tolerance | PASS (rounding/FX noise) |
| tolerance < \|delta\| ≤ 5× tolerance | WARNING |
| \|delta\| > 5× tolerance OR sign flip | FAIL |
| Material roll-up mismatch in 4.1 | FAIL |
| Source BS internal imbalance (Total Assets ≠ Total Liabilities & Equity) | FAIL |
| Unmatched account on either side (with non-zero value) | WARNING |
| `(deleted)` / `Uncategorized` / `Reconciliation` account with activity | WARNING |
| Within-tolerance noise on expected-zero accounts | INFO |

The constants ($100 floor, 0.1% / 0.05% rates, 5× warning band) are deliberate and tunable — adjust if Franzi calibrates them differently after real test runs.

---

## Phase 5 — Report

Markdown output, severity-ordered. Match `audit-model`'s format:

```
# GL Tie-Out — [Customer] [Month Year]
**Source**: [Drivepoint Income Statement / Balance Sheet / paste / file path]
**Target sheet**: R - GL ([sheet name from Index])
**Tolerance**: $X ([IS: max of $100, 0.1% of Total Income] [BS: max of $100, 0.05% of Total Assets])

## Summary
[X] Fails | [Y] Warnings | [Z] Info | Overall: [PASS / NEEDS REVIEW / FAIL]

## Roll-Up Sanity

[For Income Statement:]
| Line | Source | Model | Delta | Status |
|------|--------|-------|-------|--------|
| Total Income | $X | $Y | $Z | PASS / FAIL |
| Total COGS | … | … | … | … |
| Gross Profit | … | … | … | … |
| Net Income | … | … | … | … |

[For Balance Sheet:]
| Line | Source | Model | Delta | Status |
|------|--------|-------|-------|--------|
| Total Assets | $X | $Y | $Z | PASS / FAIL |
| Total Liabilities & Equity | $X | $Y | $Z | PASS / FAIL |
| Source internal balance (Total Assets − Total L&E) | $X | — | $Z | PASS / FAIL |

## Critical Issues (FAIL)
- [Account number] [Account name] — Source $X, R-GL $Y, delta $Z — [sign flip / material variance / unmatched]
- …

## Warnings
- [Account] — [Description and recommended check]

## What's Matching
- [If IS] [N] accounts tied within tolerance, totaling $X across the Income Statement
- [If BS] Roll-up tied at the major-totals level; line-level skipped by design

## Assumptions and Notes
- [If BS export was provided] Line-level BS tie-out skipped — Drivepoint BS export is "Activity Only" while R-GL stores closing balances. Roll-up sanity only.
- [Other call-outs as warranted]

## Recommended Next Steps
1. [Most critical fix first — usually point at the R-GL row + source row to investigate]
2. …
```

---

## Guardrails

- This skill reads and assesses only — it never writes to or modifies the workbook
- Run roll-up sanity FIRST. If totals don't tie, don't bury the lede in line-level detail
- Trust natural NetSuite sign convention on both sides — do not "normalize" signs. If signs disagree between source and R-GL, that's a real bug to flag
- If the source export was generated before the model's last roll-forward date (stale source), warn the user — late entries and reclasses can produce false discrepancies

---

## Common Mistakes to Avoid

1. Don't sum the detail rows in the source export — use the `Total - <number> - <name>` rollups directly. Detail rows split by Department × Sales Channel and double-count if you don't aggregate carefully
2. Don't treat unmatched accounts as FAIL by default — new accounts get added every month. Surface them as WARNING with a clear "update mapping" recommendation
3. Don't attempt line-level tie-out on a Drivepoint Balance Sheet export — it's "Activity Only" (period flow) while R-GL stores closing balances. Limit BS QA to roll-up sanity, or recommend a closing-balance re-export
4. Don't run this before roll-forward — comparing a stale R-GL against a fresh source produces meaningless variance
5. Don't auto-fix anything — remediation belongs in `/clean-model` or a manual re-import. This skill diagnoses, it doesn't repair

---

## Out of Scope

- **Non-NetSuite exports** (Xero, QuickBooks, etc.) — fallback path asks for a simple table or names the system. Dedicated parsers are a future addition
- **Screenshot-based QA** — needs vision support and is a separate skill
- **Non-GL R-sheets** (R-Amazon, R-Shopify, R-DTC) — the workflow generalizes but this skill targets R-GL specifically. A generalized `qa-import` is a follow-on
- **Auto-fixing the import** — tie-out is read-only; remediation is `/clean-model` or manual re-import

---

## Integration with Other Skills

- **`/monthly-report`**: Run this skill BEFORE drafting the monthly report so the underlying GL is trusted
- **`/audit-model`**: Complementary — that skill checks structural integrity (formulas, sheet structure, protocol compliance); this one checks external tie-out
- **`/variance-analysis`**: If tie-out passes but variance vs. forecast is large, that's a real variance — point at `/variance-analysis` for explanation, not data error
- **`/clean-model`**: Remediation skill if FAIL items need fixing in the workbook
- **`smartmodel-protocol`**: Prerequisite — provides the grammar for reading R-GL
