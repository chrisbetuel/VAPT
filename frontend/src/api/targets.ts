import api from '@/services/api'

export const targetsApi = {
  list: (params?: { page?: number; size?: number }) =>
    api.get('/targets', { params }),
  create: (data: any) => api.post('/targets', data),
  get: (id: number) => api.get(`/targets/${id}`),
  update: (id: number, data: any) => api.put(`/targets/${id}`, data),
  delete: (id: number) => api.delete(`/targets/${id}`),
}
