import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { Search, Mic, FileText } from "lucide-react";

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [showPw, setShowPw] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => { setMounted(true); }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(""); setLoading(true);
    try { await login(email, password); }
    catch (err) { setError(err.response?.data?.detail || "Login failed"); }
    finally { setLoading(false); }
  };

  const features = [
    { icon: Search, label: "Code Analysis", desc: "Deep codebase review" },
    { icon: Mic, label: "Voice Viva", desc: "AI speaks & listens" },
    { icon: FileText, label: "PPT Verify", desc: "Claim verification" },
  ];

  return (
    <div style={{
      minHeight: "100vh", display: "flex", background: "#fff",
      opacity: mounted ? 1 : 0, transition: "opacity 400ms ease",
    }}>
      {/* Left panel */}
      <div style={{
        width: "48%", background: "#fafafa", borderRight: "1px solid #e8e8e8",
        display: "flex", flexDirection: "column", justifyContent: "space-between", padding: "48px 56px",
      }}>
        {/* Logo */}
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{
            width: 36, height: 36, background: "#111", display: "flex",
            alignItems: "center", justifyContent: "center", borderRadius: 8, fontSize: 16,
            color: "#fff", fontWeight: 700,
          }}>A</div>
          <span style={{ fontWeight: 700, fontSize: 18, letterSpacing: "-0.01em" }}>AI Judge</span>
        </div>

        {/* Hero */}
        <div style={{ maxWidth: 420 }}>
          <div style={{
            display: "inline-flex", alignItems: "center", gap: 6, padding: "5px 12px",
            background: "#f0f0f0", borderRadius: 6, marginBottom: 24,
          }}>
            <span style={{ width: 5, height: 5, borderRadius: "50%", background: "#22c55e" }} />
            <span style={{ fontSize: 11, fontWeight: 600, color: "#555", letterSpacing: "0.03em" }}>SECURE AUTHENTICATION</span>
          </div>

          <h1 style={{ fontSize: 38, fontWeight: 700, lineHeight: 1.15, letterSpacing: "-0.02em", marginBottom: 16, color: "#111" }}>
            Context-Aware AI Judging Platform
          </h1>
          <p style={{ color: "#888", fontSize: 15, lineHeight: 1.7, maxWidth: 380 }}>
            AI that analyzes your codebase, presentation, and tech stack — then conducts an intelligent viva with voice.
          </p>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12, marginTop: 40 }}>
            {features.map((f, i) => {
              const Icon = f.icon;
              return (
                <div key={i} style={{
                  background: "#fff", border: "1px solid #e8e8e8", borderRadius: 8,
                  padding: "18px 14px", textAlign: "center", boxShadow: "var(--shadow-xs)",
                }}>
                  <div style={{ display: "flex", justifyContent: "center", marginBottom: 10 }}>
                    <Icon size={22} color="#111" strokeWidth={1.6} />
                  </div>
                  <div style={{ fontSize: 12, fontWeight: 700, color: "#111" }}>{f.label}</div>
                  <div style={{ fontSize: 11, color: "#999", marginTop: 3 }}>{f.desc}</div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Footer */}
        <div style={{ borderTop: "1px solid #e8e8e8", paddingTop: 16 }}>
          <span style={{ fontSize: 11, color: "#bbb" }}>AI Judge v2.0</span>
        </div>
      </div>

      {/* Right form */}
      <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", padding: 48 }}>
        <div style={{ width: "100%", maxWidth: 380 }}>
          <h2 style={{ fontSize: 28, fontWeight: 700, letterSpacing: "-0.02em", marginBottom: 6 }}>Welcome back</h2>
          <p style={{ color: "#999", fontSize: 14, marginBottom: 32 }}>Enter your credentials to access the platform</p>

          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 18 }}>
            {error && (
              <div style={{
                padding: "10px 14px", background: "#fef2f2", border: "1px solid #fecaca",
                borderRadius: 8, color: "#dc2626", fontSize: 13, fontWeight: 500,
              }}>
                {error}
              </div>
            )}

            <div>
              <label style={{ display: "block", marginBottom: 6, fontSize: 13, fontWeight: 600, color: "#555" }}>Email</label>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" required />
            </div>

            <div>
              <label style={{ display: "block", marginBottom: 6, fontSize: 13, fontWeight: 600, color: "#555" }}>Password</label>
              <div style={{ position: "relative" }}>
                <input type={showPw ? "text" : "password"} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Enter your password" required minLength={6} />
                <button type="button" onClick={() => setShowPw(!showPw)} style={{
                  position: "absolute", right: 12, top: "50%", transform: "translateY(-50%)",
                  background: "none", border: "none", color: "#bbb", cursor: "pointer", fontSize: 13,
                }}>{showPw ? "Hide" : "Show"}</button>
              </div>
            </div>

            <button type="submit" disabled={loading} className="btn btn-primary" style={{ height: 46, marginTop: 4, fontSize: 14 }}>
              {loading ? (
                <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <span style={{ width: 14, height: 14, border: "2px solid rgba(255,255,255,0.3)", borderTopColor: "white", borderRadius: "50%" }} className="animate-spin" />
                  Signing in...
                </span>
              ) : "Sign In"}
            </button>
          </form>

          <div style={{ textAlign: "center", marginTop: 32, paddingTop: 24, borderTop: "1px solid #e8e8e8" }}>
            <span style={{ fontSize: 14, color: "#999" }}>
              Don't have an account?{" "}
              <Link to="/register" style={{ color: "#111", fontWeight: 600, textDecoration: "none" }}>Create one</Link>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
