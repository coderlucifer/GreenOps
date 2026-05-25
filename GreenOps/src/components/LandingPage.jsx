import { Terminal, Activity, Cpu, Wallet, FlaskConical, ArrowRight, Code2, Globe, Leaf, Zap } from "lucide-react";

export default function LandingPage({ onLaunch, onDemo, user }) {
  return (
    <div className="landing-page">
      {/* Navbar */}
      <header className="landing-nav">
        <button 
          className="landing-logo" 
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          style={{ background: "none", border: "none", cursor: "pointer", padding: 0, color: "inherit", fontFamily: "inherit" }}
        >
          <Leaf size={24} color="#10b981" />
          <span>GreenOps</span>
        </button>
        <div className="landing-nav-links">
          <a href="#features">Features</a>
          <a href="#developers">For Developers</a>
          <button className="btn btn-primary" onClick={onLaunch}>
            {user ? "Open Dashboard" : "Get Started"} <ArrowRight size={16} />
          </button>
          {!user && onDemo && (
            <button className="btn btn-ghost" onClick={onDemo}>
              <Zap size={16} /> Try Demo
            </button>
          )}
        </div>
      </header>

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-bg-glow"></div>
        <div className="hero-content animate-in" style={{ '--delay': '0ms' }}>
          <div className="badge green" style={{ marginBottom: 24, fontSize: '0.85rem' }}>
            <Globe size={14} style={{ marginRight: 6 }} />
            The AI Sustainability Platform
          </div>
          <h1 className="hero-title">
            Track, Measure, and Reduce<br />
            <span className="text-gradient">Your AI Carbon Footprint.</span>
          </h1>
          <p className="hero-subtitle">
            Every AI API call consumes energy and water. GreenOps makes this invisible cost visible. 
            Integrate in minutes, track every token, and optimize for a greener future.
          </p>
          <div className="hero-actions">
            <button className="btn btn-primary" style={{ padding: '12px 24px', fontSize: '1rem' }} onClick={onLaunch}>
              {user ? "Open Dashboard" : "Get Started — It's Free"}
            </button>
            {!user && (
              <button className="btn btn-ghost" style={{ padding: '12px 24px', fontSize: '1rem' }} onClick={onDemo}>
                <Zap size={18} style={{ marginRight: 8 }} />
                Live Demo
              </button>
            )}
            <a href="https://github.com/coderlucifer/GreenOps" target="_blank" className="btn btn-ghost" style={{ padding: '12px 24px', fontSize: '1rem' }}>
              <Code2 size={18} style={{ marginRight: 8 }} />
              View Source
            </a>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="features-section">
        <div className="section-header">
          <h2>Everything you need for AI Sustainability</h2>
          <p>A complete toolkit to monitor and optimize your generative AI workloads.</p>
        </div>
        
        <div className="features-grid">
          <div className="feature-card animate-in" style={{ '--delay': '100ms' }}>
            <div className="feature-icon"><Activity size={24} color="#3b82f6" /></div>
            <h3>Real-time Tracking</h3>
            <p>Monitor API calls, token usage, energy consumption (Wh), and CO₂ emissions (g) live on a beautiful dark-mode dashboard.</p>
          </div>
          
          <div className="feature-card animate-in" style={{ '--delay': '200ms' }}>
            <div className="feature-icon"><Cpu size={24} color="#10b981" /></div>
            <h3>Model Comparison</h3>
            <p>Compare 18+ leading AI models (GPT-4o, Claude, Llama) by sustainability score, balancing quality with environmental impact.</p>
          </div>
          
          <div className="feature-card animate-in" style={{ '--delay': '300ms' }}>
            <div className="feature-icon"><Wallet size={24} color="#f59e0b" /></div>
            <h3>Carbon Budgets</h3>
            <p>Set daily, weekly, or monthly carbon emission limits for different projects and get alerted before you exceed them.</p>
          </div>
          
          <div className="feature-card animate-in" style={{ '--delay': '400ms' }}>
            <div className="feature-icon"><FlaskConical size={24} color="#a855f7" /></div>
            <h3>Optimization Simulator</h3>
            <p>Test strategies like quantization, pruning, and batching to see potential energy and water savings before deployment.</p>
          </div>
        </div>
      </section>

      {/* Developer Section */}
      <section id="developers" className="dev-section">
        <div className="dev-content animate-in" style={{ '--delay': '500ms' }}>
          <h2>Zero-friction Integration</h2>
          <p>
            Drop the GreenOps SDK into your existing Python projects in seconds. 
            Use our transparent proxy or decorators to track automatically.
          </p>
          
          <div className="code-block-wrapper">
            <div className="code-header">
              <Terminal size={14} />
              <span>app.py</span>
            </div>
            <pre className="code-block">
              <code>
<span className="keyword">import</span> greenops<br/>
<br/>
<span className="comment"># Simply add this decorator</span><br/>
<span className="decorator">@greenops.track</span><br/>
<span className="keyword">def</span> <span className="function">generate_response</span>(prompt):<br/>
&nbsp;&nbsp;&nbsp;&nbsp;<span className="keyword">return</span> client.chat.completions.create(<br/>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;model=<span className="string">"gpt-4o"</span>,<br/>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;messages=[{"{"}"role": "user", "content": prompt{"}"}]<br/>
&nbsp;&nbsp;&nbsp;&nbsp;)<br/>
<br/>
<span className="comment"># That's it! Energy & CO₂ are now tracked.</span>
              </code>
            </pre>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="footer-content">
          <div className="footer-brand">
            <Leaf size={20} color="#10b981" /> GreenOps
          </div>
          <div className="footer-text">
            Building a greener future for artificial intelligence.
          </div>
        </div>
      </footer>
    </div>
  );
}
