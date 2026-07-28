# Example Artifacts

Seven working artifact templates covering nine rendered samples. Pattern-match
against these when producing new artifacts. Each uses **synthetic data** —
when adapting for a real question, replace the embedded data with the actual
query result and update the subtitle (date range, plan, channel filter,
currency).

> ⚠️ **All numeric values in this file are illustrative placeholders.**
> Never reuse them in a response to a real user question. Always derive
> figures (and currency) from the actual query result. The `RAW` arrays in
> each example are scaffolding for the rendering pattern only.

> **Shared components.** Every example below uses `DrivepointLockup`,
> `ArtifactHeader`, `DrivepointFonts`, `DP_CHART_SERIES`, and — for Full
> documents — `ArtifactPage` / `ArtifactSection` / `SignatureFooter`
> (plus `DrivepointMark` only when a constrained mark-alone is needed).
> The canonical definitions live in `artifact-style-guide.md` § "Brand
> lockup" and § "Color tokens" — paste them into the artifact before the
> `App` component. They are not re-declared in each example.
> Pass optional `customer` (and `meta`) on `ArtifactHeader` when the
> tenant display name is known. Pass `kicker` only when the artifact has
> a category to name (Full); omit it for Compact single-answer shells.

---

## Example 1 — Monthly Revenue Dashboard

**Triggered by:** "Show me revenue by channel for the last 6 months."

**Data shape:** `[{ month, channel, currency, net_sales, orders }, …]`

**Tier:** Full — `kicker` + `ArtifactPage`.

```jsx
import React from 'react';
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend,
} from 'recharts';

const fmtMoney = (n, c) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: c, maximumFractionDigits: 0 }).format(n);
const fmtMoneyCompact = (n, c) => {
  const sym = new Intl.NumberFormat('en-US', { style: 'currency', currency: c, maximumFractionDigits: 0 })
    .formatToParts(0).find((p) => p.type === 'currency')?.value ?? c;
  if (n === 0) return `${sym}0`;
  const sign = n < 0 ? '-' : '';
  const abs = Math.abs(n);
  let scaled, suffix;
  if (abs >= 1e6) { scaled = abs / 1e6; suffix = 'M'; }
  else if (abs >= 1e3) { scaled = abs / 1e3; suffix = 'K'; }
  else return `${sign}${sym}${Math.round(abs)}`;
  const rounded = Math.round(scaled * 10) / 10;
  return `${sign}${sym}${Number.isInteger(rounded) ? rounded : rounded.toFixed(1)}${suffix}`;
};
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

const CURRENCY = RAW[0].currency;
const DATE_RANGE = 'Jun 2025 – Nov 2025';
const CUSTOMER_NAME = 'Sample Brand';

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
  <div className="bg-white border border-[#ecebe9] rounded-lg shadow-sm p-4">
    <div className="text-xs text-[#716e6b] uppercase tracking-wide">{label}</div>
    <div className="text-2xl font-semibold text-[#191815] mt-1 tabular-nums">{value}</div>
    {sub && <div className="text-xs text-[#716e6b] mt-1">{sub}</div>}
  </div>
);

export default function App() {
  return (
    <ArtifactPage>
      <ArtifactHeader
        title="Revenue by Channel"
        subtitle={`${DATE_RANGE} · all channels · ${CURRENCY}`}
        customer={CUSTOMER_NAME}
        meta={DATE_RANGE}
        kicker="Monthly business review"
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
          <CartesianGrid strokeDasharray="3 3" stroke="#ecebe9" />
          <XAxis dataKey="month" stroke="#716e6b" />
          <YAxis stroke="#716e6b" tickFormatter={(v) => fmtMoneyCompact(v, CURRENCY)} />
          <Tooltip formatter={(v) => fmtMoney(v, CURRENCY)} />
          <Legend formatter={(value) => <span style={{ color: '#191815' }}>{value}</span>} />
          {channels.map((c, i) => (
            <Line
              key={c}
              type="monotone"
              dataKey={c}
              stroke={DP_CHART_SERIES[i % DP_CHART_SERIES.length]}
              strokeWidth={2}
              dot={{ r: 3 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
      <SignatureFooter sourceLine="Source: ecommerce_transactions_order_level" />
    </ArtifactPage>
  );
}
```

**Patterns demonstrated:**
- Full tier via `kicker` + `ArtifactPage`.
- KPI card grid + line chart; series indexed with `DP_CHART_SERIES[i % …]`.
- Currency derived from the data, never hardcoded.

---

## Example 2 — P&L Summary Table

**Triggered by:** "Show me the P&L for the last quarter."

**Data shape:** `[{ report_month, metric_id, metric_name, metric_format, metric_sort_order, metric_value }, …]`

**Tier:** Full — `kicker` + `ArtifactPage`.

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
// ============================================================
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

const CURRENCY = 'USD';
const DATE_RANGE = 'Q3 2025';
const CUSTOMER_NAME = 'Sample Brand';
const COMPANY_ID = '<RESOLVED_FROM_QUERY>';
const REPORT_LINK = {
  name: 'Financial Statements',
  url: `https://app.drivepoint.io/${COMPANY_ID}/reports/bundle/finance_bundle`,
};

const SUBTOTALS = new Set([
  'incomeStatement.netSales',
  'incomeStatement.grossProfit',
  'incomeStatement.contributionProfit',
  'incomeStatement.operatingIncome',
  'incomeStatement.EBITDA',
  'incomeStatement.netIncome',
]);

const byMetric = new Map();
for (const r of RAW) {
  if (!byMetric.has(r.metric_id)) {
    byMetric.set(r.metric_id, { name: r.metric_name, sort: r.metric_sort_order, vals: {} });
  }
  byMetric.get(r.metric_id).vals[r.report_month] = r.metric_value;
}
const metrics = [...byMetric.entries()].sort((a, b) => a[1].sort - b[1].sort);
const months = [...new Set(RAW.map((r) => r.report_month))].sort();

export default function App() {
  return (
    <ArtifactPage>
      <ArtifactHeader
        title="P&amp;L Summary"
        subtitle={`${DATE_RANGE} · live plan actuals · ${CURRENCY}`}
        customer={CUSTOMER_NAME}
        meta={DATE_RANGE}
        kicker="Financial statements"
      />
      <div className="overflow-x-auto">
        <table className="w-full text-sm tabular-nums">
          <thead className="bg-[#f9f8f6] text-[#716e6b] sticky top-0">
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
                <tr key={id} className={`border-t border-[#ecebe9] ${isSub ? 'font-semibold bg-[#f9f8f6]' : ''}`}>
                  <td className="py-2 px-3">{m.name}</td>
                  {months.map((mo) => (
                    <td key={mo} className="py-2 px-3 text-right">{fmtFinancial(m.vals[mo], CURRENCY)}</td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {REPORT_LINK && (
        <div className="text-xs text-[#716e6b] mt-4">
          Also available in Drivepoint:{' '}
          <a href={REPORT_LINK.url} target="_blank" rel="noopener noreferrer" className="text-[#191815] underline hover:decoration-2">
            {REPORT_LINK.name}
          </a>
        </div>
      )}
      <SignatureFooter sourceLine="Source: smartmodel_actuals" />
    </ArtifactPage>
  );
}
```

---

## Example 3 — Actuals vs. Forecast Variance

**Triggered by:** "How are we tracking against the 2025 Base Case for net sales?"

**Data shape:** `[{ report_month, metric_name, actual_value, forecast_value, variance, variance_pct }, …]`

**Tier:** Full. Warm deltas `#2f7d54` / `#b0472f` are visible in the variance cells.

```jsx
import React from 'react';
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend,
} from 'recharts';

const fmtMoney = (n, c) =>
  n == null ? '—'
    : new Intl.NumberFormat('en-US', { style: 'currency', currency: c, maximumFractionDigits: 0 }).format(n);
const fmtMoneyCompact = (n, c) => {
  const sym = new Intl.NumberFormat('en-US', { style: 'currency', currency: c, maximumFractionDigits: 0 })
    .formatToParts(0).find((p) => p.type === 'currency')?.value ?? c;
  if (n === 0) return `${sym}0`;
  const sign = n < 0 ? '-' : '';
  const abs = Math.abs(n);
  let scaled, suffix;
  if (abs >= 1e6) { scaled = abs / 1e6; suffix = 'M'; }
  else if (abs >= 1e3) { scaled = abs / 1e3; suffix = 'K'; }
  else return `${sign}${sym}${Math.round(abs)}`;
  const rounded = Math.round(scaled * 10) / 10;
  return `${sign}${sym}${Number.isInteger(rounded) ? rounded : rounded.toFixed(1)}${suffix}`;
};
const fmtPct = (n) => (n == null ? '—' : `${(n * 100).toFixed(1)}%`);

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
const CUSTOMER_NAME = 'Sample Brand';
const CURRENCY = 'USD';
const DATE_RANGE = 'Jun 2025 – Nov 2025';

const totalActual = RAW.reduce((s, r) => s + r.actual_value, 0);
const totalForecast = RAW.reduce((s, r) => s + r.forecast_value, 0);
const totalVariance = totalActual - totalForecast;
const totalVariancePct = totalVariance / totalForecast;

const VarianceCell = ({ value, pct }) => {
  const pos = value >= 0;
  const color = pos ? '#2f7d54' : '#b0472f';
  const arrow = pos ? '↑' : '↓';
  return (
    <span className="tabular-nums" style={{ color }}>
      {arrow} {fmtMoney(Math.abs(value), CURRENCY)} ({fmtPct(Math.abs(pct))})
    </span>
  );
};

export default function App() {
  return (
    <ArtifactPage>
      <ArtifactHeader
        title={`${METRIC_NAME} — Actuals vs. ${PLAN_NAME}`}
        subtitle={`${DATE_RANGE} · ${CURRENCY}`}
        customer={CUSTOMER_NAME}
        meta={DATE_RANGE}
        kicker="Plan variance"
      />

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        <div className="bg-white border border-[#ecebe9] rounded-lg p-4">
          <div className="text-xs text-[#716e6b] uppercase">Actual (total)</div>
          <div className="text-xl font-semibold tabular-nums">{fmtMoney(totalActual, CURRENCY)}</div>
        </div>
        <div className="bg-white border border-[#ecebe9] rounded-lg p-4">
          <div className="text-xs text-[#716e6b] uppercase">Forecast (total)</div>
          <div className="text-xl font-semibold tabular-nums">{fmtMoney(totalForecast, CURRENCY)}</div>
        </div>
        <div className="bg-white border border-[#ecebe9] rounded-lg p-4">
          <div className="text-xs text-[#716e6b] uppercase">Variance</div>
          <div className="text-xl font-semibold">
            <VarianceCell value={totalVariance} pct={totalVariancePct} />
          </div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={RAW} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#ecebe9" />
          <XAxis dataKey="report_month" stroke="#716e6b" />
          <YAxis stroke="#716e6b" tickFormatter={(v) => fmtMoneyCompact(v, CURRENCY)} />
          <Tooltip formatter={(v) => fmtMoney(v, CURRENCY)} />
          <Legend formatter={(value) => <span style={{ color: '#191815' }}>{value}</span>} />
          <Bar dataKey="actual_value" name="Actual" fill={DP_CHART_SERIES[0]} />
          <Bar dataKey="forecast_value" name="Forecast" fill={DP_CHART_SERIES[19]} />
        </BarChart>
      </ResponsiveContainer>

      <div className="mt-6 overflow-x-auto">
        <table className="w-full text-sm tabular-nums">
          <thead className="bg-[#f9f8f6] text-[#716e6b]">
            <tr>
              <th className="text-left  font-medium py-2 px-3">Month</th>
              <th className="text-right font-medium py-2 px-3">Actual</th>
              <th className="text-right font-medium py-2 px-3">Forecast</th>
              <th className="text-right font-medium py-2 px-3">Variance</th>
            </tr>
          </thead>
          <tbody>
            {RAW.map((r) => (
              <tr key={r.report_month} className="border-t border-[#ecebe9] even:bg-[#f9f8f6]">
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

      <SignatureFooter sourceLine="Source: smartmodel_actuals_vs_forecast" />
    </ArtifactPage>
  );
}
```

---

## Example 4 — Scenario comparison (Layout B)

**Triggered by:** multi-scenario Raptor preview questions.

**Spec:** follow `scenario-planning.md` § "Layout B — multi-scenario comparison"
for series roles, interactivity, and table controls — **do not duplicate that
spec here.** Chrome follows the signature theme (`kicker`, `ArtifactPage`,
`SignatureFooter`).

**Series alignment:** the scenario skill and this example both use PM-314
(`DP_CHART_SERIES[0]` primary, `[1]` second, `[19]` baseline grey). The
Layout B structure and interactivity rules from the scenario skill remain
the canonical behavior contract.

```jsx
import React, { useState } from 'react';
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend,
} from 'recharts';

const fmtMoney = (n, c) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: c, maximumFractionDigits: 0 }).format(n);
const fmtMoneyCompact = (n, c) => {
  const sym = new Intl.NumberFormat('en-US', { style: 'currency', currency: c, maximumFractionDigits: 0 })
    .formatToParts(0).find((p) => p.type === 'currency')?.value ?? c;
  if (n === 0) return `${sym}0`;
  const sign = n < 0 ? '-' : '';
  const abs = Math.abs(n);
  let scaled, suffix;
  if (abs >= 1e6) { scaled = abs / 1e6; suffix = 'M'; }
  else if (abs >= 1e3) { scaled = abs / 1e3; suffix = 'K'; }
  else return `${sign}${sym}${Math.round(abs)}`;
  const rounded = Math.round(scaled * 10) / 10;
  return `${sign}${sym}${Number.isInteger(rounded) ? rounded : rounded.toFixed(1)}${suffix}`;
};

const CUSTOMER_NAME = 'Sample Brand';
const CURRENCY = 'USD';
const PLAN_NAME = '2026 Base Case';
const MONTHS = ['2026-06', '2026-07', '2026-08', '2026-09', '2026-10', '2026-11'];

const BASELINE = [2100000, 2050000, 1980000, 1920000, 1880000, 1850000];
const SCENARIOS = [
  { id: 's1', name: 'Opex trim A', recommended: true, values: [2100000, 2080000, 2065000, 2050000, 2040000, 2035000] },
  { id: 's2', name: 'Opex trim B', recommended: false, values: [2100000, 2070000, 2040000, 2010000, 1990000, 1975000] },
  { id: 's3', name: 'Ad spend cut', recommended: false, values: [2100000, 2040000, 1990000, 1950000, 1920000, 1900000] },
];

const chartData = MONTHS.map((m, i) => {
  const row = { month: m, baseline: BASELINE[i] };
  SCENARIOS.forEach((s) => { row[s.id] = s.values[i]; });
  return row;
});

export default function App() {
  const [relative, setRelative] = useState(false);
  const winner = SCENARIOS.find((s) => s.recommended);
  const winnerDelta = winner.values[3] - BASELINE[3];
  const winnerDeltaSign = winnerDelta > 0 ? '+' : winnerDelta < 0 ? '−' : '';
  const [selectedScenarioIds, setSelectedScenarioIds] = useState(
    () => new Set(winner ? [winner.id] : []),
  );
  const toggleScenario = (scenarioId) => {
    setSelectedScenarioIds((current) => {
      const next = new Set(current);
      if (next.has(scenarioId)) next.delete(scenarioId);
      else next.add(scenarioId);
      return next;
    });
  };

  return (
    <ArtifactPage width={1040}>
      <ArtifactHeader
        title="Cash · Scenario Proposals"
        subtitle={`${PLAN_NAME} · Jun–Nov 2026 · ${CURRENCY} · levers: discretionary opex`}
        customer={CUSTOMER_NAME}
        meta="Raptor preview"
        kicker="Scenario comparison"
      />

      <div className="flex items-center gap-2 mb-6">
        <span className="text-sm font-semibold text-[#191815]">Drivepoint Intelligence</span>
        <span className="rounded-full px-2 py-0.5 text-[10px] font-semibold tracking-wide" style={{ background: '#FFDE6A', color: '#191815' }}>
          BETA
        </span>
      </div>

      <ArtifactSection title="3 Scenario Proposals">
        <p className="text-sm text-[#716e6b] m-0 mb-4">
          I've identified 3 scenarios that best optimize cash based on short-term opex and seasonality.
        </p>
        <ResponsiveContainer width="100%" height={320}>
          <LineChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#ecebe9" />
            <XAxis dataKey="month" stroke="#716e6b" />
            <YAxis stroke="#716e6b" tickFormatter={(v) => fmtMoneyCompact(v, CURRENCY)} />
            <Tooltip formatter={(v) => fmtMoney(v, CURRENCY)} />
            <Legend formatter={(value) => <span style={{ color: '#191815' }}>{value}</span>} />
            <Line type="monotone" dataKey="baseline" name="Baseline" stroke={DP_CHART_SERIES[19]} strokeWidth={2} dot={false} />
            {SCENARIOS.map((s, i) => (
              <Line
                key={s.id}
                type="monotone"
                dataKey={s.id}
                name={s.name}
                stroke={DP_CHART_SERIES[(i) % DP_CHART_SERIES.length]}
                strokeWidth={2}
                dot={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </ArtifactSection>

      <section className="mt-11 rounded-lg border border-[#ecebe9] bg-[#fefefe] p-4 sm:p-5">
        <h2 className="text-[17px] font-bold m-0 mb-1 pb-1.5 border-b border-[#ecebe9] text-[#191815]">
          Scenario Details
        </h2>
        <p className="text-sm text-[#716e6b] mt-2 mb-3">
          Analyze scenario impact month by month on output variable.
        </p>
        <div className="flex flex-wrap justify-end gap-3 mb-3 text-sm">
          <label className="flex min-h-11 cursor-pointer items-center gap-2 text-[#716e6b]">
            <input type="checkbox" checked={relative} onChange={(e) => setRelative(e.target.checked)} />
            Show relative variance
          </label>
          <span className="text-[#716e6b]">Date Range: Jun–Nov 2026</span>
          <span className="text-[#716e6b]">Output: Cash</span>
        </div>
        <div className="overflow-x-auto border border-[#ecebe9] rounded-lg">
          <table className="w-full text-sm tabular-nums">
            <thead className="bg-[#f9f8f6] text-[#716e6b]">
              <tr>
                <th className="w-12 py-2 px-1">
                  <span className="sr-only">Select scenario</span>
                </th>
                <th className="text-left py-2 px-3">Scenario</th>
                {MONTHS.map((m) => (
                  <th key={m} className="text-right py-2 px-3">{m}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {SCENARIOS.map((s) => (
                <tr key={s.id} className="border-t border-[#ecebe9]">
                  <td className="py-0 px-1">
                    <label className="inline-flex h-11 w-11 cursor-pointer items-center justify-center">
                      <input
                        type="checkbox"
                        aria-label={`Select ${s.name}`}
                        checked={selectedScenarioIds.has(s.id)}
                        onChange={() => toggleScenario(s.id)}
                      />
                    </label>
                  </td>
                  <td className="py-2 px-3">
                    <div className="font-medium text-[#191815]">{s.name}</div>
                    {s.recommended ? (
                      <div className="text-xs text-[#716e6b]">Drivepoint Intelligence Winner</div>
                    ) : s.id === 's2' ? (
                      <div className="text-xs text-[#716e6b]">Secondary Pick</div>
                    ) : null}
                  </td>
                  {s.values.map((v, i) => {
                    const cell = relative ? v - BASELINE[i] : v;
                    const direction = cell > 0 ? '↑ +' : cell < 0 ? '↓ −' : '→ ';
                    const color = cell > 0 ? '#2f7d54' : cell < 0 ? '#b0472f' : '#191815';
                    const display = relative
                      ? `${direction}${fmtMoney(Math.abs(cell), CURRENCY)}`
                      : fmtMoney(v, CURRENCY);
                    return (
                      <td key={MONTHS[i]} className="py-2 px-3 text-right" style={relative ? { color } : undefined}>
                        {display}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-sm text-[#716e6b] mt-3">
          {winner.name} wins on Sep cash ({winnerDeltaSign}{fmtMoney(Math.abs(winnerDelta), CURRENCY)} vs baseline).
        </p>
      </section>

      <SignatureFooter sourceLine={`Source: plan '${PLAN_NAME}' · Raptor preview (workbook not modified)`} />
    </ArtifactPage>
  );
}
```

---

## Example 5 — CEO daily flash

**Triggered by:** "Build me a daily flash: yesterday's sales by channel, MTD vs plan, cash position."
(Field-proven showpiece from `baku/tools/starter-prompts/library.md` —
sales + margins from the model + inventory in one artifact.)

**Tier:** Full.

```jsx
import React from 'react';
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip,
} from 'recharts';

const fmtMoney = (n, c) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: c, maximumFractionDigits: 0 }).format(n);
const fmtPct = (n) => `${(n * 100).toFixed(1)}%`;

const CUSTOMER_NAME = 'Sample Brand';
const CURRENCY = 'USD';
const AS_OF = '2025-11-18';

const SALES_BY_CHANNEL = [
  { channel: 'DTC web', sales: 42000 },
  { channel: 'Amazon', sales: 31000 },
  { channel: 'Wholesale', sales: 18000 },
  { channel: 'Retail', sales: 9000 },
];

const MTD = { actual: 612000, plan: 580000 };
const MARGINS = [
  { label: 'Gross margin', value: 0.582 },
  { label: 'Contribution margin', value: 0.314 },
];
const INVENTORY = [
  { sku: 'SKU-A', weeks: 6.2, status: 'ok' },
  { sku: 'SKU-B', weeks: 2.1, status: 'watch' },
  { sku: 'SKU-C', weeks: 0.8, status: 'stockout' },
  { sku: 'SKU-D', weeks: 9.4, status: 'ok' },
];
const CASH = 1240000;

export default function App() {
  const mtdVar = MTD.actual - MTD.plan;
  return (
    <ArtifactPage width={1040}>
      <ArtifactHeader
        title="Daily flash"
        subtitle={`As of ${AS_OF} · yesterday + MTD · ${CURRENCY}`}
        customer={CUSTOMER_NAME}
        meta={AS_OF}
        kicker="Executive flash"
      />

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        {[
          { label: "Yesterday's sales", value: fmtMoney(SALES_BY_CHANNEL.reduce((s, r) => s + r.sales, 0), CURRENCY) },
          { label: 'MTD vs plan', value: `${fmtMoney(MTD.actual, CURRENCY)} (${mtdVar >= 0 ? '↑' : '↓'} ${fmtMoney(Math.abs(mtdVar), CURRENCY)})`, color: mtdVar >= 0 ? '#2f7d54' : '#b0472f' },
          { label: 'Cash position', value: fmtMoney(CASH, CURRENCY) },
          { label: 'Gross margin', value: fmtPct(MARGINS[0].value) },
        ].map((k) => (
          <div key={k.label} className="border border-[#ecebe9] rounded-lg p-4">
            <div className="text-xs text-[#716e6b] uppercase">{k.label}</div>
            <div className="text-xl font-semibold tabular-nums mt-1" style={{ color: k.color || '#191815' }}>{k.value}</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <ArtifactSection title="Yesterday by channel">
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={SALES_BY_CHANNEL} layout="vertical" margin={{ top: 4, right: 16, left: 8, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#ecebe9" />
              <XAxis type="number" stroke="#716e6b" tickFormatter={(v) => fmtMoney(v, CURRENCY)} />
              <YAxis type="category" dataKey="channel" width={90} stroke="#716e6b" />
              <Tooltip formatter={(v) => fmtMoney(v, CURRENCY)} />
              <Bar dataKey="sales" fill={DP_CHART_SERIES[0]} />
            </BarChart>
          </ResponsiveContainer>
        </ArtifactSection>

        <ArtifactSection title="Margins (model)">
          <table className="w-full text-sm tabular-nums">
            <tbody>
              {MARGINS.map((m, i) => (
                <tr key={m.label} className="border-t border-[#ecebe9]">
                  <td className="py-2 pr-3 flex items-center gap-2">
                    <span className="inline-block w-2.5 h-2.5 rounded-sm" style={{ background: DP_CHART_SERIES[i % DP_CHART_SERIES.length] }} />
                    {m.label}
                  </td>
                  <td className="py-2 text-right font-semibold">{fmtPct(m.value)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </ArtifactSection>

        <ArtifactSection title="Inventory weeks of supply">
          <table className="w-full text-sm tabular-nums">
            <thead className="text-[#716e6b]">
              <tr>
                <th className="text-left py-2">SKU</th>
                <th className="text-right py-2">Weeks</th>
                <th className="text-right py-2">Status</th>
              </tr>
            </thead>
            <tbody>
              {INVENTORY.map((r) => (
                <tr key={r.sku} className="border-t border-[#ecebe9]">
                  <td className="py-2">{r.sku}</td>
                  <td className="py-2 text-right">{r.weeks.toFixed(1)}</td>
                  <td className="py-2 text-right" style={{ color: r.status === 'ok' ? '#2f7d54' : '#b0472f' }}>
                    {r.status === 'ok' ? 'OK' : r.status === 'watch' ? 'Watch' : 'Stock-out risk'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </ArtifactSection>
      </div>

      <SignatureFooter sourceLine="Source: ecommerce_transactions_order_level · smartmodel_actuals · inventory snapshot" />
    </ArtifactPage>
  );
}
```

---

## Example 6 — Cohort retention (heavy chart)

**Triggered by:** cohort / LTV questions (`report-catalog` `cohortanalysis_bundle`).

**Tier:** Full. **24 monthly cohorts** — saturates PM-314 so adjacent hues can be judged.
**Legend:** two-column swatch grid (12 × 2) under the chart — keeps 24 entries on-canvas.
**Cycling:** `DP_CHART_SERIES[i % DP_CHART_SERIES.length]`. Series 31 would receive
position 1 (`#3975d0`) again.

```jsx
import React from 'react';
import {
  ResponsiveContainer, LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip,
} from 'recharts';

const CUSTOMER_NAME = 'Sample Brand';
const COHORTS = Array.from({ length: 24 }, (_, i) => {
  const d = new Date(2023, 11 + i, 1);
  const label = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
  return label;
});
const DATE_RANGE = `${COHORTS[0]}–${COHORTS.at(-1)}`;
const AGES = Array.from({ length: 12 }, (_, i) => `M${i}`);

// Retention decay with slight cohort-quality drift so curves cross.
const chartData = AGES.map((age, ageIdx) => {
  const row = { age };
  COHORTS.forEach((c, ci) => {
    const quality = 1 - ci * 0.008 + ((ci % 5) - 2) * 0.012;
    const base = Math.exp(-ageIdx * (0.22 + (ci % 7) * 0.008));
    row[c] = Math.max(0.04, Math.min(1, base * quality + (ageIdx === 3 && ci % 4 === 0 ? 0.06 : 0)));
  });
  return row;
});

export default function App() {
  return (
    <ArtifactPage width={1180}>
      <ArtifactHeader
        title="Cohort retention"
        subtitle={`${DATE_RANGE} · 24 monthly acquisition cohorts · DTC · synthetic scaffolding`}
        customer={CUSTOMER_NAME}
        meta="24 series"
        kicker="Cohort analysis"
      />

      <ResponsiveContainer width="100%" height={520}>
        <LineChart data={chartData} margin={{ top: 10, right: 24, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#ecebe9" />
          <XAxis dataKey="age" stroke="#716e6b" />
          <YAxis stroke="#716e6b" domain={[0, 1]} tickFormatter={(v) => `${Math.round(v * 100)}%`} />
          <Tooltip formatter={(v) => `${(v * 100).toFixed(1)}%`} />
          {COHORTS.map((c, i) => (
            <Line
              key={c}
              type="monotone"
              dataKey={c}
              stroke={DP_CHART_SERIES[i % DP_CHART_SERIES.length]}
              strokeWidth={1.5}
              dot={false}
              legendType="none"
            />
          ))}
        </LineChart>
      </ResponsiveContainer>

      <div className="mt-4 grid grid-cols-2 gap-x-6 gap-y-1.5 text-xs text-[#191815]">
        {COHORTS.map((c, i) => (
          <div key={c} className="flex items-center gap-2 min-w-0">
            <span className="inline-block w-3 h-3 rounded-sm shrink-0" style={{ background: DP_CHART_SERIES[i % DP_CHART_SERIES.length] }} />
            <span className="truncate tabular-nums">{c}</span>
          </div>
        ))}
      </div>

      <SignatureFooter sourceLine="Source: ecommerce_transactions_order_level" />
    </ArtifactPage>
  );
}
```

---

## Example 7 — Single answer (Compact × 3)

**Triggered by:** high-traffic openers like "What were my net sales for June so far?"
All three variants **omit `kicker`** — that is what makes them Compact.

### 7a — One number

```jsx
import React from 'react';

const CUSTOMER_NAME = 'Sample Brand';
const CURRENCY = 'USD';
const VALUE = 612000;

const fmtMoney = (n, c) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: c, maximumFractionDigits: 0 }).format(n);

export default function App() {
  return (
    <div className="p-6 bg-white">
      <ArtifactHeader
        title="Net sales — June MTD"
        subtitle={`As of 2025-06-18 · ${CURRENCY}`}
        customer={CUSTOMER_NAME}
        meta="MTD"
      />
      <div className="text-4xl font-bold tabular-nums text-[#191815]">{fmtMoney(VALUE, CURRENCY)}</div>
      <div className="text-xs text-[#716e6b] mt-4">Source: ecommerce_transactions_order_level</div>
    </div>
  );
}
```

### 7b — One small chart

```jsx
import React from 'react';
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
} from 'recharts';

const CUSTOMER_NAME = 'Sample Brand';
const CURRENCY = 'USD';
const RAW = [
  { day: 'Jun 1', sales: 18000 },
  { day: 'Jun 5', sales: 22000 },
  { day: 'Jun 10', sales: 19500 },
  { day: 'Jun 15', sales: 24100 },
  { day: 'Jun 18', sales: 21000 },
];
const fmtMoney = (n, c) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: c, maximumFractionDigits: 0 }).format(n);
const fmtMoneyCompact = (n, c) => {
  const sym = new Intl.NumberFormat('en-US', { style: 'currency', currency: c, maximumFractionDigits: 0 })
    .formatToParts(0).find((p) => p.type === 'currency')?.value ?? c;
  if (n === 0) return `${sym}0`;
  const sign = n < 0 ? '-' : '';
  const abs = Math.abs(n);
  let scaled, suffix;
  if (abs >= 1e6) { scaled = abs / 1e6; suffix = 'M'; }
  else if (abs >= 1e3) { scaled = abs / 1e3; suffix = 'K'; }
  else return `${sign}${sym}${Math.round(abs)}`;
  const rounded = Math.round(scaled * 10) / 10;
  return `${sign}${sym}${Number.isInteger(rounded) ? rounded : rounded.toFixed(1)}${suffix}`;
};

export default function App() {
  return (
    <div className="p-6 bg-white">
      <ArtifactHeader
        title="Net sales — June daily"
        subtitle={`Jun 1–18 2025 · ${CURRENCY}`}
        customer={CUSTOMER_NAME}
        meta="Daily"
      />
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={RAW} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#ecebe9" />
          <XAxis dataKey="day" stroke="#716e6b" />
          <YAxis stroke="#716e6b" tickFormatter={(v) => fmtMoneyCompact(v, CURRENCY)} />
          <Tooltip formatter={(v) => fmtMoney(v, CURRENCY)} />
          <Area type="monotone" dataKey="sales" stroke={DP_CHART_SERIES[0 % DP_CHART_SERIES.length]} fill={DP_CHART_SERIES[0]} fillOpacity={0.15} />
        </AreaChart>
      </ResponsiveContainer>
      <div className="text-xs text-[#716e6b] mt-4">Source: ecommerce_transactions_order_level</div>
    </div>
  );
}
```

### 7c — One small table

```jsx
import React from 'react';

const CUSTOMER_NAME = 'Sample Brand';
const CURRENCY = 'USD';
const RAW = [
  { channel: 'TikTok', sales: 84000 },
  { channel: 'Meta', sales: 112000 },
  { channel: 'Google', sales: 67000 },
];
const fmtMoney = (n, c) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: c, maximumFractionDigits: 0 }).format(n);

export default function App() {
  return (
    <div className="p-6 bg-white">
      <ArtifactHeader
        title="Gross sales by channel — last month"
        subtitle={`Oct 2025 · ${CURRENCY}`}
        customer={CUSTOMER_NAME}
        meta="Oct 2025"
      />
      <table className="w-full text-sm tabular-nums">
        <thead className="text-[#716e6b]">
          <tr>
            <th className="text-left py-2">Channel</th>
            <th className="text-right py-2">Gross sales</th>
          </tr>
        </thead>
        <tbody>
          {RAW.map((r, i) => (
            <tr key={r.channel} className="border-t border-[#ecebe9]">
              <td className="py-2 flex items-center gap-2">
                <span className="inline-block w-2.5 h-2.5 rounded-sm" style={{ background: DP_CHART_SERIES[i % DP_CHART_SERIES.length] }} />
                {r.channel}
              </td>
              <td className="py-2 text-right">{fmtMoney(r.sales, CURRENCY)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="text-xs text-[#716e6b] mt-4">Source: ecommerce_transactions_order_level</div>
    </div>
  );
}
```
