import { useState, useEffect } from "react";
import { Key, Plus, Trash2, ShieldAlert, Code2, Copy, Check, Folder, Bell, Save } from "lucide-react";
import { getProfile } from "../utils/auth";
import { createApiKey, revokeApiKey, getProjects, createProject, deleteProject, updateProjectWebhook } from "../utils/api";

export default function SettingsPage({ user }) {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [newKeyLabel, setNewKeyLabel] = useState("");
  const [creating, setCreating] = useState(false);
  const [copiedKey, setCopiedKey] = useState(null);
  const [projects, setProjects] = useState([]);
  const [newProjectName, setNewProjectName] = useState("");
  const [webhookUrls, setWebhookUrls] = useState({});

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await getProfile();
      setProfile(data);
      const projData = await getProjects();
      setProjects(projData);
      const urls = {};
      projData.forEach(p => { urls[p.name] = p.webhook_url || ""; });
      setWebhookUrls(urls);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateKey = async (e) => {
    e.preventDefault();
    if (!newKeyLabel.trim() || creating) return;

    setCreating(true);
    try {
      await createApiKey(newKeyLabel);
      setNewKeyLabel("");
      await loadData();
    } catch (err) {
      alert(err.message || "Failed to create API key");
    } finally {
      setCreating(false);
    }
  };

  const handleRevoke = async (keyId) => {
    if (!window.confirm("Are you sure you want to revoke this API key? This action cannot be undone.")) {
      return;
    }
    
    try {
      await revokeApiKey(keyId);
      await loadData();
    } catch (err) {
      alert(err.message || "Failed to revoke API key");
    }
  };

  const handleCreateProject = async (e) => {
    e.preventDefault();
    if (!newProjectName.trim() || creating) return;
    setCreating(true);
    try {
      await createProject(newProjectName);
      setNewProjectName("");
      await loadData();
    } catch (err) {
      alert(err.message || "Failed to create project");
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteProject = async (name) => {
    if (!window.confirm(`Are you sure you want to delete project '${name}'?`)) return;
    try {
      await deleteProject(name);
      await loadData();
    } catch (err) {
      alert(err.message || "Failed to delete project");
    }
  };

  const handleUpdateWebhook = async (name) => {
    try {
      await updateProjectWebhook(name, webhookUrls[name]);
      alert("Webhook updated successfully!");
    } catch (err) {
      alert(err.message || "Failed to update webhook");
    }
  };

  const isDemo = profile?.is_demo === 1;
  const isAdmin = profile?.role === "admin";

  const copyToClipboard = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(id);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  if (loading) {
    return <div className="loading-state">Loading settings...</div>;
  }

  return (
    <div className="page-container animate-in">
      <header className="page-header">
        <div>
          <h1 className="page-title">Settings & API Keys</h1>
          <p className="page-subtitle">Manage your account and API access credentials</p>
        </div>
      </header>

      {isDemo && (
        <div className="badge yellow" style={{ padding: "12px 16px", marginBottom: "24px", fontSize: "0.95rem", display: "flex", gap: "12px", alignItems: "center" }}>
          <ShieldAlert size={20} />
          <span><strong>Read-only Mode:</strong> You are using a demo account. Creating or revoking API keys is disabled.</span>
        </div>
      )}

      <div className="settings-grid" style={{ display: "grid", gap: "24px", gridTemplateColumns: "1fr" }}>
        
        {/* Profile Card */}
        <div className="card">
          <h2 style={{ fontSize: "1.1rem", marginBottom: "16px", display: "flex", alignItems: "center", gap: "8px" }}>
            Profile
          </h2>
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            <div>
              <label style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>Name</label>
              <div style={{ fontWeight: 600 }}>{profile?.name}</div>
            </div>
            <div>
              <label style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>Email</label>
              <div>{profile?.email}</div>
            </div>
            <div>
              <label style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>Role</label>
              <div>
                <span className={`badge ${isAdmin ? 'green' : 'blue'}`}>
                  {isAdmin ? "Admin" : "Viewer"}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* SDK Integration Card */}
        <div className="card">
          <h2 style={{ fontSize: "1.1rem", marginBottom: "16px", display: "flex", alignItems: "center", gap: "8px" }}>
            <Code2 size={20} className="text-blue" />
            Quick Integration
          </h2>
          <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem", marginBottom: "16px" }}>
            Use the transparent proxy to track OpenAI calls automatically. Just change your <code style={{ color: "var(--green-400)" }}>base_url</code>.
          </p>
          <pre style={{ background: "var(--bg-app)", padding: "16px", borderRadius: "8px", overflowX: "auto", fontSize: "0.85rem", border: "1px solid var(--border-subtle)" }}>
            <code>
<span style={{ color: "#c678dd" }}>import</span> openai<br/><br/>
client = openai.OpenAI(<br/>
&nbsp;&nbsp;&nbsp;&nbsp;api_key=<span style={{ color: "#98c379" }}>"sk-your-openai-key"</span>,<br/>
&nbsp;&nbsp;&nbsp;&nbsp;base_url=<span style={{ color: "#98c379" }}>"http://localhost:8000/proxy/openai/v1"</span>,<br/>
&nbsp;&nbsp;&nbsp;&nbsp;default_headers={"{"}<br/>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style={{ color: "#98c379" }}>"x-api-key"</span>: <span style={{ color: "#98c379" }}>"{profile?.api_keys?.[0]?.key || "YOUR_GREENOPS_KEY"}"</span><br/>
&nbsp;&nbsp;&nbsp;&nbsp;{"}"}<br/>
)
            </code>
          </pre>
        </div>

        {/* API Keys Card */}
        <div className="card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
            <h2 style={{ fontSize: "1.1rem", display: "flex", alignItems: "center", gap: "8px", margin: 0 }}>
              <Key size={20} className="text-green" />
              API Keys
            </h2>
          </div>

          <div style={{ marginBottom: "24px" }}>
            <form onSubmit={handleCreateKey} style={{ display: "flex", gap: "12px" }}>
              <input
                type="text"
                placeholder="Key label (e.g., Production, Local Dev)"
                value={newKeyLabel}
                onChange={(e) => setNewKeyLabel(e.target.value)}
                disabled={isDemo || creating}
                style={{
                  flex: 1, padding: "10px 14px", background: "var(--bg-app)", 
                  border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-sm)",
                  color: "white"
                }}
              />
              <button 
                type="submit" 
                className="btn btn-primary" 
                disabled={!newKeyLabel.trim() || isDemo || creating}
                style={{ padding: "10px 16px" }}
              >
                <Plus size={16} /> Create Key
              </button>
            </form>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {profile?.api_keys?.map((key) => (
              <div key={key.id} style={{ 
                background: "var(--bg-app)", border: "1px solid var(--border-subtle)", 
                borderRadius: "var(--radius-sm)", padding: "16px",
                display: "flex", justifyContent: "space-between", alignItems: "center"
              }}>
                <div>
                  <div style={{ fontWeight: 600, marginBottom: "4px" }}>{key.label}</div>
                  <div style={{ 
                    fontFamily: "monospace", color: "var(--green-400)", 
                    background: "rgba(16, 185, 129, 0.1)", padding: "4px 8px", 
                    borderRadius: "4px", fontSize: "0.85rem", display: "inline-block" 
                  }}>
                    {key.key}
                  </div>
                  <div style={{ color: "var(--text-muted)", fontSize: "0.8rem", marginTop: "8px" }}>
                    Created: {new Date(key.created_at).toLocaleDateString()}
                    {key.last_used_at && ` • Last used: ${new Date(key.last_used_at).toLocaleDateString()}`}
                  </div>
                </div>
                <div style={{ display: "flex", gap: "8px" }}>
                  <button 
                    className="btn btn-ghost" 
                    onClick={() => copyToClipboard(key.key, key.id)}
                    style={{ padding: "8px" }}
                    title="Copy key"
                  >
                    {copiedKey === key.id ? <Check size={18} className="text-green" /> : <Copy size={18} />}
                  </button>
                  <button 
                    className="btn btn-ghost" 
                    onClick={() => handleRevoke(key.id)}
                    disabled={isDemo || profile.api_keys.length === 1}
                    style={{ padding: "8px", color: profile.api_keys.length === 1 ? "var(--text-muted)" : "var(--red-400)" }}
                    title={profile.api_keys.length === 1 ? "Cannot delete your only API key" : "Revoke key"}
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>
            ))}
            {profile?.api_keys?.length === 0 && (
              <div style={{ color: "var(--text-muted)", fontSize: "0.9rem", textAlign: "center", padding: "20px" }}>
                No API keys found.
              </div>
            )}
          </div>
        </div>

        {/* Projects Card */}
        <div className="card">
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "20px" }}>
            <h2 style={{ fontSize: "1.1rem", display: "flex", alignItems: "center", gap: "8px", margin: 0 }}>
              <Folder size={20} className="text-blue" />
              Projects
            </h2>
          </div>

          {isAdmin && (
            <div style={{ marginBottom: "24px" }}>
              <form onSubmit={handleCreateProject} style={{ display: "flex", gap: "12px" }}>
                <input
                  type="text"
                  placeholder="New project name"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  disabled={isDemo || creating}
                  style={{
                    flex: 1, padding: "10px 14px", background: "var(--bg-app)", 
                    border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-sm)",
                    color: "white"
                  }}
                />
                <button 
                  type="submit" 
                  className="btn btn-primary" 
                  disabled={!newProjectName.trim() || isDemo || creating}
                  style={{ padding: "10px 16px" }}
                >
                  <Plus size={16} /> Create Project
                </button>
              </form>
            </div>
          )}

          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {projects?.map((proj) => (
              <div key={proj.id} style={{ 
                background: "var(--bg-app)", border: "1px solid var(--border-subtle)", 
                borderRadius: "var(--radius-sm)", padding: "16px",
                display: "flex", justifyContent: "space-between", alignItems: "center"
              }}>
                <div>
                  <div style={{ fontWeight: 600 }}>{proj.name}</div>
                  <div style={{ color: "var(--text-muted)", fontSize: "0.8rem", marginTop: "4px" }}>
                    Created: {new Date(proj.created_at).toLocaleDateString()}
                  </div>
                  {isAdmin && (
                    <div style={{ marginTop: "12px", display: "flex", gap: "8px" }}>
                      <input 
                        type="url"
                        placeholder="https://your-webhook-url.com"
                        value={webhookUrls[proj.name] || ""}
                        onChange={(e) => setWebhookUrls({...webhookUrls, [proj.name]: e.target.value})}
                        disabled={isDemo}
                        style={{
                          flex: 1, padding: "6px 10px", background: "rgba(255,255,255,0.05)", 
                          border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-sm)",
                          color: "white", fontSize: "0.85rem"
                        }}
                      />
                      <button 
                        className="btn btn-primary" 
                        onClick={() => handleUpdateWebhook(proj.name)}
                        disabled={isDemo}
                        style={{ padding: "6px 12px", fontSize: "0.85rem" }}
                      >
                        <Save size={14} /> Save
                      </button>
                    </div>
                  )}
                </div>
                {isAdmin && (
                  <div style={{ display: "flex", gap: "8px" }}>
                    <button 
                      className="btn btn-ghost" 
                      onClick={() => handleDeleteProject(proj.name)}
                      disabled={isDemo || proj.name === "default"}
                      style={{ padding: "8px", color: proj.name === "default" ? "var(--text-muted)" : "var(--red-400)" }}
                      title={proj.name === "default" ? "Cannot delete default project" : "Delete project"}
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                )}
              </div>
            ))}
            {projects?.length === 0 && (
              <div style={{ color: "var(--text-muted)", fontSize: "0.9rem", textAlign: "center", padding: "20px" }}>
                No projects found.
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
