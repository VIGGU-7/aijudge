import { useState, useEffect } from "react";
import OrganizerLayout from "../../components/OrganizerLayout";
import { teamApi, projectApi, plagiarismApi } from "../../lib/api";
import { ShieldAlert, RefreshCw, FileCode, AlertTriangle, CheckCircle, XCircle, ChevronDown, ChevronUp } from "lucide-react";

export default function PlagiarismReportPage() {
  const [teams, setTeams] = useState([]);
  const [reports, setReports] = useState({});
  const [loading, setLoading] = useState(true);
  const [runningTeam, setRunningTeam] = useState(null);
  const [expandedTeam, setExpandedTeam] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const [teamRes, reportRes] = await Promise.all([
          teamApi.list(),
          plagiarismApi.listReports(),
        ]);
        setTeams(teamRes.data || []);
        const reportMap = {};
        (reportRes.data || []).forEach((r) => { reportMap[r.team_id] = r; });
        setReports(reportMap);
      } catch (e) { console.error(e); }
      finally { setLoading(false); }
    })();
  }, []);

  const runCheck = async (team) => {
    const repoUrl = team.github_repo || team.github_url || team.repo_url;
    if (!repoUrl) return alert("This team has no GitHub repo URL configured.");
    setRunningTeam(team.id);
    try {
      const res = await plagiarismApi.check(team.id, repoUrl);
      setReports((prev) => ({ ...prev, [team.id]: res.data }));
      setExpandedTeam(team.id);
    } catch (e) {
      alert(e.response?.data?.detail || e.message || "Plagiarism check failed");
    } finally { setRunningTeam(null); }
  };

  const scoreColor = (s) => {
    if (s >= 50) return "#ef4444";
    if (s >= 20) return "#f59e0b";
    return "#22c55e";
  };

  const riskBadge = (level) => {
    const map = {
      high: { bg: "#fef2f2", color: "#dc2626", border: "#fecaca" },
      medium: { bg: "#fffbeb", color: "#d97706", border: "#fde68a" },
      low: { bg: "#f0fdf4", color: "#16a34a", border: "#bbf7d0" },
      minimal: { bg: "#f8fafc", color: "#64748b", border: "#e2e8f0" },
    };
    const s = map[level] || map.minimal;
    return (
      <span style={{ padding: "3px 10px", borderRadius: 999, fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em", background: s.bg, color: s.color, border: `1px solid ${s.border}` }}>
        {level}
      </span>
    );
  };

  if (loading) return <OrganizerLayout><div style={{ display: "flex", justifyContent: "center", padding: 120 }}><span className="overline animate-pulse-subtle">Loading teams...</span></div></OrganizerLayout>;

  return (
    <OrganizerLayout>
      <div style={{ marginBottom: 28 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 6 }}>
          <ShieldAlert size={22} strokeWidth={2.2} />
          <h1 className="page-title" style={{ margin: 0 }}>Plagiarism Detection</h1>
        </div>
        <p style={{ fontSize: 13, color: "#888", margin: 0 }}>Analyze team repositories for code plagiarism using AI-powered detection.</p>
      </div>

      {teams.length === 0 ? (
        <div className="card-grid" style={{ padding: 40, textAlign: "center", color: "#999" }}>
          No teams found. Teams need to submit projects first.
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {teams.map((team) => {
            const report = reports[team.id];
            const isRunning = runningTeam === team.id;
            const isExpanded = expandedTeam === team.id;
            const repoUrl = team.github_repo || team.github_url || team.repo_url;

            return (
              <div key={team.id} className="card-grid" style={{ overflow: "hidden" }}>
                {/* Team Header */}
                <div style={{ padding: "14px 20px", display: "flex", alignItems: "center", justifyContent: "space-between", borderBottom: isExpanded && report ? "1px solid #e8e8e8" : "none" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 14, flex: 1, minWidth: 0 }}>
                    <div style={{ width: 36, height: 36, background: "#111", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center", color: "#fff", fontSize: 13, fontWeight: 700, flexShrink: 0 }}>
                      {team.name?.[0]?.toUpperCase() || "T"}
                    </div>
                    <div style={{ minWidth: 0, flex: 1 }}>
                      <div style={{ fontSize: 14, fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{team.name}</div>
                      <div style={{ fontSize: 11, color: "#999", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                        {repoUrl ? <a href={repoUrl} target="_blank" rel="noopener noreferrer" style={{ color: "#666" }}>{repoUrl}</a> : <span style={{ color: "#ccc" }}>No repo linked</span>}
                      </div>
                    </div>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: 12, flexShrink: 0 }}>
                    {report && (
                      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                        {riskBadge(report.risk_level)}
                        <div style={{ width: 120, height: 8, background: "#f0f0f0", borderRadius: 999, overflow: "hidden" }}>
                          <div style={{ width: `${Math.min(report.overall_score, 100)}%`, height: "100%", background: scoreColor(report.overall_score), borderRadius: 999, transition: "width 600ms ease" }} />
                        </div>
                        <span style={{ fontSize: 13, fontWeight: 700, color: scoreColor(report.overall_score), minWidth: 36, textAlign: "right" }}>{report.overall_score}%</span>
                        <button
                          onClick={() => setExpandedTeam(isExpanded ? null : team.id)}
                          className="btn btn-outline"
                          style={{ padding: "5px 8px", fontSize: 10 }}
                        >
                          {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                        </button>
                      </div>
                    )}
                    <button
                      onClick={() => runCheck(team)}
                      disabled={isRunning || !repoUrl}
                      className="btn btn-primary"
                      style={{ fontSize: 11, padding: "7px 14px", gap: 6, opacity: !repoUrl ? 0.4 : 1 }}
                    >
                      {isRunning ? <><RefreshCw size={12} className="animate-spin" /> Analyzing...</> : <><ShieldAlert size={12} /> {report ? "Re-check" : "Run Check"}</>}
                    </button>
                  </div>
                </div>

                {/* Expanded Report Details */}
                {isExpanded && report && (
                  <div style={{ padding: 20 }}>
                    {/* Summary */}
                    <div style={{ marginBottom: 20, padding: "12px 16px", background: "#fafafa", border: "1px solid #e8e8e8", borderRadius: 8 }}>
                      <p style={{ fontSize: 13, color: "#555", margin: 0, lineHeight: 1.6 }}>{report.summary}</p>
                      <div style={{ marginTop: 8, fontSize: 11, color: "#999" }}>
                        {report.files_analyzed} files analyzed · Last checked: {new Date(report.checked_at).toLocaleString()}
                      </div>
                    </div>

                    {/* File Breakdown Table */}
                    {report.files?.length > 0 && (
                      <div style={{ border: "1px solid #e8e8e8", borderRadius: 8, overflow: "hidden" }}>
                        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                          <thead>
                            <tr style={{ background: "#fafafa", borderBottom: "1px solid #e8e8e8" }}>
                              <th style={{ padding: "10px 14px", textAlign: "left", fontWeight: 600, color: "#555", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.04em" }}>File</th>
                              <th style={{ padding: "10px 14px", textAlign: "center", fontWeight: 600, color: "#555", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.04em", width: 120 }}>Plagiarism %</th>
                              <th style={{ padding: "10px 14px", textAlign: "left", fontWeight: 600, color: "#555", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.04em" }}>Matched Source</th>
                              <th style={{ padding: "10px 14px", textAlign: "left", fontWeight: 600, color: "#555", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.04em" }}>Reason</th>
                            </tr>
                          </thead>
                          <tbody>
                            {report.files.map((file, i) => (
                              <tr key={i} style={{ borderBottom: i < report.files.length - 1 ? "1px solid #f0f0f0" : "none" }}>
                                <td style={{ padding: "10px 14px" }}>
                                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                    <FileCode size={13} style={{ color: "#888", flexShrink: 0 }} />
                                    <span style={{ fontFamily: "JetBrains Mono, monospace", fontSize: 11, color: "#333" }}>{file.filename}</span>
                                  </div>
                                </td>
                                <td style={{ padding: "10px 14px", textAlign: "center" }}>
                                  <div style={{ display: "flex", alignItems: "center", gap: 8, justifyContent: "center" }}>
                                    <div style={{ width: 50, height: 6, background: "#f0f0f0", borderRadius: 999, overflow: "hidden" }}>
                                      <div style={{ width: `${Math.min(file.plagiarism_score, 100)}%`, height: "100%", background: scoreColor(file.plagiarism_score), borderRadius: 999 }} />
                                    </div>
                                    <span style={{ fontSize: 12, fontWeight: 700, color: scoreColor(file.plagiarism_score), minWidth: 30 }}>{file.plagiarism_score}%</span>
                                  </div>
                                </td>
                                <td style={{ padding: "10px 14px", fontSize: 11, color: "#666" }}>{file.matched_source}</td>
                                <td style={{ padding: "10px 14px", fontSize: 11, color: "#888", maxWidth: 250 }}>{file.reason}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </OrganizerLayout>
  );
}
