import { useState, useEffect } from "react";
import {
  Activity,
  Zap,
  Cloud,
  Droplets,
  DollarSign,
  TreePine,
  Car,
  Smartphone,
  Wind,
  Download,
} from "lucide-react";
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import { getDashboard, getCalls } from "../utils/api";
import { getStoredToken } from "../utils/auth";

const METRIC_CONFIGS = [
  { key: "total_calls",     label: "API Calls",   color: "blue",   icon: Activity,    format: (v) => v.toLocaleString() },
  { key: "total_energy_wh", label: "Energy",       color: "green",  icon: Zap,         format: (v) => `${v.toFixed(2)} Wh` },
  { key: "total_co2_g",     label: "CO₂ Emitted", color: "amber",  icon: Cloud,       format: (v) => `${v.toFixed(2)} g` },
  { key: "total_water_ml",  label: "Water Used",   color: "cyan",   icon: Droplets,    format: (v) => `${v.toFixed(2)} mL` },
  { key: "total_cost_usd",  label: "API Cost",     color: "purple", icon: DollarSign,  format: (v) => `$${v.toFixed(2)}` },
];

const PIE_COLORS = ["#10b981", "#3b82f6", "#f59e0b", "#ef4444", "#a855f7", "#06b6d4", "#ec4899", "#84cc16", "#f97316"];

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="custom-tooltip">
      <div className="label">{label}</div>
      {payload.map((p, i) => (
        <div key={i} className="value" style={{ color: p.color }}>
          {p.name}: {typeof p.value === "number" ? p.value.toFixed(4) : p.value}
        </div>
      ))}
    </div>
  );
}

export default function DashboardPage({ user }) {
  const [data, setData] = useState(null);
  const [calls, setCalls] = useState([]);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(30);

  useEffect(() => {
    loadData();
    const intervalId = setInterval(() => {
      loadData(false); // fetch without showing full page loader
    }, 5000);
    return () => clearInterval(intervalId);
  }, [days]);

  async function loadData(showLoading = true) {
    if (showLoading) setLoading(true);
    try {
      const [dashData, callsData] = await Promise.all([
        getDashboard(days),
        getCalls(10),
      ]);
      setData(dashData);
      setCalls(callsData.calls || []);
    } catch (err) {
      console.error("Dashboard load failed:", err);
    } finally {
      if (showLoading) setLoading(false);
    }
  }

  const handleExportCSV = async () => {
    try {
      const token = getStoredToken();
      const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
      const res = await fetch(`${API_BASE}/api/export/csv`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {}
      });
      if (!res.ok) throw new Error("Export failed");
      
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `greenops_export_${user?.name?.replace(/ /g, "_").toLowerCase() || 'data'}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      alert(err.message);
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner" />
        Loading dashboard...
      </div>
    );
  }

  if (!data) return <div className="loading-container">Failed to load data</div>;

  const { totals, models, daily_trends, equivalencies, sources } = data;

  // Prepare model data for pie chart
  const modelPieData = (models || []).slice(0, 8).map((m) => ({
    name: m.model_id.length > 16 ? m.model_id.slice(0, 16) + "…" : m.model_id,
    value: Math.round(m.total_energy_wh * 10000) / 10000,
    cost: Math.round((m.total_cost_usd || 0) * 10000) / 10000,
    calls: m.call_count,
  }));

  // Prepare daily trends for area chart
  const trendData = (daily_trends || []).map((t) => ({
    date: t.date?.slice(5) || "",
    energy: Math.round(t.energy_wh * 10000) / 10000,
    co2: Math.round(t.co2_g * 10000) / 10000,
    cost: Math.round((t.cost_usd || 0) * 10000) / 10000,
    calls: t.calls,
  }));

  // Equivalency icons
  const equivIcons = {
    car_km: Car,
    tree_absorption: TreePine,
    human_breaths: Wind,
    phone_charges: Smartphone,
    led_bulb_hours: Zap,
    glasses_of_water: Droplets,
  };

  return (
    <div>
      {/* Header */}
      <div className="page-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h2>Dashboard</h2>
          <p>Real-time AI environmental impact tracking</p>
        </div>
        <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
          <div style={{ display: "flex", gap: 4, background: "var(--bg-app)", padding: 4, borderRadius: "var(--radius-sm)", border: "1px solid var(--border-subtle)" }}>
            {[7, 14, 30].map((d) => (
              <button
                key={d}
                className={days === d ? "btn btn-primary" : "btn btn-ghost"}
                onClick={() => setDays(d)}
                style={{ padding: "6px 14px", fontSize: "0.78rem" }}
              >
                {d}d
              </button>
            ))}
          </div>
          <button className="btn btn-ghost" onClick={handleExportCSV} style={{ padding: "8px 14px", fontSize: "0.85rem", display: "flex", gap: "6px", alignItems: "center" }}>
            <Download size={16} /> Export CSV
          </button>
        </div>
      </div>

      {/* Metric Cards */}
      <div className="metrics-grid">
        {METRIC_CONFIGS.map((cfg, i) => {
          const Icon = cfg.icon;
          const value = totals[cfg.key] ?? 0;
          return (
            <div key={cfg.key} className={`metric-card ${cfg.color} animate-in`}>
              <div className="metric-icon">
                <Icon size={18} />
              </div>
              <div className="metric-label">{cfg.label}</div>
              <div className="metric-value">{cfg.format(value)}</div>
            </div>
          );
        })}
      </div>

      {/* Charts */}
      <div className="charts-grid">
        {/* Energy Trend Chart */}
        <div className="chart-card animate-in">
          <h3>Energy Consumption Trend</h3>
          <div style={{ height: 280 }}>
            <ResponsiveContainer>
              <AreaChart data={trendData}>
                <defs>
                  <linearGradient id="gradEnergy" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#10b981" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="gradCO2" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#f59e0b" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="#f59e0b" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="energy" stroke="#10b981" fill="url(#gradEnergy)" strokeWidth={2} name="Energy (Wh)" />
                <Area type="monotone" dataKey="co2" stroke="#f59e0b" fill="url(#gradCO2)" strokeWidth={2} name="CO₂ (g)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Cost Trend Chart */}
        <div className="chart-card animate-in" style={{ animationDelay: "0.1s" }}>
          <h3>API Cost Trend</h3>
          <div style={{ height: 280 }}>
            <ResponsiveContainer>
              <AreaChart data={trendData}>
                <defs>
                  <linearGradient id="gradCost" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#a855f7" stopOpacity={0.3} />
                    <stop offset="100%" stopColor="#a855f7" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 11 }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 11 }} tickFormatter={(val) => `$${val}`} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="cost" stroke="#a855f7" fill="url(#gradCost)" strokeWidth={2} name="Cost ($)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Model Breakdown Pie */}
        <div className="chart-card animate-in" style={{ animationDelay: "0.2s" }}>
          <h3>Energy by Model</h3>
          <div style={{ height: 280 }}>
            <ResponsiveContainer>
              <PieChart>
                <Pie
                  data={modelPieData}
                  cx="50%"
                  cy="45%"
                  innerRadius={55}
                  outerRadius={90}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {modelPieData.map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend
                  verticalAlign="bottom"
                  iconType="circle"
                  iconSize={8}
                  formatter={(v) => <span style={{ color: "#94a3b8", fontSize: "0.7rem" }}>{v}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Cost Breakdown Pie */}
        <div className="chart-card animate-in" style={{ animationDelay: "0.3s" }}>
          <h3>Cost by Model</h3>
          <div style={{ height: 280 }}>
            <ResponsiveContainer>
              <PieChart>
                <Pie
                  data={modelPieData}
                  cx="50%"
                  cy="45%"
                  innerRadius={55}
                  outerRadius={90}
                  paddingAngle={3}
                  dataKey="cost"
                >
                  {modelPieData.map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend
                  verticalAlign="bottom"
                  iconType="circle"
                  iconSize={8}
                  formatter={(v) => <span style={{ color: "#94a3b8", fontSize: "0.7rem" }}>{v}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Bottom Grid — Equivalencies + Recent Calls */}
      <div className="charts-grid">
        {/* Equivalencies */}
        <div className="table-card animate-in">
          <h3>💡 Environmental Equivalencies</h3>
          <div className="equiv-grid" style={{ marginTop: 12 }}>
            {equivalencies && Object.entries(equivalencies).map(([key, eq]) => {
              const Icon = equivIcons[key] || Zap;
              return (
                <div key={key} className="equiv-card">
                  <div className="equiv-icon"><Icon size={22} color="#34d399" /></div>
                  <div className="equiv-text">{eq.label}</div>
                </div>
              );
            })}
            {(!equivalencies || Object.keys(equivalencies).length === 0) && (
              <p style={{ color: "var(--text-muted)", fontSize: "0.82rem" }}>
                Track more calls to see equivalencies
              </p>
            )}
          </div>
        </div>

        {/* Recent Calls */}
        <div className="table-card animate-in">
          <h3>Recent API Calls</h3>
          {calls.length > 0 ? (
            <table className="data-table">
              <thead>
                <tr>
                  <th>Model</th>
                  <th>Tokens</th>
                  <th>Energy</th>
                  <th>Source</th>
                </tr>
              </thead>
              <tbody>
                {calls.slice(0, 8).map((call, i) => (
                  <tr key={call.call_id || i}>
                    <td style={{ color: "var(--text-primary)", fontWeight: 500 }}>
                      {call.model_id?.length > 18 ? call.model_id.slice(0, 18) + "…" : call.model_id}
                    </td>
                    <td style={{ fontFamily: "var(--font-mono)", fontSize: "0.78rem" }}>
                      {call.total_tokens?.toLocaleString()}
                    </td>
                    <td style={{ fontFamily: "var(--font-mono)", fontSize: "0.78rem" }}>
                      {call.energy_wh?.toFixed(4)} Wh
                    </td>
                    <td>
                      <span className={`badge ${call.source === "sdk" ? "green" : call.source === "proxy" ? "blue" : "amber"}`}>
                        {call.source}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p style={{ color: "var(--text-muted)", fontSize: "0.82rem", padding: 20 }}>
              No calls tracked yet. Use the SDK to start tracking!
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
