# SmartModel Protocol — Structured Schema

Canonical machine-readable protocol definitions. Human-readable prose lives in
[`../skills/smartmodel-protocol/SKILL.md`](../skills/smartmodel-protocol/SKILL.md).

| File | Purpose |
|------|---------|
| `v6.yaml` | Current v6.0 spec, consumed by validators and CI |

## Who reads this

- **`drivepoint-smartmodel-service`** — `validate_v6_model.py`, `post_validate.py`,
  converter scripts. Loads `v6.yaml` to assert structural conformance on
  generated/uploaded workbooks.
- **`drivepoint-smartmodel-templates`** — CI tests assert every template +
  composite model conforms to `v6.yaml`.
- **AI agents** — loaded alongside `SKILL.md` as part of the plugin skill
  context. Agents use the prose for orientation and the YAML as ground truth
  when asked "does this model conform?"

## Conformance levels

Each rule carries a `level`:

| Level | Meaning |
|-------|---------|
| `MUST` | Non-negotiable. A workbook failing a MUST check is not a v6 SmartModel. |
| `SHOULD` | Strongly recommended. Failing indicates drift; validators SHOULD warn. |
| `MAY` | Permitted variation; validators MUST NOT flag. |
| `CONDITIONAL` | Required only when a parent feature is enabled (e.g., FY View cols). |

## Versioning

- `v6.yaml` is the current spec. Breaking changes bump the major (→ `v7.yaml`).
- Minor clarifications/additions edit `v6.yaml` in place.
- Retired versions stay in this directory as `v5.yaml`, `v4.yaml`, etc. for
  upgrader consumption.

## Updating the spec

When modifying `v6.yaml`:

1. Update the prose in `../skills/smartmodel-protocol/SKILL.md` to match.
2. Re-run `drivepoint-smartmodel-templates` CI to confirm all 9 templates +
   the composite still pass.
3. Update `drivepoint-smartmodel-service/smartmodel_utils/validate_v6_model.py`
   if new check types were introduced.

Drift between these three surfaces is the #1 historical cause of bugs — keep
them locked in step.
