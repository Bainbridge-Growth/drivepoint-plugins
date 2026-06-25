---
name: marketing-efficiency-analysis
description: Analyze marketing spend efficiency — CAC, ROAS, blended vs. channel-level spend, and return on marketing investment. Use when a user asks about marketing performance, "what's our CAC?", "is our marketing efficient?", "ROAS by channel", "marketing spend analysis", "where should we cut/increase marketing?", or "how efficient is our acquisition spend?" Also triggers on "CAC", "ROAS", "marketing ROI", "ad spend efficiency", "paid marketing performance", "direct ad spend", or "are we spending too much on ads?".
---

# Marketing Efficiency Analysis

**Purpose**: Evaluate marketing spend effectiveness — CAC by channel, ROAS, blended efficiency, and trends — to identify where acquisition spend is working and where it isn't.
**Prerequisite**: The `smartmodel-protocol` skill must be loaded.

---

## When This Skill Activates

- User asks about marketing performance or efficiency
- User wants to know CAC, ROAS, or marketing ROI
- User asks where to increase or cut marketing spend
- User wants to compare marketing performance across channels
- User is planning next period's marketing budget

---

## Phase 1 — Orient

**Step 1.1 — Use model context from the protocol**
Settings, index, and date spine are already loaded by the protocol's auto-orient. From the model context, note `companyName`, `currency`, identify the opex sheet (marketing), channel revenue sheets (DTC, AMZN), and any cohort/customer acquisition data. Determine the analysis period — use at least 3 months of Actuals for trend analysis; single-month CAC is noisy.

**Step 1.2 — Read channel structure**
Call `read_smartmodel_registries` on the opex/marketing sheet → identify how marketing spend is broken down (by channel: paid social, paid search, influencer, email, Amazon advertising, etc.).

**Step 1.3 — Detect first-order AOV inputs and any blended AOV row the model already exposes**
Call `read_smartmodel_registries` on each channel revenue sheet → identify two things:

1. **Per-segment first-order AOV Key Drivers** — one per first-order customer segment. The most common split is **OTP first-time** and **SUB first-time** (one-time-purchase vs. subscription acquisition), but segments may be structured differently per customer — B2C / B2B, product-line tiers, wholesale tiers, or channel-specific splits. Capture every distinct first-order segment that has its own AOV Key Driver.
2. **Any aggregate / blended first-order AOV row the model already exposes** — typically a Key Result on the channel or consolidation sheet that consolidates the per-segment AOVs (e.g., `blended_first_order_aov`, `aov_first_time_blended`, or similar). Note the row's location and identifier.

The skill **never synthesizes a blended AOV from per-segment values via agent-side weighted average**. Whatever the model exposes is what the skill reports. Step 1.3's discovery determines which path Phase 3 takes.

State the discovered AOV rows before proceeding. Examples:
- *"This model has two first-order AOV Key Drivers on DTC (OTP first-time, SUB first-time) and a blended first-order AOV Key Result on the consolidation sheet. CAC:AOV will use the model's blended row for the headline."*
- *"This model has per-segment first-order AOVs (OTP-FT, SUB-FT) on DTC but no model-level blended row. CAC:AOV will show each segment side by side and surface that no aggregate row is available."*
- *"This model has one first-order AOV per channel (DTC, Amazon). CAC:AOV will use that AOV directly per channel — no blending needed."*

**Step 1.4 — Detect CAC rows the model exposes**
Call `read_smartmodel_registries` on the marketing/opex sheet and each channel revenue sheet → identify any CAC Key Result rows the model already computes:

1. **Per-channel CAC Key Result rows** — typically one per acquisition channel (DTC, Amazon, etc.), located on the channel sheet or in a channel section of the opex/marketing sheet. Common patterns: `cac_dtc`, `cac_amzn`, `cac_<channel>`.
2. **Blended / aggregate CAC Key Result row** — typically on the consolidation or marketing sheet. Common patterns: `cac_blended`, `blended_cac`, `cac_total`.

The skill **never synthesizes a CAC metric from `marketing_spend ÷ new_customers` when the model exposes the corresponding CAC row**. Pull the CAC value the model has computed; the formula is the modeler's responsibility, not the agent's. The modeler's row may exclude or include spend categories the agent doesn't know about — recomputing risks drift between the agent's report and the model's own numbers. If the model exposes per-channel CAC but no blended CAC row, a blended CAC fallback is allowed only if it is clearly labeled as a fallback.

State the discovered CAC rows before proceeding. If no CAC rows exist, the skill falls back to component-level computation (documented in Phase 3) and surfaces the gap to the user explicitly.

---

## Phase 2 — Gather Data

**If a prior skill ran this session** (e.g., `/margin-analysis`, `/variance-analysis`), reuse settings, index, date spine, and any data already gathered. Do not re-read sheets that were already read.

Call `read_smartmodel_data_section` on marketing and channel sheets:

| Metric | Sheet | Identifier pattern |
|--------|-------|-------------------|
| Marketing spend by channel | Opex sheet | `marketing`, `paid_social`, `paid_search`, `influencer`, `amazon_ads` |
| New customers acquired | Channel sheets, per channel that acquires customers | `new_customers`, `new_orders`, `acquisitions` |
| **Per-channel CAC (only if the model exposes it)** | Channel or marketing/opex sheet, Key Result rows from Step 1.4 | Whatever identifier the model uses (e.g., `cac_dtc`, `cac_amzn`) |
| **Blended / aggregate CAC (only if the model exposes it)** | Marketing/opex or consolidation sheet, Key Result row from Step 1.4 | Whatever identifier (e.g., `cac_blended`, `blended_cac`) |
| **Per-segment first-order AOV** | Channel sheets, every segment identified in Step 1.3 | Use the identifiers from the channel's measure registry — common patterns: `aov_first_time_*`, `aov_*_ft` |
| **Blended / aggregate first-order AOV (only if the model exposes it)** | Channel or consolidation sheet, Key Result row identified in Step 1.3 | Whatever identifier the model uses (e.g., `blended_first_order_aov`) |
| First-order order count per segment (display context only — never used to synthesize a blend) | Channel sheets, every segment from Step 1.3 | `orders_first_time`, `new_orders_*` |
| Revenue by channel | DTC, AMZN sheets | `revenue`, `net_revenue` |
| Ad-attributed revenue (Amazon) | AMZN sheet | `ad_revenue`, `attributed_revenue` |
| Total orders | Channel sheets | `orders`, `total_orders` |

If R- sheets are populated with advertising platform data (Meta, Google, Amazon), call `read_r_sheet` for more granular campaign-level data.

---

## Phase 3 — Compute

### CAC (Customer Acquisition Cost)

**Always pull CAC from the model — never compute a CAC metric agent-side from `marketing_spend ÷ new_customers` when the model exposes the corresponding CAC row.** Models typically expose CAC as Key Result rows on channel sheets (per-channel CAC) and/or the marketing/opex or consolidation sheet (blended CAC). The modeler's formula is the source of truth.

Use the discovery from Step 1.4:

| Model exposes... | Action |
|------------------|--------|
| Blended CAC + per-channel CAC Key Result rows | Read all directly. Use blended for the headline, per-channel for the channel efficiency table. |
| Per-channel CAC only (no blended row) | Read each channel's CAC. State: *"This model exposes per-channel CAC but no aggregate blended-CAC row. Showing per-channel CAC; the blended figure is computed as a fallback from total marketing spend ÷ total new customers and flagged."* |
| No CAC rows at all | Surface the gap and fall back to component-level computation. State: *"This model doesn't expose a CAC Key Result row. Computing CAC from marketing spend ÷ new customers as a fallback — recommend adding a CAC row to the model for cleaner reporting."* |

**Hard rule**: when the model exposes a CAC row for the metric you need, read it. Do not recompute and report a different number for that same metric — the modeler's row may exclude or include spend categories the agent doesn't know about, and a recomputed value drifts from the model. If only the blended CAC row is missing, compute only the blended fallback; keep per-channel CAC tied to the model's rows.

Reference formula (documents what the model computes; used by the agent only as a flagged fallback when the corresponding CAC row is missing):

```
(reference, fallback only) CAC = Marketing Spend (period) / New Customers Acquired (period)
```

When falling back, compute and label only the missing metric:
- **Blended CAC (fallback)**: All marketing spend / all new customers, only when no blended CAC row exists
- **Channel-level CAC (fallback)**: Channel marketing spend / new customers from that channel, only for channels without a model CAC row

### First-order AOV (the right denominator for CAC)

CAC pays for the first order, so the comparison denominator is the **first-order AOV**, not the lifetime average. **Always pull the AOV from the model — never synthesize a blended AOV from per-segment values via weighted average.** Per-segment AOVs are Key Drivers (the user's inputs); any aggregated row is a Key Result the modeler authored deliberately. Either way, the agent reports what the model exposes.

Use the discovery from Step 1.3 to pick the headline AOV:

| Model exposes... | Headline AOV |
|------------------|--------------|
| A blended / aggregate first-order AOV Key Result row | Read that row's value directly. Headline ratio = CAC : model's blended AOV. Per-segment AOVs are still shown in Phase 4 as supporting context. |
| Per-segment first-order AOV Key Drivers (≥2 segments) but **no** blended row | Show CAC:AOV against each segment side by side. **Do not invent a blend.** Surface the gap explicitly: *"This model has per-segment first-order AOVs ([list]) but no aggregated blended-AOV Key Result. Showing CAC:AOV per segment — the headline ratio depends on which segment anchors it. To get a single headline number, ask the modeler to add a blended first-order AOV Key Result, or run `/cohort-analysis` for the LTV-weighted view."* |
| One first-order AOV input (single segment per channel) | Use that AOV directly. State: *"Only one first-order segment, so CAC:AOV uses [segment] first-order AOV directly."* |

**Hard rule**: never compute a weighted-average AOV agent-side. If the model doesn't expose a blended row, the right answer is the per-segment picture plus a surfaced gap — not a synthesized number. Sub first-order AOV is typically lower than OTP (subscription billing → lower per-order, higher LTV through retention), so a single-segment AOV biases the headline ratio in a direction the agent shouldn't paper over.

**Benchmarks for CPG DTC** (CAC compared against the model's first-order AOV — blended row if present, segment row if not):
| CAC Range | Assessment |
|-----------|-----------|
| < 0.5× first-order AOV | Strong — acquiring profitably |
| 0.5–1× first-order AOV | Healthy |
| 1–2× first-order AOV | Watch — depends on LTV |
| > 2× first-order AOV | At risk — acquisition is loss-making at first order |

These benchmarks only consider first-order economics. For a definitive answer to *"is CAC too high?"*, layer in retention and LTV via `/cohort-analysis` — always offer this as the natural follow-up.

### ROAS (Return on Ad Spend)

```
ROAS = Revenue Attributed to Paid Marketing / Paid Marketing Spend
```

Note: ROAS is most meaningful for DTC and Amazon where spend is directly tied to revenue. For wholesale or brand marketing, ROAS is less directly measurable.

**ROAS benchmarks (DTC):**
| Channel | Minimum viable | Healthy | Strong |
|---------|---------------|---------|--------|
| Meta / Instagram | 2× | 3–4× | >5× |
| Google / Search | 3× | 4–6× | >7× |
| Amazon PPC | 2× | 3–4× | >5× |
| TikTok | 1.5× | 2.5–3× | >4× |

### Marketing as % of revenue

```
Marketing % = Total Marketing Spend / Net Revenue
```

CPG benchmarks: DTC-heavy brands typically run 20–35% marketing as % of revenue. Blended (with wholesale) is typically 15–25%.

### MER (Marketing Efficiency Ratio / Blended ROAS)

```
MER = Total Revenue / Total Marketing Spend
```

MER is more stable than channel-level ROAS and accounts for view-through and halo effects that channel-level attribution misses.

### Trend analysis

Compare current period vs. prior 2–3 months. Flag if:
- CAC is increasing >15% period-over-period
- ROAS is declining >20% period-over-period
- Marketing % of revenue is expanding without corresponding revenue growth

---

## Phase 4 — Output

### Default output

1. **Headline** — format depends on what AOV rows the model exposes (Step 1.3):
   - **Model has a blended first-order AOV Key Result row**: *"Blended CAC is $[X] ([Y]× the model's blended first-order AOV of $[Z]). Marketing represents [W]% of revenue. [Best channel] is most efficient at [metric]; [worst channel] is underperforming at [metric]."*
   - **Model has per-segment AOVs but no blended row**: *"Blended CAC is $[X]. The model has [N] first-order segments without an aggregated blended-AOV row — CAC against [segment 1] AOV is [Y]×, against [segment 2] AOV is [Y']×. Marketing represents [W]% of revenue."*
   - **Single first-order segment**: *"CAC is $[X] ([Y]× first-order AOV of $[Z]). Marketing represents [W]% of revenue."*

2. **CAC vs. first-order AOV table** — one row per segment from Step 1.3. The "Blended (model)" row appears **only** if the model exposes a blended Key Result; pull its value directly from that row.

```
| First-order segment      | First-order AOV | First-order orders | CAC : AOV ratio |
|--------------------------|-----------------|--------------------|-----------------|
| OTP first-time           | $...            | ...                | ...×            |
| SUB first-time           | $...            | ...                | ...×            |
| (additional segments if present) | ...     | ...                | ...             |
| **Blended (model)**      | **$...**        | (n/a)              | **...×**        |
```

If only one first-order segment exists, show a single row. If the model has no blended row, omit the "Blended (model)" row entirely — do not synthesize one. If segments are not OTP/SUB (e.g., B2C/B2B), use the customer's actual segment names.

3. **Channel efficiency table** — one row per **acquisition channel** (DTC, Amazon, Wholesale, etc.). Pull CAC, AOV, and ROAS directly from the model — never synthesize any of them agent-side.

```
| Channel  | Spend | New Customers | CAC (model) | First-order AOV (model) | CAC : AOV ratio | ROAS / MER | vs. Prior Period |
|----------|-------|---------------|-------------|-------------------------|-----------------|------------|------------------|
| DTC      |       |               |             |                         |                 |            |                  |
| Amazon   |       |               |             |                         |                 |            |                  |
| (other)  |       |               |             |                         |                 |            |                  |
| **Blended** |    |               |             |                         |                 |            |                  |
```

**Per-channel rule**: never mix one channel's AOV with another channel's CAC, and never synthesize a cross-channel blended AOV agent-side. For each row, use that channel's own AOV row from the model — the channel's blended Key Result row if exposed, segment-level rows shown underneath if not. The "Blended" row is filled **only** if the model exposes both a model-level blended AOV Key Result and a model-level blended CAC Key Result; if either is missing, omit the Blended row and surface the gap in the headline.

For marketing-channel-level detail (Paid Social, Paid Search, Influencer, Amazon PPC), use the Channel efficiency ranking (section 5) — those don't have a clean per-channel AOV pairing because acquired customers may come through any acquisition channel.

4. **Trend chart** (narrative or visual): CAC and ROAS over trailing 3–6 months
5. **Channel efficiency ranking** — marketing-channel level (Paid Social, Paid Search, Influencer, Amazon PPC, etc.). Best to worst on ROAS, with CAC shown for context. Do not pair these rows with per-channel AOV — the granularity doesn't match.
6. **Budget allocation analysis**: Is spend concentrated in the highest-ROAS channels?
7. **Recommendations**: Where to increase, where to cut, what to test
8. **LTV follow-up steer**: For sub-heavy or repeat-driven businesses, the first-order CAC:AOV view understates true acquisition efficiency because sub LTV depends on retention curves this skill does not model. Always close with: *"To answer 'is CAC too high?' definitively, run `/cohort-analysis` to layer LTV by segment."*

### Excel output (if requested)

Call `create_sheet` with blue tab. Call `write_range` for the efficiency table. Call `format_range` for number formatting. Call `create_chart` (Line chart) for CAC and ROAS trends.

---

## Guardrails

- Never write to Actual columns
- **Always pull AOV (and any other Key Driver / Key Result metric) from the model — never synthesize a value via agent-side weighted average or aggregation.** The model is the source of truth: per-segment values are Key Drivers (user inputs), aggregated values are Key Results (modeler-authored formulas). When reporting current-state metrics, the agent reads what the model exposes and surfaces gaps explicitly when an aggregate row is missing. (Scenario calculations that produce *new* values to be written back — e.g., `/price-change-analysis` computing a new AOV under a hypothetical price change — are different and acceptable.)
- CAC calculation requires new customer counts — if this data isn't in the model, note the limitation and compute blended spend-per-order as a proxy (not true CAC but directionally useful)
- Do not mix platform-reported ROAS (which uses last-click attribution) with model-level revenue without flagging the attribution methodology difference

---

## Common Mistakes to Avoid

1. Don't use platform-reported ROAS as gospel — last-click attribution overcredits some channels (especially search) and undercredits others (social, influencer)
2. Don't analyze a single month of CAC — it's too noisy. Use trailing 3-month average minimum.
3. Don't ignore the spend-revenue timing mismatch — marketing spend in month N often drives revenue in month N+1 for new customer acquisition
4. Don't compare CAC without context of AOV and LTV — a $100 CAC is great if AOV is $120 and LTV is $400; it's terrible if AOV is $40
5. Don't optimize for ROAS alone — maximizing ROAS often means underinvesting in growth; optimize for profitable scale, not just efficiency
6. **Don't synthesize a blended AOV from per-segment values via weighted average.** Pull AOV from the model — Key Drivers are the user's inputs and Key Results are the modeler's deliberate aggregations. If the model has multiple per-segment first-order AOVs but no blended Key Result row, show CAC:AOV against each segment side by side and surface the gap (or steer to `/cohort-analysis`). Inventing a blend the modeler didn't author risks misweighting (orders vs. customers, period definitions) and lands a number the user can't tie back to the model.
7. **Don't anchor the headline ratio on a single segment when the model has multiple first-order segments without a blended row.** Sub first-order AOV is typically lower than OTP — OTP-only AOV inflates the apparent CAC efficiency. The right move is to show every per-segment ratio and surface the missing aggregate, not to pick one and call it the headline.
8. **Don't recompute a CAC metric when the model exposes the corresponding CAC Key Result row.** The modeler's formula may exclude or include spend categories the agent doesn't know about (e.g., capitalized influencer fees, non-marketing-coded ad spend, agency retainers). Recomputing from raw `marketing_spend / new_customers` produces a number that drifts from the model and creates inconsistency between the agent's report and the model's own dashboard. Pull CAC from the model; recompute only the missing blended or channel metric as a clearly labeled fallback.
9. **Don't mix one channel's AOV with another channel's CAC.** DTC AOV ≠ Amazon AOV ≠ Wholesale AOV. Pair each channel's CAC with that channel's own AOV row from the model. The "Blended" row in the channel efficiency table is filled only when the model exposes a model-level blended AOV row and a model-level blended CAC row — never synthesize either agent-side.

---

## Integration with Other Skills

- **`/cohort-analysis`**: LTV is the other half of the CAC:LTV equation
- **`/margin-analysis`**: Contribution margin context is needed for CAC payback calculations
- **`/variance-analysis`**: Check if efficiency metrics are a variance from plan
- **`/build-report`**: Package marketing efficiency for a board or investor update
