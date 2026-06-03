import { useQuery } from '@tanstack/react-query'
import { projectsApi, analyticsApi, agentsApi } from '@/services/api'
import { HealthBadge } from '@/components/ui/HealthBadge'
import { StatCard } from '@/components/ui/StatCard'
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid
} from 'recharts'
import { Shield, TrendingUp, AlertTriangle, DollarSign, Brain, Target } from 'lucide-react'
import type { Project } from '@/types'

const RADAR_DATA = [
  { subject: 'Delivery', A: 82, fullMark: 100 },
  { subject: 'Quality', A: 74, fullMark: 100 },
  { subject: 'Velocity', A: 88, fullMark: 100 },
  { subject: 'Risk Mgmt', A: 65, fullMark: 100 },
  { subject: 'Team Health', A: 79, fullMark: 100 },
  { subject: 'Budget', A: 71, fullMark: 100 },
]

const BUDGET_DATA = [
  { name: 'CIP', budget: 500, spent: 210 },
  { name: 'DAP', budget: 300, spent: 95 },
  { name: 'MAR', budget: 250, spent: 198 },
  { name: 'INFRA', budget: 150, spent: 62 },
]

export function ExecutiveDashboard() {
  const { data: portfolio } = useQuery({
    queryKey: ['projects', 'portfolio'],
    queryFn: projectsApi.portfolio,
  })
  const { data: riskHeatmap = [] } = useQuery({
    queryKey: ['analytics', 'risk-heatmap'],
    queryFn: analyticsApi.riskHeatmap,
  })
  const { data: tokenUsage = [] } = useQuery({
    queryKey: ['agents', 'token-usage'],
    queryFn: () => agentsApi.tokenUsage(30),
  })

  const totalCost = tokenUsage.reduce((sum: number, u: { total_cost_usd: number }) => sum + (u.total_cost_usd ?? 0), 0)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Executive Dashboard</h1>
          <p className="text-sm text-gray-500 mt-0.5">Portfolio-level strategic intelligence</p>
        </div>
        <span className="badge-purple inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-purple-900/40 text-purple-400 border border-purple-800">
          <Brain className="w-3 h-3 mr-1.5" />
          AI-Powered
        </span>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Portfolio Health"
          value={`${Math.round((portfolio?.avg_health_score ?? 0.72) * 100)}%`}
          subtitle="Average across projects"
          icon={TrendingUp}
          color="green"
        />
        <StatCard
          label="Delivery Confidence"
          value={`${Math.round((portfolio?.overall_confidence ?? 0.74) * 100)}%`}
          subtitle="AI forecast accuracy"
          icon={Target}
          color="blue"
        />
        <StatCard
          label="Strategic Risks"
          value={portfolio?.critical_risks ?? 3}
          subtitle={`${portfolio?.total_open_risks ?? 12} total open`}
          icon={AlertTriangle}
          color="red"
        />
        <StatCard
          label="AI Cost (30d)"
          value={`$${totalCost.toFixed(2)}`}
          subtitle="Token usage"
          icon={DollarSign}
          color="purple"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Radar chart */}
        <div className="card">
          <h3 className="font-semibold text-white text-sm mb-4">Portfolio Performance Radar</h3>
          <ResponsiveContainer width="100%" height={200}>
            <RadarChart data={RADAR_DATA}>
              <PolarGrid stroke="#374151" />
              <PolarAngleAxis dataKey="subject" tick={{ fill: '#9ca3af', fontSize: 11 }} />
              <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#6b7280', fontSize: 10 }} />
              <Radar name="Score" dataKey="A" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.2} strokeWidth={2} />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* Budget utilization */}
        <div className="card lg:col-span-2">
          <h3 className="font-semibold text-white text-sm mb-4">Budget Utilization ($K)</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={BUDGET_DATA} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="name" tick={{ fill: '#9ca3af', fontSize: 11 }} />
              <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} />
              <Tooltip contentStyle={{ backgroundColor: '#111827', border: '1px solid #374151', borderRadius: '8px', fontSize: '12px' }} />
              <Bar dataKey="budget" fill="#3b82f620" stroke="#3b82f6" strokeWidth={1} radius={[3, 3, 0, 0]} name="Budget" />
              <Bar dataKey="spent" fill="#10b981" radius={[3, 3, 0, 0]} name="Spent" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Project health table */}
      <div className="card">
        <h3 className="font-semibold text-white text-sm mb-4">Portfolio Status Summary</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-800 text-left">
                <th className="pb-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Project</th>
                <th className="pb-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Health</th>
                <th className="pb-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Confidence</th>
                <th className="pb-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Team</th>
                <th className="pb-3 text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {(portfolio?.projects ?? []).map((p: Project) => (
                <tr key={p.id} className="hover:bg-gray-800/30 transition-colors">
                  <td className="py-3 font-medium text-gray-200">{p.name}</td>
                  <td className="py-3">
                    <HealthBadge score={p.health_score ?? 'yellow'} />
                  </td>
                  <td className="py-3 text-gray-300">
                    {p.confidence_score ? `${Math.round(p.confidence_score * 100)}%` : '—'}
                  </td>
                  <td className="py-3 text-gray-300">{p.team_size} engineers</td>
                  <td className="py-3">
                    <span className="capitalize text-gray-400 text-xs">{p.status.replace('_', ' ')}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* AI Token usage */}
      {tokenUsage.length > 0 && (
        <div className="card">
          <h3 className="font-semibold text-white text-sm mb-4">AI Cost by Agent (30 days)</h3>
          <div className="space-y-2">
            {tokenUsage.map((u: { agent_name: string; model: string; total_tokens: number; total_cost_usd: number; call_count: number }) => (
              <div key={`${u.agent_name}-${u.model}`} className="flex items-center gap-3">
                <div className="w-28 text-xs text-gray-400 truncate capitalize">{u.agent_name.replace('_', ' ')}</div>
                <div className="flex-1 bg-gray-800 rounded-full h-1.5">
                  <div
                    className="bg-brand-500 h-1.5 rounded-full"
                    style={{ width: `${Math.min(100, (u.total_cost_usd / Math.max(totalCost, 0.01)) * 100)}%` }}
                  />
                </div>
                <div className="text-xs text-gray-400 w-16 text-right">${u.total_cost_usd.toFixed(3)}</div>
                <div className="text-xs text-gray-600 w-20 text-right">{u.total_tokens.toLocaleString()} tokens</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
