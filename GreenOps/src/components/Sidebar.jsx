import {
  LayoutDashboard,
  Cpu,
  Wallet,
  FlaskConical,
  Leaf,
  LogOut,
  User,
  Settings,
} from "lucide-react";

const NAV_ITEMS = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "models", label: "Model Comparison", icon: Cpu },
  { id: "budget", label: "Carbon Budget", icon: Wallet },
  { id: "simulator", label: "Simulator", icon: FlaskConical },
  { id: "settings", label: "Settings", icon: Settings },
];

export default function Sidebar({ active, onNavigate, onGoHome, onGoLanding, user }) {
  return (
    <aside className="sidebar">
      <div 
        className="sidebar-logo" 
        style={{ cursor: "pointer" }} 
        onClick={() => active === "dashboard" ? onGoLanding() : onNavigate("dashboard")}
      >
        <h1>
          <Leaf size={20} style={{ display: "inline", marginRight: 6, verticalAlign: "middle" }} />
          GreenOps
        </h1>
        <p>AI Sustainability Platform</p>
      </div>

      <nav className="sidebar-nav">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          return (
            <button
              key={item.id}
              className={`nav-item ${active === item.id ? "active" : ""}`}
              onClick={() => onNavigate(item.id)}
            >
              <Icon size={18} />
              {item.label}
            </button>
          );
        })}
      </nav>

      <div className="sidebar-footer" style={{ borderTop: "1px solid var(--border-subtle)", paddingTop: "12px", display: "flex", flexDirection: "column", gap: "8px" }}>
        {/* User info */}
        {user && (
          <div style={{ padding: "8px 16px", display: "flex", alignItems: "center", gap: "10px" }}>
            <div style={{
              width: 32, height: 32, borderRadius: "50%",
              background: "linear-gradient(135deg, var(--green-500), var(--blue-500))",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: "0.8rem", fontWeight: 700, flexShrink: 0,
            }}>
              {user.name ? user.name[0].toUpperCase() : <User size={14} />}
            </div>
            <div style={{ overflow: "hidden" }}>
              <div style={{ fontSize: "0.85rem", fontWeight: 600, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                {user.name || "User"}
              </div>
              <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                {user.email}
              </div>
            </div>
          </div>
        )}

        <button
          className="nav-item"
          onClick={onGoHome}
          style={{ color: "var(--text-muted)" }}
        >
          <LogOut size={18} />
          Sign Out
        </button>

        <div className="sidebar-status">
          <span className="status-dot" />
          Engine connected
        </div>
      </div>
    </aside>
  );
}
