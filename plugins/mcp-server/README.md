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

> **Delivery.** This is a marketplace **plugin** skill (Claude Code / Desktop).
> How it loads into other Drivepoint surfaces depends on each surface's skill
> configuration.
