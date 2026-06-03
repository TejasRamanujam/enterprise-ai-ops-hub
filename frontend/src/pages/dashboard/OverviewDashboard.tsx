import { useQuery } from '@tanstack/react-query'
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell
} from 'recharts'
import {
  FolderKanban, AlertTriangle, FileText, Zap,
  TrendingUp, Shield, Bot, Clock
} from 'lucide-react'
import { analyticsApi, projectsApi, reportsApi } from '@/services/api'
import { StatCard } from '@/components/ui/StatCard'
import { HealthBadge } from '@/components/ui/HealthBadge'
import { format } from 'date-fns'
import type { Project, Report } from '@/types'

const VELOCITY_DATA = [
  { sprint: 'S10', planned: 32, completed: 28 },
  { sprint: 'S11', planned: 34, completed: 31 },
  { sprint: 'S12', planned: 30, completed: 24 },
  { sprint: 'S13', planned: 36, completed: 33 },
  { sprint: 'S14', planned: 34, completed: 11 },
]

const HEALTH_PIE = [
  { name: 'Healthy', value: 2, color: '#10b981' },
  { name: 'At Risk', value: 1, color: '#f59e0b' },
  { name: 'Critical', value: 1, color: '#ef4444' },
]

export function OverviewDashboard() {
  const { data: overview } = useQuery({
    queryKey: ['analytics', 'overview'],
    queryFn: analyticsApi.overview,
  })
  const { data: portfolio } = useQuery({
    queryKey: ['projects', 'portfolio'],
    queryFn: projectsApi.portfolio,
  })
  const { data: reports } = useQuery({
    queryKey: ['reports', 'recent'],
    queryFn: () => reportsApi.list({ limit: 5 }),
  })

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Operations Overview</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {format(new Date(), 'EEEE, MMMM d, yyyy')} · Real-time AI monitoring
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="badge-green">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-1 animate-pulse" />
            AI Agents Active
          </span>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Active Projects"
          value={overview?.active_projects ?? portfolio?.active_projects ?? 4}
          subtitle={`${overview?.total_projects ?? portfolio?.total_projects ?? 6} total`}
          icon={FolderKanban}
          color="blue"
          trend="neutral"
          trendValue="No change"
        />
        <StatCard
          label="Open Risks"
          value={overview?.open_risks ?? portfolio?.total_open_risks ?? 12}
          subtitle={`${portfolio?.critical_risks ?? 3} critical`}
          icon={AlertTriangle}
          color="red"
          trend="down"
          trendValue="↓2 resolved"
        />
        <StatCard
          label="Reports (30d)"
          value={overview?.reports_generated_30d ?? 47}
          subtitle="AI-generated"
          icon={FileText}
          color="purple"
          trend="up"
          trendValue="+12 this week"
        />
        <StatCard
          label="Automation Rate"
          value={`${overview?.automation_efficiency ?? 87}%`}
          subtitle="Manual effort saved"
          icon={Zap}
          color="green"
          trend="up"
          trendValue="+3% MoM"
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Velocity chart */}
        <div className="lg:col-span-2 card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-white text-sm">Sprint Velocity Trend</h3>
            <span className="badge-blue">Portfolio Average</span>
          </div>
          <ResponsiveContainer width="100%" height={180}>
            <AreaChart data={VELOCITY_DATA} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="gradPlanned" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gradCompleted" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="sprint" tick={{ fill: '#6b7280', fontSize: 11 }} />
              <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} />
              <Tooltip
                contentStyle={{ backgroundColor: '#111827', border: '1px solid #374151', borderRadius: '8px', fontSize: '12px' }}
                labelStyle={{ color: '#e5e7eb' }}
              />
              <Area type="monotone" dataKey="planned" stroke="#3b82f6" fill="url(#gradPlanned)" strokeWidth={2} name="Planned" />
              <Area type="monotone" dataKey="completed" stroke="#10b981" fill="url(#gradCompleted)" strokeWidth={2} name="Completed" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Portfolio health pie */}
        <div className="card">
          <h3 className="font-semibold text-white text-sm mb-4">Portfolio Health</h3>
          <ResponsiveContainer width="100%" height={140}>
            <PieChart>
              <Pie data={HEALTH_PIE} cx="50%" cy="50%" innerRadius={40} outerRadius={60} paddingAngle={3} dataKey="value">
                {HEALTH_PIE.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ backgroundColor: '#111827', border: '1px solid #374151', borderRadius: '8px', fontSize: '12px' }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="space-y-1.5 mt-2">
            {HEALTH_PIE.map(item => (
              <div key={item.name} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: item.color }} />
                  <span className="text-gray-400">{item.name}</span>
                </div>
                <span className="font-medium text-white">{item.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Projects list */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-white text-sm">Active Projects</h3>
            <a href="/projects" className="text-xs text-brand-400 hover:text-brand-300">View all →</a>
          </div>
          <div className="space-y-2">
            {(portfolio?.projects ?? []).slice(0, 5).map((p: Project) => (
              <div key={p.id} className="flex items-center justify-between py-2 border-b border-gray-800 last:border-0">
                <div className="flex items-center gap-3">
                  <div className="w-7 h-7 rounded-md bg-brand-900/50 border border-brand-800/50 flex items-center justify-center text-xs font-bold text-brand-400">
                    {p.key.substring(0, 2)}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-200">{p.name}</p>
                    <p className="text-xs text-gray-500">{p.team_size} engineers</p>
                  </div>
                </div>
                <HealthBadge score={p.health_score ?? 'yellow'} />
              </div>
            ))}
          </div>
        </div>

        {/* Recent reports */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-white text-sm">Recent AI Reports</h3>
            <a href="/reports" className="text-xs text-brand-400 hover:text-brand-300">View all →</a>
          </div>
          <div className="space-y-2">
            {(reports ?? []).map((r: Report) => (
              <div key={r.id} className="flex items-start gap-3 py-2 border-b border-gray-800 last:border-0">
                <div className="p-1.5 bg-purple-900/30 rounded-md">
                  <FileText className="w-3.5 h-3.5 text-purple-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-200 truncate">{r.title}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-xs text-gray-500 capitalize">{r.report_type}</span>
                    <span className="text-gray-700">·</span>
                    <span className="text-xs text-gray-500">{r.audience}</span>
                  </div>
                </div>
                <div className="flex items-center gap-1 text-xs text-gray-600 flex-shrink-0">
                  <Clock className="w-3 h-3" />
                  {format(new Date(r.created_at), 'MMM d')}
                </div>
              </div>
            ))}
            {(!reports || reports.length === 0) && (
              <div className="flex items-center justify-center py-6 text-gray-600 text-sm">
                <Bot className="w-4 h-4 mr-2" />
                No reports yet. Run an agent workflow to generate one.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
