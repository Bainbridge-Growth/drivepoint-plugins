---
name: answer-finance-question
description: Answer a question about a Drivepoint brand's plans, actuals, ecommerce, or saved reports using the connected account.
---

Use this skill when the user asks about financial performance, a plan, actuals versus forecast, ecommerce sales, a metric, or a saved Drivepoint report.

The user's own instructions take priority over this skill. Do not invent companies, metric ids, plan ids, channels, or numbers.

1. If the company is not already confirmed in this conversation, follow the setup skill: call `get_drivepoint_user` and use a company `id` the user can access.
2. Call `list_skills`, then `get_skill` for every guide that applies before writing a query, computing a metric, or building a report. `list_skills` does not load the rules. Only `get_skill` does. Apply those rules. They override general SQL habits.
3. Use the tool the loaded skill names. Common read tools on this server are `list_company_plans`, `get_plan`, `list_datasets`, `list_tables`, `get_schema`, `run_query`, `list_reports`, and `get_report`.
4. State the company, the date range, and the plan when the answer comes from plan data. If a tool returns no rows, say so.
5. Do not call a tool that writes — including `save_plan_scenario`, `save_report`, `import_data`, `save_product_mappings`, `publish_product_mappings`, `add_plan_row`, or `disconnect_data_source` — unless the user explicitly asked to make that change.
6. If the user names a company that `get_drivepoint_user` did not return, say it is not available on this account and do not query it.
