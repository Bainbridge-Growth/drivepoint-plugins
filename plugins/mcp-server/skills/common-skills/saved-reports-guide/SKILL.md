# Saved Reports Guide

How to build, preview, save, and edit a **saved report** in Drivepoint — a
data-backed report that lives in the Drivepoint app itself, at
`{{app_base_url}}/<company>/reports`, and renders from a structured
report definition.

This is different from an in-chat artifact (see `report-creation-guide.md`):
an artifact answers today's question in this conversation; a saved report is
a durable page in the customer's Drivepoint app. Saving one requires an admin
or superAdmin Drivepoint role. When a user asks to "add this report to
Drivepoint," "save this so the team can see it," "put this on my reports
page," or "edit the retention scorecard," this guide applies.

---

## Golden rules (read first)

- **Emit the whole `report` object in one shot — no placeholders.** `blocks` is
  required and must be the complete array; every entry in `controls` must be a
  full control object. Never abbreviate with placeholder strings (`"wired
  below"`, `"..."`, `"TODO"`), never omit `blocks`, and never leave a required
  field to "fill in later". `save_report` validates the payload and rejects any
  stub or missing field, so a truncated object just fails the save. If the object
  is large, write it out in full anyway.
- **Never call `save_report` unless the user explicitly asks to save.** A
  preview is not permission to save, and write access being enabled is not
  permission either. Wait for a clear instruction in the user's latest message,
  then pass `user_requested_save: true`; the server refuses a save without it.
  Let the user pick **save as new** (create) or **update** (overwrite an
  existing definition by `report_id`). Never save to test a fix or to see a
  change: every save is a new version. If the saved report looks wrong in the
  app but the definition is correct, say so and stop instead of saving again.
- **Follow the report conventions below by default.** They are the standard for
  every saved report and match the report gallery templates. Set one aside only
  when the user explicitly asks for that choice, and say which one.
- **The artifact, the definition, and what gets saved are one object.** Build the
  full `report` ({header, blocks}) first; render an auto-opened JSX artifact (per
  `artifact-style-guide`) directly from it, every block in order; and pass that
  exact object to `save_report` unchanged. Never add, drop, or reword a block
  (text/framing and chart `orientation` included) between preview and save — if
  anything changes, it's a new draft: re-render and re-preview.
- **Decide once, then author the definition once — don't double-build.** The moment
  there's a save signal ("save this", "add to my reports page", a recurring team
  page), skip building a throwaway free-form `report-creation-guide` artifact and go
  straight to the definition object; every artifact renders from it. Render **once
  per state**, and **keep the badge in sync with reality at all times**: an
  **"Unsaved draft"** badge whenever the artifact differs from what's saved, and —
  after a successful save — **always** update that same artifact's badge to
  **"Saved"**. The chat link is *in addition to* the badge flip, never instead of
  it. `preview_report` fills live rows and validates — it is not a second authoring
  pass or a reason to rebuild.
- **One artifact per report — update it in place.** Keep a single artifact for a
  report and **update** it as its state changes (draft → saved, and on later edits);
  do not emit a new artifact each render. Reusing the same artifact keeps the thread
  clean (one obvious "live" version) and is faster and cheaper than regenerating.
  Create a **new** artifact only for a genuinely different report — e.g. a "save as
  new" that makes a separate definition.
- **Reports are query-driven, not baked.** A block never carries data; it
  names a query (by `key`) and the app runs that query at **view time**, so the
  report stays live against the warehouse. Write **one focused query per
  block**.
- **Talk to the user, not to the machine.** Refer to a report by its **title**,
  never its `report_id` or other internal ids/fields — the user neither needs
  nor recognizes them. Keep messages short and outcome-focused: don't recite a
  blow-by-blow of every block you changed, don't narrate `report_id`s, statuses,
  query keys, or the save mechanics. The artifact already shows the result; a
  one-line recap is plenty. When you must ask whether to overwrite or create,
  make it a single plain question naming the report by title (see step 6).

## Report conventions (standard for every report)

These come from the report gallery templates. Every report you build or edit
follows them unless the user explicitly asks otherwise in this conversation.
`preview_report` (when you pass the draft `report`) and `save_report` return
`convention_warnings` for anything off-convention. Fix each warning before you
show or save the report, unless the user asked for that deviation.

1. **A definition, not an artifact.** A report the user may keep is a structured
   definition (`header`, `controls`, `blocks`) with live queries. Do not save a
   React artifact as the report: an artifact-linked report is a static copy
   whose numbers never refresh, with no native controls or CSV download.
2. **Controls live in the Controls side panel.** Put every filter and view
   control in `report.controls`; Drivepoint draws them in the side panel. Never
   put controls, pickers, or "use the filter above" instructions in the report
   body, a `text` block, or a title.
3. **Queries bind to controls.** A `requery` control's `key` appears as
   `${$CONTEXT.<key>}` in every query it should scope (a `dateRange` uses
   `${$CONTEXT.<key>_start}` and `${$CONTEXT.<key>_end}`), unquoted, with a
   default on the control or in `context`. Use `clientData` only when no KPI,
   table total, or text token depends on the filtered rows and every filtered
   block carries the column.
4. **One standard date control.** A report with a date axis gets one
   `dateRange` control with `presets` `last_12_months`, `year_to_date`,
   `this_month`, `last_month`, `last_quarter` and `defaultPreset`
   `last_12_months`.
5. **Header.** A plain title and a `subtitle` that names the source and anything
   the report does not cover.
6. **Structure.** Every block has a stable `id`. Order: a `kpiGroup` when there
   are headline numbers, then a chart, then the detail table built from the same
   query as the chart, with the same title. Text blocks frame; they never hold
   data tables.
7. **Tables.** A `title`, `sortable: true`, and a `format` on every column
   (`text` for labels and dates; `currency`, `number`, or `percent` for values).
   Every table block gets the native CSV download.
8. **Charts.** Set `valueFormat`. A chart with three or more series gets a
   `seriesVisibility` control with a short `default` list.
9. **Copy.** Column, series, KPI, and control labels in Title Case. No em
   dashes anywhere.
10. **One report per title.** Before creating, call `list_reports`. If a report
    with the same title exists, update it by `report_id` or ask the user; never
    leave two copies in the Reports list.

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
  "queries": [
    {
      "key": "headline",
      "query": "SELECT SUM(net_sales) AS netSales, SUM(orders) AS orders, SAFE_DIVIDE(SUM(net_sales), SUM(orders)) AS aov FROM {ENV}_dwh_mart.sales_pulse_weekly WHERE week BETWEEN ${$CONTEXT.period_start} AND ${$CONTEXT.period_end}"
    },
    {
      "key": "weekly",
      "query": "SELECT week, net_sales AS netSales FROM {ENV}_dwh_mart.sales_pulse_weekly WHERE week BETWEEN ${$CONTEXT.period_start} AND ${$CONTEXT.period_end} ORDER BY week"
    },
    {
      "key": "weeklyTotal",
      "query": "SELECT 'Total' AS week, SUM(net_sales) AS netSales FROM {ENV}_dwh_mart.sales_pulse_weekly WHERE week BETWEEN ${$CONTEXT.period_start} AND ${$CONTEXT.period_end}"
    }
  ],
  "report": {
    "header": {
      "title": "Weekly DTC Sales Pulse",
      "subtitle": "Net sales, orders, and AOV by week from the ecommerce mart. Returns and fees are not included.",
      "generatedAt": "2026-01-31T00:00:00Z"
    },
    "controls": [
      {
        "type": "dateRange",
        "key": "period",
        "label": "Period",
        "bind": "requery",
        "presets": ["last_12_months", "year_to_date", "this_month", "last_month", "last_quarter"],
        "defaultPreset": "last_12_months"
      }
    ],
    "blocks": [
      {
        "type": "text",
        "id": "overview",
        "text": {
          "title": "Overview",
          "body": "Two sentences of plain-language context for the period."
        }
      },
      {
        "type": "kpiGroup",
        "id": "headline",
        "query": "headline",
        "kpis": [
          { "label": "Net Sales", "column": "netSales", "format": "currency", "highlight": true },
          { "label": "Orders", "column": "orders", "format": "number" },
          { "label": "AOV", "column": "aov", "format": "currency" }
        ]
      },
      {
        "type": "chart",
        "id": "chart",
        "chart": {
          "chartType": "bar",
          "title": "Weekly Net Sales",
          "query": "weekly",
          "xKey": "week",
          "series": [{ "key": "netSales", "label": "Net Sales" }],
          "valueFormat": "currency"
        }
      },
      {
        "type": "table",
        "id": "table",
        "table": {
          "title": "Weekly Net Sales",
          "query": "weekly",
          "totalQuery": "weeklyTotal",
          "sortable": true,
          "columns": [
            { "key": "week", "label": "Week", "format": "text" },
            {
              "key": "netSales",
              "label": "Net Sales",
              "format": "currency",
              "emphasize": true
            }
          ]
        }
      }
    ]
  },
  "context": { "period_start": "2025-02-01", "period_end": "2026-01-31" },
  "status": "active"
}
```

The server stamps `id`, `version`, `created_/updated_by/at` on save. Every
save snapshots the previous version to an audit history, so a bad save can be
rolled back — but treat saves as real: preview first, always.

## The four tools

| Tool             | What it does                                                                                                                                                                                                  |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `list_reports`   | Summaries of the company's saved definitions                                                                                                                                                                  |
| `get_report`     | One full definition (queries + `report` object + context)                                                                                                                                                     |
| `preview_report` | Runs a saved definition's queries — or draft `queries` you pass — against the company's live warehouse and returns the rows keyed by each query's `key` (the same rows the view endpoint feeds to each block) |
| `save_report`    | Creates a definition, or updates one when `report_id` is passed                                                                                                                                               |

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
3. **Preview the data.** `preview_report` with the draft `queries`, `controls`,
   and `report`. Fix every `convention_warnings` entry it returns. Confirm
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
   **"Saved"** once the artifact matches the saved definition. Flip the badge by
   **updating this same artifact in place** — after a successful `save_report`,
   update it to "Saved" rather than emitting a new one. Never describe the report
   only in text; never substitute a preview for a save.
6. **Stop and wait for an explicit save instruction.** Do **not** call
   `save_report` on your own — not after a preview, not because the data looks
   good, not to "finish the task". Saving is a deliberate user action. Only
   call `save_report` when the user explicitly asks, and let them choose:
   - **"save as new"** (or "create") → call `save_report` **without**
     `report_id` (creates a new definition). Check `list_reports` first; if a
     report with the same title exists, ask whether to update it instead.
   - **"update"** (or "save over the existing one") → call `save_report`
     **with** the `report_id` of the definition being edited.

   Phrase the choice as one plain question that names the report by **title**,
   e.g. _"Want me to update the **Cash Inflow Report**, or save this as a new
   report?"_ — do **not** surface the `report_id` or other internal fields.

   Always pass `user_requested_save: true` (only after that explicit ask) and a
   short `change_summary` describing what this save changed or
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
   `[<title>]({{app_base_url}}/<company>/reports/mcp/<id>)`, using the returned
   id. **Always build the link from `{{app_base_url}}`** (this skill is served
   per-environment, so that token already resolves to the right host — `app` in
   production, `app-staging` on staging, `app-local` locally); never hardcode
   `app.drivepoint.io`. If the save is rejected for the author role, hand the
   definition to a Drivepoint admin instead of retrying.

**Editing** (any request to update or change an existing report) is the same
loop starting from `get_report`: fetch the definition and **always render its
current state as a JSX artifact first** (marked **"Saved"**), so the user sees
what exists before anything changes. Then make the requested changes,
`preview_report`, and **update that same artifact in place** to the changed
state (marked **"Unsaved draft"**) — don't open a second artifact for the edit.
Only after the user has seen that updated preview, **explicitly ask whether to
update this report (save over it, using its `report_id`) or save it as a new
one** — never assume which. (A "save as new" is the one case that starts a fresh
artifact.) Never save an edit the user has not previewed and explicitly approved.
Once the save succeeds, flip that same artifact's badge back to **"Saved"** so it
never sits on a stale state.

## Report contract

`report` is `{header, blocks}`. No HTML, no scripts, no baked data — just
structured data the app maps to components, with each data block naming the
query whose rows it renders.

**header** — `{title, subtitle?, eyebrow?, generatedAt?}`. `generatedAt` is an
ISO timestamp, rendered as an "Updated <date>" line.

**blocks** — an ordered array rendered top to bottom. Each block is one of five
types (`financialStatement` renders a trended P&L, balance sheet, or cash flow
with periods as columns):

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
  `chartType` is `line | bar | area | pie | doughnut` and is the default type
  for every series; `query` is the key of the query whose rows are plotted;
  `xKey` is the field for the x-axis (or slice label for pie/doughnut); `series`
  is `[{key, label?, color?, type?, yAxis?}]` naming columns to plot (pie/doughnut use
  the first series as the value). For a **combo chart**, give series their own
  `type` (`line | bar | area`) — e.g. two `bar` series plus one `line` on shared
  axes; a series without `type` falls back to `chartType`. For a **dual-axis
  chart** (two measures on different scales, e.g. net sales in $ and order counts),
  set `yAxis: "right"` on the series that belongs on the secondary axis (default
  `"left"`) — typically paired with a `type` so it reads as bars-on-left +
  line-on-right; dual-axis applies to vertical charts only. `stacked` stacks the
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
- **Standard structure, sized to the data.** Follow the order in the report
  conventions: `kpiGroup` for headline numbers, then the chart, then the detail
  `table` from the same query, with optional `text` framing at the top and
  takeaways at the bottom. Drop a block only when the data for it is missing,
  and say which. Do not invent a new layout for each report.
- **Drivepoint house style.** Concise, plain language. **No em dashes** in any
  copy (titles, labels, body) — use commas, periods, or "to" for ranges.

## Controls (in the side panel)

A report carries a top-level `controls` array (a sibling of `header`/`blocks`)
of renderer-owned interactive controls. Drivepoint draws every one of them in
the Controls side panel, never in the report body. A report with a date axis
always gets the standard `dateRange` control (see the conventions); add other
controls when the user wants to slice or reshape the report. Every control is `{type, key, label, ...}` where `key` is a unique id.
There are two families:

- **View controls** change what the reader sees without touching data. They
  target blocks, so give each affected block a stable `id` and reference it:
  - `seriesVisibility` — show/hide a chart's series.
  - `columnSet` — switch a table between named column subsets.
  - `tabs` — show one group of blocks at a time.
  - `blockVisibility` — toggle a group of blocks on/off.
  - (a `table` can also set `sortable: true` on its own, no control needed.)
- **Global filter controls** — `select`, `multiSelect`, `dateRange`, `number`,
  `text` — carry a `bind`:
  - `bind: "clientData"` filters the rows already on the page against a
    `column`. Only use it where **every** affected block carries that column,
    else its KPIs/totals/prose go stale.
  - `bind: "requery"` re-runs the queries with the value bound into a
    `${$CONTEXT.<key>}` token. The control `key` **is** the token: you MUST also
    put `${$CONTEXT.<key>}` into the query it should scope (e.g.
    `WHERE channel = ${$CONTEXT.channel}`) and must **NOT** quote it — the value
    is inserted as a ready SQL literal (strings/dates quoted, numbers bare;
    `multiSelect` expands to a comma list for `IN (...)`; `dateRange` exposes
    `${$CONTEXT.<key>_start}` and `${$CONTEXT.<key>_end}`; `number` binds a bare
    numeric literal; `text` binds a quoted string). A query with no token is
    left unchanged. Give every requery token a default in `context`.

Per type:
- `select` / `multiSelect` — options come from `{source: "static" | "data" |
  "query"}` (`static` lists them inline; `data`/`query` derive them from rows).
- `dateRange` — a start/end picker.
- `number` — a free-form numeric input with optional `min` / `max` / `step`
  (the value is clamped to min/max). For a **threshold/cap/floor** use
  `bind: "requery"` and compare it in SQL (e.g. `WHERE margin_pct >=
  ${$CONTEXT.minMargin}`); with `bind: "clientData"` it filters to rows whose
  `column` **equals** the value (exact match, not a range).
- `text` — a free-form string input; with `clientData` it does a
  case-insensitive **contains** match on `column`.

Limits (state these honestly, don't imply otherwise):
- Controls are **global or target a whole block by `id`** — there is **no
  per-row control**. Per-table-row editable cells, per-row growth inputs, and
  per-row checkboxes **cannot be saved**; they stay in the interactive artifact
  only. The savable equivalent is a global `number`/`select`/`text` that
  re-queries or filters the whole block.
- `clientData` only reshapes rows already fetched; anything that must change
  totals/KPIs honestly should be `requery`.

```json
"controls": [
  { "type": "dateRange", "key": "period", "label": "Period", "bind": "requery" },
  { "type": "select", "key": "channel", "label": "Channel", "bind": "requery",
    "options": { "source": "static", "values": ["DTC", "Amazon", "Retail"] } },
  { "type": "number", "key": "minMargin", "label": "Min margin %", "bind": "requery",
    "min": 0, "max": 100, "step": 1 }
]
```

## Governance (do not work around)

- Queries run only in the company's own warehouse project and only against
  the allowed datasets; `save_report` dry-runs every query and rejects
  anything that is not a same-project SELECT. If a dataset you need is blocked,
  say so.
- Every query key a block references must exist in `queries`; a definition that
  points a block at an unknown key is rejected on save.
- Saves are versioned and audited (who, when, what changed). A save that
  changes nothing returns `action: "unchanged"` and creates no version. Use
  `status: "archived"` to retire a report, only when the user agrees; do not
  overwrite a report with an empty `report` to "delete" it.
- An artifact-linked save (`artifact_id`) is a static copy. Make one only when
  the user explicitly asks to keep that exact artifact as a static report, and
  pass `allow_static_snapshot: true`.
- A save is always user-initiated (see Golden rules). Do not auto-save, save
  "to be helpful", or re-save on your own after an edit.
- One tenant per definition. For the same report across tenants, save the
  same definition per company.
