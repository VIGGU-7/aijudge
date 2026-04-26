import { useState, useEffect, useRef } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import ParticipantLayout from "../../components/ParticipantLayout";
import VoiceVisualizer from "../../components/shared/VoiceVisualizer";
import { useTextToSpeech } from "../../hooks/useTextToSpeech";
import { vivaApi, videoVivaApi, teamApi, projectApi, aiApi } from "../../lib/api";
import { Mic, MicOff, Camera, Volume2, VolumeX, ArrowRight, RotateCcw, AlertTriangle } from "lucide-react";

export default function VivaSessionPage() {
  const { speak, stop: stopSpeech, isSpeaking, prepare: prepareSpeech, utteranceRef } = useTextToSpeech();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const videoSessionId = searchParams.get("video_session");
  const [isVideoMode, setIsVideoMode] = useState(false);
  const [videoQuestions, setVideoQuestions] = useState([]);
  const [videoCurrentIdx, setVideoCurrentIdx] = useState(0);
  const isMutedRef = useRef(sessionStorage.getItem("viva_muted") === "true");
  const [isMuted, setIsMuted] = useState(isMutedRef.current);

  const [myTeam, setMyTeam] = useState(null);
  const [profile, setProfile] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [evaluation, setEvaluation] = useState(null);
  const [questionHistory, setQuestionHistory] = useState([]);
  const [sessionSummary, setSessionSummary] = useState(null);
  const [questionNumber, setQuestionNumber] = useState(0);
  const [totalQuestions, setTotalQuestions] = useState(0);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [manualAnswer, setManualAnswer] = useState("");
  const [transcript, setTranscript] = useState("");
  const [speechError, setSpeechError] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [useVoice, setUseVoice] = useState(true);

  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const audioStreamRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const stopRequestedRef = useRef(false);
  const cancelSpeechAggressively = () => {
    try {
      if (window.speechSynthesis) {
        window.speechSynthesis.pause();
        window.speechSynthesis.cancel();
      }
    } catch (e) {}
    if (utteranceRef?.current) {
      if (typeof utteranceRef.current.cancel === "function") {
        try { utteranceRef.current.cancel(); } catch {}
      }
      utteranceRef.current = null;
    }
  };

  // Mute-aware speak helper — always cancels existing speech first
  const safeSay = (text) => {
    cancelSpeechAggressively();
    stopSpeech();
    if (!isMutedRef.current && text?.trim()) speak(text);
  };

  useEffect(() => {
    (async () => {
      try {
        const tRes = await teamApi.getMy();
        if (tRes.data) {
          setMyTeam(tRes.data);
          const pRes = await projectApi.getProfile(tRes.data.id);
          if (pRes.data) setProfile(pRes.data.profile);
        }
      } catch {}
      // If video_session param exists, load video questions automatically
      if (videoSessionId) {
        try {
          prepareSpeech();
          await startCamera();
          const res = await videoVivaApi.getQuestions(videoSessionId);
          const qs = res.data.questions || [];
          if (qs.length > 0) {
            setIsVideoMode(true);
            setVideoQuestions(qs);
            setVideoCurrentIdx(0);
            setSessionId(videoSessionId);
            setCurrentQuestion(qs[0]);
            setQuestionHistory([qs[0]]);
            setQuestionNumber(1);
            setTotalQuestions(qs.length);
            setEvaluation(null);
            setSessionSummary(null);
            setTranscript("");
            setManualAnswer("");
            setSpeechError("");
            setTimeout(() => { if (qs[0]?.question) safeSay(qs[0].question); }, 500);
          }
        } catch (e) { console.error("Failed to load video session:", e); }
      }
      setLoading(false);
    })();
    // Kill TTS on page refresh or unload
    const handleBeforeUnload = () => { 
      try {
        if (window.speechSynthesis) {
          window.speechSynthesis.pause();
          window.speechSynthesis.cancel();
        }
      } catch (e) {}
    };
    window.addEventListener("beforeunload", handleBeforeUnload);
    window.addEventListener("pagehide", handleBeforeUnload);

    return () => {
      // Cancel speech on unmount
      cancelSpeechAggressively();
      stopSpeech();
      window.removeEventListener("beforeunload", handleBeforeUnload);
      window.removeEventListener("pagehide", handleBeforeUnload);
      if (streamRef.current) streamRef.current.getTracks().forEach((track) => track.stop());
      if (audioStreamRef.current) audioStreamRef.current.getTracks().forEach((track) => track.stop());
    };
  }, []);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      streamRef.current = stream;
      // Retry attaching to video element — it may not be mounted yet during useEffect
      const attach = () => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.play().catch(() => {});
        } else {
          setTimeout(attach, 200);
        }
      };
      attach();
    } catch (err) {
      const msg = err?.name === "NotAllowedError" ? "Camera permission was denied"
        : err?.name === "NotFoundError" ? "No camera found on this device"
        : err?.message || "Could not access camera";
      setSpeechError(msg);
    }
  };

  const handleStartViva = async () => {
    cancelSpeechAggressively();
    if (!myTeam) return;
    setStarting(true);
    try {
      prepareSpeech();
      await startCamera();
      const res = await vivaApi.start(myTeam.id);
      setSessionId(res.data.session_id);
      const q = res.data.question;
      setCurrentQuestion(q);
      setQuestionHistory([q]);
      setEvaluation(null);
      setSessionSummary(null);
      setQuestionNumber(1);
      setTotalQuestions(res.data.total_questions || 5);
      setTranscript("");
      setSpeechError("");
      setManualAnswer("");
      if (q?.question) safeSay(q.question);
    } catch (e) { console.error(e); }
    finally { setStarting(false); }
  };

  const handleSubmitAnswer = async () => {
    const answer = useVoice ? transcript : manualAnswer;
    if (!answer.trim() || !sessionId || !currentQuestion) return;
    setSubmitting(true);
    try {
      prepareSpeech();
      stopSpeech();
      if (isListening) stopAudioRecording();
      let res;
      if (isVideoMode) {
        res = await videoVivaApi.submitAnswer(sessionId, currentQuestion.id, answer);
      } else {
        res = await vivaApi.submitAnswer(sessionId, currentQuestion.id, answer);
      }
      setEvaluation(res.data);
      if (res.data.completed) {
        setSessionSummary({ overall_score: 0, completed: true });
      } else if (isVideoMode && res.data.completed) {
        setSessionSummary({ overall_score: 0, completed: true });
      } else {
        setSessionSummary(res.data.session_summary || null);
      }
      setQuestionNumber(res.data.question_number || questionNumber);
      setTotalQuestions(res.data.total_questions || totalQuestions);
      if (res.data?.feedback) safeSay(res.data.feedback);
    } catch (e) { console.error(e); }
    finally { setSubmitting(false); }
  };

  const handleNextQuestion = async () => {
    cancelSpeechAggressively();
    if (!sessionId) return;
    // Block if we've hit the 5-question limit
    if (questionNumber >= (totalQuestions || 5)) {
      setSessionSummary({ completed: true });
      return;
    }
    setStarting(true);
    try {
      prepareSpeech();
      if (isVideoMode) {
        const nextIdx = videoCurrentIdx + 1;
        if (nextIdx < videoQuestions.length) {
          const q = videoQuestions[nextIdx];
          setVideoCurrentIdx(nextIdx);
          setCurrentQuestion(q);
          setQuestionHistory((prev) => [...prev, q]);
          setEvaluation(null);
          setQuestionNumber(nextIdx + 1);
          setTranscript("");
          setSpeechError("");
          setManualAnswer("");
          if (q?.question) safeSay(q.question);
        }
      } else {
        if (!myTeam) return;
        const res = await vivaApi.nextQuestion(myTeam.id, sessionId);
        const q = res.data.question;
        setCurrentQuestion(q);
        setQuestionHistory((prev) => [...prev, q]);
        setEvaluation(null);
        setQuestionNumber(res.data.question_number || questionNumber + 1);
        setTotalQuestions(res.data.total_questions || totalQuestions);
        setTranscript("");
        setSpeechError("");
        setManualAnswer("");
        if (q?.question) safeSay(q.question);
      }
    } catch (e) { console.error(e); }
    finally { setStarting(false); }
  };

  const destroyAudioSession = () => {
    // Fully destroy any existing recording session
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      try { mediaRecorderRef.current.stop(); } catch {}
    }
    mediaRecorderRef.current = null;
    if (audioStreamRef.current) {
      audioStreamRef.current.getTracks().forEach((track) => track.stop());
      audioStreamRef.current = null;
    }
    stopRequestedRef.current = true;
  };

  const startAudioRecording = async () => {
    cancelSpeechAggressively();
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      setSpeechError("Audio recording is not supported in this browser");
      return;
    }
    // Fully destroy any previous session first
    destroyAudioSession();
    // Stop TTS before recording to prevent AI voice bleeding into mic
    stopSpeech();

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      audioStreamRef.current = stream;
      
      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;
      let audioChunks = [];

      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunks.push(event.data);
        }
      };
      
      recorder.onerror = (event) => {
        console.error("Recording error:", event.error);
        setSpeechError(event.error?.message || "Audio recording failed");
        setIsListening(false);
      };
      
      recorder.onstop = async () => {
        setIsListening(false);
        stopRequestedRef.current = true;
        
        if (audioStreamRef.current) {
          audioStreamRef.current.getTracks().forEach((track) => track.stop());
          audioStreamRef.current = null;
        }

        if (audioChunks.length === 0) {
          setSpeechError("No speech detected. Try recording again.");
          return;
        }

        const blob = new Blob(audioChunks, { type: recorder.mimeType || "audio/webm" });
        audioChunks = []; // clear chunks

        setTranscribing(true);
        setTranscript("Transcribing...");
        try {
          const extension = blob.type.includes("mp4") ? "mp4" : blob.type.includes("ogg") ? "ogg" : "webm";
          const file = new File([blob], `viva-answer.${extension}`, { type: blob.type });
          const res = await aiApi.transcribeAudio(file);
          const text = (res.data.transcript || "").trim();
          setTranscript(text);
          if (!text) {
             setSpeechError("Could not understand audio. Try again.");
          }
        } catch (e) {
          console.error(e);
          setSpeechError(e.response?.data?.detail || e.message || "Audio transcription failed");
          setTranscript("");
        } finally {
          setTranscribing(false);
        }
      };

      setSpeechError("");
      setTranscript("");
      setIsListening(true);
      recorder.start(); // collect all data in one go on stop
    } catch (err) {
      const message = err?.name === "NotAllowedError" ? "Microphone permission was denied"
        : err?.name === "NotFoundError" ? "No microphone was found on this device"
        : err?.message || "Could not access microphone";
      setSpeechError(message);
      setIsListening(false);
    }
  };

  const stopAudioRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      mediaRecorderRef.current.stop();
    }
  };

  const toggleListening = async () => {
    if (isListening) { stopAudioRecording(); return; }
    // Stop AI speech before starting mic to prevent echo
    cancelSpeechAggressively();
    stopSpeech();
    setSpeechError("");
    setTranscript("");
    await startAudioRecording();
  };

  const scoreColor = (s) => s >= 80 ? "#22c55e" : s >= 60 ? "#f59e0b" : "#ef4444";
  const isSessionComplete = isVideoMode
    ? Boolean(evaluation?.completed || (videoCurrentIdx >= videoQuestions.length - 1 && evaluation))
    : Boolean(evaluation?.completed || sessionSummary);

  if (loading) return <ParticipantLayout><div style={{ display: "flex", justifyContent: "center", padding: 80 }}><span className="overline animate-pulse-subtle">Loading...</span></div></ParticipantLayout>;

  return (
    <ParticipantLayout>
      <div style={{ display: "flex", flexDirection: "column", gap: 22 }}>
        {/* Header */}
        <div className="animate-enter" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", paddingBottom: 20, borderBottom: "1px solid #e8e8e8" }}>
          <div>
            <h1 style={{ fontSize: 28, fontWeight: 700, letterSpacing: "-0.02em", display: "flex", alignItems: "center", gap: 10 }}>
              <Mic size={24} /> AI Viva Session
            </h1>
            <p style={{ color: "#999", fontSize: 13, marginTop: 4 }}>
              Team: <span style={{ color: "#111" }}>{myTeam?.name || "—"}</span>
              {profile && <> · <span style={{ color: "#22c55e" }}>Context Profile Ready</span></>}
            </p>
          </div>
          <div style={{ display: "flex", gap: 6 }}>
            <div style={{ padding: "5px 10px", background: "#fafafa", border: "1px solid #e8e8e8", borderRadius: 6, display: "flex", alignItems: "center", gap: 5 }}>
              <span style={{ width: 6, height: 6, borderRadius: "50%", background: isSpeaking ? "#111" : "#ddd" }} />
              <span style={{ fontSize: 10, fontWeight: 600, color: "#999" }}>{isSpeaking ? "AI Speaking" : "AI Silent"}</span>
            </div>
            <div style={{ padding: "5px 10px", background: "#fafafa", border: "1px solid #e8e8e8", borderRadius: 6, display: "flex", alignItems: "center", gap: 5 }}>
              <span style={{ width: 6, height: 6, borderRadius: "50%", background: isListening ? "#22c55e" : transcribing ? "#f59e0b" : "#ddd" }} />
              <span style={{ fontSize: 10, fontWeight: 600, color: "#999" }}>{isListening ? "Recording" : transcribing ? "Transcribing" : "Mic Off"}</span>
            </div>
            <button
              onClick={() => {
                const next = !isMuted;
                isMutedRef.current = next;
                setIsMuted(next);
                sessionStorage.setItem("viva_muted", String(next));
                if (next) { cancelSpeechAggressively(); stopSpeech(); }
              }}
              style={{ padding: "5px 10px", background: isMuted ? "#fef2f2" : "#fafafa", border: `1px solid ${isMuted ? "#fecaca" : "#e8e8e8"}`, borderRadius: 6, display: "flex", alignItems: "center", gap: 5, cursor: "pointer", transition: "all 150ms" }}
              title={isMuted ? "Unmute AI voice" : "Mute AI voice"}
            >
              {isMuted ? <VolumeX size={12} color="#dc2626" /> : <Volume2 size={12} color="#999" />}
              <span style={{ fontSize: 10, fontWeight: 600, color: isMuted ? "#dc2626" : "#999" }}>{isMuted ? "Muted" : "Sound On"}</span>
            </button>
          </div>
        </div>

        {!profile && (
          <div className="card-grid" style={{ padding: 24, display: "flex", alignItems: "center", gap: 12, borderLeft: "3px solid #f59e0b" }}>
            <AlertTriangle size={18} color="#d97706" />
            <div>
              <p style={{ fontWeight: 600, color: "#92400e", fontSize: 14 }}>No Context Profile</p>
              <p style={{ fontSize: 13, color: "#999" }}>Go to Project Setup first to upload your code, PPT, and features.</p>
            </div>
          </div>
        )}

        <div style={{ display: "grid", gridTemplateColumns: "1fr 320px", gap: 20 }}>
          {/* Main Column */}
          <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
            {/* Pre-session CTA */}
            {!sessionId && (
              <div className="card-grid animate-enter" style={{ padding: 24, borderLeft: "3px solid #111" }}>
                <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}>Quick Evaluation</h3>
                <p style={{ color: "#999", fontSize: 13, marginBottom: 16 }}>
                  The AI will ask a fixed sequence of questions covering code understanding, features, architecture, tech stack, and presentation claims.
                </p>
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 14 }}>
                  <label style={{ fontSize: 12, color: "#888", display: "flex", alignItems: "center", gap: 6, cursor: "pointer" }}>
                    <input type="checkbox" checked={useVoice} onChange={(e) => setUseVoice(e.target.checked)} style={{ width: 15, height: 15 }} />
                    Use voice input (recommended)
                  </label>
                </div>
                <button onClick={handleStartViva} disabled={starting || !myTeam} className="btn btn-primary" style={{ width: "100%", height: 46, fontSize: 14 }}>
                  {starting ? "Starting..." : "Start Quick Evaluation"}
                </button>
              </div>
            )}

            {/* Camera */}
            <div className="card-grid" style={{ overflow: "hidden" }}>
              <div style={{ padding: "10px 16px", borderBottom: "1px solid #e8e8e8", background: "#fafafa", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontSize: 12, fontWeight: 600, display: "flex", alignItems: "center", gap: 6 }}><Camera size={13} /> Camera</span>
                <VoiceVisualizer active={isSpeaking || isListening} listening={isListening} />
              </div>
              <div style={{ aspectRatio: "16/9", background: "#f5f5f5", position: "relative" }}>
                <video ref={videoRef} autoPlay muted playsInline style={{ width: "100%", height: "100%", objectFit: "cover" }} />
              </div>
            </div>

            {/* Current Question */}
            {currentQuestion && (
              <div className="card-grid animate-enter" style={{ overflow: "hidden" }}>
                <div style={{ padding: "10px 16px", borderBottom: "1px solid #e8e8e8", background: "#fafafa", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontSize: 12, fontWeight: 600 }}>AI Question</span>
                  <div style={{ display: "flex", gap: 6 }}>
                    <span className="badge badge-info" style={{ fontSize: 10 }}>Q{questionNumber}/{totalQuestions || questionHistory.length}</span>
                    <span className={`badge badge-${currentQuestion.difficulty === "hard" ? "cheat" : currentQuestion.difficulty === "medium" ? "warning" : "human"}`} style={{ fontSize: 10 }}>{currentQuestion.difficulty}</span>
                    <span className="badge badge-info" style={{ fontSize: 10 }}>{currentQuestion.category?.replace(/_/g, " ")}</span>
                  </div>
                </div>
                <div style={{ padding: 20 }}>
                  <p style={{ fontSize: 15, lineHeight: 1.7 }}>{currentQuestion.question}</p>
                  {currentQuestion.reference && <p style={{ marginTop: 10, fontSize: 12, color: "#999", fontFamily: "JetBrains Mono" }}>Ref: {currentQuestion.reference}</p>}
                  <button onClick={() => safeSay(currentQuestion.question)} className="btn btn-outline" style={{ marginTop: 12, fontSize: 11, padding: "5px 12px", gap: 4 }}>
                    <Volume2 size={12} /> Replay
                  </button>
                </div>
              </div>
            )}

            {/* Answer Input */}
            {currentQuestion && !evaluation && (
              <div className="card-grid animate-enter" style={{ padding: 20, borderLeft: "3px solid #111" }}>
                <label style={{ fontSize: 12, fontWeight: 600, color: "#999", textTransform: "uppercase", letterSpacing: "0.04em", display: "block", marginBottom: 12 }}>Your Answer</label>
                {useVoice ? (
                  <div>
                    <div style={{ background: "#fafafa", border: "1px solid #e8e8e8", borderRadius: 8, padding: 14, minHeight: 100, marginBottom: 14, fontSize: 14, lineHeight: 1.6, color: transcript ? "#111" : "#bbb" }}>
                      {transcript || (isListening ? "Recording... (speak now)" : transcribing ? "Transcribing..." : "Press the microphone button and start speaking...")}
                    </div>
                    {speechError && (
                      <div style={{ marginBottom: 14, padding: "8px 12px", background: "#fef2f2", border: "1px solid #fecaca", borderRadius: 8, color: "#dc2626", fontSize: 12, fontFamily: "JetBrains Mono" }}>
                        {speechError}
                      </div>
                    )}
                    <div style={{ display: "flex", gap: 10 }}>
                      <button onClick={toggleListening} disabled={transcribing && !isListening} className={`btn ${isListening ? "btn-danger" : "btn-primary"}`} style={{ flex: 1, height: 42, gap: 6 }}>
                        {isListening ? <><MicOff size={14} /> Stop Recording</> : transcribing ? "Transcribing..." : <><Mic size={14} /> Start Recording</>}
                      </button>
                      <button onClick={handleSubmitAnswer} disabled={submitting || isListening || transcribing || !transcript.trim()} className="btn btn-primary" style={{ flex: 1, height: 42 }}>
                        {submitting ? "Evaluating..." : "Submit Answer"}
                      </button>
                    </div>
                  </div>
                ) : (
                  <div>
                    <textarea value={manualAnswer} onChange={(e) => setManualAnswer(e.target.value)} placeholder="Type your answer here..." rows={5} style={{ resize: "vertical", marginBottom: 14 }} />
                    <button onClick={handleSubmitAnswer} disabled={submitting || !manualAnswer.trim()} className="btn btn-primary" style={{ width: "100%", height: 42 }}>
                      {submitting ? "Evaluating..." : "Submit Answer"}
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Evaluation */}
            {evaluation && (
              <div className="card-grid animate-enter" style={{ overflow: "hidden" }}>
                <div style={{ padding: "10px 16px", borderBottom: "1px solid #e8e8e8", background: "#fafafa", display: "flex", justifyContent: "space-between" }}>
                  <span style={{ fontSize: 12, fontWeight: 600 }}>{isSessionComplete ? "Quick Evaluation Complete" : "Evaluation"}</span>
                  <span style={{ width: 7, height: 7, borderRadius: "50%", background: "#22c55e" }} className="animate-pulse-subtle" />
                </div>
                <div style={{ padding: 20, display: "flex", flexDirection: "column", gap: 16 }}>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                    <div style={{ background: "#fafafa", border: "1px solid #e8e8e8", borderRadius: 8, padding: 18, textAlign: "center" }}>
                      <div style={{ fontSize: 11, fontWeight: 600, color: "#999", textTransform: "uppercase", marginBottom: 6 }}>Score</div>
                      <div style={{ fontSize: 36, fontWeight: 700, fontFamily: "JetBrains Mono", color: scoreColor(evaluation.score) }}>{evaluation.score}<span style={{ fontSize: 14, color: "#ccc" }}>/100</span></div>
                    </div>
                    <div style={{ background: "#fafafa", border: "1px solid #e8e8e8", borderRadius: 8, padding: 18, textAlign: "center", display: "flex", flexDirection: "column", justifyContent: "center" }}>
                      <div style={{ fontSize: 11, fontWeight: 600, color: "#999", textTransform: "uppercase", marginBottom: 6 }}>Understanding</div>
                      <div style={{ fontSize: 14, fontWeight: 600, textTransform: "capitalize" }}>{evaluation.understanding_level}</div>
                    </div>
                  </div>

                  <div style={{ background: "#fafafa", border: "1px solid #e8e8e8", borderRadius: 8, padding: 14 }}>
                    <div style={{ fontSize: 11, fontWeight: 600, color: "#999", textTransform: "uppercase", marginBottom: 6 }}>Feedback</div>
                    <p style={{ fontSize: 13, lineHeight: 1.7, color: "#555" }}>{evaluation.feedback}</p>
                  </div>

                  {sessionSummary && (
                    <div style={{ background: "#fafafa", border: "1px solid #e8e8e8", borderRadius: 8, padding: 14 }}>
                      <div style={{ fontSize: 11, fontWeight: 600, color: "#999", textTransform: "uppercase", marginBottom: 10 }}>Overall Score</div>
                      <div style={{ display: "flex", alignItems: "baseline", gap: 10, marginBottom: 10 }}>
                        <span style={{ fontSize: 32, fontWeight: 700, fontFamily: "JetBrains Mono", color: scoreColor(sessionSummary.overall_score) }}>{sessionSummary.overall_score}</span>
                        <span style={{ fontSize: 13, color: "#999", textTransform: "capitalize" }}>{sessionSummary.understanding_level}</span>
                      </div>
                      <p style={{ fontSize: 12, color: "#999", marginBottom: 8 }}>{sessionSummary.questions_answered} of {totalQuestions || sessionSummary.questions_answered} questions completed</p>
                      {sessionSummary.strengths?.length > 0 && <p style={{ fontSize: 12, color: "#555", marginBottom: 4 }}>Strengths: {sessionSummary.strengths.join(", ")}</p>}
                      {sessionSummary.weaknesses?.length > 0 && <p style={{ fontSize: 12, color: "#555" }}>Gaps: {sessionSummary.weaknesses.join(", ")}</p>}
                    </div>
                  )}

                  <div style={{ display: "flex", gap: 10 }}>
                    {!isSessionComplete ? (
                      <button onClick={handleNextQuestion} disabled={starting} className="btn btn-primary" style={{ flex: 1, height: 42, gap: 6 }}>
                        {starting ? "Loading..." : <>Next Question <ArrowRight size={14} /></>}
                      </button>
                    ) : (
                      <div style={{ display: "flex", gap: 10, flex: 1 }}>
                        <button onClick={() => {
                          setSessionId(null); setCurrentQuestion(null); setEvaluation(null); setQuestionHistory([]); setSessionSummary(null);
                          setQuestionNumber(0); setTotalQuestions(0); setTranscript(""); setManualAnswer(""); setSpeechError("");
                          setIsVideoMode(false); setVideoQuestions([]); setVideoCurrentIdx(0);
                        }} className="btn btn-outline" style={{ flex: 1, height: 42, gap: 6 }}>
                          <RotateCcw size={14} /> New Session
                        </button>
                        <button onClick={() => navigate("/p/results")} className="btn btn-primary" style={{ flex: 1, height: 42, gap: 6 }}>
                          View Results <ArrowRight size={14} />
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Sidebar — Question Timeline */}
          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div className="card-grid" style={{ overflow: "hidden" }}>
              <div style={{ padding: "10px 16px", borderBottom: "1px solid #e8e8e8", background: "#fafafa" }}>
                <span style={{ fontSize: 12, fontWeight: 600 }}>Question Timeline</span>
              </div>
              <div style={{ padding: 14, display: "flex", flexDirection: "column", gap: 8, maxHeight: 500, overflowY: "auto" }}>
                {questionHistory.length === 0 ? (
                  <p style={{ color: "#bbb", fontSize: 12, padding: 8 }}>Questions appear here during viva.</p>
                ) : questionHistory.map((q, i) => (
                  <div key={i} style={{ padding: 10, background: "#fafafa", border: "1px solid #e8e8e8", borderRadius: 8 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                      <span style={{ fontSize: 10, fontWeight: 600, color: "#999" }}>Q{i + 1}</span>
                      <span className="badge badge-info" style={{ fontSize: 9, padding: "1px 6px" }}>{q.category?.replace(/_/g, " ")}</span>
                    </div>
                    <p style={{ fontSize: 12, color: "#555", lineHeight: 1.5 }}>{q.question?.slice(0, 80)}...</p>
                  </div>
                ))}
              </div>
            </div>

            {profile && (
              <div className="card-grid" style={{ overflow: "hidden" }}>
                <div style={{ padding: "10px 16px", borderBottom: "1px solid #e8e8e8", background: "#fafafa" }}>
                  <span style={{ fontSize: 12, fontWeight: 600 }}>Context Summary</span>
                </div>
                <div style={{ padding: 14, display: "flex", flexDirection: "column", gap: 8 }}>
                  {profile.codebase?.total_files > 0 && (
                    <div style={{ padding: 10, background: "#fafafa", border: "1px solid #e8e8e8", borderRadius: 8 }}>
                      <div style={{ fontSize: 10, fontWeight: 600, color: "#999", marginBottom: 3 }}>Codebase</div>
                      <div style={{ fontSize: 13 }}>{profile.codebase.total_files} files analyzed</div>
                    </div>
                  )}
                  {profile.presentation?.total_slides > 0 && (
                    <div style={{ padding: 10, background: "#fafafa", border: "1px solid #e8e8e8", borderRadius: 8 }}>
                      <div style={{ fontSize: 10, fontWeight: 600, color: "#999", marginBottom: 3 }}>Presentation</div>
                      <div style={{ fontSize: 13 }}>{profile.presentation.total_slides} slides</div>
                    </div>
                  )}
                  {profile.ai_analysis?.authenticity_score != null && (
                    <div style={{ padding: 10, background: "#fafafa", border: "1px solid #e8e8e8", borderRadius: 8 }}>
                      <div style={{ fontSize: 10, fontWeight: 600, color: "#999", marginBottom: 3 }}>Authenticity</div>
                      <div style={{ fontSize: 18, fontWeight: 700, color: scoreColor(profile.ai_analysis.authenticity_score) }}>{profile.ai_analysis.authenticity_score}%</div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </ParticipantLayout>
  );
}
