import { useState, useEffect } from "react";
import "./App.css";
import Sidebar from "./components/Sidebar";
import DashboardPage from "./components/DashboardPage";
import ModelsPage from "./components/ModelsPage";
import BudgetPage from "./components/BudgetPage";
import SimulatorPage from "./components/SimulatorPage";
import SettingsPage from "./components/SettingsPage";
import LandingPage from "./components/LandingPage";
import AuthPage from "./components/AuthPage";
import { getStoredUser, clearAuth } from "./utils/auth";

const PAGES = {
  dashboard: DashboardPage,
  models: ModelsPage,
  budget: BudgetPage,
  simulator: SimulatorPage,
  settings: SettingsPage,
};

export default function App() {
  // "landing" → "auth" → "app"
  const [screen, setScreen] = useState("landing");
  const [user, setUser] = useState(null);
  const [activePage, setActivePage] = useState("dashboard");

  // Restore session on mount
  useEffect(() => {
    const stored = getStoredUser();
    if (stored) {
      setUser(stored);
      setScreen("app");
    }
  }, []);

  const handleAuth = (userData) => {
    setUser(userData);
    setScreen("app");
  };

  const handleLogout = () => {
    clearAuth();
    setUser(null);
    setScreen("landing");
    setActivePage("dashboard");
  };

  const handleGoLanding = () => {
    setScreen("landing");
  };

  // Landing page
  if (screen === "landing") {
    return (
      <LandingPage
        user={user}
        onLaunch={() => {
          if (user) setScreen("app");
          else setScreen("auth");
        }}
        onDemo={async () => {
          const { loginDemo } = await import("./utils/auth");
          const data = await loginDemo();
          handleAuth(data.user);
        }}
      />
    );
  }

  // Auth page
  if (screen === "auth") {
    return <AuthPage onAuth={handleAuth} onGoHome={() => setScreen("landing")} />;
  }

  // App (dashboard)
  const PageComponent = PAGES[activePage] || DashboardPage;

  return (
    <div className="app-layout">
      {/* Demo banner */}
      {user?.is_demo && (
        <div className="demo-banner" style={{ position: "fixed", top: 0, left: 0, right: 0, zIndex: 200, borderRadius: 0 }}>
          <span>🎭 You're viewing the demo dashboard with simulated data.</span>
          <a href="#" onClick={(e) => { e.preventDefault(); handleLogout(); }}>
            Sign up for your own →
          </a>
        </div>
      )}

      <Sidebar
        active={activePage}
        onNavigate={setActivePage}
        onGoHome={handleLogout}
        onGoLanding={handleGoLanding}
        user={user}
      />
      <main className="main-content" style={user?.is_demo ? { paddingTop: "72px" } : {}}>
        <PageComponent key={activePage} user={user} />
      </main>
    </div>
  );
}