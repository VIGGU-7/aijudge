import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { Zap, Shield } from "lucide-react";

export default function RegisterPage() {
  const { register } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("participant");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => { setMounted(true); }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(""); setLoading(true);
    try { await register(email, password, name, role); }
    catch (err) { setError(err.response?.data?.detail || "Registration failed"); }
    finally { setLoading(false); }
  };

  const roles = [
    { value: "participant", icon: Zap, label: "Participant", desc: "Upload code, face viva, get mentored" },
    { value: "organizer", icon: Shield, label: "Organizer", desc: "Manage hackathons, analyze teams" },
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
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{
            width: 36, height: 36, background: "#111", display: "flex",
            alignItems: "center", justifyContent: "center", borderRadius: 8, color: "#fff", fontWeight: 700, fontSize: 16,
          }}>A</div>
          <span style={{ fontWeight: 700, fontSize: 18, letterSpacing: "-0.01em" }}>AI Judge</span>
        </div>

        <div style={{ maxWidth: 420 }}>
          <div style={{
            display: "inline-flex", alignItems: "center", gap: 6, padding: "5px 12px",
            background: "#f0f0f0", borderRadius: 6, marginBottom: 24,
          }}>
            <span style={{ width: 5, height: 5, borderRadius: "50%", background: "#22c55e" }} />
            <span style={{ fontSize: 11, fontWeight: 600, color: "#555", letterSpacing: "0.03em" }}>NEW REGISTRATION</span>
          </div>

          <h1 style={{ fontSize: 38, fontWeight: 700, lineHeight: 1.15, letterSpacing: "-0.02em", marginBottom: 16, color: "#111" }}>
            Choose Your Role
          </h1>
          <p style={{ color: "#888", fontSize: 15, lineHeight: 1.7 }}>
            Participants upload projects and face AI viva. Organizers manage hackathons and view analysis.
          </p>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginTop: 40 }}>
            {roles.map((r) => {
              const Icon = r.icon;
              return (
                <div key={r.value} style={{
                  background: "#fff", border: "1px solid #e8e8e8", borderRadius: 8,
                  padding: 24, textAlign: "center", boxShadow: "var(--shadow-xs)",
                }}>
                  <div style={{ display: "flex", justifyContent: "center", marginBottom: 12 }}>
                    <Icon size={28} color="#111" strokeWidth={1.6} />
                  </div>
                  <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 4 }}>{r.label}</div>
                  <div style={{ fontSize: 12, color: "#999", lineHeight: 1.5 }}>{r.desc}</div>
                </div>
              );
            })}
          </div>
        </div>

        <div style={{ borderTop: "1px solid #e8e8e8", paddingTop: 16 }}>
          <span style={{ fontSize: 11, color: "#bbb" }}>AI Judge v2.0</span>
        </div>
      </div>

      {/* Right form */}
      <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", padding: 48 }}>
        <div style={{ width: "100%", maxWidth: 380 }}>
          <h2 style={{ fontSize: 28, fontWeight: 700, letterSpacing: "-0.02em", marginBottom: 6 }}>Create Account</h2>
          <p style={{ color: "#999", fontSize: 14, marginBottom: 32 }}>Set up your credentials to get started</p>

          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {error && (
              <div style={{
                padding: "10px 14px", background: "#fef2f2", border: "1px solid #fecaca",
                borderRadius: 8, color: "#dc2626", fontSize: 13, fontWeight: 500,
              }}>{error}</div>
            )}

            <div>
              <label style={{ display: "block", marginBottom: 6, fontSize: 13, fontWeight: 600, color: "#555" }}>Full Name</label>
              <input type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="Your Name" required />
            </div>
            <div>
              <label style={{ display: "block", marginBottom: 6, fontSize: 13, fontWeight: 600, color: "#555" }}>Email</label>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" required />
            </div>
            <div>
              <label style={{ display: "block", marginBottom: 6, fontSize: 13, fontWeight: 600, color: "#555" }}>Password</label>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Min 6 characters" required minLength={6} />
            </div>

            <div>
              <label style={{ display: "block", marginBottom: 8, fontSize: 13, fontWeight: 600, color: "#555" }}>Role</label>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                {roles.map((r) => {
                  const Icon = r.icon;
                  return (
                    <button key={r.value} type="button" onClick={() => setRole(r.value)} style={{
                      padding: 12, borderRadius: 8, fontSize: 13, fontWeight: 600,
                      cursor: "pointer", transition: "all 150ms", display: "flex", alignItems: "center", justifyContent: "center", gap: 8,
                      background: role === r.value ? "#111" : "#fafafa",
                      border: `1px solid ${role === r.value ? "#111" : "#e8e8e8"}`,
                      color: role === r.value ? "#fff" : "#888",
                    }}>
                      <Icon size={14} /> {r.label}
                    </button>
                  );
                })}
              </div>
            </div>

            <button type="submit" disabled={loading} className="btn btn-primary" style={{ height: 46, marginTop: 4, fontSize: 14 }}>
              {loading ? (
                <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <span style={{ width: 14, height: 14, border: "2px solid rgba(255,255,255,0.3)", borderTopColor: "white", borderRadius: "50%" }} className="animate-spin" />
                  Creating...
                </span>
              ) : "Create Account"}
            </button>
          </form>

          <div style={{ textAlign: "center", marginTop: 32, paddingTop: 24, borderTop: "1px solid #e8e8e8" }}>
            <span style={{ fontSize: 14, color: "#999" }}>
              Already have an account?{" "}
              <Link to="/login" style={{ color: "#111", fontWeight: 600, textDecoration: "none" }}>Sign In</Link>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
