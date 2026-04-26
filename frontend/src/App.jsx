import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";

import LoginPage from "./pages/auth/LoginPage";
import RegisterPage from "./pages/auth/RegisterPage";
import ParticipantDashboard from "./pages/participant/ParticipantDashboard";
import ProjectSetupPage from "./pages/participant/ProjectSetupPage";
import VivaSessionPage from "./pages/participant/VivaSessionPage";
import MentorChatPage from "./pages/participant/MentorChatPage";
import MyResultsPage from "./pages/participant/MyResultsPage";
import VideoVivaPage from "./pages/participant/VideoVivaPage";
import OrganizerDashboard from "./pages/organizer/OrganizerDashboard";
import HackathonManagerPage from "./pages/organizer/HackathonManagerPage";
import TeamOverviewPage from "./pages/organizer/TeamOverviewPage";
import TeamAnalysisControlRoom from "./pages/organizer/TeamAnalysisControlRoom";
import LeaderboardPage from "./pages/organizer/LeaderboardPage";
import PlagiarismReportPage from "./pages/organizer/PlagiarismReportPage";

function ProtectedRoute({ children, allowedRoles }) {
  const { user, loading } = useAuth();
  if (loading) return <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "#09090B", color: "#71717A", fontFamily: "JetBrains Mono", fontSize: 12, textTransform: "uppercase", letterSpacing: "0.1em" }}>Initializing...</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to={user.role === "organizer" ? "/o/dashboard" : "/p/dashboard"} replace />;
  }
  return children;
}

function PublicRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (user) return <Navigate to={user.role === "organizer" ? "/o/dashboard" : "/p/dashboard"} replace />;
  return children;
}

function RoleRedirect() {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/login" replace />;
  return <Navigate to={user.role === "organizer" ? "/o/dashboard" : "/p/dashboard"} replace />;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<RoleRedirect />} />
      <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
      <Route path="/register" element={<PublicRoute><RegisterPage /></PublicRoute>} />

      {/* Participant routes */}
      <Route path="/p/dashboard" element={<ProtectedRoute allowedRoles={["participant"]}><ParticipantDashboard /></ProtectedRoute>} />
      <Route path="/p/setup" element={<ProtectedRoute allowedRoles={["participant"]}><ProjectSetupPage /></ProtectedRoute>} />
      <Route path="/p/viva" element={<ProtectedRoute allowedRoles={["participant"]}><VivaSessionPage /></ProtectedRoute>} />
      <Route path="/p/mentor" element={<ProtectedRoute allowedRoles={["participant"]}><MentorChatPage /></ProtectedRoute>} />
      <Route path="/p/results" element={<ProtectedRoute allowedRoles={["participant"]}><MyResultsPage /></ProtectedRoute>} />
      <Route path="/p/video-viva" element={<ProtectedRoute allowedRoles={["participant"]}><VideoVivaPage /></ProtectedRoute>} />

      {/* Organizer routes */}
      <Route path="/o/dashboard" element={<ProtectedRoute allowedRoles={["organizer", "admin"]}><OrganizerDashboard /></ProtectedRoute>} />
      <Route path="/o/hackathons" element={<ProtectedRoute allowedRoles={["organizer", "admin"]}><HackathonManagerPage /></ProtectedRoute>} />
      <Route path="/o/teams" element={<ProtectedRoute allowedRoles={["organizer", "admin"]}><TeamOverviewPage /></ProtectedRoute>} />
      <Route path="/o/analysis/:teamId" element={<ProtectedRoute allowedRoles={["organizer", "admin"]}><TeamAnalysisControlRoom /></ProtectedRoute>} />
      <Route path="/o/analysis" element={<ProtectedRoute allowedRoles={["organizer", "admin"]}><TeamOverviewPage /></ProtectedRoute>} />
      <Route path="/o/plagiarism" element={<ProtectedRoute allowedRoles={["organizer", "admin"]}><PlagiarismReportPage /></ProtectedRoute>} />
      <Route path="/o/leaderboard" element={<ProtectedRoute allowedRoles={["organizer", "admin"]}><LeaderboardPage /></ProtectedRoute>} />

      <Route path="*" element={<RoleRedirect />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  );
}
