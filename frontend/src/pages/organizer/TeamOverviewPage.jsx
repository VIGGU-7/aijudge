import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import OrganizerLayout from "../../components/OrganizerLayout";
import { teamApi } from "../../lib/api";
import { Search, Users, GitBranch, ArrowRight } from "lucide-react";

export default function TeamOverviewPage() {
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    const fetchTeams = async () => {
      setLoading(true);
      try {
        if (searchQuery.trim()) {
          setTeams((await teamApi.search(searchQuery)).data);
        } else {
          setTeams((await teamApi.list()).data);
        }
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    const timer = setTimeout(fetchTeams, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  return (
    <OrganizerLayout>
      <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
        <div className="animate-enter" style={{ paddingBottom: 20, borderBottom: "1px solid #e8e8e8", display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
          <div>
            <h1 style={{ fontSize: 28, fontWeight: 700, letterSpacing: "-0.02em" }}>All Teams</h1>
            <p style={{ color: "#999", fontSize: 14, marginTop: 4 }}>Browse registered teams and access analysis</p>
          </div>
          <div style={{ position: "relative", width: 280 }}>
            <Search size={16} color="#999" style={{ position: "absolute", left: 14, top: "50%", transform: "translateY(-50%)" }} />
            <input
              type="text"
              placeholder="Search teams by name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input-field"
              style={{ paddingLeft: 40, width: "100%" }}
            />
          </div>
        </div>

        {loading ? (
          <div style={{ display: "flex", justifyContent: "center", padding: 80 }}><span className="overline animate-pulse-subtle">Loading teams...</span></div>
        ) : teams.length === 0 ? (
          <div className="card-grid" style={{ padding: 80, textAlign: "center" }}>
            <Users size={28} color="#ddd" style={{ marginBottom: 10 }} />
            <p style={{ color: "#bbb", fontSize: 14 }}>No teams registered yet</p>
          </div>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
            {teams.map((t) => (
              <Link key={t.id} to={`/o/analysis/${t.id}`} className="card-grid" style={{
                padding: 22, textDecoration: "none", color: "inherit", transition: "box-shadow 200ms ease",
              }}>
                <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
                  <div style={{
                    width: 38, height: 38, borderRadius: 9, background: "#111",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: 15, fontWeight: 700, color: "#fff",
                  }}>{t.name?.[0]?.toUpperCase()}</div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 15, fontWeight: 600 }}>{t.name}</div>
                    <div style={{ fontSize: 12, color: "#999", marginTop: 1 }}>{t.members?.length || 0} member{(t.members?.length || 0) !== 1 ? "s" : ""}</div>
                  </div>
                </div>

                <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 10 }}>
                  {(t.members || []).slice(0, 4).map((m, i) => (
                    <span key={i} className={`badge ${m.role === "leader" ? "badge-ai" : "badge-info"}`} style={{ fontSize: 10 }}>
                      {m.role === "leader" ? "★ " : ""}{m.name}
                    </span>
                  ))}
                  {(t.members || []).length > 4 && <span className="badge" style={{ background: "#f5f5f5", color: "#999", fontSize: 10 }}>+{t.members.length - 4}</span>}
                </div>

                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div style={{ fontSize: 12, color: "#999", display: "flex", alignItems: "center", gap: 4 }}>
                    <GitBranch size={12} /> {t.github_repo ? "GitHub linked" : "No GitHub"}
                  </div>
                  <span style={{ fontSize: 12, color: "#111", fontWeight: 600, display: "flex", alignItems: "center", gap: 4 }}>Analysis <ArrowRight size={11} /></span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </OrganizerLayout>
  );
}
