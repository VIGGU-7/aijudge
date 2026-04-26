import { useState, useEffect } from "react";
import OrganizerLayout from "../../components/OrganizerLayout";
import { evalApi, hackathonApi } from "../../lib/api";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from "recharts";
import { BarChart3 } from "lucide-react";

function ScoreRing({ score, size = 52 }) {
  const color = score >= 80 ? "#22c55e" : score >= 60 ? "#f59e0b" : "#ef4444";
  const radius = (size - 6) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  return (
    <div style={{ position: "relative", width: size, height: size }}>
      <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
        <circle cx={size/2} cy={size/2} r={radius} fill="none" stroke="#f0f0f0" strokeWidth={3} />
        <circle cx={size/2} cy={size/2} r={radius} fill="none" stroke={color} strokeWidth={3}
          strokeDasharray={circumference} strokeDashoffset={offset} strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 1s ease" }} />
      </svg>
      <div style={{
        position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center",
        fontWeight: 700, fontSize: size * 0.28, color,
      }}>{score}</div>
    </div>
  );
}

export default function LeaderboardPage() {
  const [hackathons, setHackathons] = useState([]);
  const [selectedHackathon, setSelectedHackathon] = useState("");
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    (async () => { try { const r = await hackathonApi.list(); setHackathons(r.data); if (r.data[0]) setSelectedHackathon(r.data[0].id); } catch {} })();
  }, []);

  useEffect(() => {
    if (!selectedHackathon) return;
    (async () => { setLoading(true); try { setLeaderboard((await evalApi.leaderboard(selectedHackathon)).data); } catch {} setLoading(false); })();
  }, [selectedHackathon]);

  const getScoreColor = (score) => score >= 80 ? "#22c55e" : score >= 60 ? "#f59e0b" : "#ef4444";
  const medalLabels = ["1st", "2nd", "3rd"];

  const chartData = leaderboard.slice(0, 10).map((e) => ({
    name: e.team_name?.length > 12 ? e.team_name.slice(0, 12) + "…" : e.team_name,
    score: e.avg_score,
  }));

  return (
    <OrganizerLayout>
      <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
        <div className="animate-enter" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", paddingBottom: 20, borderBottom: "1px solid #e8e8e8" }}>
          <div>
            <h1 style={{ fontSize: 28, fontWeight: 700, letterSpacing: "-0.02em" }}>Leaderboard</h1>
            <p style={{ color: "#999", fontSize: 14, marginTop: 4 }}>Rankings based on AI evaluation scores</p>
          </div>
          <select value={selectedHackathon} onChange={(e) => setSelectedHackathon(e.target.value)} style={{ width: 260 }}>
            {hackathons.map((h) => <option key={h.id} value={h.id}>{h.name}</option>)}
          </select>
        </div>

        {loading ? (
          <div style={{ display: "flex", justifyContent: "center", padding: 80 }}><span className="overline animate-pulse-subtle">Loading rankings...</span></div>
        ) : leaderboard.length === 0 ? (
          <div className="card-grid" style={{ padding: 80, textAlign: "center" }}>
            <BarChart3 size={32} color="#ddd" style={{ marginBottom: 12 }} />
            <p style={{ color: "#bbb", fontSize: 14 }}>No evaluations submitted yet</p>
          </div>
        ) : (
          <>
            {/* Chart */}
            <div className="card-grid animate-enter" style={{ overflow: "hidden" }}>
              <div style={{ padding: "12px 18px", borderBottom: "1px solid #e8e8e8" }}>
                <span style={{ fontSize: 13, fontWeight: 600 }}>Score Distribution</span>
              </div>
              <div style={{ padding: "16px 10px 6px 0" }}>
                <ResponsiveContainer width="100%" height={230}>
                  <BarChart data={chartData} barSize={24}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="name" tick={{ fill: "#999", fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis domain={[0, 100]} tick={{ fill: "#999", fontSize: 11 }} axisLine={false} tickLine={false} />
                    <Tooltip />
                    <Bar dataKey="score" radius={[4, 4, 0, 0]}>
                      {chartData.map((_, i) => <Cell key={i} fill={i === 0 ? "#111" : i === 1 ? "#555" : "#ccc"} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Top 3 */}
            {leaderboard.length >= 3 && (
              <div className="animate-enter" style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 14 }}>
                {leaderboard.slice(0, 3).map((entry, i) => (
                  <div key={entry.team_id} className="card-grid" style={{ padding: 24, textAlign: "center", borderTop: `3px solid ${i === 0 ? "#111" : i === 1 ? "#888" : "#ccc"}` }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: "#999", marginBottom: 8 }}>{medalLabels[i]}</div>
                    <div style={{ fontSize: 17, fontWeight: 700, marginBottom: 4 }}>{entry.team_name}</div>
                    <div style={{ fontSize: 12, color: "#999", marginBottom: 14 }}>{entry.count} evaluations</div>
                    <div style={{ display: "flex", justifyContent: "center" }}>
                      <ScoreRing score={entry.avg_score} size={64} />
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Full List */}
            <div className="card-grid animate-enter" style={{ overflow: "hidden" }}>
              <div style={{ padding: "12px 18px", borderBottom: "1px solid #e8e8e8" }}>
                <span style={{ fontSize: 13, fontWeight: 600 }}>Full Rankings</span>
              </div>
              {leaderboard.map((entry, i) => (
                <div key={entry.team_id} style={{ padding: "14px 18px", display: "flex", alignItems: "center", gap: 14, borderBottom: "1px solid #f0f0f0" }}>
                  <div style={{
                    width: 34, height: 34, display: "flex", alignItems: "center", justifyContent: "center",
                    borderRadius: 8, fontSize: 13, fontWeight: 700,
                    background: i < 3 ? "#111" : "#f5f5f5",
                    color: i < 3 ? "#fff" : "#999",
                  }}>#{entry.rank}</div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 14, fontWeight: 600 }}>{entry.team_name}</div>
                    <div style={{ fontSize: 12, color: "#999", marginTop: 1 }}>{entry.count} eval{entry.count !== 1 ? "s" : ""}</div>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <div style={{ width: 80, height: 5, background: "#f0f0f0", borderRadius: 3, overflow: "hidden" }}>
                      <div style={{ height: "100%", width: `${entry.avg_score}%`, background: getScoreColor(entry.avg_score), borderRadius: 3, transition: "width 1s ease" }} />
                    </div>
                    <span style={{ fontSize: 18, fontWeight: 700, color: getScoreColor(entry.avg_score), minWidth: 40, textAlign: "right" }}>{entry.avg_score}</span>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </OrganizerLayout>
  );
}
