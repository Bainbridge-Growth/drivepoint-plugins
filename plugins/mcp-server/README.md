# Drivepoint MCP Server — Claude Plugin

**Published by**: Drivepoint (drivepoint.io)

Connects a Claude session to a Drivepoint brand's analytics data through the
Drivepoint MCP server — read-only access to the brand's BigQuery-backed data
marts, plus Drivepoint's analysis skills, plans, and schema-discovery tools.

## What it provides

Once connected, the Drivepoint MCP server exposes tools such as:

- `list_skills` / `get_skill` — Drivepoint's analysis methodology and data guidance
- `list_datasets` / `list_tables` / `get_schema` — discover the brand's data marts
- `run_query` — read-only GoogleSQL against the brand's marts
- `get_plan` / `list_company_plans` — Drivepoint financial plans
- `get_drivepoint_user` — the connected user's context

## Configuration — required before use

`.mcp.json` ships with a **placeholder** endpoint:

```json
{
  "mcpServers": {
    "drivepoint": {
      "type": "http",
      "url": "https://YOUR-DRIVEPOINT-MCP-ENDPOINT"
    }
  }
}
```

Replace `https://YOUR-DRIVEPOINT-MCP-ENDPOINT` with the real Drivepoint MCP
server URL (production). The server uses Streamable HTTP transport;
authentication is handled by the MCP host's connector flow.

## Skills

MCP-specific skills live in `skills/<name>/SKILL.md`:

- **`cpg-finance-context`** — a CPG finance vocabulary-and-concepts bridge.
  Maps how a CPG operator talks ("net sales", "top line", "margin", "CAC",
  "payback") to the SmartModel's actual lines and `metric_id`s, so the
  assistant never reports a metric as missing when the model carries it under
  another name. Includes a "never strand the user" behavioral protocol, a
  ~70-row alias map, and a CPG finance primer (gross-to-net, contribution-margin
  tiers, trade spend/deductions, channel economics, working capital).
- **`system-prompt`** — project instructions for the analytics assistant: hard
  rules, aggregation rules, ecommerce and SmartModel footguns, cost limits.
- **`data-dictionary`** — the mart contract: tables, grain, materialization,
  metric taxonomy, canonical statement rollups, per-session footguns.
- **`sample-queries`** — 12 GoogleSQL templates for the most common questions.
- **`analysis-skills-guide`** — how to frame, decompose, and sanity-check an
  analytical question before and while writing SQL.
- **`report-creation-guide`** — anatomy and source-mart routing for
  multi-section reports.
- **`report-catalog`** — stock report bundles and their tenant-prefixed URLs.
- **`artifact-style-guide`** — visual rules for React artifacts (brand lockup,
  tokens, number formatting, chart selection).
- **`example-artifacts`** — three working artifact templates to pattern-match.
- **`scenario-planning`** — the Key Driver what-if loop via
  `preview_plan_scenario`.
- **`import-data`** — running an import definition into a plan's workbook.
- **`product-mapping`** — cross-channel product reconciliation and how to
  record the decisions.
- **`starter-prompt`** — the paste-in first turn for a new conversation.

> **Delivery.** These are marketplace **plugin** skills (Claude Code / Desktop).
> How they load into other Drivepoint surfaces depends on each surface's skill
> configuration.
