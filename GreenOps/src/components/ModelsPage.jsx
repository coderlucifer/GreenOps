import { useState, useEffect } from "react";
import { Zap, ShieldCheck, TrendingDown, Award } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  Cell,
  Legend,
  ScatterChart,
  Scatter,
  ZAxis,
} from "recharts";
import { compareModels, getModelCatalog } from "../utils/api";

const PROVIDER_COLORS = {
  openai: "#10b981",
  anthropic: "#a855f7",
  google: "#3b82f6",
  meta: "#f59e0b",
  mistral: "#ef4444",
  deepseek: "#06b6d4",
};

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload;
  if (!d) return null;
  return (
    <div className="custom-tooltip">
      <div style={{ fontWeight: 700, color: "var(--text-primary)", marginBottom: 4 }}>{d.display_name}</div>
      <div className="value">Energy: {d.energy_wh?.toFixed(6)} Wh</div>
      <div className="value">CO₂: {d.co2_g?.toFixed(6)} g</div>
      <div className="value">Cost: ${d.cost_usd?.toFixed(4)}</div>
      <div className="value">Quality: {d.quality_score}/100</div>
      <div className="value">Sustainability: {d.sustainability_score}</div>
    </div>
  );
}

export default function ModelsPage() {
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(true);
  const [inputTokens, setInputTokens] = useState(1000);
  const [outputTokens, setOutputTokens] = useState(500);
  const [region, setRegion] = useState("global_average");

  useEffect(() => {
    loadComparison();
  }, []);

  async function loadComparison() {
    setLoading(true);
    try {
      const data = await compareModels(inputTokens, outputTokens, region);
      setComparison(data);
    } catch (err) {
      console.error("Comparison failed:", err);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner" />
        Loading model comparison...
      </div>
    );
  }

  const models = comparison?.models || [];
  const greenest = comparison?.greenest;

  // Bar chart data — energy comparison
  const barData = models.map((m) => ({
    name: m.display_name.length > 14 ? m.display_name.slice(0, 14) + "…" : m.display_name,
    energy: Math.round(m.energy_wh * 1000000) / 1000000,
    co2: m.co2_g,
    quality: m.quality_score,
    sustainability_score: m.sustainability_score,
    ...m,
  }));

  // Scatter data — quality vs energy
  const scatterData = models.map((m) => ({
    x: m.energy_wh * 1000,
    y: m.quality_score,
    z: m.sustainability_score,
    name: m.display_name,
    provider: m.provider,
    ...m,
  }));

  return (
    <div>
      <div className="page-header">
        <h2>Model Comparison</h2>
        <p>Compare AI models by sustainability, quality, and cost</p>
      </div>

      {/* Controls */}
      <div className="glass-card animate-in" style={{ marginBottom: 20, display: "flex", gap: 16, alignItems: "flex-end", flexWrap: "wrap" }}>
        <div style={{ flex: "1 1 150px" }}>
          <label className="form-label">Input Tokens</label>
          <input
            type="number"
            className="input"
            value={inputTokens}
            onChange={(e) => setInputTokens(Number(e.target.value))}
          />
        </div>
        <div style={{ flex: "1 1 150px" }}>
          <label className="form-label">Output Tokens</label>
          <input
            type="number"
            className="input"
            value={outputTokens}
            onChange={(e) => setOutputTokens(Number(e.target.value))}
          />
        </div>
        <div style={{ flex: "1 1 180px" }}>
          <label className="form-label">Region</label>
          <select className="select" value={region} onChange={(e) => setRegion(e.target.value)}>
            <option value="global_average">Global Average</option>
            <option value="us_oregon">US Oregon (Clean)</option>
            <option value="us_virginia">US Virginia</option>
            <option value="eu_sweden">EU Sweden (Very Clean)</option>
            <option value="eu_ireland">EU Ireland</option>
            <option value="india">India (Coal Heavy)</option>
          </select>
        </div>
        <button className="btn btn-primary" onClick={loadComparison}>
          Compare
        </button>
      </div>

      {/* Winner Banner */}
      {greenest && (
        <div
          className="glass-card animate-in"
          style={{
            marginBottom: 20,
            background: "linear-gradient(135deg, rgba(16,185,129,0.1), rgba(16,185,129,0.02))",
            border: "1px solid rgba(16,185,129,0.2)",
            display: "flex",
            alignItems: "center",
            gap: 16,
          }}
        >
          <Award size={32} color="#34d399" />
          <div>
            <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", fontWeight: 600 }}>
              Most Sustainable Choice
            </div>
            <div style={{ fontSize: "1.1rem", fontWeight: 700, color: "var(--green-400)" }}>
              {models.find((m) => m.model_id === greenest)?.display_name || greenest}
            </div>
          </div>
        </div>
      )}

      {/* Charts */}
      <div className="charts-grid">
        {/* Energy Bar Chart */}
        <div className="chart-card animate-in">
          <h3>Energy per Request (Wh)</h3>
          <div style={{ height: 320 }}>
            <ResponsiveContainer>
              <BarChart data={barData} layout="vertical" margin={{ left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                <XAxis type="number" stroke="#64748b" tick={{ fontSize: 10 }} />
                <YAxis dataKey="name" type="category" width={110} stroke="#64748b" tick={{ fontSize: 11 }} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="energy" radius={[0, 4, 4, 0]} barSize={16}>
                  {barData.map((entry, i) => (
                    <Cell key={i} fill={PROVIDER_COLORS[entry.provider] || "#64748b"} fillOpacity={0.8} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Quality vs Energy Scatter */}
        <div className="chart-card animate-in">
          <h3>Quality vs Energy Trade-off</h3>
          <p style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: -12, marginBottom: 12 }}>
            Top-left = best (high quality, low energy)
          </p>
          <div style={{ height: 300 }}>
            <ResponsiveContainer>
              <ScatterChart margin={{ bottom: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                <XAxis dataKey="x" name="Energy (mWh)" stroke="#64748b" tick={{ fontSize: 10 }} label={{ value: "Energy (mWh)", position: "bottom", fill: "#64748b", fontSize: 10 }} />
                <YAxis dataKey="y" name="Quality" stroke="#64748b" tick={{ fontSize: 10 }} domain={[60, 100]} />
                <ZAxis dataKey="z" range={[40, 200]} />
                <Tooltip
                  content={({ active, payload }) => {
                    if (!active || !payload?.length) return null;
                    const d = payload[0]?.payload;
                    return (
                      <div className="custom-tooltip">
                        <div style={{ fontWeight: 700, color: "var(--text-primary)" }}>{d?.name}</div>
                        <div className="value">Quality: {d?.y}</div>
                        <div className="value">Energy: {d?.x?.toFixed(3)} mWh</div>
                      </div>
                    );
                  }}
                />
                <Scatter data={scatterData} fill="#10b981">
                  {scatterData.map((entry, i) => (
                    <Cell key={i} fill={PROVIDER_COLORS[entry.provider] || "#64748b"} />
                  ))}
                </Scatter>
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Full Ranking Table */}
      <div className="table-card animate-in" style={{ marginTop: 20 }}>
        <h3>Full Sustainability Ranking</h3>
        <table className="data-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Model</th>
              <th>Provider</th>
              <th>Quality</th>
              <th>Energy</th>
              <th>CO₂</th>
              <th>Cost</th>
              <th>Score</th>
            </tr>
          </thead>
          <tbody>
            {models.map((m, i) => (
              <tr key={m.model_id}>
                <td>
                  <span className={`model-rank ${i === 0 ? "gold" : i === 1 ? "silver" : i === 2 ? "bronze" : "normal"}`}>
                    {i + 1}
                  </span>
                </td>
                <td style={{ color: "var(--text-primary)", fontWeight: 600 }}>
                  {m.display_name}
                </td>
                <td>
                  <span className="badge" style={{ background: `${PROVIDER_COLORS[m.provider]}22`, color: PROVIDER_COLORS[m.provider] }}>
                    {m.provider}
                  </span>
                </td>
                <td style={{ fontFamily: "var(--font-mono)" }}>{m.quality_score}</td>
                <td style={{ fontFamily: "var(--font-mono)" }}>{m.energy_wh?.toFixed(6)}</td>
                <td style={{ fontFamily: "var(--font-mono)" }}>{m.co2_g?.toFixed(6)}g</td>
                <td style={{ fontFamily: "var(--font-mono)" }}>${m.cost_usd?.toFixed(4)}</td>
                <td>
                  <span style={{ color: "var(--green-400)", fontWeight: 700, fontFamily: "var(--font-mono)" }}>
                    {m.sustainability_score?.toLocaleString()}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
