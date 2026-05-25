import { useState, useEffect } from "react";
import { Wallet, Plus, AlertTriangle, CheckCircle, Clock } from "lucide-react";
import { getBudget, setBudget } from "../utils/api";

export default function BudgetPage() {
  const [budgets, setBudgets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [project, setProject] = useState("default");
  const [showForm, setShowForm] = useState(false);

  // Form state
  const [formProject, setFormProject] = useState("default");
  const [formPeriod, setFormPeriod] = useState("daily");
  const [formLimit, setFormLimit] = useState(100);

  useEffect(() => {
    loadBudgets();
  }, [project]);

  async function loadBudgets() {
    setLoading(true);
    try {
      const data = await getBudget(project);
      setBudgets(data.budgets || []);
    } catch (err) {
      console.error("Budget load failed:", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateBudget(e) {
    e.preventDefault();
    try {
      await setBudget(formProject, formPeriod, Number(formLimit));
      setShowForm(false);
      setProject(formProject);
      await loadBudgets();
    } catch (err) {
      console.error("Create budget failed:", err);
    }
  }

  function getStatusColor(status) {
    if (status === "exceeded") return "red";
    if (status === "warning") return "amber";
    return "green";
  }

  function getStatusIcon(status) {
    if (status === "exceeded") return AlertTriangle;
    if (status === "warning") return Clock;
    return CheckCircle;
  }

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner" />
        Loading budgets...
      </div>
    );
  }

  return (
    <div>
      <div className="page-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h2>Carbon Budget</h2>
          <p>Set and track CO₂ emission limits for your AI usage</p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <select
            className="select"
            style={{ width: "auto" }}
            value={project}
            onChange={(e) => setProject(e.target.value)}
          >
            <option value="default">Default</option>
            <option value="chatbot">Chatbot</option>
            <option value="research">Research</option>
            <option value="fraud-detection">Fraud Detection</option>
            <option value="document-processing">Document Processing</option>
          </select>
          <button className="btn btn-primary" onClick={() => setShowForm(!showForm)}>
            <Plus size={16} /> New Budget
          </button>
        </div>
      </div>

      {/* Create Budget Form */}
      {showForm && (
        <div className="glass-card animate-in" style={{ marginBottom: 24 }}>
          <h3 style={{ fontSize: "0.95rem", fontWeight: 600, marginBottom: 16 }}>Create Budget</h3>
          <form onSubmit={handleCreateBudget} style={{ display: "flex", gap: 16, alignItems: "flex-end", flexWrap: "wrap" }}>
            <div style={{ flex: "1 1 160px" }}>
              <label className="form-label">Project</label>
              <input className="input" value={formProject} onChange={(e) => setFormProject(e.target.value)} />
            </div>
            <div style={{ flex: "1 1 140px" }}>
              <label className="form-label">Period</label>
              <select className="select" value={formPeriod} onChange={(e) => setFormPeriod(e.target.value)}>
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
              </select>
            </div>
            <div style={{ flex: "1 1 140px" }}>
              <label className="form-label">CO₂ Limit (grams)</label>
              <input className="input" type="number" min="1" value={formLimit} onChange={(e) => setFormLimit(e.target.value)} />
            </div>
            <button className="btn btn-primary" type="submit">Create</button>
            <button className="btn btn-ghost" type="button" onClick={() => setShowForm(false)}>Cancel</button>
          </form>
        </div>
      )}

      {/* Budget Cards */}
      {budgets.length === 0 ? (
        <div className="glass-card" style={{ textAlign: "center", padding: 60 }}>
          <Wallet size={48} color="var(--text-muted)" style={{ marginBottom: 16 }} />
          <h3 style={{ color: "var(--text-secondary)", fontWeight: 600 }}>No budgets configured</h3>
          <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginTop: 8 }}>
            Click "New Budget" to set your first carbon limit.
          </p>
        </div>
      ) : (
        <div className="budget-grid">
          {budgets.map((b, i) => {
            const color = getStatusColor(b.status);
            const StatusIcon = getStatusIcon(b.status);
            const pct = Math.min(b.usage_percent, 100);

            return (
              <div key={`${b.period}-${i}`} className="budget-card animate-in">
                <div className="budget-header">
                  <div className="budget-title">
                    {b.period} Budget
                  </div>
                  <span className={`badge ${color}`}>
                    <StatusIcon size={12} />
                    {b.status}
                  </span>
                </div>

                <div className="budget-pct" style={{
                  color: color === "green" ? "var(--green-400)" : color === "amber" ? "var(--amber-400)" : "var(--red-400)"
                }}>
                  {b.usage_percent}%
                </div>

                <div className="progress-bar" style={{ marginBottom: 16 }}>
                  <div
                    className={`progress-fill ${color}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>

                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                  <div>
                    <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>Used</div>
                    <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.9rem", fontWeight: 600 }}>
                      {b.co2_used_g.toFixed(2)}g
                    </div>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em" }}>Limit</div>
                    <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.9rem", fontWeight: 600 }}>
                      {b.co2_limit_g}g
                    </div>
                  </div>
                </div>

                <div style={{ display: "flex", justifyContent: "space-between", paddingTop: 12, borderTop: "1px solid var(--border-subtle)" }}>
                  <div>
                    <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>Remaining</div>
                    <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.82rem", color: "var(--green-400)" }}>
                      {b.co2_remaining_g.toFixed(2)}g
                    </div>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>Calls</div>
                    <div style={{ fontFamily: "var(--font-mono)", fontSize: "0.82rem" }}>
                      {b.call_count}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
