import axios from "axios";

const API = `${import.meta.env.VITE_BACKEND_URL}/api`;

axios.defaults.withCredentials = true;

export const authApi = {
  login: (email, password) => axios.post(`${API}/auth/login`, { email, password }),
  register: (email, password, name, role) => axios.post(`${API}/auth/register`, { email, password, name, role }),
  logout: () => axios.post(`${API}/auth/logout`),
  me: () => axios.get(`${API}/auth/me`),
  refresh: () => axios.post(`${API}/auth/refresh`),
};

export const hackathonApi = {
  list: (status) => axios.get(`${API}/hackathons${status ? `?status=${status}` : ""}`),
  get: (id) => axios.get(`${API}/hackathons/${id}`),
  create: (data) => axios.post(`${API}/hackathons`, data),
  updateStatus: (id, status) => axios.patch(`${API}/hackathons/${id}/status`, { status }),
};

export const teamApi = {
  list: (hackathonId) => axios.get(`${API}/teams${hackathonId ? `?hackathon_id=${hackathonId}` : ""}`),
  get: (id) => axios.get(`${API}/teams/${id}`),
  create: (data) => axios.post(`${API}/teams`, data),
  join: (id) => axios.post(`${API}/teams/${id}/join`),
  getMy: () => axios.get(`${API}/teams/my/current`),
  addMember: (id, email) => axios.post(`${API}/teams/${id}/add-member`, { email }),
  search: (query) => axios.get(`${API}/teams/search?query=${encodeURIComponent(query)}`),
};

export const projectApi = {
  getInfo: (tid) => axios.get(`${API}/teams/${tid}/project-info`),
  getPpt: (tid) => axios.get(`${API}/teams/${tid}/ppt`),
  submitInfo: (tid, data) => axios.post(`${API}/teams/${tid}/project-info`, data),
  uploadPpt: (tid, file) => {
    const fd = new FormData();
    fd.append("file", file);
    return axios.post(`${API}/teams/${tid}/upload-ppt`, fd);
  },
  buildContext: (tid) => axios.post(`${API}/teams/${tid}/build-context`),
  getProfile: (tid) => axios.get(`${API}/teams/${tid}/context-profile`),
};

export const vivaApi = {
  start: (teamId) => axios.post(`${API}/ai/viva/start`, { team_id: teamId }),
  nextQuestion: (teamId, sessionId) => axios.post(`${API}/ai/viva/next-question?session_id=${sessionId}`, { team_id: teamId }),
  submitAnswer: (sessionId, questionId, answer) => axios.post(`${API}/ai/viva/answer`, { session_id: sessionId, question_id: questionId, answer }),
  getSessions: (tid) => axios.get(`${API}/ai/viva/sessions/${tid}`),
};

export const videoVivaApi = {
  upload: (file) => {
    const fd = new FormData();
    fd.append("file", file);
    return axios.post(`${API}/ai/video-viva/upload`, fd, { timeout: 300000 });
  },
  getQuestions: (sessionId) => axios.get(`${API}/ai/video-viva/questions/${sessionId}`),
  submitAnswer: (sessionId, questionId, answer) => axios.post(`${API}/ai/video-viva/answer`, { session_id: sessionId, question_id: questionId, answer }),
};

export const aiApi = {
  analyzeCode: (code, language) => axios.post(`${API}/ai/analyze-code`, { code, language }),
  transcribeAudio: (file) => {
    const fd = new FormData();
    fd.append("file", file);
    return axios.post(`${API}/transcribe`, fd);
  },
  mentorChat: (message, sessionId, codeContext) => axios.post(`${API}/ai/mentor/chat`, { message, session_id: sessionId, code_context: codeContext }),
  mentorHistory: (sessionId) => axios.get(`${API}/ai/mentor/history/${sessionId}`),
};

export const evalApi = {
  create: (data) => axios.post(`${API}/evaluations`, data),
  getForTeam: (tid) => axios.get(`${API}/evaluations/${tid}`),
  leaderboard: (hid) => axios.get(`${API}/leaderboard/${hid}`),
};

export const statsApi = {
  dashboard: () => axios.get(`${API}/stats/dashboard`),
};

export const plagiarismApi = {
  check: (teamId, repoUrl) => axios.post(`${API}/plagiarism/check`, { team_id: teamId, repo_url: repoUrl }, { timeout: 120000 }),
  listReports: () => axios.get(`${API}/plagiarism/reports`),
  getReport: (teamId) => axios.get(`${API}/plagiarism/reports/${teamId}`),
};

export const reportApi = {
  participantPdf: (userId) => axios.get(`${API}/report/participant/${userId}`, { responseType: "blob", timeout: 60000 }),
  hackathonPdf: (hackathonId) => axios.get(`${API}/report/hackathon/${hackathonId}`, { responseType: "blob", timeout: 60000 }),
};

export const extensionApi = {
  link: (teamName) => axios.post(`${API}/extension/link`, { team_name: teamName }),
  sendTelemetry: (data) => axios.post(`${API}/extension/telemetry`, data),
  getTelemetry: (tid) => axios.get(`${API}/extension/telemetry/${tid}`),
};
