# Saved Reports Guide

How to build, preview, save, and edit a **saved report** in Drivepoint — a
data-backed HTML report that lives in the Drivepoint app itself, at
`https://app.drivepoint.io/<company>/reports`, and re-renders with live data
every time someone opens it.

This is different from an in-chat artifact (see `report-creation-guide.md`):
an artifact answers today's question in this conversation; a saved report is
a durable page in the customer's Drivepoint app. Saving one requires an admin
or superAdmin Drivepoint role. When a user asks to "add this report to
Drivepoint," "save this so the team can see it," "put this on my reports
page," or "edit the retention scorecard," this guide applies.

---

## What a saved report is

A versioned, tenant-scoped **report definition**: named SELECT-only SQL
queries plus an HTML template plus metadata. It is data, not code — saving
one requires no deploy, and it appears in the app's Reports list immediately.

```json
{
  "title": "Weekly DTC Sales Pulse",
  "description": "Net sales, orders, and AOV by week and channel.",
  "report_type": "sales-pulse",
  "queries": [{"key": "rows", "query": "SELECT ... FROM {ENV}_dwh_mart. ..."}],
  "template": "<style>...</style><div class=\"rp-root\">... ${$.rows.length} ...</div>",
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
| `get_report` | One full definition (queries + template + context) |
| `preview_report` | Runs a saved definition's queries — or draft `queries` you pass — against the company's live warehouse and returns the rows keyed exactly as the template will see them |
| `save_report` | Creates a definition, or updates one when `report_id` is passed |

## The authoring loop

1. **Discover the data.** Use `list_datasets` / `list_tables` / `get_schema`
   and the `data-dictionary` / `sample-queries` skills. Never guess column
   names.
2. **Draft the queries.** SELECT-only. Reference datasets with the `{ENV}_`
   prefix token (e.g. `{ENV}_dwh_mart.orders`) — it is substituted per
   environment at render time. Parameterize with `${$CONTEXT.<param>}` tokens
   and put defaults for every param in `context`. Keep result sets small and
   aggregated: the template receives raw rows.
3. **Preview.** `preview_report` with the draft `queries`. Confirm every key
   returns rows, the numbers are sane (spot-check against a known figure),
   and nothing is truncated. Fix and re-preview until clean.
4. **Build the template.** See the template contract below. Render it
   yourself against the preview rows to check the output reads correctly.
5. **Save.** `save_report`. Report back the title and the app path
   `/:company/reports/html/<id>` (the report also appears in the Reports
   list). If save is rejected for the author role, hand the definition to a
   Drivepoint admin instead of retrying.

**Editing** is the same loop starting from `get_report`: fetch, change the
queries and/or template, `preview_report`, then `save_report` with the
`report_id`. Never save an edit you have not previewed.

## Template contract

The template is rendered as a **JavaScript template literal** in the app.
`${...}` expressions can read:

- `$[key]` — each query's rows, under the query's `key` (a single query with
  key `"rows"` reads as `$.rows`). Rows are plain objects keyed by the SELECT
  column names.
- `$.company` — `.name`, `.id` of the tenant.
- `$.context` — the merged context params.
- `$.generatedAt` — ISO timestamp of the render.

Rules that keep templates robust:

- **Inline everything.** One self-contained fragment: a `<style>` block plus
  markup. No external scripts; no `<html>`/`<head>`/`<body>` wrapper — the
  fragment is injected into the app page.
- **Namespace CSS classes** with a report-specific prefix (`.sc-`, `.rp-`)
  so styles cannot leak into the app.
- **Compute inside one IIFE.** Do the grouping/derivation in a single
  `${(function () { ... return html; })()}` block that builds the HTML with
  string concatenation. Guard the empty case first and return a friendly
  "no data yet" panel.
- **Format defensively.** `Number(...)` every value before math;
  `toLocaleString` for counts; explicit rounding for percents.
- **Drivepoint brand**: Manrope for headings, Roboto for body, the dp-design
  light palette (ink `#191815`, muted `#7a7774`, accent `#76a4ea`, borders
  `#ecebe9`). No em dashes in copy.

A minimal template that follows every rule above (namespaced style block,
one IIFE, empty-state guard, defensive formatting):

```html
<style>
.sp-root { font-family:"Roboto",sans-serif; color:#191815; padding:24px 0; }
.sp-title { font-family:"Manrope",sans-serif; font-weight:700; font-size:26px; }
.sp-tbl { width:100%; border-collapse:collapse; font-size:13.5px; }
.sp-tbl th, .sp-tbl td { padding:9px 14px; border-bottom:1px solid #ecebe9; text-align:right; }
.sp-tbl th:first-child, .sp-tbl td:first-child { text-align:left; }
</style>
<div class="sp-root">
  <h1 class="sp-title">Sales Pulse</h1>
  ${(function () {
    var rows = Array.isArray($.rows) ? $.rows : [];
    if (!rows.length) { return "<p>No sales data yet for this period.</p>"; }
    var fmt = function (v) { return Math.round(Number(v)).toLocaleString("en-US"); };
    var html = "<table class='sp-tbl'><thead><tr><th>Month</th><th>Channel</th><th>Orders</th><th>Net sales</th></tr></thead><tbody>";
    rows.forEach(function (r) {
      html += "<tr><td>" + r.month + "</td><td>" + r.channel + "</td><td>" + fmt(r.orders) + "</td><td>" + fmt(r.net_sales) + "</td></tr>";
    });
    return html + "</tbody></table>";
  })()}
</div>
```

Scale the same shape up for richer reports: KPI card rows, per-section
tables, comparison layouts. The section design rules in
`report-creation-guide.md` (source-mart routing, comparisons, commentary
discipline, pre-publish cross-checks) apply to saved reports too — the
output medium changes, the analytical discipline does not. To match an
existing house style, `list_reports` + `get_report` any definition already
saved for the tenant and mirror its structure.

## Rendering a saved report in-chat

To show a saved report to the user in the conversation: `get_report` +
`preview_report`, then interpolate the rows into the template exactly as the
app would (same `$` globals). The result should match what the user sees in
the app pixel-for-pixel modulo fonts.

## Governance (do not work around)

- Queries run only in the company's own warehouse project and only against
  the allowed datasets; `save_report` dry-runs every query and rejects
  anything else. If a dataset you need is blocked, say so — do not smuggle
  data in through the template.
- Saves are versioned and audited (who, when, what changed). Use
  `status: "archived"` to retire a report; do not overwrite a report with an
  empty template to "delete" it.
- One tenant per definition. For the same report across tenants, save the
  same definition per company (keep `report_type` identical so instances stay
  linked).
