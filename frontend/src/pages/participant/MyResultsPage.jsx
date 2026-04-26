import { useState, useEffect } from "react";
import ParticipantLayout from "../../components/ParticipantLayout";
import { vivaApi, evalApi, teamApi, reportApi } from "../../lib/api";
import { useAuth } from "../../context/AuthContext";
import { RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import { Mic, BarChart3, HelpCircle, ClipboardList, FileDown, Loader } from "lucide-react";

function ScoreRing({ score, size = 56 }) {
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

export default function MyResultsPage() {
  const { user } = useAuth();
  const [sessions, setSessions] = useState([]);
  const [evaluations, setEvaluations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const tRes = await teamApi.getMy();
        if (tRes.data) {
          const [sRes, eRes] = await Promise.all([vivaApi.getSessions(tRes.data.id), evalApi.getForTeam(tRes.data.id)]);
          setSessions(sRes.data || []);
          setEvaluations(eRes.data || []);
        }
      } catch {}
      setLoading(false);
    })();
  }, []);

  const avgVivaScore = () => {
    const scores = sessions.map((s) => s.summary?.overall_score ?? null).filter((score) => score != null);
    return scores.length ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : null;
  };

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

  const progressData = [...sessions].reverse().map((s, i) => ({
    session: `S${i + 1}`,
    score: s.summary?.overall_score || 0,
  }));

  const totalQuestions = sessions.reduce((sum, s) => sum + (s.questions?.length || 0), 0);
  const scoreColor = (s) => s >= 80 ? "#22c55e" : s >= 60 ? "#f59e0b" : "#ef4444";

  if (loading) return <ParticipantLayout><div style={{ display: "flex", justifyContent: "center", padding: 120 }}><span className="overline animate-pulse-subtle">Loading results...</span></div></ParticipantLayout>;

  return (
    <ParticipantLayout>
      <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
        <div className="animate-enter" style={{ paddingBottom: 20, borderBottom: "1px solid #e8e8e8", display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <h1 style={{ fontSize: 28, fontWeight: 700, letterSpacing: "-0.02em" }}>My Results</h1>
            <p style={{ color: "#999", fontSize: 14, marginTop: 4 }}>Your viva performance and evaluation history</p>
          </div>
          {user && (
            <button
              onClick={async () => {
                setDownloading(true);
                try {
                  const res = await reportApi.participantPdf(user._id || user.id);
                  const url = window.URL.createObjectURL(new Blob([res.data], { type: "application/pdf" }));
                  const a = document.createElement("a"); a.href = url;
                  a.download = `${(user.name || "report").replace(/\s+/g, "_")}_report.pdf`;
                  document.body.appendChild(a); a.click(); a.remove();
                  window.URL.revokeObjectURL(url);
                } catch (e) { console.error(e); alert("Failed to generate report"); }
                finally { setDownloading(false); }
              }}
              disabled={downloading}
              className="btn btn-primary"
              style={{ fontSize: 12, padding: "9px 18px", gap: 7, display: "flex", alignItems: "center" }}
            >
              {downloading ? <><Loader size={13} className="animate-spin" /> Generating...</> : <><FileDown size={14} /> Download My Report</>}
            </button>
          )}
        </div>

        {/* Stats */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 14 }}>
          {[
            { label: "Sessions", value: sessions.length, icon: Mic, color: "#111" },
            { label: "Avg Score", value: avgVivaScore() ?? "—", icon: BarChart3, color: avgVivaScore() ? scoreColor(avgVivaScore()) : "#ccc" },
            { label: "Questions", value: totalQuestions, icon: HelpCircle, color: "#111" },
            { label: "Evaluations", value: evaluations.length, icon: ClipboardList, color: "#111" },
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
                <span className="stat-number" style={{ color: s.color }}>{s.value}</span>
              </div>
            );
          })}
        </div>

        {/* Charts */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          {radarData.length > 0 && (
            <div className="card-grid animate-enter" style={{ overflow: "hidden" }}>
              <div style={{ padding: "12px 18px", borderBottom: "1px solid #e8e8e8" }}>
                <span style={{ fontSize: 13, fontWeight: 600 }}>Skill Breakdown</span>
                <p style={{ fontSize: 12, color: "#999", marginTop: 2 }}>Average score per category</p>
              </div>
              <div style={{ padding: 14 }}>
                <ResponsiveContainer width="100%" height={240}>
                  <RadarChart data={radarData}>
                    <PolarGrid stroke="#f0f0f0" />
                    <PolarAngleAxis dataKey="category" tick={{ fill: "#999", fontSize: 11 }} />
                    <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
                    <Radar name="Score" dataKey="score" stroke="#111" fill="#111" fillOpacity={0.08} strokeWidth={2} />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {progressData.length > 1 && (
            <div className="card-grid animate-enter" style={{ overflow: "hidden" }}>
              <div style={{ padding: "12px 18px", borderBottom: "1px solid #e8e8e8" }}>
                <span style={{ fontSize: 13, fontWeight: 600 }}>Score Progress</span>
                <p style={{ fontSize: 12, color: "#999", marginTop: 2 }}>Your improvement over time</p>
              </div>
              <div style={{ padding: "14px 10px 6px 0" }}>
                <ResponsiveContainer width="100%" height={240}>
                  <AreaChart data={progressData}>
                    <defs>
                      <linearGradient id="progressGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#111" stopOpacity={0.1}/>
                        <stop offset="95%" stopColor="#111" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="session" tick={{ fill: "#999", fontSize: 11 }} axisLine={false} tickLine={false} />
                    <YAxis domain={[0, 100]} tick={{ fill: "#999", fontSize: 11 }} axisLine={false} tickLine={false} />
                    <Tooltip />
                    <Area type="monotone" dataKey="score" stroke="#111" fill="url(#progressGrad)" strokeWidth={2} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </div>

        {/* Session History */}
        <div className="card-grid animate-enter" style={{ overflow: "hidden" }}>
          <div style={{ padding: "12px 18px", borderBottom: "1px solid #e8e8e8" }}>
            <span style={{ fontSize: 13, fontWeight: 600 }}>Viva Session History</span>
          </div>
          <div style={{ padding: 14, display: "flex", flexDirection: "column", gap: 12 }}>
            {sessions.length === 0 ? (
              <div style={{ textAlign: "center", padding: 36 }}>
                <Mic size={28} color="#ddd" style={{ marginBottom: 10 }} />
                <p style={{ color: "#bbb", fontSize: 13 }}>No viva sessions yet — start one to see results!</p>
              </div>
            ) : sessions.map((s, i) => (
              <div key={i} className="card-grid" style={{ overflow: "hidden" }}>
                <div style={{ padding: "10px 14px", display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #f0f0f0" }}>
                  <span style={{ fontSize: 13, fontWeight: 600 }}>Session {sessions.length - i}</span>
                  <span className="badge badge-info">{s.created_at?.split("T")[0]}</span>
                </div>
                <div style={{ padding: 14 }}>
                  {s.summary && (
                    <div style={{ display: "flex", alignItems: "center", gap: 16, padding: 14, background: "#fafafa", border: "1px solid #e8e8e8", borderRadius: 8, marginBottom: 10 }}>
                      <ScoreRing score={s.summary.overall_score || 0} size={50} />
                      <div>
                        <div style={{ fontSize: 14, fontWeight: 600, textTransform: "capitalize" }}>{s.summary.understanding_level}</div>
                        <div style={{ fontSize: 12, color: "#999", marginTop: 2 }}>{s.questions?.length || 0} questions</div>
                      </div>
                    </div>
                  )}
                  {(s.questions || []).map((q, j) => (
                    <div key={j} style={{ padding: 10, background: "#fafafa", border: "1px solid #e8e8e8", borderRadius: 8, marginBottom: 6 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                        <span className="badge badge-info" style={{ fontSize: 10 }}>{q.category?.replace(/_/g, " ")}</span>
                        {q.evaluation && <span style={{ fontSize: 13, fontWeight: 700, color: scoreColor(q.evaluation.score) }}>{q.evaluation.score}/100</span>}
                      </div>
                      <p style={{ fontSize: 12, color: "#555", lineHeight: 1.5 }}>{q.question?.slice(0, 120)}</p>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </ParticipantLayout>
  );
}
