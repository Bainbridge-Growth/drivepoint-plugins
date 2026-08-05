# Saved Reports Guide

How to build, preview, save, and edit a **saved report** in Drivepoint — a
data-backed report that lives in the Drivepoint app itself, at
`https://app.drivepoint.io/<company>/reports`, and renders from a structured
report definition.

This is different from an in-chat artifact (see `report-creation-guide.md`):
an artifact answers today's question in this conversation; a saved report is
a durable page in the customer's Drivepoint app. Saving one requires an admin
or superAdmin Drivepoint role. When a user asks to "add this report to
Drivepoint," "save this so the team can see it," "put this on my reports
page," or "edit the retention scorecard," this guide applies.

---

## Golden rules (read first)

- **Never call `save_report` unless the user explicitly asks to save.** A
  preview is not permission to save. Wait for a clear instruction, and let the
  user pick **save as new** (create) or **update** (overwrite an existing
  definition by `report_id`).
- **Always show a preview as an auto-opened JSX artifact** built to the
  `artifact-style-guide`, before any save.

## What a saved report is

A versioned, tenant-scoped **report definition**: named SELECT-only SQL
queries plus a structured `report` object plus metadata. It is data, not code
— saving one requires no deploy, and it appears in the app's Reports list
immediately. There is no HTML template: the app renders the `report` object
with built-in components.

```json
{
  "title": "Weekly DTC Sales Pulse",
  "description": "Net sales, orders, and AOV by week and channel.",
  "report_type": "sales-pulse",
  "queries": [{"key": "rows", "query": "SELECT ... FROM {ENV}_dwh_mart. ..."}],
  "report": {
    "header": {"title": "Weekly DTC Sales Pulse", "subtitle": "Last 12 weeks", "generatedAt": "2026-01-31T00:00:00Z"},
    "blocks": [
      {"type": "text", "text": {"title": "Overview", "body": "Two sentences of plain-language context for the period."}},
      {"type": "kpiGroup", "kpis": [{"label": "Net sales", "value": 9880021, "format": "currency", "highlight": true}]},
      {"type": "chart", "chart": {"chartType": "bar", "xKey": "week", "series": [{"key": "netSales", "label": "Net sales"}], "valueFormat": "currency", "data": [{"week": "W1", "netSales": 812345}]}},
      {"type": "table", "table": {"columns": [{"key": "week", "label": "Week"}, {"key": "netSales", "label": "Net sales", "format": "currency", "emphasize": true}], "rows": [{"week": "W1", "netSales": 812345}]}}
    ]
  },
  "context": {"weeks": 12},
  "status": "active"
}
```

The server stamps `id`, `version`, `created_/updated_by/at` on save. Every
save snapshots the previous version to an audit history, so a bad save can be
rolled back — but treat saves as real: preview first, always.

## The four tools

| Tool | What it does |
|---|---|
| `list_reports` | Summaries of the company's saved definitions |
| `get_report` | One full definition (queries + `report` object + context) |
| `preview_report` | Runs a saved definition's queries — or draft `queries` you pass — against the company's live warehouse and returns the rows keyed by each query's `key` |
| `save_report` | Creates a definition, or updates one when `report_id` is passed |

## The authoring loop

1. **Discover the data.** Use `list_datasets` / `list_tables` / `get_schema`
   and the `data-dictionary` / `sample-queries` skills. Never guess column
   names.
2. **Draft the queries.** SELECT-only. Reference datasets with the `{ENV}_`
   prefix token (e.g. `{ENV}_dwh_mart.orders`) — it is substituted per
   environment. Parameterize with `${$CONTEXT.<param>}` tokens and put
   defaults for every param in `context`. Keep result sets small and
   aggregated.
3. **Preview the data.** `preview_report` with the draft `queries`. Confirm
   every key returns rows, the numbers are sane (spot-check against a known
   figure), and nothing is truncated. Fix and re-preview until clean.
4. **Build the report.** Turn the previewed rows into `report.blocks` (see the
   report contract below). The values are baked into the blocks — the app does
   not re-run your SQL at render time.
5. **Show a preview artifact — always.** Render the report as an in-chat
   **JSX/React artifact** that follows the `artifact-style-guide` skill, and
   **auto-open** it so the user sees it immediately. This is the review step:
   the artifact must mirror what the saved report will look like (same header,
   same blocks, same numbers). Never describe the report only in text; never
   substitute a preview for a save.
6. **Stop and wait for an explicit save instruction.** Do **not** call
   `save_report` on your own — not after a preview, not because the data looks
   good, not to "finish the task". Saving is a deliberate user action. Only
   call `save_report` when the user explicitly asks, and let them choose:
   - **"save as new"** (or "create") → call `save_report` **without**
     `report_id` (creates a new definition).
   - **"update"** (or "save over the existing one") → call `save_report`
     **with** the `report_id` of the definition being edited.

   If it is ambiguous which they mean, ask. After a save, report the title and
   the app path `/:company/reports/mcp/<id>`. If the save is rejected for the
   author role, hand the definition to a Drivepoint admin instead of retrying.

**Editing** is the same loop starting from `get_report`: fetch, change the
queries and/or the `report` blocks, `preview_report`, show the updated preview
artifact, then wait for the user to say "update" (or "save as new") before
calling `save_report`. Never save an edit the user has not previewed and
explicitly approved.

## Report contract

`report` is `{header, blocks}`. No HTML, no scripts — just structured data the
app maps to components.

**header** — `{title, subtitle?, eyebrow?, generatedAt?}`. `generatedAt` is an
ISO timestamp, rendered as an "Updated <date>" line.

**blocks** — an ordered array rendered top to bottom. Each block is one of four
types:

- **`kpiGroup`** — a row of KPI cards.
  `{"type": "kpiGroup", "kpis": [{...}]}` where each kpi is
  `{label, value, format?, note?, highlight?, delta?}`. `value` is a string or
  number; `format` is one of `number | currency | percent | text`; `delta` is
  `{value, goodDirection?}` where `value` is fractional (0.12 renders as +12%)
  and `goodDirection` (`up` | `down`, default `up`) colors it.
- **`chart`** — `{"type": "chart", "chart": {...}}` where chart is
  `{chartType, title?, data, xKey, series, stacked?, valueFormat?, height?, colors?}`.
  `chartType` is `line | bar | area | pie | doughnut`; `data` is the array of
  row objects to plot; `xKey` is the field for the x-axis (or slice label for
  pie/doughnut); `series` is `[{key, label?, color?}]` (pie/doughnut use the
  first series as the value); `valueFormat` formats the axis/tooltips.
- **`table`** — `{"type": "table", "table": {...}}` where table is
  `{title?, columns, rows, total?}`. Each column is
  `{key, label, align?, format?, emphasize?}` (`align` defaults to right for
  numeric formats, else left; `emphasize` bolds the column). `rows` are objects
  keyed by column `key`; `total` is an optional bold footer row keyed the same.
- **`text`** — `{"type": "text", "text": {title?, body}}` where `body` is a
  single string or an array of strings (each rendered as its own paragraph).
  Use it for a short overview at the top or a "what stands out" takeaways
  section. Prefer real `text` blocks over faking prose with a one-column table.

Rules that keep reports clean:

- **Bake real numbers in.** Put previewed values directly into `kpis`,
  `chart.data`, and `table.rows`. Round and pre-format in SQL or when building
  the blocks; do not ship raw, unrounded floats.
- **Pick the right block.** KPIs for headline metrics, chart for trend/mix,
  table for detail, text for narrative. A typical report is: a short `text`
  overview, a `kpiGroup`, one or two charts, a detail `table`, and a closing
  `text` takeaways block.
- **Drivepoint house style.** Concise, plain language. **No em dashes** in any
  copy (titles, labels, body) — use commas, periods, or "to" for ranges.

## Governance (do not work around)

- Queries run only in the company's own warehouse project and only against
  the allowed datasets; `save_report` dry-runs every query and rejects
  anything else. If a dataset you need is blocked, say so.
- Saves are versioned and audited (who, when, what changed). Use
  `status: "archived"` to retire a report; do not overwrite a report with an
  empty `report` to "delete" it.
- A save is always user-initiated. Do not auto-save, save "to be helpful", or
  re-save on your own after an edit. Preview, then wait for an explicit "save
  as new" or "update".
- One tenant per definition. For the same report across tenants, save the
  same definition per company (keep `report_type` identical so instances stay
  linked).
