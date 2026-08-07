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
- **The preview artifact and the saved definition are the same object.** Build
  the full `report` ({header, blocks}) first, then — before any save — **always**
  render an auto-opened JSX artifact (per `artifact-style-guide`) directly from
  that object, every block in order, and pass that exact object to `save_report`
  unchanged. Never hand-author the artifact separately, and never add, drop, or
  reword a block (text/framing and chart `orientation` included) between preview
  and save. If anything changes after previewing, re-render and re-preview.
- **Reports are query-driven, not baked.** A block never carries data; it
  names a query (by `key`) and the app runs that query at **view time**, so the
  report stays live against the warehouse. Write **one focused query per
  block**.

## What a saved report is

A versioned, tenant-scoped **report definition**: named SELECT-only SQL
queries plus a structured `report` object plus metadata. It is data, not code
— saving one requires no deploy, and it appears in the app's Reports list
immediately. There is no HTML template: the app renders the `report` object
with built-in components, running each block's query when the page is viewed.

```json
{
  "title": "Weekly DTC Sales Pulse",
  "description": "Net sales, orders, and AOV by week.",
  "report_type": "sales-pulse",
  "queries": [
    {"key": "headline", "query": "SELECT net_sales AS netSales, orders, aov, net_sales_wow AS netSalesWow FROM {ENV}_dwh_mart.sales_pulse_summary WHERE weeks = ${$CONTEXT.weeks}"},
    {"key": "weekly", "query": "SELECT week, net_sales AS netSales FROM {ENV}_dwh_mart.sales_pulse_weekly ORDER BY week"},
    {"key": "weeklyTotal", "query": "SELECT 'Total' AS week, SUM(net_sales) AS netSales FROM {ENV}_dwh_mart.sales_pulse_weekly"}
  ],
  "report": {
    "header": {"title": "Weekly DTC Sales Pulse", "subtitle": "Last 12 weeks", "generatedAt": "2026-01-31T00:00:00Z"},
    "blocks": [
      {"type": "text", "text": {"title": "Overview", "body": "Two sentences of plain-language context for the period."}},
      {"type": "kpiGroup", "query": "headline", "kpis": [
        {"label": "Net sales", "column": "netSales", "format": "currency", "highlight": true, "delta": {"column": "netSalesWow", "goodDirection": "up"}},
        {"label": "Orders", "column": "orders", "format": "number"},
        {"label": "AOV", "column": "aov", "format": "currency"}
      ]},
      {"type": "chart", "chart": {"chartType": "bar", "query": "weekly", "xKey": "week", "series": [{"key": "netSales", "label": "Net sales"}], "valueFormat": "currency"}},
      {"type": "table", "table": {"query": "weekly", "totalQuery": "weeklyTotal", "columns": [{"key": "week", "label": "Week"}, {"key": "netSales", "label": "Net sales", "format": "currency", "emphasize": true}]}}
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
| `preview_report` | Runs a saved definition's queries — or draft `queries` you pass — against the company's live warehouse and returns the rows keyed by each query's `key` (the same rows the view endpoint feeds to each block) |
| `save_report` | Creates a definition, or updates one when `report_id` is passed |

## The authoring loop

1. **Discover the data.** Use `list_datasets` / `list_tables` / `get_schema`
   and the `data-dictionary` / `sample-queries` skills. Never guess column
   names.
2. **Draft one query per data block** (text-only blocks need none, and a
   text-only report needs no queries at all). SELECT-only. Reference datasets
   with the `{ENV}_` prefix token (e.g. `{ENV}_dwh_mart.orders`) — substituted per
   environment. Parameterize with `${$CONTEXT.<param>}` tokens and put defaults
   for every param in `context`. Each query should SELECT **exactly** the
   columns and rows its block renders: a `kpiGroup` query returns a **single
   row** with one column per KPI (and per delta); chart/table queries return
   the rows to plot or list. Do the rounding, aliasing, and formatting in SQL.
3. **Preview the data.** `preview_report` with the draft `queries`. Confirm
   every key returns rows, the shape matches the block that will consume it
   (KPI row has the right columns; chart/table rows have `xKey`/column keys),
   the numbers are sane (spot-check against a known figure), and nothing is
   truncated. Fix and re-preview until clean.
4. **Build the report.** Wire each block to a query by `key` — do **not** copy
   rows into the blocks:
   - `kpiGroup` → set the block's `query`, and give each kpi a `column` (and
     `delta.column`) naming a field in that query's single row.
   - `chart` → set `chart.query`, plus `xKey` and `series[].key` naming columns
     in that query's rows.
   - `table` → set `table.query`, list `columns` (each `key` a column in the
     query's rows), and optionally `table.totalQuery` for a footer row.
   The app runs these queries at view time, so the report always reflects the
   latest data.
5. **Show a preview artifact — always, rendered from the definition.** Render
   the report as an in-chat **JSX/React artifact** that follows the
   `artifact-style-guide` skill by walking the `report` object you built in
   step 4 — **every block, in the same order** — filling data blocks with the
   previewed rows and resolving text `{{token}}`s. **Auto-open** it. The
   definition is the single source of truth, so the artifact must be a
   one-to-one rendering of it: same header, same block list / order / types
   (KPIs, charts, tables, **and every text/framing block**), same chart types
   and `orientation`, same numbers the live queries return. Before saving, diff
   the artifact against the definition block-for-block; if they differ, the
   artifact is wrong (or you edited the definition after building it) — fix and
   re-render. Show a small **status badge** at the top of the artifact so the
   user can always tell what they are looking at: **"Unsaved draft"** whenever
   there are changes not yet saved (including a brand-new report), and
   **"Saved"** once the artifact matches the saved definition (re-render with the
   saved state after a successful `save_report`). Never describe the report only
   in text; never substitute a preview for a save.
6. **Stop and wait for an explicit save instruction.** Do **not** call
   `save_report` on your own — not after a preview, not because the data looks
   good, not to "finish the task". Saving is a deliberate user action. Only
   call `save_report` when the user explicitly asks, and let them choose:
   - **"save as new"** (or "create") → call `save_report` **without**
     `report_id` (creates a new definition).
   - **"update"** (or "save over the existing one") → call `save_report`
     **with** the `report_id` of the definition being edited.

   Always pass a short `change_summary` describing what this save changed or
   added (e.g. `"Added a channel-split bar chart and a % of total data bar."`).
   It's shown in the report's version history so a reader can scan who changed
   what, when. On a brand-new report it defaults to "Report was created", so you
   only need it on updates.

   If it is ambiguous which they mean, ask. **Don't re-run the queries to
   save.** You already previewed the data in step 3; if the queries and `report`
   are unchanged, call `save_report` directly — it dry-run-validates every query
   itself, so a fresh `preview_report` at save time is wasted warehouse work.
   Save the **exact** `report` object you rendered the artifact from — do not add,
   drop, or reword blocks (or flip a chart's `orientation`, or slip in extra
   framing text) at save time. If you change anything, it's a new draft:
   re-render the artifact and let the user see it before saving.
   After a save, give the user a **clickable link** to the report in chat, e.g.
   `[<title>](https://app.drivepoint.io/<company>/reports/mcp/<id>)`, using the
   returned id. If the save is rejected for the author role, hand the definition
   to a Drivepoint admin instead of retrying.

**Editing** (any request to update or change an existing report) is the same
loop starting from `get_report`: fetch the definition and **always render its
current state as a JSX artifact first** (marked **"Saved"**), so the user sees
what exists before anything changes. Then make the requested changes,
`preview_report`, and re-render the updated artifact (marked **"Unsaved
draft"**). Only after the user has seen that updated preview, **explicitly ask
whether to update this report (save over it, using its `report_id`) or save it
as a new one** — never assume which. Never save an edit the user has not
previewed and explicitly approved.

## Report contract

`report` is `{header, blocks}`. No HTML, no scripts, no baked data — just
structured data the app maps to components, with each data block naming the
query whose rows it renders.

**header** — `{title, subtitle?, eyebrow?, generatedAt?}`. `generatedAt` is an
ISO timestamp, rendered as an "Updated <date>" line.

**blocks** — an ordered array rendered top to bottom. Each block is one of four
types:

- **`kpiGroup`** — a row of KPI cards.
  `{"type": "kpiGroup", "query": "<key>", "kpis": [{...}]}`. The named query
  returns **one row**; each kpi is `{label, column, format?, note?, highlight?,
  delta?}`. `column` names the field in that row to read the value from;
  `format` is one of `number | currency | percent | text`; `delta` is
  `{column, goodDirection?}` where `column` holds a fractional change (0.12
  renders as +12%) and `goodDirection` (`up` | `down`, default `up`) colors it.
- **`chart`** — `{"type": "chart", "chart": {...}}` where chart is
  `{chartType, title?, subtitle?, query, xKey, series, stacked?, orientation?, valueFormat?, height?, colors?}`.
  `subtitle` is a small caption under the title (period or a one-line takeaway).
  `chartType` is `line | bar | area | pie | doughnut`; `query` is the key of the
  query whose rows are plotted; `xKey` is the field for the x-axis (or slice
  label for pie/doughnut); `series` is `[{key, label?, color?}]` naming columns
  to plot (pie/doughnut use the first series as the value); `stacked` stacks the
  series; `orientation` is `vertical` (default) or `horizontal` — pair
  `orientation: "horizontal"` with `stacked: true` for a horizontal stacked bar;
  `valueFormat` formats the axis/tooltips.
- **`table`** — `{"type": "table", "table": {...}}` where table is
  `{title?, subtitle?, query, columns, totalQuery?}` (`subtitle` is a small caption
  under the title, e.g. the period or a one-line takeaway). `query` is the key of
  the query whose rows fill the table. Each column is
  `{key, label, align?, format?, emphasize?, chart?, bar?}` (`align` defaults to
  right for numeric formats, else left; `emphasize` bolds the column); each `key`
  names a column in the query's rows. `totalQuery` is an optional key of a query
  whose first row renders as a bold footer, keyed the same as `columns`. Two
  in-cell visual options (use at most one per column):
  - `chart: {type?: line|bar|area, color?, series?}` renders each cell as a
    **sparkline**. Single series: the query returns this column as an **array of
    numbers per row** (e.g. `ARRAY_AGG(net_sales ORDER BY month) AS trend`). For
    **multi-series** (overlaid lines, grouped bars, stacked areas), return one
    array per series field and list them in `series: [{key, color?, label?}]` —
    each `key` names a row field holding its own array; all share one cell.
  - `bar: {color?, max?}` renders each cell as an in-cell **horizontal data bar**
    from a **single numeric value per row** (e.g. `pct_of_total` shown as a
    proportional bar). `max` is the value that fills the bar (defaults to `1` for
    `percent` format, else the column's max). Use this for share-of-total columns.
- **`text`** — `{"type": "text", "text": {title?, body}}` where `body` is a
  single string or an array of strings (each rendered as its own paragraph).
  Use it for a short overview at the top or a "what stands out" takeaways
  section. Prefer real `text` blocks over faking prose with a one-column table.
  Text is not re-derived from data, so **never type live numbers into prose** —
  they go stale. Instead:
  - **Embed value tokens.** Write `{{queryKey.column}}` or
    `{{queryKey.column:format}}` (format: `number | currency | percent`) inside
    the body; the app substitutes the value from that query's **first row** at
    view time. e.g. `Net sales reached {{headline.netSales:currency}} on
    {{headline.orders:number}} orders.` Point a token at a single-row query so
    "first row" is unambiguous.
  - **Date qualitative analysis.** Trend reads and standouts ("peaked in late
    summer", "the standout SKU") are reasoning a token can't express and become
    a point-in-time snapshot. Frame them as of the report's `generatedAt`
    (e.g. a "Highlights (as of <generatedAt>)" title) so viewers know they are a
    snapshot, and refresh them on a later edit.
  - **Keep framing evergreen.** Overview/context prose (what the report covers,
    window, methodology) should carry no baked figures so it stays true.

Rules that keep reports clean:

- **One focused query per block.** Shape data in SQL (round, alias to the exact
  column keys the block uses, return only the rows it needs); do not over-fetch
  or reshape client-side.
- **Blocks are optional — compose to the ask.** No block type is required.
  Include only what the data and the user's request call for: a report can be a
  single `table`, KPIs only, a chart plus takeaways, or `text`-only (which needs
  no `queries`). Let the request and the data drive the shape, not a template.
  As a rule of thumb, KPIs suit headline metrics, charts suit trend/mix, tables
  suit detail, and text suits narrative; a fuller report often runs `text`
  overview → `kpiGroup` → chart(s) → detail `table` → `text` takeaways, but drop
  anything that doesn't serve the question.
- **Drivepoint house style.** Concise, plain language. **No em dashes** in any
  copy (titles, labels, body) — use commas, periods, or "to" for ranges.

## Governance (do not work around)

- Queries run only in the company's own warehouse project and only against
  the allowed datasets; `save_report` dry-runs every query and rejects
  anything that is not a same-project SELECT. If a dataset you need is blocked,
  say so.
- Every query key a block references must exist in `queries`; a definition that
  points a block at an unknown key is rejected on save.
- Saves are versioned and audited (who, when, what changed). Use
  `status: "archived"` to retire a report; do not overwrite a report with an
  empty `report` to "delete" it.
- A save is always user-initiated (see Golden rules). Do not auto-save, save
  "to be helpful", or re-save on your own after an edit.
- One tenant per definition. For the same report across tenants, save the
  same definition per company (keep `report_type` identical so instances stay
  linked).
