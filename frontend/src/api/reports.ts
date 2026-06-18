import api from '@/services/api'

export const reportsApi = {
  list: (params?: { page?: number; size?: number; scan_id?: number }) =>
    api.get('/reports', { params }),
  generate: (data: any) => api.post('/reports', data),
  get: (id: number) => api.get(`/reports/${id}`),
  download: (id: number, format: string) =>
    api.get(`/reports/${id}/download/${format}`, { responseType: 'blob' }),
  delete: (id: number) => api.delete(`/reports/${id}`),
}
