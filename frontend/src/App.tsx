import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from '@/store/auth'
import { AppLayout } from '@/components/layout/AppLayout'
import { LoginPage } from '@/pages/auth/LoginPage'
import { OverviewDashboard } from '@/pages/dashboard/OverviewDashboard'
import { ProjectsPage } from '@/pages/projects/ProjectsPage'
import { ProjectDetailPage } from '@/pages/projects/ProjectDetailPage'
import { ExecutiveDashboard } from '@/pages/dashboard/ExecutiveDashboard'
import { ReportsPage } from '@/pages/reports/ReportsPage'
import { KnowledgePage } from '@/pages/knowledge/KnowledgePage'
import { WorkflowsPage } from '@/pages/workflows/WorkflowsPage'
import { SettingsPage } from '@/pages/settings/SettingsPage'

function RequireAuth({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <RequireAuth>
            <AppLayout />
          </RequireAuth>
        }
      >
        <Route index element={<OverviewDashboard />} />
        <Route path="projects" element={<ProjectsPage />} />
        <Route path="projects/:id" element={<ProjectDetailPage />} />
        <Route path="executive" element={<ExecutiveDashboard />} />
        <Route path="reports" element={<ReportsPage />} />
        <Route path="knowledge" element={<KnowledgePage />} />
        <Route path="workflows" element={<WorkflowsPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
