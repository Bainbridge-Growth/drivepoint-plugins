---
name: setup
description: Connect a Drivepoint account and choose which company later questions should use.
---

Use this skill when the user installs Drivepoint, asks to connect or switch accounts, or has not yet chosen a company.

The user's own instructions take priority over this skill.

1. The Drivepoint MCP server requires the user to sign in. If a tool returns an authentication error, ask the user to finish the Drivepoint sign-in and then continue. Do not invent a session or paste a token.
2. Call `get_drivepoint_user` with no company selected. It returns the signed-in user and the companies they can access.
3. If there is one company, tell the user you will use that company's `id` for later calls, and show its `name`.
4. If there are several companies, list `name` and `id` and ask which company to use. Do not guess.
5. If there are no companies, say this account cannot access a Drivepoint company and stop.
6. Remember the chosen `id`. Pass that exact value as `company_id` on later tools. Never pass the company `name` or a `bbcust-*` project id as `company_id`.

Do not call tools that change plans, mappings, imports, routines, or access during setup.
