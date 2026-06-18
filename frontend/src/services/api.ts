import axios, {
  type AxiosInstance,
  type InternalAxiosRequestConfig,
} from "axios";
import { useAuthStore } from "@/stores/authStore";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";

const api: AxiosInstance = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const { tokens } = useAuthStore.getState();
    if (tokens?.access_token) {
      config.headers.Authorization = `Bearer ${tokens.access_token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const { tokens } = useAuthStore.getState();
      if (tokens?.refresh_token) {
        try {
          const { data } = await axios.post(`${API_BASE}/auth/refresh`, {
            refresh_token: tokens.refresh_token,
          });
          useAuthStore.getState().setTokens(data);
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
          return api(originalRequest);
        } catch {
          useAuthStore.getState().logout();
        }
      }
    }
    return Promise.reject(error);
  },
);

export default api;

// =============================================================================
// Auth API
// =============================================================================
export const authApi = {
  login: (email: string, password: string) =>
    api.post("/auth/login", { email, password }),
  register: (data: { email: string; password: string; first_name: string; last_name: string }) =>
    api.post("/auth/register", data),
  refresh: (refreshToken: string) =>
    api.post("/auth/refresh", { refresh_token: refreshToken }),
  me: () => api.get("/auth/me"),
};

// =============================================================================
// Scans API
// =============================================================================
export const scansApi = {
  list: (params?: { page?: number; size?: number; status?: string; target_id?: number }) =>
    api.get("/scans", { params }),
  create: (data: any) => api.post("/scans", data),
  get: (id: number) => api.get(`/scans/${id}`),
  start: (id: number) => api.post(`/scans/${id}/start`),
  stop: (id: number) => api.post(`/scans/${id}/stop`),
  pause: (id: number) => api.post(`/scans/${id}/pause`),
  resume: (id: number) => api.post(`/scans/${id}/resume`),
  delete: (id: number) => api.delete(`/scans/${id}`),
};

// =============================================================================
// Targets API
// =============================================================================
export const targetsApi = {
  list: (params?: { page?: number; size?: number }) =>
    api.get("/targets", { params }),
  create: (data: any) => api.post("/targets", data),
  get: (id: number) => api.get(`/targets/${id}`),
  update: (id: number, data: any) => api.put(`/targets/${id}`, data),
  delete: (id: number) => api.delete(`/targets/${id}`),
};

// =============================================================================
// Reports API
// =============================================================================
export const reportsApi = {
  list: (params?: { page?: number; size?: number; scan_id?: number }) =>
    api.get("/reports", { params }),
  generate: (data: any) => api.post("/reports", data),
  get: (id: number) => api.get(`/reports/${id}`),
  download: (id: number, format: string) =>
    api.get(`/reports/${id}/download/${format}`, { responseType: "blob" }),
  delete: (id: number) => api.delete(`/reports/${id}`),
};

// =============================================================================
// Dashboard API
// =============================================================================
export const dashboardApi = {
  stats: () => api.get("/dashboard/stats"),
  recentScans: () => api.get("/dashboard/scans/recent"),
  vulnerabilitySummary: () => api.get("/dashboard/vulnerabilities/summary"),
  vulnerabilityTrends: () => api.get("/dashboard/vulnerabilities/trends"),
};

// =============================================================================
// Users API (Admin)
// =============================================================================
export const usersApi = {
  list: () => api.get("/users"),
  create: (data: any) => api.post("/users", data),
  get: (id: number) => api.get(`/users/${id}`),
  update: (id: number, data: any) => api.put(`/users/${id}`, data),
  delete: (id: number) => api.delete(`/users/${id}`),
};
