import api from '@/services/api'

export const dashboardApi = {
  stats: () => api.get('/dashboard/stats'),
  recentScans: () => api.get('/dashboard/scans/recent'),
  vulnerabilitySummary: () => api.get('/dashboard/vulnerabilities/summary'),
  vulnerabilityTrends: () => api.get('/dashboard/vulnerabilities/trends'),
}
