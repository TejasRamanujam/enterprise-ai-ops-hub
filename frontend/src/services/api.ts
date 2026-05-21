import axios from 'axios'
import { useAuthStore } from '@/store/auth'

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
})

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      const refreshToken = useAuthStore.getState().refreshToken
      if (refreshToken) {
        try {
          const { data } = await axios.post('/api/v1/auth/refresh', { refresh_token: refreshToken })
          useAuthStore.getState().setAuth(data.user, data.access_token, data.refresh_token)
          original.headers.Authorization = `Bearer ${data.access_token}`
          return api(original)
        } catch {
          useAuthStore.getState().logout()
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)

export default api

// Auth
export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }).then(r => r.data),
  me: () => api.get('/auth/me').then(r => r.data),
  logout: () => {},
}

// Projects
export const projectsApi = {
  list: (params?: Record<string, unknown>) =>
    api.get('/projects', { params }).then(r => r.data),
  get: (id: string) => api.get(`/projects/${id}`).then(r => r.data),
  create: (data: unknown) => api.post('/projects', data).then(r => r.data),
  update: (id: string, data: unknown) => api.patch(`/projects/${id}`, data).then(r => r.data),
  portfolio: () => api.get('/projects/portfolio').then(r => r.data),
  sprints: (id: string) => api.get(`/projects/${id}/sprints`).then(r => r.data),
  risks: (id: string) => api.get(`/projects/${id}/risks`).then(r => r.data),
}

// Reports
export const reportsApi = {
  list: (params?: Record<string, unknown>) =>
    api.get('/reports', { params }).then(r => r.data),
  get: (id: string) => api.get(`/reports/${id}`).then(r => r.data),
  generate: (data: unknown) => api.post('/reports/generate', data).then(r => r.data),
  approvals: () => api.get('/reports/approvals/pending').then(r => r.data),
  processApproval: (id: string, decision: string, notes?: string) =>
    api.post(`/reports/approvals/${id}`, { approval_id: id, decision, notes }).then(r => r.data),
}

// Knowledge
export const knowledgeApi = {
  query: (query: string, options?: Record<string, unknown>) =>
    api.post('/knowledge/query', { query, ...options }).then(r => r.data),
  sources: () => api.get('/knowledge/sources').then(r => r.data),
  integrations: () => api.get('/knowledge/integrations').then(r => r.data),
  triggerSync: (id: string) =>
    api.post(`/knowledge/integrations/${id}/sync`).then(r => r.data),
}

// Agents
export const agentsApi = {
  run: (agentName: string, projectId?: string, params?: Record<string, unknown>) =>
    api.post('/agents/run', { agent_name: agentName, project_id: projectId, parameters: params }).then(r => r.data),
  runWorkflow: (projectId: string, agents?: string[]) =>
    api.post('/agents/workflow/run', { project_id: projectId, include_agents: agents }).then(r => r.data),
  taskStatus: (taskId: string) =>
    api.get(`/agents/tasks/${taskId}`).then(r => r.data),
  tokenUsage: (days?: number) =>
    api.get('/agents/token-usage', { params: { days } }).then(r => r.data),
}

// Analytics
export const analyticsApi = {
  overview: () => api.get('/analytics/overview').then(r => r.data),
  velocity: (projectId?: string) =>
    api.get('/analytics/velocity', { params: { project_id: projectId } }).then(r => r.data),
  riskHeatmap: () => api.get('/analytics/risk-heatmap').then(r => r.data),
  auditLogs: (params?: Record<string, unknown>) =>
    api.get('/analytics/audit-logs', { params }).then(r => r.data),
}
