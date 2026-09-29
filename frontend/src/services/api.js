// API Client for SafiBot Backend
const API_BASE = (import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || '/api').replace(/\/+$/, '');

const TOKEN_KEY = 'safibot_auth_token';
const USER_KEY = 'safibot_auth_user';

export function setAuth(token, user) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function getAuthToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function getAuthUser() {
  const user = localStorage.getItem(USER_KEY);
  if (!user) return null;
  try {
    return JSON.parse(user);
  } catch {
    return null;
  }
}

export function clearAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

function getHeaders(contentType = 'application/json') {
  const headers = {};
  if (contentType) {
    headers['Content-Type'] = contentType;
  }
  const token = getAuthToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

async function safeParseJson(res, defaultErrorMsg = 'Request failed') {
  const text = await res.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch {
    if (!res.ok) {
      throw new Error(`Server Error (${res.status}): ${text.slice(0, 150) || 'Internal server error'}`);
    }
    throw new Error('Received unexpected non-JSON response from server');
  }
  if (!res.ok) {
    throw new Error(data.detail || data.message || defaultErrorMsg);
  }
  return data;
}

// ----------------- Auth Endpoints -----------------
export async function registerStudent(registrationData) {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(registrationData),
  });
  const data = await safeParseJson(res, 'Registration failed');
  setAuth(data.access_token, data.user);
  return data;
}

export async function loginStudent(identifier, password) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ identifier, password }),
  });
  const data = await safeParseJson(res, 'Invalid email/admission number or password');
  setAuth(data.access_token, data.user);
  return data;
}

export async function loginAdmin(identifier, password) {
  const res = await fetch(`${API_BASE}/auth/admin/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ identifier, password }),
  });
  const data = await safeParseJson(res, 'Invalid admin credentials');
  setAuth(data.access_token, data.user);
  return data;
}

export async function fetchUserProfile() {
  const res = await fetch(`${API_BASE}/profile`, {
    headers: getHeaders(),
  });
  return safeParseJson(res, 'Failed to load profile');
}

export async function fetchMyDashboard() {
  const res = await fetch(`${API_BASE}/dashboard/me`, {
    headers: getHeaders(),
  });
  return safeParseJson(res, 'Failed to load personalized dashboard');
}

// ----------------- Public & Data Endpoints -----------------
export async function fetchStudents() {
  const res = await fetch(`${API_BASE}/students`, {
    headers: getHeaders(),
  });
  return safeParseJson(res, 'Failed to load students');
}

export async function fetchDashboard(studentId) {
  const targetId = studentId || 'guest';
  const res = await fetch(`${API_BASE}/dashboard/${targetId}`, {
    headers: getHeaders(),
  });
  return safeParseJson(res, 'Failed to load dashboard data');
}

export async function fetchNotices(studentId = null) {
  const url = studentId ? `${API_BASE}/notices?student_id=${studentId}` : `${API_BASE}/notices`;
  const res = await fetch(url, { headers: getHeaders() });
  return safeParseJson(res, 'Failed to load notices');
}

export async function fetchEvents(studentId = null) {
  const url = studentId ? `${API_BASE}/events?student_id=${studentId}` : `${API_BASE}/events`;
  const res = await fetch(url, { headers: getHeaders() });
  return safeParseJson(res, 'Failed to load events');
}

export async function fetchDeadlines(course = null, semester = null) {
  let url = `${API_BASE}/deadlines`;
  const params = [];
  if (course) params.push(`course=${encodeURIComponent(course)}`);
  if (semester) params.push(`semester=${semester}`);
  if (params.length > 0) url += `?${params.join('&')}`;

  const res = await fetch(url, { headers: getHeaders() });
  return safeParseJson(res, 'Failed to load deadlines');
}

export async function fetchTimetable(course, semester, isExam = null) {
  let url = `${API_BASE}/timetable?course=${encodeURIComponent(course)}&semester=${semester}`;
  if (isExam !== null) url += `&is_exam=${isExam}`;
  const res = await fetch(url, { headers: getHeaders() });
  return safeParseJson(res, 'Failed to load timetable');
}

export async function fetchDocuments() {
  const res = await fetch(`${API_BASE}/documents`, { headers: getHeaders() });
  return safeParseJson(res, 'Failed to load documents');
}

export async function sendChatMessage(studentId, message, course = null, semester = null) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({
      student_id: studentId,
      message,
      course,
      semester,
    }),
  });
  return safeParseJson(res, 'Chat message failed');
}

// ----------------- Administrative Endpoints (Require Admin Auth) -----------------
export async function extractAnnouncement(text) {
  const res = await fetch(`${API_BASE}/admin/extract-announcement`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ text }),
  });
  if (res.status === 403) throw new Error('Forbidden: Administrative privileges required.');
  if (!res.ok) throw new Error('Failed to extract announcement details');
  return res.json();
}

export async function publishAnnouncement(announcementData) {
  const res = await fetch(`${API_BASE}/admin/publish-announcement`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(announcementData),
  });
  if (res.status === 403) throw new Error('Forbidden: Administrative privileges required.');
  if (!res.ok) throw new Error('Failed to publish announcement');
  return res.json();
}

export async function uploadDocument(formData) {
  const headers = {};
  const token = getAuthToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}/documents/upload`, {
    method: 'POST',
    headers,
    body: formData,
  });
  if (res.status === 403) throw new Error('Forbidden: Administrative privileges required.');
  if (!res.ok) throw new Error('Failed to upload document');
  return res.json();
}

export async function syncWebsite() {
  const res = await fetch(`${API_BASE}/admin/sync-website`, {
    method: 'POST',
    headers: getHeaders(),
  });
  if (res.status === 403) throw new Error('Forbidden: Administrative privileges required.');
  if (!res.ok) throw new Error('Failed to synchronize website');
  return res.json();
}

export async function createManualEvent(eventData) {
  const res = await fetch(`${API_BASE}/events`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(eventData),
  });
  if (res.status === 403) throw new Error('Forbidden: Administrative privileges required.');
  if (!res.ok) throw new Error('Failed to create event');
  return res.json();
}

export async function createManualNotice(noticeData) {
  const res = await fetch(`${API_BASE}/notices`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(noticeData),
  });
  if (res.status === 403) throw new Error('Forbidden: Administrative privileges required.');
  if (!res.ok) throw new Error('Failed to create notice');
  return res.json();
}

// ----------------- Continuous Knowledge Improvement -----------------
export async function submitFeedback(feedbackData) {
  const res = await fetch(`${API_BASE}/feedback`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(feedbackData),
  });
  if (!res.ok) throw new Error('Failed to submit feedback');
  return res.json();
}

export async function fetchLearningQueue() {
  const res = await fetch(`${API_BASE}/admin/learning-queue`, {
    headers: getHeaders(),
  });
  if (res.status === 403) throw new Error('Forbidden: Administrative privileges required.');
  if (!res.ok) throw new Error('Failed to load learning queue');
  return res.json();
}

export async function resolveLearningQueueItem(itemId, resolveData) {
  const res = await fetch(`${API_BASE}/admin/learning-queue/${itemId}/resolve`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(resolveData),
  });
  if (res.status === 403) throw new Error('Forbidden: Administrative privileges required.');
  if (!res.ok) throw new Error('Failed to resolve question');
  return res.json();
}

export async function ignoreLearningQueueItem(itemId) {
  const res = await fetch(`${API_BASE}/admin/learning-queue/${itemId}/ignore`, {
    method: 'POST',
    headers: getHeaders(),
  });
  if (res.status === 403) throw new Error('Forbidden: Administrative privileges required.');
  if (!res.ok) throw new Error('Failed to ignore item');
  return res.json();
}

export async function fetchAdminFeedback() {
  const res = await fetch(`${API_BASE}/admin/feedback`, {
    headers: getHeaders(),
  });
  if (res.status === 403) throw new Error('Forbidden: Administrative privileges required.');
  if (!res.ok) throw new Error('Failed to load feedback');
  return res.json();
}

