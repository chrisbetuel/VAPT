import api from '@/services/api'
import type { AxiosResponse } from 'axios'

export const adminApi = {
  listUsers: () => api.get('/users'),
  getUser: (id: number) => api.get(`/users/${id}`),
  createUser: (data: any) => api.post('/users', data),
  updateUser: (id: number, data: any) => api.put(`/users/${id}`, data),
  deleteUser: (id: number) => api.delete(`/users/${id}`),
  getSystemLogs: (params?: any) => api.get('/admin/logs', { params }),
  getSystemStats: () => api.get('/admin/stats'),
}
