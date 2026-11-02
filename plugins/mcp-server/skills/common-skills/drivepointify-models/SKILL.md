# Drivepointify Models — check the uploaded plan

The conversion rules live in the SmartModel plugin skill `drivepointify-models`
(`plugins/smartmodel/skills/drivepointify-models`: scripts, date spine, markers,
and gates). This skill is only the Drivepoint connector check after upload.

Read this when the chat has the Drivepoint connector and the user has uploaded
a workbook as a plan, or asks to drivepointify a file from a conversation that
cannot run that plugin skill.

Say "model", not "plan", to the user.

Without code execution and the SmartModel plugin, do not write the workbook.
Send the user to a session that has the plugin skill, then return here after
they upload the file (Drivepoint app → Plans → Upload Plan). Any `.xlsx` connects.

## After upload

1. `list_company_plans` — find the new model.
2. `get_valid_plan_tabs` — every schedule tab must be listed. A missing tab
   means Drivepoint did not accept that sheet as a time series. Fix it in the
   plugin skill, not by restating the sheet rules here.
3. `list_plan_key_drivers_and_results` — every marked row must come back with
   its id and name.
4. To fix a marker on the live model: `search_plan_row` finds the row, then
   `mark_key_driver_or_result` (with confirm) sets it.

`get_drivepoint_user` is the tenant id when Settings need it. Do not invent one.

## What to report

- Which model `list_company_plans` matched.
- Which tabs `get_valid_plan_tabs` returned, and any schedule tab that was missing.
- Which marked rows came back, and any marker you changed.
