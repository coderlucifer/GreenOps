import { useState } from "react";
import { FlaskConical, Zap, Cloud, Droplets, TrendingDown, AlertTriangle, CheckCircle, DollarSign } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  Legend,
  Cell,
} from "recharts";
import { runSimulator } from "../utils/api";

const OPTIMIZATIONS = [
  { key: "pruning",      label: "Pruning",      desc: "Remove redundant parameters", aggressive: true },
  { key: "quantization", label: "Quantization", desc: "Reduce numerical precision (FP32 → INT8)", aggressive: false },
  { key: "distillation", label: "Distillation", desc: "Create smaller student model", aggressive: true },
  { key: "caching",      label: "Caching",      desc: "Avoid repeated inference computation", aggressive: false },
  { key: "batching",     label: "Batching",     desc: "Combine multiple requests", aggressive: false },
  { key: "compilation",  label: "Compilation",  desc: "Optimize execution graphs", aggressive: false },
];

const WORKLOAD_PROFILES = {
  "": [],
  chatbot:  ["quantization", "compilation"],
  fraud:    ["compilation"],
  batch:    ["batching", "quantization", "compilation"],
  research: ["pruning", "quantization", "distillation", "caching", "batching", "compilation"],
};

export default function SimulatorPage() {
  const [energy, setEnergy] = useState(1000);
  const [selected, setSelected] = useState(["quantization", "batching", "compilation"]);
  const [workload, setWorkload] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const isAggressive = selected.includes("pruning") || selected.includes("distillation");

  const toggleOpt = (key) => {
    setSelected((prev) =>
      prev.includes(key) ? prev.filter((o) => o !== key) : [...prev, key]
    );
  };

  async function handleRun() {
    if (selected.length === 0) {
      setError("Select at least one optimization");
      return;
    }
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const data = await runSimulator(Number(energy), selected);
      setResult(data);
    } catch (err) {
      setError(err.message || "Simulation failed");
    } finally {
      setLoading(false);
    }
  }

  const chartData = result
    ? [
        { name: "Energy (Wh)", Baseline: result.baseline_energy_wh, Optimized: result.optimized_energy_wh },
        { name: "CO₂ (g)", Baseline: result.baseline_co2_g, Optimized: result.optimized_co2_g },
        { name: "Water (mL)", Baseline: result.baseline_water_ml, Optimized: result.optimized_water_ml },
      ]
    : [];

  return (
    <div>
      <div className="page-header">
        <h2>Optimization Simulator</h2>
        <p>Simulate sustainability optimization strategies before deployment</p>
      </div>

      {/* Input Section */}
      <div className="glass-card animate-in" style={{ marginBottom: 20 }}>
        <div style={{ display: "flex", gap: 20, marginBottom: 20, flexWrap: "wrap" }}>
          <div style={{ flex: "1 1 200px" }}>
            <label className="form-label">Baseline Energy (Wh)</label>
            <input
              type="number"
              className="input"
              value={energy}
              onChange={(e) => setEnergy(e.target.value)}
              min="1"
            />
          </div>
          <div style={{ flex: "1 1 200px" }}>
            <label className="form-label">Workload Type</label>
            <select
              className="select"
              value={workload}
              onChange={(e) => {
                const w = e.target.value;
                setWorkload(w);
                if (WORKLOAD_PROFILES[w]) setSelected(WORKLOAD_PROFILES[w]);
              }}
            >
              <option value="">Select workload type</option>
              <option value="chatbot">Real-time Chatbot</option>
              <option value="fraud">Fraud Detection</option>
              <option value="batch">Batch Analytics</option>
              <option value="research">Internal R&D</option>
            </select>
          </div>
        </div>

        {/* Optimization Layers */}
        <label className="form-label" style={{ marginBottom: 10 }}>Optimization Layers</label>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))", gap: 8, marginBottom: 16 }}>
          {OPTIMIZATIONS.map((opt) => (
            <label
              key={opt.key}
              className={`opt-toggle ${selected.includes(opt.key) ? "active" : ""}`}
            >
              <input
                type="checkbox"
                checked={selected.includes(opt.key)}
                onChange={() => toggleOpt(opt.key)}
              />
              <div>
                <div style={{ fontWeight: 600 }}>
                  {opt.label}
                  {opt.aggressive && (
                    <AlertTriangle size={12} color="var(--amber-400)" style={{ marginLeft: 6, verticalAlign: "middle" }} />
                  )}
                </div>
                <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: 2 }}>
                  {opt.desc}
                </div>
              </div>
            </label>
          ))}
        </div>

        {/* Strategy Badge */}
        {selected.length > 0 && (
          <div
            style={{
              padding: "10px 16px",
              borderRadius: "var(--radius-sm)",
              marginBottom: 16,
              fontSize: "0.82rem",
              fontWeight: 600,
              display: "flex",
              alignItems: "center",
              gap: 8,
              background: isAggressive ? "rgba(239, 68, 68, 0.1)" : "rgba(16, 185, 129, 0.1)",
              border: `1px solid ${isAggressive ? "rgba(239, 68, 68, 0.2)" : "rgba(16, 185, 129, 0.2)"}`,
              color: isAggressive ? "var(--red-400)" : "var(--green-400)",
            }}
          >
            {isAggressive ? <AlertTriangle size={16} /> : <CheckCircle size={16} />}
            {isAggressive
              ? "Aggressive Strategy — Maximum reduction with potential accuracy/latency trade-offs"
              : "Balanced Strategy — Sustainable reduction with minimal performance risk"}
          </div>
        )}

        <button className="btn btn-primary" onClick={handleRun} disabled={loading} style={{ width: "100%" }}>
          <FlaskConical size={16} />
          {loading ? "Running Simulation..." : "Run Simulation"}
        </button>

        {error && (
          <div style={{ color: "var(--red-400)", marginTop: 12, fontSize: "0.85rem" }}>{error}</div>
        )}
      </div>

      {/* Results */}
      {result && (
        <>
          {/* Savings Metrics */}
          <div className="metrics-grid" style={{ marginBottom: 20 }}>
            <div className="metric-card green animate-in">
              <div className="metric-icon"><TrendingDown size={18} /></div>
              <div className="metric-label">Reduction</div>
              <div className="metric-value">{result.reduction_percent}%</div>
            </div>
            <div className="metric-card green animate-in">
              <div className="metric-icon"><Zap size={18} /></div>
              <div className="metric-label">Energy Saved</div>
              <div className="metric-value">{result.energy_saved_wh.toFixed(1)} Wh</div>
            </div>
            <div className="metric-card amber animate-in">
              <div className="metric-icon"><Cloud size={18} /></div>
              <div className="metric-label">CO₂ Saved</div>
              <div className="metric-value">{result.co2_saved_g.toFixed(2)} g</div>
            </div>
            <div className="metric-card cyan animate-in">
              <div className="metric-icon"><Droplets size={18} /></div>
              <div className="metric-label">Water Saved</div>
              <div className="metric-value">{result.water_saved_ml.toFixed(1)} mL</div>
            </div>
            <div className="metric-card purple animate-in">
              <div className="metric-icon"><DollarSign size={18} /></div>
              <div className="metric-label">Cost Saved</div>
              <div className="metric-value">${(result.cost_saved_usd || 0).toFixed(2)}</div>
            </div>
          </div>

          {/* Chart */}
          <div className="chart-card animate-in" style={{ marginBottom: 20 }}>
            <h3>Before vs After Comparison</h3>
            <div style={{ height: 320 }}>
              <ResponsiveContainer>
                <BarChart data={chartData} barGap={4}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                  <XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 12 }} />
                  <YAxis stroke="#64748b" tick={{ fontSize: 11 }} />
                  <Tooltip
                    contentStyle={{
                      background: "var(--bg-card)",
                      border: "1px solid var(--border-default)",
                      borderRadius: "var(--radius-sm)",
                    }}
                    labelStyle={{ color: "var(--text-muted)" }}
                    itemStyle={{ color: "var(--text-primary)" }}
                  />
                  <Legend />
                  <Bar dataKey="Baseline" fill="#ef4444" radius={[4, 4, 0, 0]} opacity={0.8} />
                  <Bar dataKey="Optimized" fill="#10b981" radius={[4, 4, 0, 0]} opacity={0.9} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Equivalencies */}
          {result.savings_equivalencies && Object.keys(result.savings_equivalencies).length > 0 && (
            <div className="table-card animate-in">
              <h3>💡 By optimizing, you save the equivalent of:</h3>
              <div className="equiv-grid" style={{ marginTop: 12 }}>
                {Object.entries(result.savings_equivalencies).map(([key, eq]) => (
                  <div key={key} className="equiv-card">
                    <div className="equiv-icon" style={{ fontSize: "1.5rem" }}>
                      {key.includes("car") ? "🚗" : key.includes("tree") ? "🌳" : key.includes("phone") ? "📱" : key.includes("water") ? "💧" : key.includes("led") ? "💡" : "🌍"}
                    </div>
                    <div className="equiv-text">{eq.label}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Applied optimizations */}
          <div style={{ marginTop: 16, fontSize: "0.82rem", color: "var(--text-muted)" }}>
            <strong style={{ color: "var(--text-secondary)" }}>Applied:</strong>{" "}
            {result.applied_optimizations.join(", ")}
          </div>
        </>
      )}
    </div>
  );
}
