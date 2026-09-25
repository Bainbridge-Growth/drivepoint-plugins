---
name: change-safety
description: Answer "if I change this, what breaks?" for a SmartModel workbook — before the user makes the edit. Use when they ask whether it is safe to rename a row, hardcode a formula, type over a value, add or delete a row or sheet, or restructure a tab; when they say "what's breakable", "what are the don't-dos", "will this mess anything up", "is it safe to"; or when they are about to edit structure rather than inputs. Also use proactively when a user describes an edit they have already made to anything other than a Key Driver input cell.
---

# Change Safety

**Purpose**: Tell the user what a proposed Excel edit will break, grounded in *their* workbook's actual
formulas — not in general Excel intuition and not in the protocol alone.
**Prerequisite**: The `smartmodel-protocol` skill must be loaded.

Excel is open-ended; a SmartModel is not. The gap between those two facts is the single most common
source of customer anxiety, and it is usually unspoken. A finance owner who has been told "don't break
it" without being told *what breaking looks like* will either freeze or guess. Both are worse than
asking.

---

## When This Skill Activates

- The user asks whether an edit is safe, in any phrasing — "will this mess anything up", "can I just
  hardcode this", "is it okay if I rename", "what happens if I delete".
- The user asks the general question: what is breakable, what are the don't-dos, what should I avoid.
- The user describes an edit they have **already made** to anything that is not a Key Driver input cell.
  Do not wait to be asked; run the check and report.
- Before this skill's own recommendation would have the user edit structure.

**Never answer any of these from the protocol grammar alone.** The grammar says what a row *means*.
Only the formulas say what depends on it. See Phase 2 — this is the whole point of the skill.

---

## The safety model, in one screen

Three things in a SmartModel carry machine meaning. Everything else is presentation.

| Zone | What it is | If the user changes it |
|---|---|---|
| **Column A marker** | The storage contract. `•` = visual only, not stored. `•⚡ Key Driver` = stored as a user input. `⚡ Key Result` = stored as a calculated result. | Changes whether the row exists to Drivepoint at all. Never change silently. |
| **Column B identifier** | The machine address — a formula producing e.g. `="hydrating-serum_orders"`. This, not the label, is the row's identity. | Breaks the row's link to the database, the add-in, reports and scenario planning. |
| **Cell role** (font colour + fill) | Data lineage. Orange = actual from the accounting source of truth. Blue on grey = the user's input. Green on grey = an actualized import. Green, no fill = a reference to another sheet. Black, no fill = calculated. | Repainting a cell is never cosmetic — the role encodes lineage. Writing a forecast into an orange `actual` cell is a structural error. |

**Column C — the human label — is presentation.** By the grammar, renaming it does not change the row's
identity. **But that is not the same as safe**: a SUMIFS elsewhere in the workbook may match on the label
text. This is exactly the kind of coupling Phase 2 exists to find, and the reason "the protocol says
labels are free" is an answer you must never give on its own.

Tab colours carry meaning too: yellow = schedule (where modelling happens), blue = report (derived
output, read-only for most users), `R-` prefix = the import landing layer (**the add-in overwrites these
on every import — never hand-edit an R- sheet**), dark grey = Settings (add-in owned, never edited
directly).

A common and half-correct user belief: *"the blue tabs are just reporting, so I can tweak them without
affecting the model."* The first half is right — reports are derived and do not drive the model. The
second half is not a licence: errors surfacing on a report tab are almost always symptoms of an upstream
break, so **fix the cause, not the display**. Say both halves.

---

## Phase 1 — Classify the change

Restate the user's proposed edit in one line, then place it:

| Change | Default posture |
|---|---|
| Typing a value into a blue-on-grey forecast cell on a Key Driver row | **Safe.** This is what the model is for. |
| Typing over a green-on-grey (`imported_input`) cell | **Safe but transient** — the next import overwrites it. Say so. |
| Typing over an orange (`actual`) cell | **Structural error.** Refuse and explain: actuals come from the accounting source of truth. |
| Hardcoding a black (`calculated`) Key Result cell | **Breaks the calc chain** at that cell and every cell downstream. Always run Phase 2. |
| Renaming a column C label | **Check required.** Grammar says free; formulas may disagree. |
| Changing a column B identifier | **Breaks the row's identity.** Never without an explicit rebuild. |
| Changing a column A marker | **Changes the storage contract.** Route to the FDE; this is a model change, not an edit. |
| Inserting or deleting a row | **Check required.** Addressing is by durable id, so shifts are tolerated — but SUMIFS ranges, section totals and cross-sheet references may not be. |
| Renaming or deleting a sheet | **Check required, high risk.** Every cross-sheet formula referencing it breaks. |
| Editing an `R-` sheet by hand | **Pointless and unsafe** — overwritten on next import. |
| Editing the Settings tab | **Never.** Add-in owned. `settings.smartmodelSpec` is the detection gate; a wrong value makes the workbook stop being recognised as a SmartModel. |

A posture is a starting point, not the answer. Everything marked *check required* — and every hardcode —
goes to Phase 2 before you say a word to the user.

---

## Phase 2 — Find the actual dependents

This is the phase that makes the answer true for *this* workbook.

1. **Read the target.** `read_range` on the cell or row → its current value, formula, and role.
2. **Find what points at it.** For the target sheet and every schedule and report sheet that could
   reference it, `read_range` across the formula layer and collect every formula mentioning:
   - the sheet name (for a sheet rename or delete),
   - the row's durable identifier from column B,
   - the cell address or a range containing it,
   - **the label text from column C** — this is what catches a SUMIFS keyed on a human label, and it is
     the check people skip.
3. **Follow one hop further** on anything found in a Key Result row: read the formulas of cells that
   reference *that* cell, so the report lands on the real blast radius rather than the first ring.
4. **Check the period.** `read_smartmodel_date_spine` — if the edit lands in an Actual column, that
   changes the verdict on its own.

If a read fails or a sheet cannot be scanned, say that the check is incomplete and name what was not
covered. **An unchecked area is never reported as safe.**

---

## Phase 3 — Give the verdict

One of exactly three, stated first, in plain language:

- **Safe** — nothing references it in a way this edit disturbs. Say what you checked.
- **Safe, with one step** — the edit works if something else is updated with it. Name the step.
- **This breaks something** — name what, where, and what it will look like when it breaks (`#REF!`, a
  total that silently stops including a row, a report that drops a line).

Then, always:

- **What you checked**, as a list of sheets and what you matched on. The user is trying to learn the
  system, not just clear one edit; showing the method is most of the value.
- **The safer alternative**, if there is one. Most "can I hardcode this" questions have a real answer
  that keeps the wiring intact.
- **The self-check**, once per session: how they could have answered this themselves — select the cell,
  read the formula bar, see what it matches on.

Never expose durable ids, raw column letters or row indices as the primary language. Say "the Total
Selling row on the AMZ tab", then give `B64` in parentheses if precision helps.

---

## Standing don't-dos

These hold for every SmartModel and can be stated without a workbook read:

1. **Never type into an orange cell.** Those are actuals from the accounting system.
2. **Never hand-edit an `R-` sheet.** The next import overwrites it.
3. **Never edit the Settings tab.**
4. **Never repaint a cell to change its colour.** The colour is lineage, not formatting.
5. **Never overwrite a formula in a Key Result row** to force a number. If the number is wrong, the
   input or the formula is wrong.
6. **Never work in the live model to test an idea.** Save a copy first — that is the undo, and it costs
   nothing.

Everything *not* on that list is likely fine, and saying so plainly matters as much as the warnings. A
user who believes the whole file is fragile will not use it.

---

## Escalation

Route to the FDE rather than answering when:

- The change would alter a column A marker or a column B identifier.
- The workbook combines a Drivepoint model with a customer-built model, and the change crosses the
  boundary — roll-forward, scenario planning and key-driver tagging behave differently on each side.
- The user is asking to make a non-Drivepoint tab compatible with Drivepoint mechanics. That is a
  build, not an edit.

Say who is picking it up and when. "Ask your FDE" on its own is a dead end.

---

## Related Skills

- `smartmodel-protocol` — the grammar this skill enforces (prerequisite).
- `audit-model` — run after any accepted structural change.
- `clean-model` — repairing what is already broken.
- `interrogate-model` — tracing a number to its source.
