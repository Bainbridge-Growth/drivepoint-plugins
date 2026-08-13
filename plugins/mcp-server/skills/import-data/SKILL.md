---
name: import-data
description: How to run a Drivepoint data-import definition (Shopify, Amazon, TikTok, Cin7, finance, custom BigQuery pulls) into a customer plan's Excel workbook with the list_import_definitions and import_data MCP tools. Required reading whenever the user asks to import, refresh, pull, or sync data into a plan, a tab, or the workbook, or names a stock import such as DTC Retention, Shopify raw pivot, Amazon monthly, Wholesale DC, or TikTok retention. Covers the single supported workflow, presenting inputs for confirmation, handling import errors, caching, and what is out of scope.
---

# Data Imports

How to run a Drivepoint data-import definition (Shopify, Amazon, TikTok,
Cin7, finance, custom BigQuery pulls, etc.) into a customer plan's Excel
workbook via the MCP tools.

Reading this skill is required any time the user asks to "import",
"refresh", "pull", or "sync" data into a plan, a tab, or the workbook,
or names one of the stock imports (e.g. "DTC Retention", "Shopify raw
pivot", "Amazon monthly", "Wholesale DC", "TikTok retention").

The MCP server exposes exactly two import tools:

- `list_import_definitions` — read-only; returns every import available
  to the current company, with each input already enriched by the
  server.
- `import_data` — writes rows into a plan's destination worksheet tab.

Everything else is out of scope. Do not use `run_query`,
`list_datasets`, `list_tables`, `describe_table`, or any other
data-catalog / schema tool as part of an import — the server has
already resolved the inputs and the query.

---

## The one workflow

Follow these steps in order. Never skip a step, never reorder them.

1. **Pick the plan.** Call `list_company_plans` and select the target
   plan. You need its `plan_id` for `import_data`. If the user already
   named the plan, match by name; if not, ask.
2. **List the imports.** Call `list_import_definitions` for the same
   `company_id`. The response is the single source of truth for what
   imports exist and what values each one accepts. It is cached
   server-side for five minutes.
3. **Pick the definition.** Match the user's intent to one
   definition's `id` / `displayName` / `sourceId` / `tabName`. If
   ambiguous, ask.
4. **Read the inputs.** For the chosen definition, look at
   `definition.inputs[]`. Every input carries:
   - `key` (or `name`) — the field name you must pass in
     `field_values`.
   - `display_name` — the human label to show the user.
   - `input_type` (or `type`) — `bigquery`, `javascript`, `select`,
     `multiselect`, `text`, `date`, `checkbox`, etc.
   - `resolvedDefault` — the concrete default the server computed by
     evaluating that input's `default_value` (or the literal value if
     `default_value` is not JS). Present in most cases; absent when the
     definition doesn't declare a default.
   - `possibleValues` — the resolved list of legal values, when the
     server can compute one:
     - `input_type: "bigquery"` → the distinct column values pulled
       from the customer's warehouse.
     - `input_type: "javascript"` → the array the JS expression
       evaluates to.
     - Any input carrying a literal array in `values` / `options` /
       `enum` / `choices` → that array.
   - `possibleValuesTruncated: true` — set when the list was capped
     (currently at 1000 values). Tell the user the list is truncated
     if you show it.
5. **Confirm with the user.** For every input the definition declares,
   surface the label, the default (if any), and the legal choices (if
   any). Ask the user to accept the default or pick a specific value.
   Skip this step only when the definition has zero inputs.
6. **Import.** Call `import_data` with:
   - `company_id`
   - `plan_id`
   - `definition_id`
   - `field_values` — an object keyed by the input's `key` (or
     `name`), containing the user's picks. Inputs the user does not
     explicitly override fall back to `resolvedDefault` on the server;
     you do **not** need to re-send unchanged defaults.
   - `historical_start_date` — only when the template requires it
     (rare; the field will be referenced in the definition or the
     server will tell you it is missing).

A successful `import_data` returns `{status: "success", tabName,
rowCount}`. Report both to the user so they know where the data
landed.

---

## Never do

These are the mistakes that cause the import path to fail or misfire.
Every one of them is already prevented by the tool contract; if you
find yourself about to do one, stop and re-read this section.

- **Never guess values.** If an input's `resolvedDefault` /
  `possibleValues` is not enough to decide, ask the user. The user is
  always the source of truth for input choices.
- **Never invent values that are not in `possibleValues`.** If the
  server returned a list, it is exhaustive (or truncated with
  `possibleValuesTruncated: true`, in which case the user can also
  type a value they know exists). Do not pass a value that isn't in
  the list unless the user typed it themselves.
- **Never call `run_query`, `list_datasets`, `list_tables`, or
  `describe_table` to figure out an input's legal values.** The server
  has already run the equivalent query and returned the result on
  `possibleValues`. Calling a catalog tool is redundant, slower, and
  usually rejected by the allowlist.
- **Never send raw SQL as part of an import.** Templates live in
  Firestore and are rendered server-side; the agent has no channel to
  influence the query beyond the declared `field_values`.
- **Never auto-select a value silently.** If you decide to use a
  default, say so ("I'll use the default: `retention_type = actuals`")
  so the user has a chance to override.
- **Never bypass `list_import_definitions`.** Even if you remember the
  definition from an earlier turn, re-read the inputs — company
  configuration and dynamic `possibleValues` change over time.
- **Never fabricate a `plan_id`.** Always resolve it via
  `list_company_plans`. Plan ids are SharePoint drive-item ids and are
  not guessable.

---

## Handling common errors from `import_data`

The server returns actionable error strings. Map them to a next step:

- **`missing field_values for inputs: <name1>, <name2>, ...`** — one
  or more inputs have no user pick and no default. Re-read
  `list_import_definitions` for those inputs and ask the user. Do not
  retry with empty strings, empty arrays, or invented values.
- **`import type "<type>" is not supported over MCP (only
  "bigquery")`** — the chosen definition is a client-side sentinel
  (e.g. `r_gl_replace`, `get_data_from_warehouse`, `financial`) that
  the MCP server cannot execute. Tell the user to run the import from
  the Excel add-in, and offer a suitable `bigquery` alternative if one
  exists in the listing.
- **`import definition "<id>" not found`** — the id is wrong or gated
  off for this company. List again and pick from the fresh response.
- **`company "<id>" has no sharepoint_site_id`** — the company is not
  wired to a SharePoint site. Escalate; MCP cannot fix this.
- **Any BigQuery syntax error** — a template referenced a variable
  the user's `field_values` didn't set (defaults resolved, but the
  variable name in the template is different from the input key).
  Report the raw error verbatim, do not retry the import against
  guesses. This is a Firestore-config bug, not a user-input bug.

---

## Presenting inputs to the user (recipe)

For a definition with inputs, produce a compact confirmation before
calling `import_data`. One line per input, in the order the definition
lists them.

Format:

```
- <display_name> (`<key>`, <input_type>) — default: <resolvedDefault>
  options: <first 5 possibleValues>[, … N more]
```

When `possibleValuesTruncated: true`, add "(list truncated at 1000)"
after the options. When there are no `possibleValues`, drop the
"options:" line.

Do not include this scaffolding for definitions with `inputs: []` —
just call `import_data` and report the result.

---

## Examples

### Zero-input definition (Shopify raw pivot)

```
list_company_plans({company_id: "…"}) → pick plan_id
list_import_definitions({company_id: "…"}) → find definition_id = "shopifyRawDataPivoted"
import_data({company_id, plan_id, definition_id: "shopifyRawDataPivoted"})
```

Report back: `Wrote 1,240 rows to "R - Monthly Shopify Data Pivot"`.

### BigQuery-typed input (DTC Retention → `retention_type`)

`list_import_definitions` returns something like:

```json
{
  "id": "dtc_retention",
  "displayName": "DTC Retention",
  "tabName": "R - DTC Retention",
  "type": "bigquery",
  "inputs": [
    {"key": "created_at", "input_type": "date", "display_name": "Prediction Created At", "resolvedDefault": "2026-06-01T00:00:00"},
    {"key": "forecast_length", "input_type": "text", "display_name": "Forecast Years", "resolvedDefault": "5"},
    {"key": "retention_type", "input_type": "bigquery",
     "display_name": "Retention Type",
     "resolvedDefault": ["actuals", "prediction"],
     "possibleValues": ["actuals", "prediction"]}
  ]
}
```

Confirm with the user:

```
- Prediction Created At (`created_at`, date) — default: 2026-06-01T00:00:00
- Forecast Years (`forecast_length`, text) — default: 5
- Retention Type (`retention_type`, bigquery) — default: ["actuals", "prediction"]
  options: actuals, prediction
```

User picks `retention_type: ["actuals"]`. Import:

```
import_data({
  company_id, plan_id,
  definition_id: "dtc_retention",
  field_values: {retention_type: ["actuals"]}
})
```

`created_at` and `forecast_length` fall back to their defaults.

### Multiselect / dimensional import

Financial dimensional imports declare a single multiselect input,
usually `key: "dimensions"`, with `possibleValues` such as
`[{"key":"class","label":"Class"}, {"key":"dimension1","label":"Dimension 1"}, {"key":"channel","label":"Drivepoint Channel"}]`.
Preserve the objects (do not flatten to strings) when the user picks a
subset — the template consumes them as objects.

---

## Caching

`list_import_definitions` results are cached server-side per
`(company_id, cloudProjectId)` for five minutes. That is usually fine:
input `possibleValues` don't churn faster than that, and defaults are
recomputed on every call anyway. If the user just changed a Firestore
definition or expects a newly-added value in `possibleValues` and does
not see it, wait 5 minutes and try again — there is no cache-bust tool
exposed over MCP.

---

## Out of scope

The MCP import path exists to run individual `bigquery`-type imports
end-to-end into a plan's workbook. It does not:

- Run "Import All Default Tables" — that is an add-in feature.
- Support the FAM v2 R-GL replace sentinel (`r_gl_replace`) — run
  from the add-in.
- Return the imported rows themselves — the tool writes them to
  Excel and reports `rowCount` only. If the user wants to see the
  rows in chat, run the equivalent analytical query via the read
  tools instead of importing.

If a request lands outside those boundaries, tell the user and stop —
do not synthesize a workaround with `run_query`.
