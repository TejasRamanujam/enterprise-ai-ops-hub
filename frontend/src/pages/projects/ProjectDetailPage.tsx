import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Bot, AlertTriangle, GitBranch, Zap, CheckCircle2, Clock, TrendingUp, Loader2 } from 'lucide-react'
import { projectsApi, agentsApi } from '@/services/api'
import { HealthBadge } from '@/components/ui/HealthBadge'
import { StatCard } from '@/components/ui/StatCard'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { format } from 'date-fns'
import toast from 'react-hot-toast'
import type { Sprint, Risk } from '@/types'
import clsx from 'clsx'

const SEVERITY_COLORS = {
  critical: 'badge-red',
  high: 'badge-red',
  medium: 'badge-yellow',
  low: 'badge-blue',
}

export function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>()
  const queryClient = useQueryClient()

  const { data: project, isLoading } = useQuery({
    queryKey: ['project', id],
    queryFn: () => projectsApi.get(id!),
    enabled: !!id,
  })

  const { data: sprints = [] } = useQuery({
    queryKey: ['sprints', id],
    queryFn: () => projectsApi.sprints(id!),
    enabled: !!id,
  })

  const { data: risks = [] } = useQuery({
    queryKey: ['risks', id],
    queryFn: () => projectsApi.risks(id!),
    enabled: !!id,
  })

  const runWorkflow = useMutation({
    mutationFn: () => agentsApi.runWorkflow(id!),
    onSuccess: () => {
      toast.success('AI workflow started! Results will appear shortly.')
      queryClient.invalidateQueries({ queryKey: ['project', id] })
    },
    onError: () => toast.error('Failed to start workflow'),
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-6 h-6 animate-spin text-brand-400" />
      </div>
    )
  }

  if (!project) return <div className="text-gray-400">Project not found</div>

  const activeSprint = (sprints as Sprint[]).find(s => s.status === 'active')
  const sprintData = (sprints as Sprint[]).slice(0, 6).map(s => ({
    name: s.name,
    planned: s.planned_points,
    completed: s.completed_points,
  })).reverse()

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-brand-900/50 border border-brand-800/50 flex items-center justify-center text-base font-bold text-brand-400">
            {project.key.substring(0, 2)}
          </div>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-xl font-bold text-white">{project.name}</h1>
              <HealthBadge score={project.health_score ?? 'yellow'} />
            </div>
            <p className="text-sm text-gray-500 mt-0.5">{project.description}</p>
          </div>
        </div>
        <button
          onClick={() => runWorkflow.mutate()}
          disabled={runWorkflow.isPending}
          className="btn-primary flex items-center gap-2"
        >
          {runWorkflow.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Bot className="w-4 h-4" />}
          Run AI Analysis
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Confidence Score"
          value={`${Math.round((project.confidence_score ?? 0) * 100)}%`}
          icon={TrendingUp}
          color="blue"
        />
        <StatCard
          label="Team Size"
          value={project.team_size}
          icon={Zap}
          color="purple"
        />
        <StatCard
          label="Open Risks"
          value={(risks as Risk[]).filter(r => r.status === 'open').length}
          subtitle={`${(risks as Risk[]).filter(r => r.severity === 'critical').length} critical`}
          icon={AlertTriangle}
          color="red"
        />
        <StatCard
          label="Sprint Progress"
          value={activeSprint ? `${Math.round((activeSprint.completed_points / Math.max(activeSprint.planned_points, 1)) * 100)}%` : 'N/A'}
          subtitle={activeSprint?.name}
          icon={CheckCircle2}
          color="green"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Sprint velocity */}
        <div className="card">
          <h3 className="font-semibold text-white text-sm mb-4">Sprint Velocity History</h3>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={sprintData} margin={{ top: 5, right: 5, left: -25, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 10 }} />
              <YAxis tick={{ fill: '#6b7280', fontSize: 10 }} />
              <Tooltip contentStyle={{ backgroundColor: '#111827', border: '1px solid #374151', borderRadius: '8px', fontSize: '12px' }} />
              <Bar dataKey="planned" fill="#3b82f620" stroke="#3b82f6" strokeWidth={1} radius={[3, 3, 0, 0]} name="Planned" />
              <Bar dataKey="completed" fill="#10b981" radius={[3, 3, 0, 0]} name="Completed" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Active sprint */}
        {activeSprint && (
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-white text-sm">{activeSprint.name}</h3>
              <span className="badge-blue">Active</span>
            </div>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-xs mb-1.5">
                  <span className="text-gray-400">Story Points</span>
                  <span className="text-white font-medium">{activeSprint.completed_points} / {activeSprint.planned_points}</span>
                </div>
                <div className="w-full bg-gray-800 rounded-full h-2">
                  <div
                    className="h-2 rounded-full bg-gradient-to-r from-brand-500 to-emerald-500 transition-all"
                    style={{ width: `${Math.min(100, (activeSprint.completed_points / Math.max(activeSprint.planned_points, 1)) * 100)}%` }}
                  />
                </div>
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div className="card-sm text-center">
                  <p className="text-lg font-bold text-white">{activeSprint.tickets_done}</p>
                  <p className="text-xs text-gray-500">Done</p>
                </div>
                <div className="card-sm text-center">
                  <p className="text-lg font-bold text-amber-400">{activeSprint.blocker_count}</p>
                  <p className="text-xs text-gray-500">Blockers</p>
                </div>
                <div className="card-sm text-center">
                  <p className="text-lg font-bold text-white">
                    {activeSprint.success_likelihood ? `${Math.round(activeSprint.success_likelihood * 100)}%` : 'N/A'}
                  </p>
                  <p className="text-xs text-gray-500">Success</p>
                </div>
              </div>
              {activeSprint.ai_summary && (
                <div className="p-3 bg-brand-900/20 border border-brand-800/30 rounded-lg">
                  <div className="flex items-center gap-1.5 mb-1.5">
                    <Bot className="w-3.5 h-3.5 text-brand-400" />
                    <span className="text-xs font-medium text-brand-400">AI Summary</span>
                  </div>
                  <p className="text-xs text-gray-300">{activeSprint.ai_summary}</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Risks */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-white text-sm">Risk Register</h3>
          <span className="text-xs text-gray-500">{(risks as Risk[]).filter(r => r.status === 'open').length} open risks</span>
        </div>
        <div className="space-y-2">
          {(risks as Risk[]).slice(0, 6).map(risk => (
            <div key={risk.id} className="flex items-start gap-3 p-3 bg-gray-800/50 rounded-lg border border-gray-800">
              <AlertTriangle className={clsx('w-4 h-4 mt-0.5 flex-shrink-0',
                risk.severity === 'critical' ? 'text-red-400' :
                risk.severity === 'high' ? 'text-orange-400' :
                risk.severity === 'medium' ? 'text-amber-400' : 'text-blue-400'
              )} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <p className="text-sm font-medium text-gray-200">{risk.title}</p>
                  <span className={SEVERITY_COLORS[risk.severity as keyof typeof SEVERITY_COLORS] ?? 'badge-blue'}>
                    {risk.severity}
                  </span>
                  {risk.is_ai_generated && (
                    <span className="inline-flex items-center gap-1 text-xs text-purple-400">
                      <Bot className="w-3 h-3" /> AI
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-500 line-clamp-1">{risk.description}</p>
                {risk.mitigation && (
                  <p className="text-xs text-emerald-400 mt-1">→ {risk.mitigation}</p>
                )}
              </div>
              <div className="text-right flex-shrink-0">
                <p className="text-sm font-bold text-white">{risk.risk_score.toFixed(1)}</p>
                <p className="text-xs text-gray-600">score</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
