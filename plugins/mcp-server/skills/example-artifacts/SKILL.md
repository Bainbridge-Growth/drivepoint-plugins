---
name: example-artifacts
description: Three working Drivepoint React artifact templates to pattern-match against - a monthly revenue dashboard, a P&L summary table, and an actuals versus forecast variance view. Use when building a new artifact and you want the established data-shape and rendering pattern rather than starting from scratch. Every embedded number is a synthetic placeholder and must be replaced with the real query result. The shared brand components these templates assume live in the artifact-style-guide skill.
---

# Example Artifacts

Three working artifact templates. Pattern-match against these when producing
new artifacts. Each uses **synthetic data** — when adapting for a real
question, replace the embedded data with the actual query result and update
the subtitle (date range, plan, channel filter, currency).

> ⚠️ **All numeric values in this file are illustrative placeholders.**
> Never reuse them in a response to a real user question. Always derive
> figures (and currency) from the actual query result. The `RAW` arrays in
> each example are scaffolding for the rendering pattern only.

> **Shared components.** Every example below uses `DrivepointMark`,
> `DrivepointWordmark`, and `ArtifactHeader`. The canonical definitions
> live in `artifact-style-guide.md` § "Brand lockup" — paste them into
> the artifact before the `App` component. They are not re-declared in
> each example to keep the templates focused on the data-shape pattern.

---

## Example 1 — Monthly Revenue Dashboard

**Triggered by:** "Show me revenue by channel for the last 6 months."

**Data shape:** `[{ month, channel, currency, net_sales, orders }, …]`

```jsx
import React from 'react';
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend,
} from 'recharts';

const COLORS = ['#5b8dd8', '#E1BD3D', '#76A4EA', '#64748b'];

const fmtMoney = (n, c) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: c, maximumFractionDigits: 0 }).format(n);
const fmtCount = (n) => new Intl.NumberFormat('en-US').format(n);
const fmtPct = (n) => `${(n * 100).toFixed(1)}%`;

// ============================================================
// SYNTHETIC SAMPLE DATA — DEMONSTRATION ONLY.
// Replace with the actual query result. NEVER reuse these
// values in a response to a real user question.
// ============================================================
const RAW = [
  { month: '2025-06', channel: 'Channel A', currency: 'USD', net_sales: 482000, orders: 4100 },
  { month: '2025-06', channel: 'Channel B', currency: 'USD', net_sales: 211000, orders: 1850 },
  { month: '2025-06', channel: 'Channel C', currency: 'USD', net_sales: 96000,  orders: 920 },
  { month: '2025-07', channel: 'Channel A', currency: 'USD', net_sales: 510000, orders: 4380 },
  { month: '2025-07', channel: 'Channel B', currency: 'USD', net_sales: 226000, orders: 1940 },
  { month: '2025-07', channel: 'Channel C', currency: 'USD', net_sales: 104000, orders: 980 },
  { month: '2025-08', channel: 'Channel A', currency: 'USD', net_sales: 498000, orders: 4250 },
  { month: '2025-08', channel: 'Channel B', currency: 'USD', net_sales: 240000, orders: 2020 },
  { month: '2025-08', channel: 'Channel C', currency: 'USD', net_sales: 112000, orders: 1010 },
  { month: '2025-09', channel: 'Channel A', currency: 'USD', net_sales: 532000, orders: 4490 },
  { month: '2025-09', channel: 'Channel B', currency: 'USD', net_sales: 248000, orders: 2080 },
  { month: '2025-09', channel: 'Channel C', currency: 'USD', net_sales: 118000, orders: 1050 },
  { month: '2025-10', channel: 'Channel A', currency: 'USD', net_sales: 561000, orders: 4720 },
  { month: '2025-10', channel: 'Channel B', currency: 'USD', net_sales: 263000, orders: 2200 },
  { month: '2025-10', channel: 'Channel C', currency: 'USD', net_sales: 124000, orders: 1090 },
  { month: '2025-11', channel: 'Channel A', currency: 'USD', net_sales: 598000, orders: 4990 },
  { month: '2025-11', channel: 'Channel B', currency: 'USD', net_sales: 274000, orders: 2280 },
  { month: '2025-11', channel: 'Channel C', currency: 'USD', net_sales: 131000, orders: 1140 },
];

// Derive currency from the data. NEVER hardcode 'USD'.
const CURRENCY = RAW[0].currency;
const DATE_RANGE = 'Jun 2025 – Nov 2025';

const channels = [...new Set(RAW.map((r) => r.channel))];
const pivoted = [...new Set(RAW.map((r) => r.month))].map((m) => {
  const row = { month: m };
  channels.forEach((c) => {
    row[c] = RAW.find((r) => r.month === m && r.channel === c)?.net_sales ?? 0;
  });
  return row;
});

const total = (key) => RAW.reduce((s, r) => s + r[key], 0);
const totalSales = total('net_sales');
const totalOrders = total('orders');
const aov = totalSales / totalOrders;
const firstMonthSales = pivoted[0] && channels.reduce((s, c) => s + pivoted[0][c], 0);
const lastMonthSales = pivoted.at(-1) && channels.reduce((s, c) => s + pivoted.at(-1)[c], 0);
const momChange = (lastMonthSales - firstMonthSales) / firstMonthSales;

const KpiCard = ({ label, value, sub }) => (
  <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-4">
    <div className="text-xs text-slate-500 uppercase tracking-wide">{label}</div>
    <div className="text-2xl font-semibold text-slate-900 mt-1 tabular-nums">{value}</div>
    {sub && <div className="text-xs text-slate-500 mt-1">{sub}</div>}
  </div>
);

export default function App() {
  return (
    <div className="p-6 bg-white">
      <ArtifactHeader
        title="Revenue by Channel"
        subtitle={`${DATE_RANGE} · all channels · ${CURRENCY}`}
      />
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <KpiCard label="Net Sales" value={fmtMoney(totalSales, CURRENCY)} sub="6-month total" />
        <KpiCard label="Orders" value={fmtCount(totalOrders)} sub={`AOV ${fmtMoney(aov, CURRENCY)}`} />
        <KpiCard
          label="MoM Δ (first → last)"
          value={fmtPct(momChange)}
          sub={momChange >= 0 ? '↑ vs. period start' : '↓ vs. period start'}
        />
      </div>
      <ResponsiveContainer width="100%" height={360}>
        <LineChart data={pivoted} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="month" stroke="#64748b" />
          <YAxis stroke="#64748b" tickFormatter={(v) => fmtMoney(v, CURRENCY)} />
          <Tooltip formatter={(v) => fmtMoney(v, CURRENCY)} />
          <Legend />
          {channels.map((c, i) => (
            <Line
              key={c}
              type="monotone"
              dataKey={c}
              stroke={COLORS[i % COLORS.length]}
              strokeWidth={2}
              dot={{ r: 3 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
      <div className="text-xs text-slate-400 mt-4">
        Source: {{env_prefix}}_dwh_mart.ecommerce_transactions_order_level
      </div>
    </div>
  );
}
```

**Patterns demonstrated:**
- KPI card grid + line chart layout.
- Pivot from long-format query result to chart-ready rows.
- Currency derived from the data, never hardcoded.
- `ArtifactHeader` carries the Drivepoint lockup and the date-range /
  scope / currency subtitle.

---

## Example 2 — P&L Summary Table

**Triggered by:** "Show me the P&L for the last quarter."

**Data shape:** `[{ report_month, metric_id, metric_name, metric_format, metric_sort_order, metric_value }, …]`

The supporting SQL should `ORDER BY metric_sort_order` so the array arrives
pre-sorted. The component uses that ordering directly instead of a
hardcoded list.

```jsx
import React from 'react';

const fmtMoney = (n, c) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: c, maximumFractionDigits: 0 }).format(n);
const fmtFinancial = (n, c) => {
  if (n == null) return '—';
  const s = fmtMoney(Math.abs(n), c);
  return n < 0 ? `(${s})` : s;
};

// ============================================================
// SYNTHETIC SAMPLE DATA — DEMONSTRATION ONLY.
// Replace with the actual query result. NEVER reuse these
// values in a response to a real user question.
// ============================================================
//
// `metric_value` sign convention is metric-dependent. This example
// assumes COGS is stored as negative; flip the sign in your pivot if
// your customer's model stores it positive. Verify with a probe before
// rendering.
const RAW = [
  { report_month: '2025-09', metric_id: 'incomeStatement.grossSales',         metric_name: 'Gross Sales',         metric_sort_order: 10, metric_value:  920000 },
  { report_month: '2025-09', metric_id: 'incomeStatement.netSales',           metric_name: 'Net Sales',           metric_sort_order: 20, metric_value:  860000 },
  { report_month: '2025-09', metric_id: 'incomeStatement.costOfGoodsSold',    metric_name: 'COGS',                metric_sort_order: 30, metric_value: -340000 },
  { report_month: '2025-09', metric_id: 'incomeStatement.grossProfit',        metric_name: 'Gross Profit',        metric_sort_order: 40, metric_value:  520000 },
  { report_month: '2025-09', metric_id: 'incomeStatement.contributionProfit', metric_name: 'Contribution Profit', metric_sort_order: 50, metric_value:  280000 },
  { report_month: '2025-09', metric_id: 'incomeStatement.operatingIncome',    metric_name: 'Operating Income',    metric_sort_order: 60, metric_value:  140000 },
  { report_month: '2025-09', metric_id: 'incomeStatement.EBITDA',             metric_name: 'EBITDA',              metric_sort_order: 70, metric_value:  160000 },
  { report_month: '2025-09', metric_id: 'incomeStatement.netIncome',          metric_name: 'Net Income',          metric_sort_order: 80, metric_value:   95000 },
  { report_month: '2025-10', metric_id: 'incomeStatement.grossSales',         metric_name: 'Gross Sales',         metric_sort_order: 10, metric_value:  978000 },
  { report_month: '2025-10', metric_id: 'incomeStatement.netSales',           metric_name: 'Net Sales',           metric_sort_order: 20, metric_value:  912000 },
  { report_month: '2025-10', metric_id: 'incomeStatement.costOfGoodsSold',    metric_name: 'COGS',                metric_sort_order: 30, metric_value: -358000 },
  { report_month: '2025-10', metric_id: 'incomeStatement.grossProfit',        metric_name: 'Gross Profit',        metric_sort_order: 40, metric_value:  554000 },
  { report_month: '2025-10', metric_id: 'incomeStatement.contributionProfit', metric_name: 'Contribution Profit', metric_sort_order: 50, metric_value:  302000 },
  { report_month: '2025-10', metric_id: 'incomeStatement.operatingIncome',    metric_name: 'Operating Income',    metric_sort_order: 60, metric_value:  155000 },
  { report_month: '2025-10', metric_id: 'incomeStatement.EBITDA',             metric_name: 'EBITDA',              metric_sort_order: 70, metric_value:  178000 },
  { report_month: '2025-10', metric_id: 'incomeStatement.netIncome',          metric_name: 'Net Income',          metric_sort_order: 80, metric_value:  104000 },
  { report_month: '2025-11', metric_id: 'incomeStatement.grossSales',         metric_name: 'Gross Sales',         metric_sort_order: 10, metric_value: 1031000 },
  { report_month: '2025-11', metric_id: 'incomeStatement.netSales',           metric_name: 'Net Sales',           metric_sort_order: 20, metric_value:  962000 },
  { report_month: '2025-11', metric_id: 'incomeStatement.costOfGoodsSold',    metric_name: 'COGS',                metric_sort_order: 30, metric_value: -376000 },
  { report_month: '2025-11', metric_id: 'incomeStatement.grossProfit',        metric_name: 'Gross Profit',        metric_sort_order: 40, metric_value:  586000 },
  { report_month: '2025-11', metric_id: 'incomeStatement.contributionProfit', metric_name: 'Contribution Profit', metric_sort_order: 50, metric_value:  320000 },
  { report_month: '2025-11', metric_id: 'incomeStatement.operatingIncome',    metric_name: 'Operating Income',    metric_sort_order: 60, metric_value:  168000 },
  { report_month: '2025-11', metric_id: 'incomeStatement.EBITDA',             metric_name: 'EBITDA',              metric_sort_order: 70, metric_value:  192000 },
  { report_month: '2025-11', metric_id: 'incomeStatement.netIncome',          metric_name: 'Net Income',          metric_sort_order: 80, metric_value:  113000 },
];

// SmartModel doesn't carry currency per row — use the model's base currency,
// confirmed with the customer. Replace before rendering for a real user.
const CURRENCY = 'USD';
const DATE_RANGE = 'Q3 2025';

// COMPANY_ID comes from the query result. Never hardcode for a real user.
const COMPANY_ID = '<RESOLVED_FROM_QUERY>';

// If report-catalog.md is in Knowledge AND a bundle matches the
// question's intent, set REPORT_LINK. Otherwise leave it null and the
// footer block below renders nothing. Do not fabricate a bundle ID.
const REPORT_LINK = {
  name: 'Financial Statements',
  url: `https://app.drivepoint.io/${COMPANY_ID}/reports/bundle/finance_bundle`,
};

// Subtotals: conventional CPG P&L headline rollups. Adjust to match a
// customer-specific chart of accounts if needed.
const SUBTOTALS = new Set([
  'incomeStatement.netSales',
  'incomeStatement.grossProfit',
  'incomeStatement.contributionProfit',
  'incomeStatement.operatingIncome',
  'incomeStatement.EBITDA',
  'incomeStatement.netIncome',
]);

// Build the row order from metric_sort_order (preferred) rather than a
// hardcoded list, so customer-specific line items render correctly.
const byMetric = new Map();
for (const r of RAW) {
  if (!byMetric.has(r.metric_id)) {
    byMetric.set(r.metric_id, {
      name: r.metric_name,
      sort: r.metric_sort_order,
      vals: {},
    });
  }
  byMetric.get(r.metric_id).vals[r.report_month] = r.metric_value;
}
const metrics = [...byMetric.entries()].sort((a, b) => a[1].sort - b[1].sort);
const months = [...new Set(RAW.map((r) => r.report_month))].sort();

export default function App() {
  return (
    <div className="p-6 bg-white">
      <ArtifactHeader
        title="P&amp;L Summary"
        subtitle={`${DATE_RANGE} · live plan actuals · ${CURRENCY}`}
      />
      <div className="overflow-x-auto">
        <table className="w-full text-sm tabular-nums">
          <thead className="bg-slate-50 text-slate-600 sticky top-0">
            <tr>
              <th className="text-left font-medium py-2 px-3">Line item</th>
              {months.map((m) => (
                <th key={m} className="text-right font-medium py-2 px-3">{m}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {metrics.map(([id, m]) => {
              const isSub = SUBTOTALS.has(id);
              return (
                <tr
                  key={id}
                  className={`border-t border-slate-100 ${isSub ? 'font-semibold bg-slate-50' : ''}`}
                >
                  <td className="py-2 px-3">{m.name}</td>
                  {months.map((mo) => (
                    <td key={mo} className="py-2 px-3 text-right">
                      {fmtFinancial(m.vals[mo], CURRENCY)}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {REPORT_LINK && (
        <div className="text-xs text-slate-500 mt-4">
          📊 Also available in Drivepoint:{' '}
          <a
            href={REPORT_LINK.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-slate-700 underline hover:text-slate-900"
          >
            {REPORT_LINK.name}
          </a>
        </div>
      )}
      <div className="text-xs text-slate-400 mt-2">
        Source: {{env_prefix}}_dwh_mart.smartmodel_actuals
      </div>
    </div>
  );
}
```

**Patterns demonstrated:**
- Long-format SmartModel rows pivoted into months-as-columns.
- Display order driven by `metric_sort_order` from the query, not a
  hardcoded array — portable across customers.
- Subtotal rows visually distinguished via background + bold.
- Negative values rendered in parentheses, not minus.
- Comment flags the `metric_value` sign assumption so the next reader
  knows to verify.
- `ArtifactHeader` carries the Drivepoint lockup; `REPORT_LINK` footer
  points to the matching stock bundle from `report-catalog.md`. Set
  `REPORT_LINK` to `null` when no bundle is a clean intent match — never
  render a generic "go to Reports" link.

---

## Example 3 — Actuals vs. Forecast Variance

**Triggered by:** "How are we tracking against the 2025 Base Case for net sales?"

**Data shape:** `[{ report_month, metric_name, actual_value, forecast_value, variance, variance_pct }, …]`

```jsx
import React from 'react';
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend,
} from 'recharts';

const fmtMoney = (n, c) =>
  n == null ? '—'
    : new Intl.NumberFormat('en-US', { style: 'currency', currency: c, maximumFractionDigits: 0 }).format(n);
const fmtPct = (n) => (n == null ? '—' : `${(n * 100).toFixed(1)}%`);

// ============================================================
// SYNTHETIC SAMPLE DATA — DEMONSTRATION ONLY.
// Replace with the actual query result. NEVER reuse these
// values in a response to a real user question.
// ============================================================
const RAW = [
  { report_month: '2025-06', actual_value: 692000, forecast_value: 670000, variance:  22000, variance_pct:  0.033 },
  { report_month: '2025-07', actual_value: 740000, forecast_value: 695000, variance:  45000, variance_pct:  0.065 },
  { report_month: '2025-08', actual_value: 718000, forecast_value: 720000, variance:  -2000, variance_pct: -0.003 },
  { report_month: '2025-09', actual_value: 760000, forecast_value: 745000, variance:  15000, variance_pct:  0.020 },
  { report_month: '2025-10', actual_value: 798000, forecast_value: 770000, variance:  28000, variance_pct:  0.036 },
  { report_month: '2025-11', actual_value: 762000, forecast_value: 795000, variance: -33000, variance_pct: -0.042 },
];
const METRIC_NAME = 'Net Sales';
const PLAN_NAME = '2025 Base Case';

// SmartModel doesn't carry currency per row — use the model's base currency,
// confirmed with the customer. Replace before rendering for a real user.
const CURRENCY = 'USD';
const DATE_RANGE = 'Jun 2025 – Nov 2025';

const totalActual = RAW.reduce((s, r) => s + r.actual_value, 0);
const totalForecast = RAW.reduce((s, r) => s + r.forecast_value, 0);
const totalVariance = totalActual - totalForecast;
const totalVariancePct = totalVariance / totalForecast;

const VarianceCell = ({ value, pct }) => {
  const pos = value >= 0;
  const color = pos ? 'text-emerald-600' : 'text-red-600';
  const arrow = pos ? '↑' : '↓';
  return (
    <span className={`${color} tabular-nums`}>
      {arrow} {fmtMoney(Math.abs(value), CURRENCY)} ({fmtPct(Math.abs(pct))})
    </span>
  );
};

export default function App() {
  return (
    <div className="p-6 bg-white">
      <ArtifactHeader
        title={`${METRIC_NAME} — Actuals vs. ${PLAN_NAME}`}
        subtitle={`${DATE_RANGE} · ${CURRENCY}`}
      />

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <div className="text-xs text-slate-500 uppercase">Actual (total)</div>
          <div className="text-xl font-semibold tabular-nums">{fmtMoney(totalActual, CURRENCY)}</div>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <div className="text-xs text-slate-500 uppercase">Forecast (total)</div>
          <div className="text-xl font-semibold tabular-nums">{fmtMoney(totalForecast, CURRENCY)}</div>
        </div>
        <div className="bg-white border border-slate-200 rounded-lg p-4">
          <div className="text-xs text-slate-500 uppercase">Variance</div>
          <div className="text-xl font-semibold">
            <VarianceCell value={totalVariance} pct={totalVariancePct} />
          </div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={RAW} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="report_month" stroke="#64748b" />
          <YAxis stroke="#64748b" tickFormatter={(v) => fmtMoney(v, CURRENCY)} />
          <Tooltip formatter={(v) => fmtMoney(v, CURRENCY)} />
          <Legend />
          <Bar dataKey="actual_value"   name="Actual"   fill="#5b8dd8" />
          <Bar dataKey="forecast_value" name="Forecast" fill="#cbd5e1" />
        </BarChart>
      </ResponsiveContainer>

      <div className="mt-6 overflow-x-auto">
        <table className="w-full text-sm tabular-nums">
          <thead className="bg-slate-50 text-slate-600">
            <tr>
              <th className="text-left  font-medium py-2 px-3">Month</th>
              <th className="text-right font-medium py-2 px-3">Actual</th>
              <th className="text-right font-medium py-2 px-3">Forecast</th>
              <th className="text-right font-medium py-2 px-3">Variance</th>
            </tr>
          </thead>
          <tbody>
            {RAW.map((r) => (
              <tr key={r.report_month} className="border-t border-slate-100 even:bg-slate-50">
                <td className="py-2 px-3">{r.report_month}</td>
                <td className="py-2 px-3 text-right">{fmtMoney(r.actual_value, CURRENCY)}</td>
                <td className="py-2 px-3 text-right">{fmtMoney(r.forecast_value, CURRENCY)}</td>
                <td className="py-2 px-3 text-right">
                  <VarianceCell value={r.variance} pct={r.variance_pct} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="text-xs text-slate-400 mt-4">
        Source: {{env_prefix}}_dwh_mart.smartmodel_actuals_vs_forecast
      </div>
    </div>
  );
}
```

**Patterns demonstrated:**
- Grouped bar chart with solid actual + lighter forecast.
- Variance encoded with both color and an arrow (never color alone).
- Totals row + supporting monthly table.
- Comment flags the SmartModel base-currency assumption so the next reader
  knows to verify.
- `ArtifactHeader` carries the Drivepoint lockup.
