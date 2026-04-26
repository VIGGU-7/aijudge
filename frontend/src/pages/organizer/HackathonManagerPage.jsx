import { useState, useEffect } from "react";
import OrganizerLayout from "../../components/OrganizerLayout";
import { hackathonApi, teamApi } from "../../lib/api";
import { Plus, UserPlus } from "lucide-react";

export default function HackathonManagerPage() {
  const [hackathons, setHackathons] = useState([]);
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ name: "", description: "", start_time: "", end_time: "", max_team_size: 4 });
  const [creating, setCreating] = useState(false);
  const [showCreateTeam, setShowCreateTeam] = useState(null);
  const [teamName, setTeamName] = useState("");
  const [addingTo, setAddingTo] = useState(null);
  const [memberEmail, setMemberEmail] = useState("");
  const [addStatus, setAddStatus] = useState("");

  useEffect(() => { load(); }, []);

  const load = async () => {
    try {
      const [hRes, tRes] = await Promise.all([hackathonApi.list(), teamApi.list()]);
      setHackathons(hRes.data);
      setTeams(tRes.data);
    } catch {}
    setLoading(false);
  };

  const handleCreate = async (e) => {
    e.preventDefault(); setCreating(true);
    try { await hackathonApi.create(form); setShowCreate(false); setForm({ name: "", description: "", start_time: "", end_time: "", max_team_size: 4 }); load(); }
    catch {} finally { setCreating(false); }
  };

  const handleStatusChange = async (id, status) => {
    try { await hackathonApi.updateStatus(id, status); load(); } catch {}
  };

  const handleCreateTeam = async (hackathonId) => {
    if (!teamName.trim()) return;
    try { await teamApi.create({ name: teamName, hackathon_id: hackathonId }); setTeamName(""); setShowCreateTeam(null); load(); } catch {}
  };

  const handleAddMember = async (teamId) => {
    if (!memberEmail.trim()) return;
    setAddStatus("");
    try {
      const res = await teamApi.addMember(teamId, memberEmail);
      setAddStatus(res.data.message);
      setMemberEmail("");
      load();
    } catch (e) { setAddStatus(e.response?.data?.detail || "Error adding member"); }
  };

  const getTeamsForHackathon = (hid) => teams.filter(t => t.hackathon_id === hid);
  const nextStatus = { draft: "active", active: "completed", completed: "draft" };

  return (
    <OrganizerLayout>
      <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
        <div className="animate-enter" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", paddingBottom: 20, borderBottom: "1px solid #e8e8e8" }}>
          <div>
            <h1 style={{ fontSize: 28, fontWeight: 700, letterSpacing: "-0.02em" }}>Hackathons</h1>
            <p style={{ color: "#999", fontSize: 14, marginTop: 4 }}>Create and manage hackathon events</p>
          </div>
          <button onClick={() => setShowCreate(!showCreate)} className="btn btn-primary" style={{ gap: 6 }}><Plus size={14} /> Create Hackathon</button>
        </div>

        {showCreate && (
          <form onSubmit={handleCreate} className="card-grid animate-enter" style={{ padding: 24, display: "flex", flexDirection: "column", gap: 16, borderLeft: "3px solid #111" }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>New Hackathon</span>
            <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Hackathon Name" required />
            <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="Description" required rows={2} style={{ resize: "vertical" }} />
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10 }}>
              <div>
                <label style={{ display: "block", marginBottom: 4, fontSize: 12, fontWeight: 600, color: "#999" }}>Start</label>
                <input type="datetime-local" value={form.start_time} onChange={(e) => setForm({ ...form, start_time: e.target.value })} required />
              </div>
              <div>
                <label style={{ display: "block", marginBottom: 4, fontSize: 12, fontWeight: 600, color: "#999" }}>End</label>
                <input type="datetime-local" value={form.end_time} onChange={(e) => setForm({ ...form, end_time: e.target.value })} required />
              </div>
              <div>
                <label style={{ display: "block", marginBottom: 4, fontSize: 12, fontWeight: 600, color: "#999" }}>Team Size</label>
                <input type="number" value={form.max_team_size} onChange={(e) => setForm({ ...form, max_team_size: parseInt(e.target.value) })} min={1} max={10} />
              </div>
            </div>
            <button type="submit" disabled={creating} className="btn btn-primary" style={{ height: 44 }}>{creating ? "Creating..." : "Create Hackathon"}</button>
          </form>
        )}

        {loading ? (
          <div style={{ display: "flex", justifyContent: "center", padding: 80 }}><span className="overline animate-pulse-subtle">Loading...</span></div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {hackathons.map((h) => (
              <div key={h.id} className="card-grid animate-enter" style={{ overflow: "hidden" }}>
                <div style={{ padding: "14px 18px", display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #f0f0f0" }}>
                  <div>
                    <div style={{ fontSize: 16, fontWeight: 600 }}>{h.name}</div>
                    <div style={{ fontSize: 12, color: "#999", marginTop: 2 }}>{h.description?.slice(0, 80)}</div>
                  </div>
                  <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                    <span className={`badge badge-${h.status === "active" ? "human" : h.status === "completed" ? "ai" : "warning"}`}>{h.status}</span>
                    <button onClick={() => handleStatusChange(h.id, nextStatus[h.status] || "active")} className="btn btn-outline" style={{ fontSize: 11, padding: "4px 10px" }}>
                      → {nextStatus[h.status] || "active"}
                    </button>
                  </div>
                </div>

                <div style={{ padding: "12px 18px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                    <span style={{ fontSize: 12, fontWeight: 600, color: "#999" }}>Teams ({getTeamsForHackathon(h.id).length})</span>
                    <button onClick={() => setShowCreateTeam(showCreateTeam === h.id ? null : h.id)} className="btn btn-outline" style={{ fontSize: 11, padding: "4px 10px", gap: 4 }}><Plus size={11} /> Add Team</button>
                  </div>

                  {showCreateTeam === h.id && (
                    <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
                      <input value={teamName} onChange={(e) => setTeamName(e.target.value)} placeholder="Team name" style={{ flex: 1 }} />
                      <button onClick={() => handleCreateTeam(h.id)} className="btn btn-primary" style={{ fontSize: 12, padding: "8px 18px" }}>Create</button>
                    </div>
                  )}

                  {getTeamsForHackathon(h.id).length === 0 ? (
                    <p style={{ color: "#bbb", fontSize: 12, padding: "6px 0" }}>No teams yet</p>
                  ) : getTeamsForHackathon(h.id).map((t) => (
                    <div key={t.id} style={{ background: "#fafafa", border: "1px solid #e8e8e8", borderRadius: 8, padding: 14, marginBottom: 8 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                          <div style={{
                            width: 26, height: 26, borderRadius: 6, background: "#111",
                            display: "flex", alignItems: "center", justifyContent: "center",
                            fontSize: 11, fontWeight: 700, color: "#fff",
                          }}>{t.name?.[0]?.toUpperCase()}</div>
                          <span style={{ fontSize: 14, fontWeight: 600 }}>{t.name}</span>
                        </div>
                        <button onClick={() => { setAddingTo(addingTo === t.id ? null : t.id); setAddStatus(""); setMemberEmail(""); }}
                          className="btn btn-outline" style={{ fontSize: 10, padding: "3px 10px", gap: 4 }}><UserPlus size={11} /> Member</button>
                      </div>

                      <div style={{ display: "flex", flexWrap: "wrap", gap: 5, marginBottom: addingTo === t.id ? 10 : 0 }}>
                        {(t.members || []).map((m, i) => (
                          <span key={i} className={`badge ${m.role === "leader" ? "badge-ai" : "badge-info"}`} style={{ fontSize: 10 }}>
                            {m.role === "leader" ? "★ " : ""}{m.name}
                          </span>
                        ))}
                      </div>

                      {addingTo === t.id && (
                        <div>
                          <div style={{ display: "flex", gap: 8 }}>
                            <input value={memberEmail} onChange={(e) => setMemberEmail(e.target.value)} placeholder="User email" style={{ flex: 1 }}
                              onKeyDown={(e) => e.key === "Enter" && handleAddMember(t.id)} />
                            <button onClick={() => handleAddMember(t.id)} className="btn btn-primary" style={{ fontSize: 11, padding: "8px 16px" }}>Add</button>
                          </div>
                          {addStatus && (
                            <p style={{
                              marginTop: 6, fontSize: 12, fontWeight: 500,
                              color: addStatus.includes("Error") || addStatus.includes("No user") ? "#dc2626" : "#16a34a",
                            }}>{addStatus}</p>
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </OrganizerLayout>
  );
}
