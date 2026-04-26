import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import OrganizerLayout from "../../components/OrganizerLayout";
import { statsApi, hackathonApi, teamApi, reportApi } from "../../lib/api";
import { useAuth } from "../../context/AuthContext";
import { AreaChart, Area, PieChart, Pie, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis, CartesianGrid } from "recharts";
import { Trophy, Users, UserCircle, ClipboardList, BarChart3, Search, ArrowRight, FileDown, Loader, ShieldAlert } from "lucide-react";

function AnimatedNumber({ value, color }) {
  const [displayed, setDisplayed] = useState(0);
  useEffect(() => {
    if (!value) return;
    let start = 0;
    const duration = 800;
    const step = (ts) => {
      if (!start) start = ts;
      const progress = Math.min((ts - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplayed(Math.floor(eased * value));
      if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [value]);
  return <span className="stat-number" style={{ color }}>{displayed}</span>;
}

export default function OrganizerDashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [hackathons, setHackathons] = useState([]);
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [downloadingId, setDownloadingId] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const [sRes, hRes, tRes] = await Promise.all([statsApi.dashboard(), hackathonApi.list(), teamApi.list()]);
        setStats(sRes.data);
        setHackathons(hRes.data.slice(0, 5));
        setTeams(tRes.data || []);
      } catch {}
      setLoading(false);
    })();
  }, []);

  if (loading) return <OrganizerLayout><div style={{ display: "flex", justifyContent: "center", alignItems: "center", padding: 120 }}><span className="overline animate-pulse-subtle">Loading dashboard...</span></div></OrganizerLayout>;

  const activityData = Array.from({ length: 7 }, (_, i) => ({
    day: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][i],
    teams: Math.max(1, (stats?.teams || 0) - Math.floor(Math.random() * 3)),
    evaluations: Math.max(0, (stats?.evaluations || 0) - Math.floor(Math.random() * 2)),
  }));

  const statusCounts = { active: 0, draft: 0, completed: 0 };
  hackathons.forEach(h => { statusCounts[h.status] = (statusCounts[h.status] || 0) + 1; });
  const pieData = Object.entries(statusCounts).filter(([,v]) => v > 0).map(([name, value]) => ({ name: name.charAt(0).toUpperCase() + name.slice(1), value }));
  const pieColors = { Active: "#22c55e", Draft: "#ccc", Completed: "#111" };

  const now = new Date();
  const greeting = now.getHours() < 12 ? "Good morning" : now.getHours() < 18 ? "Good afternoon" : "Good evening";

  return (
    <OrganizerLayout>
      <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
        {/* Header */}
        <div className="animate-enter" style={{ paddingBottom: 20, borderBottom: "1px solid #e8e8e8" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <div>
              <h1 style={{ fontSize: 28, fontWeight: 700, letterSpacing: "-0.02em", marginBottom: 4 }}>{greeting}, {user?.name?.split(" ")[0]}</h1>
              <p style={{ color: "#999", fontSize: 14 }}>Here's what's happening across your hackathons today.</p>
            </div>
            <Link to="/o/hackathons" className="btn btn-primary" style={{ fontSize: 12, padding: "9px 18px" }}>+ New Hackathon</Link>
          </div>
        </div>

        {/* Stat Cards */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 14 }}>
          {[
            { label: "Hackathons", value: stats?.hackathons || 0, icon: Trophy },
            { label: "Teams", value: stats?.teams || 0, icon: Users },
            { label: "Users", value: stats?.users || 0, icon: UserCircle },
            { label: "Evaluations", value: stats?.evaluations || 0, icon: ClipboardList },
          ].map((s, i) => {
            const Icon = s.icon;
            return (
              <div key={s.label} className="stat-card animate-enter" style={{ animationDelay: `${i * 60}ms` }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 14 }}>
                  <span style={{ fontSize: 11, fontWeight: 600, color: "#999", letterSpacing: "0.04em", textTransform: "uppercase" }}>{s.label}</span>
                  <div style={{ width: 32, height: 32, background: "#f5f5f5", borderRadius: 7, display: "flex", alignItems: "center", justifyContent: "center" }}>
                    <Icon size={15} color="#888" />
                  </div>
                </div>
                <AnimatedNumber value={s.value} color="#111" />
              </div>
            );
          })}
        </div>

        {/* Charts Row */}
        <div style={{ display: "grid", gridTemplateColumns: "3fr 2fr", gap: 16 }}>
          <div className="card-grid animate-enter" style={{ overflow: "hidden" }}>
            <div style={{ padding: "12px 18px", borderBottom: "1px solid #e8e8e8" }}>
              <span style={{ fontSize: 13, fontWeight: 600 }}>Weekly Activity</span>
              <p style={{ fontSize: 12, color: "#999", marginTop: 2 }}>Teams and evaluations trend</p>
            </div>
            <div style={{ padding: "14px 10px 6px 0" }}>
              <ResponsiveContainer width="100%" height={200}>
                <AreaChart data={activityData}>
                  <defs>
                    <linearGradient id="colorT" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#111" stopOpacity={0.1}/><stop offset="95%" stopColor="#111" stopOpacity={0}/></linearGradient>
                    <linearGradient id="colorE" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#22c55e" stopOpacity={0.15}/><stop offset="95%" stopColor="#22c55e" stopOpacity={0}/></linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="day" tick={{ fill: "#999", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: "#999", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <Tooltip />
                  <Area type="monotone" dataKey="teams" stroke="#111" fill="url(#colorT)" strokeWidth={2} />
                  <Area type="monotone" dataKey="evaluations" stroke="#22c55e" fill="url(#colorE)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
              <div style={{ display: "flex", justifyContent: "center", gap: 20, padding: "6px 0" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 11, color: "#999" }}><div style={{ width: 8, height: 8, borderRadius: "50%", background: "#111" }} /> Teams</div>
                <div style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 11, color: "#999" }}><div style={{ width: 8, height: 8, borderRadius: "50%", background: "#22c55e" }} /> Evaluations</div>
              </div>
            </div>
          </div>

          <div className="card-grid animate-enter" style={{ overflow: "hidden" }}>
            <div style={{ padding: "12px 18px", borderBottom: "1px solid #e8e8e8" }}>
              <span style={{ fontSize: 13, fontWeight: 600 }}>Hackathon Status</span>
            </div>
            <div style={{ padding: 14, display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column" }}>
              {pieData.length > 0 ? (
                <>
                  <ResponsiveContainer width="100%" height={170}>
                    <PieChart>
                      <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={44} outerRadius={66} paddingAngle={3} strokeWidth={0}>
                        {pieData.map((entry) => <Cell key={entry.name} fill={pieColors[entry.name] || "#ccc"} />)}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                  <div style={{ display: "flex", gap: 14, marginTop: 6 }}>
                    {pieData.map(d => (
                      <div key={d.name} style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 12, color: "#999" }}>
                        <div style={{ width: 8, height: 8, borderRadius: "50%", background: pieColors[d.name] || "#ccc" }} /> {d.name} ({d.value})
                      </div>
                    ))}
                  </div>
                </>
              ) : <div style={{ padding: 40, color: "#ccc", fontSize: 13 }}>No hackathons yet</div>}
            </div>
          </div>
        </div>

        {/* Bottom */}
        <div style={{ display: "grid", gridTemplateColumns: "3fr 2fr", gap: 16 }}>
          <div className="card-grid animate-enter" style={{ overflow: "hidden" }}>
            <div style={{ padding: "12px 18px", borderBottom: "1px solid #e8e8e8", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: 13, fontWeight: 600 }}>Recent Hackathons</span>
              <Link to="/o/hackathons" style={{ fontSize: 12, color: "#111", textDecoration: "none", fontWeight: 600, display: "flex", alignItems: "center", gap: 4 }}>View All <ArrowRight size={11} /></Link>
            </div>
            {hackathons.length === 0 ? (
              <div style={{ padding: 48, textAlign: "center" }}><Trophy size={28} color="#ddd" style={{ marginBottom: 10 }} /><p style={{ color: "#bbb", fontSize: 13 }}>No hackathons created yet</p></div>
            ) : hackathons.map((h) => (
              <div key={h.id} style={{ padding: "12px 18px", borderBottom: "1px solid #f0f0f0", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600 }}>{h.name}</div>
                  <div style={{ fontSize: 12, color: "#999", marginTop: 2 }}>{h.description?.slice(0, 50)}</div>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <button
                    onClick={async () => {
                      setDownloadingId(h.id);
                      try {
                        const res = await reportApi.hackathonPdf(h.id);
                        const url = window.URL.createObjectURL(new Blob([res.data], { type: "application/pdf" }));
                        const a = document.createElement("a"); a.href = url;
                        a.download = `${(h.name || "hackathon").replace(/\s+/g, "_")}_report.pdf`;
                        document.body.appendChild(a); a.click(); a.remove();
                        window.URL.revokeObjectURL(url);
                      } catch (e) { console.error(e); alert("Failed to generate report"); }
                      finally { setDownloadingId(null); }
                    }}
                    disabled={downloadingId === h.id}
                    className="btn btn-outline"
                    style={{ fontSize: 10, padding: "5px 10px", gap: 4, display: "flex", alignItems: "center" }}
                  >
                    {downloadingId === h.id ? <><Loader size={11} className="animate-spin" /> PDF...</> : <><FileDown size={12} /> Report</>}
                  </button>
                  <span className={`badge badge-${h.status === "active" ? "human" : h.status === "completed" ? "ai" : "warning"}`}>{h.status}</span>
                </div>
              </div>
            ))}
          </div>

          <div className="card-grid animate-enter" style={{ overflow: "hidden" }}>
            <div style={{ padding: "12px 18px", borderBottom: "1px solid #e8e8e8" }}>
              <span style={{ fontSize: 13, fontWeight: 600 }}>Quick Actions</span>
            </div>
            <div style={{ padding: 12, display: "flex", flexDirection: "column", gap: 4 }}>
              {[
                { label: "Manage Hackathons", path: "/o/hackathons", icon: Trophy, desc: "Create and configure events" },
                { label: "View Teams", path: "/o/teams", icon: Users, desc: "Browse all registered teams" },
                { label: "Team Analysis", path: "/o/analysis", icon: Search, desc: "AI-powered code review" },
                { label: "Leaderboard", path: "/o/leaderboard", icon: BarChart3, desc: "Rankings and scores" },
              ].map((a) => {
                const Icon = a.icon;
                return (
                  <Link key={a.label} to={a.path} style={{
                    display: "flex", alignItems: "center", gap: 12, padding: "10px 12px",
                    borderRadius: 8, textDecoration: "none", color: "inherit", transition: "background 150ms",
                  }}
                  onMouseOver={(e) => e.currentTarget.style.background = "#f5f5f5"}
                  onMouseOut={(e) => e.currentTarget.style.background = "transparent"}
                  >
                    <div style={{ width: 34, height: 34, borderRadius: 7, background: "#f5f5f5", display: "flex", alignItems: "center", justifyContent: "center" }}>
                      <Icon size={15} color="#888" />
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 13, fontWeight: 600 }}>{a.label}</div>
                      <div style={{ fontSize: 11, color: "#999" }}>{a.desc}</div>
                    </div>
                    <ArrowRight size={13} color="#ccc" />
                  </Link>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </OrganizerLayout>
  );
}
