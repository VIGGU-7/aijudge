import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { LayoutDashboard, Settings, Mic, Bot, Trophy, Video, LogOut } from "lucide-react";

const navItems = [
  { path: "/p/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { path: "/p/setup", label: "Project Setup", icon: Settings },
  { path: "/p/video-viva", label: "Demo Drop", icon: Video },
  { path: "/p/viva", label: "AI Viva", icon: Mic },
  { path: "/p/mentor", label: "AI Mentor", icon: Bot },
  { path: "/p/results", label: "My Results", icon: Trophy },
];

export default function ParticipantLayout({ children }) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const isActive = (path) => location.pathname === path || location.pathname.startsWith(path + "/");

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <aside className="sidebar">
        <div style={{ padding: "20px 20px", borderBottom: "1px solid var(--border-default)" }}>
          <Link to="/p/dashboard" style={{ display: "flex", alignItems: "center", gap: 10, textDecoration: "none", color: "inherit" }}>
            <div style={{
              width: 32, height: 32, background: "#111", display: "flex",
              alignItems: "center", justifyContent: "center", borderRadius: 8, fontSize: 15, color: "#fff",
              fontWeight: 700,
            }}>A</div>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, letterSpacing: "-0.01em" }}>AI Judge</div>
              <div style={{ fontSize: 10, color: "var(--text-muted)" }}>Participant</div>
            </div>
          </Link>
        </div>

        <div style={{ padding: "12px 10px", flex: 1, display: "flex", flexDirection: "column", gap: 1 }}>
          <div style={{ padding: "6px 12px", marginBottom: 6 }}>
            <span style={{ fontSize: 10, fontWeight: 600, color: "var(--text-muted)", letterSpacing: "0.06em", textTransform: "uppercase" }}>Menu</span>
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.path);
            return (
              <Link
                key={item.path}
                to={item.path}
                style={{
                  display: "flex", alignItems: "center", gap: 10,
                  padding: "9px 12px", borderRadius: 7,
                  fontSize: 13, fontWeight: active ? 600 : 500, textDecoration: "none",
                  transition: "all 150ms ease",
                  background: active ? "#f0f0f0" : "transparent",
                  color: active ? "#111" : "#888",
                }}
              >
                <Icon size={16} strokeWidth={active ? 2.2 : 1.8} />
                {item.label}
              </Link>
            );
          })}
        </div>

        <div style={{ padding: 14, borderTop: "1px solid var(--border-default)" }}>
          <div style={{
            display: "flex", alignItems: "center", gap: 10, padding: "8px 10px",
            background: "#fff", border: "1px solid var(--border-default)",
            borderRadius: 8, marginBottom: 8,
          }}>
            <div style={{
              width: 28, height: 28, background: "#111", display: "flex",
              alignItems: "center", justifyContent: "center", borderRadius: 6,
              fontSize: 11, fontWeight: 700, color: "#fff",
            }}>{user?.name?.[0]?.toUpperCase() || "P"}</div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 12, fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{user?.name}</div>
              <div style={{ fontSize: 10, color: "var(--text-muted)", textTransform: "capitalize" }}>{user?.role}</div>
            </div>
          </div>
          <button onClick={logout} className="btn btn-outline" style={{ width: "100%", fontSize: 12, padding: "7px 12px", gap: 6 }}>
            <LogOut size={13} /> Sign Out
          </button>
        </div>
      </aside>

      <main className="main-content">
        <div className="page-container">{children}</div>
      </main>
    </div>
  );
}
