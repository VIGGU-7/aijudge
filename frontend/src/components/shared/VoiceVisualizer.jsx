export default function VoiceVisualizer({ active, listening }) {
  const barCount = 8;
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: 32, gap: 0 }}>
      {Array.from({ length: barCount }).map((_, i) => (
        <span
          key={i}
          className={`voice-bar ${listening ? "listening" : ""}`}
          style={{
            animationPlayState: active ? "running" : "paused",
            height: active ? undefined : "4px",
          }}
        />
      ))}
    </div>
  );
}
