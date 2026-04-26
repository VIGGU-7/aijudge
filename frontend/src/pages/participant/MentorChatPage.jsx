import { useState, useEffect } from "react";
import ParticipantLayout from "../../components/ParticipantLayout";
import { aiApi } from "../../lib/api";
import { Bot, Send } from "lucide-react";

export default function MentorChatPage() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sessionId] = useState(() => "mentor-" + Date.now());
  const [sending, setSending] = useState(false);

  useEffect(() => {
    setMessages([{ role: "assistant", content: "Hey! I'm your AI mentor. Ask me anything about coding, debugging, or your project. I'm here to help you learn!" }]);
  }, []);

  const handleSend = async () => {
    if (!input.trim()) return;
    const msg = input.trim();
    setMessages((p) => [...p, { role: "user", content: msg }]);
    setInput(""); setSending(true);
    try {
      const res = await aiApi.mentorChat(msg, sessionId);
      setMessages((p) => [...p, { role: "assistant", content: res.data.response }]);
    } catch { setMessages((p) => [...p, { role: "assistant", content: "Sorry, I had trouble processing that. Try again?" }]); }
    finally { setSending(false); }
  };

  return (
    <ParticipantLayout>
      <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 64px)" }}>
        <div className="animate-enter" style={{ paddingBottom: 14, marginBottom: 14, borderBottom: "1px solid #e8e8e8" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{ width: 36, height: 36, background: "#111", borderRadius: 8, display: "flex", alignItems: "center", justifyContent: "center" }}>
              <Bot size={18} color="#fff" />
            </div>
            <div>
              <h1 style={{ fontSize: 22, fontWeight: 700, letterSpacing: "-0.02em" }}>AI Mentor</h1>
              <p style={{ color: "#999", fontSize: 12 }}>Get coding help, debugging tips, and guidance</p>
            </div>
          </div>
        </div>

        <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: 12, paddingBottom: 14 }}>
          {messages.map((m, i) => (
            <div key={i} style={{ display: "flex", justifyContent: m.role === "user" ? "flex-end" : "flex-start" }}>
              <div style={{
                maxWidth: "72%", padding: "12px 16px",
                borderRadius: m.role === "user" ? "10px 10px 2px 10px" : "10px 10px 10px 2px",
                fontSize: 14, lineHeight: 1.65, whiteSpace: "pre-wrap",
                background: m.role === "user" ? "#111" : "#fafafa",
                color: m.role === "user" ? "#fff" : "#333",
                border: m.role === "user" ? "none" : "1px solid #e8e8e8",
              }}>
                {m.role === "assistant" && (
                  <div style={{ display: "flex", alignItems: "center", gap: 5, marginBottom: 6 }}>
                    <Bot size={12} color="#999" />
                    <span style={{ fontSize: 11, fontWeight: 600, color: "#999" }}>AI Mentor</span>
                  </div>
                )}
                {m.content}
              </div>
            </div>
          ))}
          {sending && (
            <div style={{ display: "flex", justifyContent: "flex-start" }}>
              <div style={{ padding: "12px 16px", background: "#fafafa", border: "1px solid #e8e8e8", borderRadius: "10px 10px 10px 2px" }}>
                <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
                  {[0, 1, 2].map(i => (
                    <div key={i} style={{
                      width: 5, height: 5, borderRadius: "50%", background: "#bbb",
                      animation: "pulse-subtle 1.5s ease-in-out infinite", animationDelay: `${i * 0.2}s`,
                    }} />
                  ))}
                  <span style={{ fontSize: 12, color: "#999", marginLeft: 8 }}>Thinking...</span>
                </div>
              </div>
            </div>
          )}
        </div>

        <div style={{ display: "flex", gap: 8, paddingTop: 14, borderTop: "1px solid #e8e8e8" }}>
          <input value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleSend()} placeholder="Ask anything about your code..." style={{ flex: 1 }} />
          <button onClick={handleSend} disabled={sending || !input.trim()} className="btn btn-primary" style={{ padding: "10px 20px", gap: 6 }}>
            <Send size={14} /> Send
          </button>
        </div>
      </div>
    </ParticipantLayout>
  );
}
