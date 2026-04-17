const API_BASE = localStorage.getItem("medibook_api_base") || "http://localhost:8000/api";

const api = {
  token: () => localStorage.getItem("medibook_token"),
  user: () => JSON.parse(localStorage.getItem("medibook_user") || "null"),

  headers() {
    const h = { "Content-Type": "application/json" };
    if (this.token()) h["Authorization"] = `Bearer ${this.token()}`;
    return h;
  },

  async request(method, path, body = null) {
    const opts = { method, headers: this.headers() };
    if (body !== null) opts.body = JSON.stringify(body);
    const res = await fetch(`${API_BASE}${path}`, opts);
    const contentType = res.headers.get("content-type") || "";
    const data = contentType.includes("application/json") ? await res.json() : await res.text();
    if (!res.ok) {
      const message = typeof data === "object" ? (data.detail || data.message || "Request failed") : "Request failed";
      throw new Error(message);
    }
    return data;
  },

  get: (path) => api.request("GET", path),
  post: (path, body) => api.request("POST", path, body),
  put: (path, body) => api.request("PUT", path, body),
  delete: (path) => api.request("DELETE", path),
};

function setAuth(data) {
  localStorage.setItem("medibook_token", data.token);
  localStorage.setItem("medibook_user", JSON.stringify(data.user));
}

function clearAuth() {
  localStorage.removeItem("medibook_token");
  localStorage.removeItem("medibook_user");
}

function logout() {
  clearAuth();
  window.location.href = "login.html";
}

function requireAuth(adminOnly = false) {
  const user = api.user();
  if (!user || !api.token()) {
    window.location.href = "login.html";
    return null;
  }
  if (adminOnly && user.role !== "admin") {
    window.location.href = "dashboard.html";
    return null;
  }
  return user;
}

function redirectIfLoggedIn() {
  const user = api.user();
  if (user && api.token()) {
    window.location.href = user.role === "admin" ? "admin.html" : "dashboard.html";
  }
}

function showAlert(containerId, type, msg) {
  const icons = { success: "✓", error: "✗", info: "ℹ", warning: "⚠" };
  const el = document.getElementById(containerId);
  if (!el) return;
  el.innerHTML = `<div class="alert alert-${type}">${icons[type] || "•"} ${msg}</div>`;
  setTimeout(() => { if (el.innerHTML.includes(msg)) el.innerHTML = ""; }, 4000);
}

function specialtyEmoji(spec) {
  const map = {
    "Cardiologist": "🫀", "Dermatologist": "🧴", "Neurologist": "🧠",
    "Orthopedic": "🦴", "Pediatrician": "👶", "General Physician": "🩺",
    "Gynecologist": "🌸", "Psychiatrist": "💆"
  };
  return map[spec] || "👨‍⚕️";
}

function getInitials(name = "") {
  return name.split(" ").filter(Boolean).map(w => w[0]).join("").slice(0, 2).toUpperCase();
}

function formatDate(dateStr) {
  if (!dateStr) return "";
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
}

function statusBadge(status = "pending") {
  const safe = String(status).toLowerCase();
  const typeMap = {
    pending: "warning",
    confirmed: "success",
    cancelled: "danger"
  };
  return `<span class="badge badge-${typeMap[safe] || 'muted'}">${safe[0].toUpperCase() + safe.slice(1)}</span>`;
}
