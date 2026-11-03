# Drivepoint for ChatGPT and Codex

Connects ChatGPT and Codex to the Drivepoint MCP server at
`https://mcp.drivepoint.ai/mcp`. The server already exposes the tools
(plans, queries, reports, skills, product mappings). This package is the
plugin manifest, OAuth declaration, and workflow skills.

Sign-in is the existing Drivepoint OAuth flow. The manifest uses dynamic
client registration (`client.mode: "dcr"`). There is no client secret in
this package.

## Connect in ChatGPT

1. Open [ChatGPT Plugins](https://chatgpt.com/plugins).
2. Select the plus button, then **Add custom MCP server**.
3. Name it Drivepoint. Server URL: `https://mcp.drivepoint.ai/mcp`.
4. Choose **OAuth**. The server publishes discovery at
   `https://mcp.drivepoint.ai/.well-known/oauth-authorization-server`
   and protected-resource metadata at
   `https://mcp.drivepoint.ai/.well-known/oauth-protected-resource`.
5. Review the risk warning, continue, and select **Create as a plugin**.
6. Install it from your personal plugins.
7. In a Work chat, type `@` and select Drivepoint. Ask which companies
   you can access. The plugin should call `get_drivepoint_user`.

Do not choose **No authentication**. The server returns 401 until the
user signs in through Drivepoint.

## Install from this repo

ChatGPT desktop and Codex read `.agents/plugins/marketplace.json` at the
repo root. Restart the desktop app, open the Plugins directory, and
install **Drivepoint** from the Drivepoint marketplace.

## Local server

The committed server URL is production. To point a local plugin at a
dev server, change `mcp.json` `url` to that server's `/mcp` endpoint
(the mcp-server app listens on port 8081 by default) and match
`authorizationUrl`, `tokenUrl`, `registrationUrl`, `resource`, and the
OIDC URLs to the same origin.

```bash
cd apps/mcp-server
npm install
npm run dev
```

Run that from the `webapp-server` checkout. Local sign-in still uses the
`auth.sign_in_url` in `config/config.local.json`.
