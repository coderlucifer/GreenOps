import { useState } from "react";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
  Legend,
} from "recharts";

const OPTIMIZATIONS = [
  { key: "pruning", label: "Pruning" },
  { key: "quantization", label: "Quantization" },
  { key: "distillation", label: "Distillation" },
  { key: "caching", label: "Caching" },
  { key: "batching", label: "Batching" },
  { key: "compilation", label: "Compilation" },
];
const WORKLOAD_PROFILES = {
  chatbot: ["quantization", "compilation"],
  fraud: ["compilation"],
  batch: ["batching", "quantization", "compilation"],
  research: [
    "pruning",
    "quantization",
    "distillation",
    "caching",
    "batching",
    "compilation",
  ],
};

export default function App() {
  const [energy, setEnergy] = useState(1000);
  const [selected, setSelected] = useState([
    "quantization",
    "batching",
    "compilation",
  ]);
  const [workloadType, setWorkloadType] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const isAggressive =
    selected.includes("pruning") ||
    selected.includes("distillation");
  const optimizationMode = isAggressive ? "Aggressive" : "Balanced";
  const toggleOptimization = (key) => {
    setSelected((prev) =>
      prev.includes(key)
        ? prev.filter((o) => o !== key)
        : [...prev, key]
    );
  };

  const runGreenOps = async () => {
    setLoading(true);
    setError("");
    setResult(null);

    try {
      const res = await fetch("http://localhost:8000/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          baseline_energy_wh: Number(energy),
          optimizations: selected,
        }),
      });

      if (!res.ok) {
        throw new Error("Backend error");
      }

      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError("Could not connect to GreenOps engine");
    } finally {
      setLoading(false);
    }
  };

  const chartData =
  result && [
    {
      name: "Energy (Wh)",
      Baseline: result.baseline_energy_wh,
      Optimized: result.optimized_energy_wh,
    },
    {
      name: "CO₂ (g)",
      Baseline: result.baseline_co2_g,
      Optimized: result.optimized_co2_g,
    },
    {
      name: "Water (mL)",
      Baseline: result.baseline_water_ml,
      Optimized: result.optimized_water_ml,
    },
  ]; 

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="bg-white w-full max-w-3xl rounded-xl shadow-lg p-8 space-y-6">
        {/* HEADER */}
        <div>
          <h1 className="text-3xl font-bold text-emerald-600">
            GreenOps 
          </h1>
          <p className="text-slate-600 mt-1">
            Measure & reduce the environmental impact of GenAI workloads
          </p>
        </div>

        {/* INPUT */}
        <div>
          <label className="block font-medium mb-1">
            Baseline Energy (Wh)
          </label>
          <input
            type="number"
            value={energy}
            onChange={(e) => setEnergy(e.target.value)}
            className="w-full border rounded-md px-3 py-2"
          />
        </div>
        <div>
  <label className="block font-medium mb-1">
    Workload Type
  </label>
  <select
    value={workloadType}
    onChange={(e) => {
      const type = e.target.value;
      setWorkloadType(type);

      if (WORKLOAD_PROFILES[type]) {
        setSelected(WORKLOAD_PROFILES[type]);
      }
    }}
    className="w-full border rounded-md px-3 py-2"
  >
    <option value="">Select workload type</option>
    <option value="chatbot">Real-time Chatbot</option>
    <option value="fraud">Fraud Detection</option>
    <option value="batch">Batch Analytics</option>
    <option value="research">Internal R&D</option>
  </select>
</div>
        {/* OPTIMIZATIONS */}
        <div>
          <p className="font-medium mb-2">Optimization Layers</p>
          <div className="grid grid-cols-2 gap-2">
            {OPTIMIZATIONS.map((opt) => (
              <label
                key={opt.key}
                className="flex items-center gap-2 border rounded-md px-3 py-2 cursor-pointer"
              >
                <input
                  type="checkbox"
                  checked={selected.includes(opt.key)}
                  onChange={() => toggleOptimization(opt.key)}
                />
                {opt.label}
              </label>
            ))}
          </div>
        </div>
        {selected.length > 0 && (
        <div
          className={`mt-4 px-4 py-2 rounded-md text-sm font-semibold ${
            optimizationMode === "Aggressive"
              ? "bg-red-100 text-red-700"
              : "bg-emerald-100 text-emerald-700"
          }`}
        >
          {optimizationMode === "Aggressive"
            ? "🔴 Aggressive Optimization Strategy – Maximum reduction with potential accuracy/latency trade-offs."
            : "🟢 Balanced Optimization Strategy – Sustainable reduction with minimal performance risk."}
        </div>
      )}
        {/* BUTTON */}
        <button
          onClick={runGreenOps}
          disabled={loading}
          className="w-full bg-emerald-600 text-white py-2 rounded-md font-semibold hover:bg-emerald-700 transition"
        >
          {loading ? "Running GreenOps..." : "Run GreenOps"}
        </button>

        {/* ERROR */}
        {error && (
          <p className="text-red-600 font-medium">{error}</p>
        )}

        {/* RESULTS */}
        {result && (
          <div className="grid grid-cols-2 gap-4 pt-4">
            <Metric
              label="Energy Saved"
              value={`${result.energy_saved_wh} Wh`}
            />
            <Metric
              label="CO₂ Saved"
              value={`${result.co2_saved_g} g`}
            />
            <Metric
              label="Water Saved"
              value={`${result.water_saved_ml} mL`}
            />
            <Metric
              label="Reduction"
              value={`${result.reduction_percent}%`}
            />

            <div className="col-span-2 text-sm text-slate-600">
              <strong>Applied:</strong>{" "}
              {result.applied_optimizations.join(", ")}
            </div>
          </div>
        )}
        {result && (
        <div className="mt-8">
          <h2 className="text-lg font-semibold mb-4">
            Before vs After Comparison
          </h2>

          <div className="w-full h-80">
            <ResponsiveContainer>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="Baseline" fill="#ef4444" />
                <Bar dataKey="Optimized" fill="#10b981" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
      </div>
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div className="border rounded-lg p-4 text-center">
      <p className="text-sm text-slate-500">{label}</p>
      <p className="text-xl font-bold text-emerald-700">{value}</p>
    </div>
  );
}