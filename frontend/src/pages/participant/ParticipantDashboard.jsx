import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import ParticipantLayout from "../../components/ParticipantLayout";
import { hackathonApi, teamApi } from "../../lib/api";
import { Settings, Mic, Bot, ArrowRight, GitBranch, Users, CheckCircle2 } from "lucide-react";

export default function ParticipantDashboard() {
  const { user } = useAuth();
  const [hackathons, setHackathons] = useState([]);
  const [myTeam, setMyTeam] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const [hRes, tRes] = await Promise.all([hackathonApi.list(), teamApi.getMy()]);
        setHackathons(hRes.data.slice(0, 5));
        setMyTeam(tRes.data);
      } catch (e) { console.error(e); }
      finally { setLoading(false); }
    })();
  }, []);

  const now = new Date();
  const greeting = now.getHours() < 12 ? "Good morning" : now.getHours() < 18 ? "Good afternoon" : "Good evening";

  if (loading) return <ParticipantLayout><div style={{ display: "flex", justifyContent: "center", padding: 120 }}><span className="overline animate-pulse-subtle">Loading...</span></div></ParticipantLayout>;

  const steps = [
    { done: !!myTeam, label: "Join a team", path: "/p/setup" },
    { done: !!myTeam?.github_repo, label: "Link GitHub repo", path: "/p/setup" },
    { done: false, label: "Complete AI viva", path: "/p/viva" },
  ];
  const completedSteps = steps.filter(s => s.done).length;

  return (
    <ParticipantLayout>
      <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
        {/* Header */}
        <div className="animate-enter" style={{ paddingBottom: 20, borderBottom: "1px solid #e8e8e8" }}>
          <h1 style={{ fontSize: 28, fontWeight: 700, letterSpacing: "-0.02em", marginBottom: 4 }}>
            {greeting}, {user?.name?.split(" ")[0]}
          </h1>
          <p style={{ color: "#999", fontSize: 14 }}>Set up your project, face the AI viva, and get mentored.</p>
        </div>

        {/* Getting Started */}
        <div className="card-grid animate-enter" style={{ padding: 24 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>Getting Started</span>
            <span style={{ fontSize: 12, color: "#999" }}>{completedSteps}/{steps.length} complete</span>
          </div>
          <div className="progress-bar" style={{ marginBottom: 18 }}>
            <div className="progress-bar-fill" style={{ width: `${(completedSteps / steps.length) * 100}%` }} />
          </div>
          <div style={{ display: "flex", gap: 10 }}>
            {steps.map((step, i) => (
              <Link key={i} to={step.path} style={{
                flex: 1, padding: "12px 14px", borderRadius: 8,
                background: step.done ? "#f0fdf4" : "#fafafa",
                border: `1px solid ${step.done ? "#bbf7d0" : "#e8e8e8"}`,
                textDecoration: "none", color: "inherit", display: "flex", alignItems: "center", gap: 8,
              }}>
                <div style={{
                  width: 22, height: 22, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center",
                  background: step.done ? "#22c55e" : "#eee",
                  color: step.done ? "#fff" : "#999", fontSize: 11,
                }}>
                  {step.done ? <CheckCircle2 size={13} /> : i + 1}
                </div>
                <span style={{ fontSize: 13, fontWeight: 500, color: step.done ? "#16a34a" : "#555" }}>{step.label}</span>
              </Link>
            ))}
          </div>
        </div>

        {/* Quick Actions */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 14 }}>
          {[
            { title: "Project Setup", desc: "Upload code, PPT & features", icon: Settings, path: "/p/setup" },
            { title: "AI Viva", desc: "Face the AI interviewer", icon: Mic, path: "/p/viva" },
            { title: "AI Mentor", desc: "Get coding help & tips", icon: Bot, path: "/p/mentor" },
          ].map((a, i) => {
            const Icon = a.icon;
            return (
              <Link key={a.title} to={a.path} className="card-grid animate-enter" style={{
                padding: 24, textDecoration: "none", color: "inherit",
                transition: "box-shadow 200ms ease",
              }}>
                <div style={{
                  width: 40, height: 40, borderRadius: 8, background: "#f5f5f5",
                  display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 14,
                }}>
                  <Icon size={18} color="#111" strokeWidth={1.8} />
                </div>
                <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 4 }}>{a.title}</div>
                <div style={{ fontSize: 13, color: "#999" }}>{a.desc}</div>
                <div style={{ marginTop: 14, fontSize: 12, color: "#111", fontWeight: 600, display: "flex", alignItems: "center", gap: 4 }}>
                  Get started <ArrowRight size={12} />
                </div>
              </Link>
            );
          })}
        </div>

        {/* Team Status */}
        <div className="card-grid animate-enter" style={{ overflow: "hidden" }}>
          <div style={{ padding: "14px 20px", borderBottom: "1px solid #e8e8e8", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>Team Status</span>
            {myTeam && <Link to="/p/setup" style={{ fontSize: 12, color: "#111", textDecoration: "none", fontWeight: 600, display: "flex", alignItems: "center", gap: 4 }}>Manage <ArrowRight size={11} /></Link>}
          </div>
          <div style={{ padding: 20 }}>
            {myTeam ? (
              <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
                <div style={{
                  width: 44, height: 44, borderRadius: 10, background: "#111",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 17, fontWeight: 700, color: "#fff",
                }}>{myTeam.name?.[0]?.toUpperCase()}</div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 16, fontWeight: 600 }}>{myTeam.name}</div>
                  <div style={{ display: "flex", gap: 8, marginTop: 6 }}>
                    <span className="badge badge-info" style={{ display: "flex", alignItems: "center", gap: 4 }}><Users size={10} /> {myTeam.members?.length || 0} members</span>
                    <span className={`badge ${myTeam.github_repo ? "badge-human" : "badge-warning"}`} style={{ display: "flex", alignItems: "center", gap: 4 }}>
                      <GitBranch size={10} /> {myTeam.github_repo ? "Linked" : "Not linked"}
                    </span>
                  </div>
                  <div style={{ marginTop: 12, padding: "10px 14px", background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 8, fontSize: 12, color: "#334155" }}>
                    <div style={{ fontWeight: 600, marginBottom: 4, color: "#0f172a" }}>VS Code Extension Config</div>
                    <div>To link HackGuard, use Team Name: <span style={{ fontWeight: 700, fontFamily: "monospace", background: "#e2e8f0", padding: "2px 6px", borderRadius: 4 }}>{myTeam.name}</span></div>
                    {myTeam.extension_key && <div style={{ marginTop: 6, fontSize: 11 }}>Extension Key: <span style={{ fontFamily: "monospace", color: "#64748b" }}>{myTeam.extension_key}</span></div>}
                  </div>
                </div>
              </div>
            ) : (
              <div style={{ textAlign: "center", padding: 20 }}>
                <Users size={28} color="#ccc" style={{ marginBottom: 12 }} />
                <p style={{ color: "#999", marginBottom: 14, fontSize: 13 }}>You haven't joined a team yet</p>
                <Link to="/p/setup" className="btn btn-primary" style={{ fontSize: 13 }}>Create or Join Team</Link>
              </div>
            )}
          </div>
        </div>

        {/* Available Hackathons */}
        <div className="card-grid animate-enter" style={{ overflow: "hidden" }}>
          <div style={{ padding: "14px 20px", borderBottom: "1px solid #e8e8e8" }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>Available Hackathons</span>
          </div>
          {hackathons.length === 0 ? (
            <div style={{ padding: 48, textAlign: "center", color: "#ccc", fontSize: 13 }}>No hackathons available</div>
          ) : hackathons.map((h) => (
            <div key={h.id} style={{
              padding: "12px 20px", borderBottom: "1px solid #f0f0f0",
              display: "flex", alignItems: "center", justifyContent: "space-between",
            }}>
              <div>
                <div style={{ fontSize: 14, fontWeight: 600 }}>{h.name}</div>
                <div style={{ fontSize: 12, color: "#999", marginTop: 2 }}>{h.description?.slice(0, 60)}</div>
              </div>
              <span className={`badge ${h.status === "active" ? "badge-human" : "badge-info"}`}>{h.status}</span>
            </div>
          ))}
        </div>
      </div>
    </ParticipantLayout>
  );
}
