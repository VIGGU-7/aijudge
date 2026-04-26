import { useState } from "react";
import { useNavigate } from "react-router-dom";
import ParticipantLayout from "../../components/ParticipantLayout";
import { videoVivaApi } from "../../lib/api";
import { Video, Upload, Loader, CheckCircle2, FileVideo, AlertTriangle } from "lucide-react";

const PIPELINE_STEPS = [
  "Uploading video to server...",
  "Extracting audio & generating transcript...",
  "Analyzing video frames chronologically...",
  "Building comprehensive summary...",
  "Generating 5 targeted viva questions...",
];

export default function VideoVivaPage() {
  const navigate = useNavigate();
  const [videoFile, setVideoFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [pipelineStep, setPipelineStep] = useState(0);
  const [error, setError] = useState("");

  const handleUpload = async () => {
    if (!videoFile) return;
    setUploading(true);
    setError("");
    setPipelineStep(0);

    const interval = setInterval(() => {
      setPipelineStep((p) => (p < PIPELINE_STEPS.length - 1 ? p + 1 : p));
    }, 8000);

    try {
      const res = await videoVivaApi.upload(videoFile);
      clearInterval(interval);
      const sessionId = res.data.session_id;
      // Redirect to AI Viva Session with the video session ID
      navigate(`/p/viva?video_session=${sessionId}`);
    } catch (e) {
      clearInterval(interval);
      setError(e.response?.data?.detail || e.message || "Video processing failed. Please try again.");
      setUploading(false);
    }
  };

  return (
    <ParticipantLayout>
      <div style={{ display: "flex", flexDirection: "column", gap: 22 }}>
        {/* Header */}
        <div className="animate-enter" style={{ paddingBottom: 18, borderBottom: "1px solid #e8e8e8" }}>
          <h1 style={{ fontSize: 28, fontWeight: 700, letterSpacing: "-0.02em", display: "flex", alignItems: "center", gap: 10 }}>
            <Video size={24} /> Video Viva
          </h1>
          <p style={{ color: "#999", fontSize: 13, marginTop: 4 }}>
            Upload your hackathon explanation video — the AI will analyze it and generate a live viva session.
          </p>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 300px", gap: 20 }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

            {/* Upload Section */}
            {!uploading && (
              <div className="card-grid animate-enter" style={{ padding: 28, borderLeft: "3px solid #111" }}>
                <h3 style={{ fontSize: 15, fontWeight: 600, marginBottom: 6 }}>Upload Explanation Video</h3>
                <p style={{ color: "#999", fontSize: 13, marginBottom: 18 }}>
                  Record a video explaining your project — what you built, how it works, and your tech decisions.
                  The AI will watch, transcribe, and generate 5 targeted questions for a live viva session.
                </p>

                <div
                  style={{
                    border: "2px dashed #ddd", borderRadius: 10, padding: 36, textAlign: "center",
                    cursor: "pointer", marginBottom: 16, transition: "border-color 150ms",
                  }}
                  onClick={() => document.getElementById("video-input").click()}
                  onDragOver={(e) => { e.preventDefault(); e.currentTarget.style.borderColor = "#111"; }}
                  onDragLeave={(e) => { e.currentTarget.style.borderColor = "#ddd"; }}
                  onDrop={(e) => { e.preventDefault(); e.currentTarget.style.borderColor = "#ddd"; if (e.dataTransfer.files[0]) setVideoFile(e.dataTransfer.files[0]); }}
                >
                  <input id="video-input" type="file" accept="video/*" onChange={(e) => setVideoFile(e.target.files[0])} style={{ display: "none" }} />
                  {videoFile ? (
                    <>
                      <FileVideo size={32} color="#111" style={{ marginBottom: 8 }} />
                      <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 4 }}>{videoFile.name}</div>
                      <div style={{ fontSize: 12, color: "#999" }}>{(videoFile.size / (1024 * 1024)).toFixed(1)} MB</div>
                    </>
                  ) : (
                    <>
                      <Upload size={32} color="#ccc" style={{ marginBottom: 8 }} />
                      <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 4 }}>Drop your video here or click to browse</div>
                      <div style={{ fontSize: 12, color: "#bbb" }}>MP4, WebM, MOV — up to 200 MB</div>
                    </>
                  )}
                </div>

                {error && (
                  <div style={{ padding: "10px 14px", background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 8, color: "#dc2626", fontSize: 13, marginBottom: 14, display: "flex", alignItems: "center", gap: 8 }}>
                    <AlertTriangle size={14} /> {error}
                  </div>
                )}

                <button onClick={handleUpload} disabled={!videoFile} className="btn btn-primary" style={{ width: "100%", height: 46, fontSize: 14 }}>
                  Start Video Analysis Pipeline
                </button>
              </div>
            )}

            {/* Pipeline Loading */}
            {uploading && (
              <div className="card-grid animate-enter" style={{ padding: 32, textAlign: "center" }}>
                <Loader size={36} color="#111" className="animate-spin" style={{ margin: "0 auto 20px" }} />
                <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 16 }}>Processing Your Video</h3>
                <p style={{ color: "#999", fontSize: 13, marginBottom: 24 }}>
                  This may take 1–3 minutes depending on video length. You'll be redirected to the live viva session automatically.
                </p>
                <div style={{ display: "flex", flexDirection: "column", gap: 8, maxWidth: 360, margin: "0 auto" }}>
                  {PIPELINE_STEPS.map((step, i) => (
                    <div key={i} style={{
                      display: "flex", alignItems: "center", gap: 10, padding: "8px 12px",
                      background: i <= pipelineStep ? "#f0fdf4" : "#fafafa",
                      border: `1px solid ${i <= pipelineStep ? "#bbf7d0" : "#e8e8e8"}`,
                      borderRadius: 8, transition: "all 300ms",
                    }}>
                      {i < pipelineStep ? (
                        <CheckCircle2 size={14} color="#22c55e" />
                      ) : i === pipelineStep ? (
                        <Loader size={14} color="#111" className="animate-spin" />
                      ) : (
                        <div style={{ width: 14, height: 14, borderRadius: "50%", background: "#eee" }} />
                      )}
                      <span style={{ fontSize: 12, fontWeight: i <= pipelineStep ? 600 : 400, color: i <= pipelineStep ? "#111" : "#999" }}>
                        {step}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Right Sidebar — How It Works */}
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div className="card-grid" style={{ overflow: "hidden" }}>
              <div style={{ padding: "10px 16px", borderBottom: "1px solid #e8e8e8", background: "#fafafa" }}>
                <span style={{ fontSize: 12, fontWeight: 600 }}>How It Works</span>
              </div>
              <div style={{ padding: 12, display: "flex", flexDirection: "column", gap: 6 }}>
                {[
                  "Upload your project explanation video",
                  "AI extracts audio & transcribes speech",
                  "Visual frames analyzed in 10-second chunks",
                  "Summary + transcript → 5 targeted questions",
                  "Live AI viva session with voice interaction",
                ].map((s, i) => (
                  <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 11, color: "#888" }}>
                    <div style={{ width: 18, height: 18, borderRadius: "50%", background: "#f5f5f5", border: "1px solid #e8e8e8", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 9, fontWeight: 700, color: "#999", flexShrink: 0 }}>{i + 1}</div>
                    {s}
                  </div>
                ))}
              </div>
            </div>

            <div className="card-grid" style={{ padding: 14 }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: "#999", textTransform: "uppercase", marginBottom: 8 }}>What happens next</div>
              <p style={{ fontSize: 12, color: "#666", lineHeight: 1.6 }}>
                After processing, you'll be redirected to the <strong>AI Viva Session</strong> page where the AI will ask you each question using voice.
                Answer by speaking into your mic or typing. Each answer gets scored in real-time.
              </p>
            </div>
          </div>
        </div>
      </div>
    </ParticipantLayout>
  );
}
