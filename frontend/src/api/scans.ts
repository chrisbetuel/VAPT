import api from '@/services/api'

export const scansApi = {
  list: (params?: { page?: number; size?: number; status?: string; target_id?: number }) =>
    api.get('/scans', { params }),
  create: (data: any) => api.post('/scans', data),
  get: (id: number) => api.get(`/scans/${id}`),
  start: (id: number) => api.post(`/scans/${id}/start`),
  stop: (id: number) => api.post(`/scans/${id}/stop`),
  pause: (id: number) => api.post(`/scans/${id}/pause`),
  resume: (id: number) => api.post(`/scans/${id}/resume`),
  delete: (id: number) => api.delete(`/scans/${id}`),
}
