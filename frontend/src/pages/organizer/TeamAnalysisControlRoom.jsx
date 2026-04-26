import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import OrganizerLayout from "../../components/OrganizerLayout";
import { teamApi, projectApi, vivaApi, evalApi } from "../../lib/api";
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from "recharts";
import { Search, AlertTriangle, MessageCircle } from "lucide-react";

function ScoreRing({ score, label, size = 80 }) {
  const color = score >= 80 ? "#22c55e" : score >= 60 ? "#f59e0b" : "#ef4444";
  const radius = (size - 8) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6 }}>
      <div style={{ position: "relative", width: size, height: size }}>
        <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
          <circle cx={size/2} cy={size/2} r={radius} fill="none" stroke="#f0f0f0" strokeWidth={4} />
          <circle cx={size/2} cy={size/2} r={radius} fill="none" stroke={color} strokeWidth={4}
            strokeDasharray={circumference} strokeDashoffset={offset} strokeLinecap="round"
            style={{ transition: "stroke-dashoffset 1.2s ease" }} />
        </svg>
        <div style={{
          position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center",
          flexDirection: "column",
        }}>
          <span style={{ fontWeight: 700, fontSize: size * 0.28, color }}>{score}</span>
          <span style={{ fontSize: 9, color: "#bbb" }}>/ 100</span>
        </div>
      </div>
      <span style={{ fontSize: 11, fontWeight: 600, color: "#999", textTransform: "uppercase", letterSpacing: "0.03em" }}>{label}</span>
    </div>
  );
}

export default function TeamAnalysisControlRoom() {
  const { teamId } = useParams();
  const [team, setTeam] = useState(null);
  const [profile, setProfile] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [evaluations, setEvaluations] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!teamId) return;
    (async () => {
      try {
        const [tRes, pRes, sRes, eRes] = await Promise.all([
          teamApi.get(teamId), projectApi.getProfile(teamId),
          vivaApi.getSessions(teamId), evalApi.getForTeam(teamId),
        ]);
        setTeam(tRes.data);
        setProfile(pRes.data?.profile || null);
        setSessions(sRes.data || []);
        setEvaluations(eRes.data || []);
      } catch {}
      setLoading(false);
    })();
  }, [teamId]);

  const scoreColor = (s) => s >= 80 ? "#22c55e" : s >= 60 ? "#f59e0b" : "#ef4444";

  if (loading) return <OrganizerLayout><div style={{ display: "flex", justifyContent: "center", padding: 120 }}><span className="overline animate-pulse-subtle">Analyzing team data...</span></div></OrganizerLayout>;
  if (!team) return <OrganizerLayout><div style={{ textAlign: "center", padding: 120, color: "#bbb" }}>Team not found</div></OrganizerLayout>;

  const categoryScores = {};
  sessions.forEach(s => {
    (s.questions || []).forEach(q => {
      if (q.evaluation?.score && q.category) {
        const cat = q.category.replace(/_/g, " ");
        if (!categoryScores[cat]) categoryScores[cat] = [];
        categoryScores[cat].push(q.evaluation.score);
      }
    });
  });
  const radarData = Object.entries(categoryScores).map(([cat, scores]) => ({
    category: cat.charAt(0).toUpperCase() + cat.slice(1),
    score: Math.round(scores.reduce((a, b) => a + b, 0) / scores.length),
    fullMark: 100,
  }));

  const difficultyDist = {};
  sessions.forEach(s => {
    (s.questions || []).forEach(q => {
      const d = q.difficulty || "unknown";
      difficultyDist[d] = (difficultyDist[d] || 0) + 1;
    });
  });
  const diffPieData = Object.entries(difficultyDist).map(([name, value]) => ({ name: name.charAt(0).toUpperCase() + name.slice(1), value }));
  const diffColors = { Easy: "#22c55e", Medium: "#f59e0b", Hard: "#ef4444", Unknown: "#ccc" };

  const totalQuestions = sessions.reduce((sum, s) => sum + (s.questions?.length || 0), 0);
  const answeredQuestions = sessions.reduce((sum, s) => sum + (s.questions?.filter(q => q.answer)?.length || 0), 0);

  return (
    <OrganizerLayout>
      <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
        {/* Header */}
        <div className="animate-enter" style={{ paddingBottom: 20, borderBottom: "1px solid #e8e8e8" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 6 }}>
            <div style={{ width: 40, height: 40, background: "#111", borderRadius: 10, display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Search size={18} color="#fff" />
            </div>
            <div>
              <h1 style={{ fontSize: 26, fontWeight: 700, letterSpacing: "-0.02em" }}>{team.name}</h1>
              <p style={{ color: "#999", fontSize: 13 }}>{team.members?.length} members · {team.github_repo || "No GitHub linked"}</p>
            </div>
          </div>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginTop: 10 }}>
            {(team.members || []).map((m, i) => (
              <span key={i} className={`badge ${m.role === "leader" ? "badge-ai" : "badge-info"}`}>{m.role === "leader" ? "★ " : ""}{m.name}</span>
            ))}
          </div>
        </div>

        {/* Score Gauges */}
        {profile?.ai_analysis && (
          <div className="card-grid animate-enter" style={{ padding: 28 }}>
            <div style={{ display: "flex", justifyContent: "space-around", alignItems: "center", flexWrap: "wrap", gap: 20 }}>
              <ScoreRing score={profile.ai_analysis.authenticity_score ?? 0} label="Authenticity" size={90} />
              <ScoreRing score={profile.ai_analysis.code_vs_claims_match ?? 0} label="Code Match" size={90} />
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6 }}>
                <div style={{
                  width: 90, height: 90, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center",
                  background: "#f5f5f5", border: "2px solid #e8e8e8",
                }}>
                  <span style={{ fontWeight: 700, fontSize: 14, textTransform: "capitalize" }}>{profile.ai_analysis.complexity_assessment || "—"}</span>
                </div>
                <span style={{ fontSize: 11, fontWeight: 600, color: "#999", textTransform: "uppercase" }}>Complexity</span>
              </div>
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6 }}>
                <div style={{
                  width: 90, height: 90, borderRadius: "50%", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
                  background: "#f5f5f5", border: "2px solid #e8e8e8",
                }}>
                  <span style={{ fontWeight: 700, fontSize: 26 }}>{sessions.length}</span>
                  <span style={{ fontSize: 9, color: "#999" }}>sessions</span>
                </div>
                <span style={{ fontSize: 11, fontWeight: 600, color: "#999", textTransform: "uppercase" }}>Viva Sessions</span>
              </div>
            </div>
          </div>
        )}

        {/* Charts */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          {radarData.length > 0 && (
            <div className="card-grid animate-enter" style={{ overflow: "hidden" }}>
              <div style={{ padding: "12px 18px", borderBottom: "1px solid #e8e8e8" }}>
                <span style={{ fontSize: 13, fontWeight: 600 }}>Skill Breakdown</span>
              </div>
              <div style={{ padding: 14 }}>
                <ResponsiveContainer width="100%" height={240}>
                  <RadarChart data={radarData}>
                    <PolarGrid stroke="#f0f0f0" />
                    <PolarAngleAxis dataKey="category" tick={{ fill: "#999", fontSize: 11 }} />
                    <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
                    <Radar name="Score" dataKey="score" stroke="#111" fill="#111" fillOpacity={0.06} strokeWidth={2} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          <div className="card-grid animate-enter" style={{ overflow: "hidden" }}>
            <div style={{ padding: "12px 18px", borderBottom: "1px solid #e8e8e8" }}>
              <span style={{ fontSize: 13, fontWeight: 600 }}>Question Analysis</span>
            </div>
            <div style={{ padding: 14, display: "flex", flexDirection: "column", alignItems: "center", gap: 14 }}>
              {diffPieData.length > 0 ? (
                <>
                  <ResponsiveContainer width="100%" height={160}>
                    <PieChart>
                      <Pie data={diffPieData} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={36} outerRadius={60} paddingAngle={3} strokeWidth={0}>
                        {diffPieData.map((d) => <Cell key={d.name} fill={diffColors[d.name] || "#ccc"} />)}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                  <div style={{ display: "flex", gap: 14, flexWrap: "wrap", justifyContent: "center" }}>
                    {diffPieData.map(d => (
                      <div key={d.name} style={{ display: "flex", alignItems: "center", gap: 5, fontSize: 12, color: "#999" }}>
                        <div style={{ width: 8, height: 8, borderRadius: "50%", background: diffColors[d.name] || "#ccc" }} /> {d.name} ({d.value})
                      </div>
                    ))}
                  </div>
                </>
              ) : <p style={{ color: "#bbb", fontSize: 13, padding: 16 }}>No questions asked yet</p>}
              <div style={{ width: "100%", display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                <div style={{ background: "#fafafa", border: "1px solid #e8e8e8", borderRadius: 8, padding: 12, textAlign: "center" }}>
                  <div style={{ fontSize: 20, fontWeight: 700 }}>{totalQuestions}</div>
                  <div style={{ fontSize: 11, color: "#999" }}>Total Questions</div>
                </div>
                <div style={{ background: "#fafafa", border: "1px solid #e8e8e8", borderRadius: 8, padding: 12, textAlign: "center" }}>
                  <div style={{ fontSize: 20, fontWeight: 700, color: "#22c55e" }}>{answeredQuestions}</div>
                  <div style={{ fontSize: 11, color: "#999" }}>Answered</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Red Flags */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          {profile?.ai_analysis?.claimed_but_not_found?.length > 0 && (
            <div className="card-grid animate-enter" style={{ overflow: "hidden", borderLeft: "3px solid #ef4444" }}>
              <div style={{ padding: "12px 18px", borderBottom: "1px solid #e8e8e8" }}>
                <span style={{ fontSize: 13, fontWeight: 600, color: "#dc2626", display: "flex", alignItems: "center", gap: 6 }}><AlertTriangle size={14} /> Red Flags — Not Found in Code</span>
              </div>
              <div style={{ padding: 14, display: "flex", flexDirection: "column", gap: 6 }}>
                {profile.ai_analysis.claimed_but_not_found.map((c, i) => (
                  <div key={i} style={{ padding: "8px 12px", background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 8, fontSize: 13 }}>{c}</div>
                ))}
              </div>
            </div>
          )}
          {profile?.ai_analysis?.key_areas_to_question?.length > 0 && (
            <div className="card-grid animate-enter" style={{ overflow: "hidden", borderLeft: "3px solid #f59e0b" }}>
              <div style={{ padding: "12px 18px", borderBottom: "1px solid #e8e8e8" }}>
                <span style={{ fontSize: 13, fontWeight: 600, color: "#d97706", display: "flex", alignItems: "center", gap: 6 }}><Search size={14} /> Areas to Investigate</span>
              </div>
              <div style={{ padding: 14, display: "flex", flexDirection: "column", gap: 6 }}>
                {profile.ai_analysis.key_areas_to_question.map((a, i) => (
                  <div key={i} style={{ padding: "8px 12px", background: "#fffbeb", border: "1px solid #fde68a", borderRadius: 8, fontSize: 13 }}>{a}</div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Viva Sessions */}
        <div className="card-grid animate-enter" style={{ overflow: "hidden" }}>
          <div style={{ padding: "12px 18px", borderBottom: "1px solid #e8e8e8", display: "flex", alignItems: "center", gap: 6 }}>
            <MessageCircle size={14} />
            <span style={{ fontSize: 13, fontWeight: 600 }}>Viva Session History</span>
          </div>
          <div style={{ padding: 14 }}>
            {sessions.length === 0 ? (
              <p style={{ color: "#bbb", textAlign: "center", padding: 28 }}>No viva sessions conducted yet</p>
            ) : sessions.map((s, si) => (
              <div key={si} style={{ marginBottom: 18 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                  <span style={{ fontSize: 12, fontWeight: 600, color: "#999" }}>Session {sessions.length - si}</span>
                  <span className="badge badge-info">{s.created_at?.split("T")[0]}</span>
                </div>
                {s.summary && (
                  <div style={{ display: "flex", alignItems: "center", gap: 14, padding: 12, background: "#fafafa", border: "1px solid #e8e8e8", borderRadius: 8, marginBottom: 8 }}>
                    <ScoreRing score={s.summary.overall_score || 0} label="" size={48} />
                    <div>
                      <div style={{ fontSize: 14, fontWeight: 600, textTransform: "capitalize" }}>{s.summary.understanding_level}</div>
                      <div style={{ fontSize: 12, color: "#999" }}>Overall session score</div>
                    </div>
                  </div>
                )}
                {(s.questions || []).map((q, qi) => (
                  <div key={qi} style={{ padding: 12, background: "#fafafa", border: "1px solid #e8e8e8", borderRadius: 8, marginBottom: 6 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                      <div style={{ display: "flex", gap: 5 }}>
                        <span className="badge badge-info" style={{ fontSize: 10 }}>{q.category?.replace(/_/g, " ")}</span>
                        {q.difficulty && <span className={`badge badge-${q.difficulty === "hard" ? "cheat" : q.difficulty === "medium" ? "warning" : "human"}`} style={{ fontSize: 10 }}>{q.difficulty}</span>}
                      </div>
                      {q.evaluation && <span style={{ fontSize: 14, fontWeight: 700, color: scoreColor(q.evaluation.score) }}>{q.evaluation.score}/100</span>}
                    </div>
                    <p style={{ fontSize: 13, color: "#555", marginBottom: 4 }}>Q: {q.question}</p>
                    {q.answer && <p style={{ fontSize: 12, color: "#999", marginBottom: 4 }}>A: {q.answer?.slice(0, 200)}{q.answer?.length > 200 ? "..." : ""}</p>}
                    {q.evaluation?.feedback && <p style={{ fontSize: 12, color: "#3b82f6", marginTop: 6 }}>💡 {q.evaluation.feedback?.slice(0, 200)}</p>}
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>

        {/* Raw Profile */}
        {profile && (
          <div className="card-grid animate-enter" style={{ overflow: "hidden" }}>
            <div style={{ padding: "12px 18px", borderBottom: "1px solid #e8e8e8" }}>
              <span style={{ fontSize: 13, fontWeight: 600 }}>Full AI Context Profile</span>
            </div>
            <div style={{ padding: 14 }}>
              <pre style={{
                background: "#fafafa", padding: 16, borderRadius: 8,
                border: "1px solid #e8e8e8", fontSize: 11, fontFamily: "JetBrains Mono",
                overflow: "auto", maxHeight: 400, whiteSpace: "pre-wrap", color: "#555", lineHeight: 1.7,
              }}>
                {JSON.stringify(profile, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </div>
    </OrganizerLayout>
  );
}
