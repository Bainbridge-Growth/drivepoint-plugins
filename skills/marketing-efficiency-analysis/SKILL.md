---
name: marketing-efficiency-analysis
description: Analyze marketing spend efficiency — CAC, ROAS, blended vs. channel-level spend, and return on marketing investment. Use when a user asks about marketing performance, "what's our CAC?", "is our marketing efficient?", "ROAS by channel", "marketing spend analysis", "where should we cut/increase marketing?", or "how efficient is our acquisition spend?" Also triggers on "CAC", "ROAS", "marketing ROI", "ad spend efficiency", or "paid marketing performance".
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

---

## Phase 2 — Gather Data

**If a prior skill ran this session** (e.g., `/margin-analysis`, `/variance-analysis`), reuse settings, index, date spine, and any data already gathered. Do not re-read sheets that were already read.

Call `read_smartmodel_data_section` on marketing and channel sheets:

| Metric | Sheet | Identifier pattern |
|--------|-------|-------------------|
| Marketing spend by channel | Opex sheet | `marketing`, `paid_social`, `paid_search`, `influencer`, `amazon_ads` |
| New customers acquired | DTC sheet | `new_customers`, `new_orders`, `acquisitions` |
| Revenue by channel | DTC, AMZN sheets | `revenue`, `net_revenue` |
| Ad-attributed revenue (Amazon) | AMZN sheet | `ad_revenue`, `attributed_revenue` |
| Total orders | Channel sheets | `orders`, `total_orders` |

If R- sheets are populated with advertising platform data (Meta, Google, Amazon), call `read_r_sheet` for more granular campaign-level data.

---

## Phase 3 — Compute

### CAC (Customer Acquisition Cost)

```
CAC = Total Marketing Spend (period) / New Customers Acquired (period)
```

Compute both:
- **Blended CAC**: All marketing spend / all new customers
- **Channel-level CAC**: Channel marketing spend / new customers from that channel

**Benchmarks for CPG DTC:**
| CAC Range | Assessment |
|-----------|-----------|
| < 0.5× AOV | Strong — acquiring profitably |
| 0.5–1× AOV | Healthy |
| 1–2× AOV | Watch — depends on LTV |
| > 2× AOV | At risk — acquisition is loss-making at first order |

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

1. **Headline**: "Blended CAC is $[X] ([Y]× AOV). Marketing represents [Z]% of revenue. [Best channel] is most efficient at [metric]; [worst channel] is underperforming at [metric]."
2. **Efficiency summary table**:

```
| Channel | Spend | New Customers | CAC | ROAS / MER | vs. Prior Period |
|---------|-------|--------------|-----|------------|-----------------|
| DTC - Paid Social | | | | | |
| DTC - Paid Search | | | | | |
| Amazon Advertising | | | | | |
| Blended | | | | | |
```

3. **Trend chart** (narrative or visual): CAC and ROAS over trailing 3–6 months
4. **Channel efficiency ranking**: Best to worst on ROAS or CAC:AOV ratio
5. **Budget allocation analysis**: Is spend concentrated in the highest-ROAS channels?
6. **Recommendations**: Where to increase, where to cut, what to test

### Excel output (if requested)

Call `create_sheet` with blue tab. Call `write_range` for the efficiency table. Call `format_range` for number formatting. Call `create_chart` (Line chart) for CAC and ROAS trends.

---

## Guardrails

- Never write to Actual columns
- CAC calculation requires new customer counts — if this data isn't in the model, note the limitation and compute blended spend-per-order as a proxy (not true CAC but directionally useful)
- Do not mix platform-reported ROAS (which uses last-click attribution) with model-level revenue without flagging the attribution methodology difference

---

## Common Mistakes to Avoid

1. Don't use platform-reported ROAS as gospel — last-click attribution overcredits some channels (especially search) and undercredits others (social, influencer)
2. Don't analyze a single month of CAC — it's too noisy. Use trailing 3-month average minimum.
3. Don't ignore the spend-revenue timing mismatch — marketing spend in month N often drives revenue in month N+1 for new customer acquisition
4. Don't compare CAC without context of AOV and LTV — a $100 CAC is great if AOV is $120 and LTV is $400; it's terrible if AOV is $40
5. Don't optimize for ROAS alone — maximizing ROAS often means underinvesting in growth; optimize for profitable scale, not just efficiency

---

## Integration with Other Skills

- **`/cohort-analysis`**: LTV is the other half of the CAC:LTV equation
- **`/margin-analysis`**: Contribution margin context is needed for CAC payback calculations
- **`/variance-analysis`**: Check if efficiency metrics are a variance from plan
- **`/build-report`**: Package marketing efficiency for a board or investor update
