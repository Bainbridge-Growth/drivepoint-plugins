# Drivepoint customer project-instruction template

The canonical skeleton for the **project/system instruction** an FDE pastes into a fresh Claude
project before a customer working session or call. It tells Claude to use the Drivepoint MCP for
one brand, load the right guidance, apply that brand's query conventions, and answer the brand's
way.

**Do not paste this file as-is.** Fill every `{{PLACEHOLDER}}` from live MCP discovery for the
specific customer, then paste the rendered **Instruction block** (between the `===` rules) into
the project. The `drivepoint-customer` skill (in the `drivepoint-customers` repo) automates the
discovery + render and writes the result to `customers/<slug>/notes/project-instructions.md`.

**Why fill from discovery, never by hand:** mart names drift, MCP skill slugs drift, and the
subscription/segment field differs per customer (different column, different string values, or no
subscription business at all). Discovering at generation time keeps the instruction correct; the
ON LOAD block then re-verifies so it self-heals if the warehouse changes before the call.

## How to fill each placeholder

| Placeholder | Source (Drivepoint MCP) |
|---|---|
| `{{CUSTOMER_NAME}}`, `{{COMPANY_ID}}` | `get_drivepoint_user` → match the name/slug to a company `id`. |
| `{{ENV}}` / `{{DATASET}}` | `production` / `production_dwh_mart` (default). Use `staging` / `staging_dwh_mart` only on request. |
| `{{GENERATION_DATE}}` | The date you generate it (YYYY-MM-DD). |
| `{{MART_LIST}}` | `list_tables(company_id, '{{DATASET}}')` → list the real tables. Ignore `mart_test_model`. |
| `{{SEGMENT_RULE}}` | `SELECT DISTINCT segment, COUNT(*) FROM {{DATASET}}.ecommerce_transactions_order_level GROUP BY segment`. Pin the exact column + exact string values. If `segment` doesn't carry the sub/non-sub split, probe `tags` / `customer_type` / `customer_type_segment` (`get_schema` first). If the brand has no subscription business, replace the rule with "This customer has no subscription business — do not split on sub/non-sub." |
| `{{CHANNELS}}` | `SELECT DISTINCT channel FROM {{DATASET}}.ecommerce_transactions_order_level`. Note any channel (retail/wholesale) that lives only in the SmartModel, not the ecommerce mart. |

---

## Instruction block (render and paste everything between the rules)

```markdown
# Drivepoint project instructions — {{CUSTOMER_NAME}} ({{COMPANY_ID}})
<!-- Generated {{GENERATION_DATE}} by the drivepoint-customer skill · company={{COMPANY_ID}} · env={{ENV}}.
     Values below are pinned from live MCP discovery; the ON LOAD block re-verifies them so this
     self-heals if the warehouse drifts before the call. Re-run /drivepoint-customer to refresh. -->

Use the **Drivepoint MCP server ({{ENV}})**. Company = `{{COMPANY_ID}}` ({{CUSTOMER_NAME}}).

## ON LOAD — before waiting for any question
1. `get_drivepoint_user` → confirm `{{COMPANY_ID}}` is accessible. If not, stop and tell me.
2. `list_skills`, then `get_skill` on everything it returns — at minimum `data-dictionary`,
   `sample-queries`, `artifact-style-guide`, and `example-artifacts`. Apply them. Load whatever
   `list_skills` returns; don't trust the names here to still be current.
3. `list_tables` for `{{DATASET}}` and confirm the marts. Expected at generation: {{MART_LIST}}.
   If one is missing/renamed, use the closest current match and tell me what changed.
   (`mart_test_model` is internal — ignore it.)
4. Load this project's attached Drivepoint plugin skills, if present.

## QUERY RULES
- Default to the `{{DATASET}}` tables. Actuals → `smartmodel_actuals`; forecasts / variance →
  `smartmodel` / `smartmodel_actuals_vs_forecast` (filter by `plan_id` first); order & SKU detail
  → `ecommerce_transactions_order_level` / `_line_item_level`.
- **Subscription vs non-subscription** → {{SEGMENT_RULE}}. Verify on load and use what the query
  returns.
- Ecommerce channels: {{CHANNELS}}.
- Supported surface is `{{DATASET}}`. `production_executiveDashboard`, `production_ltvReport*`, and
  `production_smartModelData` are reachable but **undocumented** — only use them if a number
  genuinely isn't in the marts, `get_schema` first, and say so.
- `rows` is reserved in GoogleSQL — alias any `rows` identifier to something else.
- Never `SELECT *` on the ecommerce tables; list columns. State date range / plan / channel /
  currency in every numeric answer.

## OUTPUT
Answer with a **visual artifact built to the artifact style guide** (`artifact-style-guide` +
`example-artifacts`), opening with the Drivepoint `ArtifactHeader`. Don't answer inline unless the
result is ≤5 rows / 1 dimension. Then wait for my first question.
```

---

Rendered example: `drivepoint-customers/customers/immieats/notes/project-instructions.md`.
