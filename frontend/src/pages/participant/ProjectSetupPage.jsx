import { useState, useEffect } from "react";
import ParticipantLayout from "../../components/ParticipantLayout";
import { projectApi, teamApi } from "../../lib/api";
import { Link2, Zap, Wrench, FileUp, Brain, AlertTriangle, Plus, X } from "lucide-react";

export default function ProjectSetupPage() {
  const [myTeam, setMyTeam] = useState(null);
  const [githubUrl, setGithubUrl] = useState("");
  const [features, setFeatures] = useState([""]);
  const [techStack, setTechStack] = useState([""]);
  const [description, setDescription] = useState("");
  const [pptFile, setPptFile] = useState(null);
  const [pptMeta, setPptMeta] = useState(null);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [building, setBuilding] = useState(false);
  const [status, setStatus] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const res = await teamApi.getMy();
        if (res.data) {
          setMyTeam(res.data);
          await Promise.all([loadProjectInfo(res.data.id), loadPptInfo(res.data.id), loadProfile(res.data.id)]);
        }
      } catch {}
      finally { setLoading(false); }
    })();
  }, []);

  const loadProjectInfo = async (tid) => {
    try {
      const r = await projectApi.getInfo(tid);
      if (!r.data) return;
      setGithubUrl(r.data.github_url || "");
      setFeatures(r.data.features?.length ? r.data.features : [""]);
      setTechStack(r.data.tech_stack?.length ? r.data.tech_stack : [""]);
      setDescription(r.data.project_description || "");
    } catch {}
  };

  const loadProfile = async (tid) => {
    try { const r = await projectApi.getProfile(tid); if (r.data) setProfile(r.data.profile); } catch {}
  };

  const loadPptInfo = async (tid) => {
    try {
      const r = await projectApi.getPpt(tid);
      setPptMeta(r.data || null);
    } catch {}
  };

  const handleSaveInfo = async () => {
    if (!myTeam) return;
    setSaving(true); setStatus("");
    try {
      await projectApi.submitInfo(myTeam.id, { github_url: githubUrl || null, features: features.filter(Boolean), tech_stack: techStack.filter(Boolean), project_description: description });
      setStatus("Project info saved!");
    } catch (e) { setStatus("Error saving: " + (e.response?.data?.detail || e.message)); }
    finally { setSaving(false); }
  };

  const handleUploadPpt = async () => {
    if (!myTeam || !pptFile) return;
    setUploading(true); setStatus("");
    try {
      const r = await projectApi.uploadPpt(myTeam.id, pptFile);
      setPptMeta({ filename: r.data.filename, slides_count: r.data.slides_count, format: r.data.format });
      setStatus(`PPT uploaded! ${r.data.slides_count} slides extracted.`);
    } catch (e) { setStatus("Upload error: " + (e.response?.data?.detail || e.message)); }
    finally { setUploading(false); }
  };

  const handleBuildContext = async () => {
    if (!myTeam) return;
    setBuilding(true); setStatus("Building AI context profile... This may take a minute.");
    try {
      const r = await projectApi.buildContext(myTeam.id);
      setProfile(r.data.profile);
      setStatus("Context profile built successfully!");
    } catch (e) { setStatus("Build error: " + (e.response?.data?.detail || e.message)); }
    finally { setBuilding(false); }
  };

  const addField = (arr, setArr) => setArr([...arr, ""]);
  const updateField = (arr, setArr, i, val) => { const n = [...arr]; n[i] = val; setArr(n); };
  const removeField = (arr, setArr, i) => setArr(arr.filter((_, j) => j !== i));
  const hasProjectInput = Boolean(githubUrl.trim() || description.trim() || features.some((f) => f.trim()) || techStack.some((t) => t.trim()) || pptMeta);

  if (loading) return <ParticipantLayout><div style={{ display: "flex", justifyContent: "center", padding: 80 }}><span className="overline animate-pulse-subtle">Loading project setup...</span></div></ParticipantLayout>;

  return (
    <ParticipantLayout>
      <div style={{ display: "flex", flexDirection: "column", gap: 22 }}>
        <div className="animate-enter" style={{ paddingBottom: 20, borderBottom: "1px solid #e8e8e8" }}>
          <h1 style={{ fontSize: 28, fontWeight: 700, letterSpacing: "-0.02em" }}>Project Setup</h1>
          <p style={{ color: "#999", fontSize: 14, marginTop: 4 }}>Submit your project details so the AI can analyze your codebase and ask targeted viva questions.</p>
        </div>

        {!myTeam && (
          <div className="card-grid" style={{ padding: 28, display: "flex", alignItems: "center", gap: 12, borderLeft: "3px solid #f59e0b" }}>
            <AlertTriangle size={18} color="#d97706" />
            <div>
              <p style={{ fontWeight: 600, fontSize: 14, color: "#92400e" }}>You need to join a team first</p>
              <p style={{ fontSize: 13, color: "#999", marginTop: 2 }}>Ask your organizer to add you to a hackathon team.</p>
            </div>
          </div>
        )}

        {myTeam && (
          <>
            {/* GitHub & Description */}
            <div className="card-grid animate-enter" style={{ overflow: "hidden" }}>
              <div style={{ padding: "12px 18px", borderBottom: "1px solid #e8e8e8", background: "#fafafa", display: "flex", alignItems: "center", gap: 8 }}>
                <Link2 size={14} color="#555" />
                <span style={{ fontSize: 13, fontWeight: 600 }}>Project Info</span>
              </div>
              <div style={{ padding: 22, display: "flex", flexDirection: "column", gap: 16 }}>
                <div>
                  <label style={{ display: "block", marginBottom: 6, fontSize: 13, fontWeight: 600, color: "#555" }}>GitHub Repository URL</label>
                  <input type="url" value={githubUrl} onChange={(e) => setGithubUrl(e.target.value)} placeholder="https://github.com/user/repo" />
                </div>
                <div>
                  <label style={{ display: "block", marginBottom: 6, fontSize: 13, fontWeight: 600, color: "#555" }}>Project Description</label>
                  <textarea value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Describe what your project does..." rows={3} style={{ resize: "vertical" }} />
                </div>
              </div>
            </div>

            {/* Features */}
            <div className="card-grid animate-enter" style={{ overflow: "hidden" }}>
              <div style={{ padding: "12px 18px", borderBottom: "1px solid #e8e8e8", background: "#fafafa", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <Zap size={14} color="#555" />
                  <span style={{ fontSize: 13, fontWeight: 600 }}>Features You Built</span>
                </div>
                <button onClick={() => addField(features, setFeatures)} className="btn btn-outline" style={{ fontSize: 11, padding: "4px 10px", gap: 4 }}><Plus size={11} /> Add</button>
              </div>
              <div style={{ padding: 22, display: "flex", flexDirection: "column", gap: 10 }}>
                {features.map((f, i) => (
                  <div key={i} style={{ display: "flex", gap: 8 }}>
                    <input value={f} onChange={(e) => updateField(features, setFeatures, i, e.target.value)} placeholder={`Feature ${i + 1}`} style={{ flex: 1 }} />
                    {features.length > 1 && <button onClick={() => removeField(features, setFeatures, i)} style={{ background: "none", border: "1px solid #fecaca", color: "#dc2626", borderRadius: 8, padding: "0 10px", cursor: "pointer", display: "flex", alignItems: "center" }}><X size={14} /></button>}
                  </div>
                ))}
              </div>
            </div>

            {/* Tech Stack */}
            <div className="card-grid animate-enter" style={{ overflow: "hidden" }}>
              <div style={{ padding: "12px 18px", borderBottom: "1px solid #e8e8e8", background: "#fafafa", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <Wrench size={14} color="#555" />
                  <span style={{ fontSize: 13, fontWeight: 600 }}>Tech Stack</span>
                </div>
                <button onClick={() => addField(techStack, setTechStack)} className="btn btn-outline" style={{ fontSize: 11, padding: "4px 10px", gap: 4 }}><Plus size={11} /> Add</button>
              </div>
              <div style={{ padding: 22, display: "flex", flexDirection: "column", gap: 10 }}>
                {techStack.map((t, i) => (
                  <div key={i} style={{ display: "flex", gap: 8 }}>
                    <input value={t} onChange={(e) => updateField(techStack, setTechStack, i, e.target.value)} placeholder={`Technology ${i + 1}`} style={{ flex: 1 }} />
                    {techStack.length > 1 && <button onClick={() => removeField(techStack, setTechStack, i)} style={{ background: "none", border: "1px solid #fecaca", color: "#dc2626", borderRadius: 8, padding: "0 10px", cursor: "pointer", display: "flex", alignItems: "center" }}><X size={14} /></button>}
                  </div>
                ))}
              </div>
            </div>

            <button onClick={handleSaveInfo} disabled={saving} className="btn btn-primary" style={{ height: 46 }}>{saving ? "Saving..." : "Save Project Info"}</button>

            {/* PPT Upload */}
            <div className="card-grid animate-enter" style={{ overflow: "hidden" }}>
              <div style={{ padding: "12px 18px", borderBottom: "1px solid #e8e8e8", background: "#fafafa", display: "flex", alignItems: "center", gap: 8 }}>
                <FileUp size={14} color="#555" />
                <span style={{ fontSize: 13, fontWeight: 600 }}>Presentation Upload</span>
              </div>
              <div style={{ padding: 22, display: "flex", flexDirection: "column", gap: 14 }}>
                <div style={{ border: "2px dashed #ddd", borderRadius: 8, padding: 28, textAlign: "center", cursor: "pointer" }} onClick={() => document.getElementById("ppt-input").click()}>
                  <input id="ppt-input" type="file" accept=".pptx,.pdf" onChange={(e) => setPptFile(e.target.files[0])} style={{ display: "none" }} />
                  <FileUp size={28} color="#ccc" style={{ marginBottom: 8 }} />
                  <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 4 }}>{pptFile ? pptFile.name : "Click to upload your PPT/PDF"}</div>
                  <div style={{ fontSize: 12, color: "#bbb" }}>Supports PPTX and PDF</div>
                </div>
                {pptMeta && (
                  <div style={{ padding: 12, background: "#f0fdf4", border: "1px solid #bbf7d0", borderRadius: 8 }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: "#16a34a", marginBottom: 4 }}>Uploaded presentation ready</div>
                    <div style={{ fontSize: 11, color: "#888" }}>{pptMeta.filename} · {pptMeta.slides_count ?? 0} slides · {String(pptMeta.format || "").toUpperCase()}</div>
                  </div>
                )}
                <button onClick={handleUploadPpt} disabled={!pptFile || uploading} className="btn btn-outline" style={{ height: 42 }}>{uploading ? "Uploading..." : "Upload Presentation"}</button>
              </div>
            </div>

            {/* Build Context */}
            <div className="card-grid animate-enter" style={{ padding: 24, borderLeft: "3px solid #111" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                <Brain size={16} color="#111" />
                <h3 style={{ fontSize: 15, fontWeight: 600 }}>Build AI Context Profile</h3>
              </div>
              <p style={{ color: "#999", fontSize: 13, marginBottom: 16 }}>Once you've saved your info and uploaded your PPT, click below to let the AI analyze everything and build your context profile.</p>
              <button onClick={handleBuildContext} disabled={building || !hasProjectInput} className="btn btn-primary" style={{ height: 46 }}>{building ? "Building... (this takes ~30s)" : "Build AI Context Profile"}</button>
              {!hasProjectInput && <p style={{ fontSize: 12, color: "#999", marginTop: 10 }}>Save project info or upload a presentation first.</p>}
            </div>

            {status && <div style={{ padding: "10px 14px", background: "#fafafa", border: "1px solid #e8e8e8", borderRadius: 8, fontSize: 13, fontFamily: "JetBrains Mono" }}>{status}</div>}

            {/* Profile Preview */}
            {profile && (
              <div className="card-grid animate-enter" style={{ overflow: "hidden" }}>
                <div style={{ padding: "12px 18px", borderBottom: "1px solid #e8e8e8", background: "#fafafa", display: "flex", alignItems: "center", gap: 8 }}>
                  <Brain size={14} color="#555" />
                  <span style={{ fontSize: 13, fontWeight: 600 }}>AI Context Profile</span>
                </div>
                <div style={{ padding: 18 }}>
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
          </>
        )}
      </div>
    </ParticipantLayout>
  );
}
