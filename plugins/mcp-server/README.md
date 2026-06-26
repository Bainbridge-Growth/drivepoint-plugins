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

## Templates

`templates/customer-project-instructions.template.md` is the canonical skeleton for the
per-customer **project/system instruction** an FDE pastes into a fresh Claude project before a
customer call (use the MCP for one brand, load guidance, apply that brand's query/segment
conventions, answer as a branded artifact). Fill every `{{PLACEHOLDER}}` from live MCP discovery
for the customer — do not paste it as-is. The `drivepoint-customer` skill (in the
`drivepoint-customers` repo) automates the discovery + render.

## Skills

`skills/` is reserved for MCP-specific skills (for example query patterns or
data-dictionary helpers). None are defined yet.
