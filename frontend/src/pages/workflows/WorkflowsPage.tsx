import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { agentsApi, projectsApi } from '@/services/api'
import { Workflow, Play, CheckCircle, XCircle, Clock, Bot, Zap, Loader2, ChevronDown } from 'lucide-react'
import toast from 'react-hot-toast'
import clsx from 'clsx'

const AGENTS = [
  { id: 'data_aggregation', name: 'Data Aggregation', description: 'Collects data from Jira, GitHub, Confluence, Slack', color: 'blue' },
  { id: 'project_health', name: 'Project Health', description: 'Analyzes velocity, delivery confidence, technical debt', color: 'green' },
  { id: 'risk_detection', name: 'Risk Detection', description: 'Identifies blockers, resource constraints, and threats', color: 'red' },
  { id: 'executive_reporting', name: 'Executive Reporting', description: 'Generates audience-specific status reports', color: 'purple' },
  { id: 'knowledge_retrieval', name: 'Knowledge Retrieval', description: 'RAG-based enterprise knowledge search', color: 'yellow' },
  { id: 'action_items', name: 'Action Items', description: 'Generates prioritized follow-ups with owners & deadlines', color: 'orange' },
]

const COLOR_MAP: Record<string, string> = {
  blue: 'bg-blue-900/30 border-blue-800/40 text-blue-400',
  green: 'bg-emerald-900/30 border-emerald-800/40 text-emerald-400',
  red: 'bg-red-900/30 border-red-800/40 text-red-400',
  purple: 'bg-purple-900/30 border-purple-800/40 text-purple-400',
  yellow: 'bg-amber-900/30 border-amber-800/40 text-amber-400',
  orange: 'bg-orange-900/30 border-orange-800/40 text-orange-400',
}

export function WorkflowsPage() {
  const [selectedProject, setSelectedProject] = useState('')
  const [selectedAgents, setSelectedAgents] = useState<string[]>(AGENTS.map(a => a.id))
  const [taskId, setTaskId] = useState<string | null>(null)

  const { data: projects = [] } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.list(),
  })

  const { data: taskStatus } = useQuery({
    queryKey: ['task', taskId],
    queryFn: () => agentsApi.taskStatus(taskId!),
    enabled: !!taskId,
    refetchInterval: (data: { status: string } | undefined) => {
      if (!data) return 2000
      return ['SUCCESS', 'FAILURE'].includes(data.status) ? false : 2000
    },
  })

  const runWorkflow = useMutation({
    mutationFn: () => agentsApi.runWorkflow(selectedProject || 'portfolio', selectedAgents),
    onSuccess: (data: { task_id: string }) => {
      setTaskId(data.task_id)
      toast.success('Workflow started!')
    },
    onError: () => toast.error('Failed to start workflow'),
  })

  const toggleAgent = (id: string) => {
    setSelectedAgents(prev =>
      prev.includes(id) ? prev.filter(a => a !== id) : [...prev, id]
    )
  }

  const taskRunning = taskStatus && !['SUCCESS', 'FAILURE'].includes(taskStatus.status)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Workflow Center</h1>
          <p className="text-sm text-gray-500 mt-0.5">Orchestrate multi-agent AI workflows across your projects</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Configuration */}
        <div className="lg:col-span-2 space-y-4">
          <div className="card">
            <h3 className="font-semibold text-white text-sm mb-4">Configure Workflow</h3>
            <div className="space-y-4">
              <div>
                <label className="text-xs text-gray-400 block mb-1.5">Target Project</label>
                <select
                  value={selectedProject}
                  onChange={e => setSelectedProject(e.target.value)}
                  className="input w-full"
                >
                  <option value="">Portfolio (all projects)</option>
                  {projects.map((p: { id: string; name: string }) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs text-gray-400 block mb-2">Select Agents ({selectedAgents.length}/{AGENTS.length})</label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {AGENTS.map(agent => {
                    const selected = selectedAgents.includes(agent.id)
                    return (
                      <button
                        key={agent.id}
                        onClick={() => toggleAgent(agent.id)}
                        className={clsx(
                          'flex items-start gap-3 p-3 rounded-lg border text-left transition-all',
                          selected
                            ? `${COLOR_MAP[agent.color]} border-opacity-100`
                            : 'bg-gray-800/50 border-gray-800 text-gray-500 hover:border-gray-700'
                        )}
                      >
                        <div className={clsx('w-4 h-4 rounded border flex-shrink-0 mt-0.5 flex items-center justify-center',
                          selected ? 'bg-current border-current' : 'border-gray-600'
                        )}>
                          {selected && <CheckCircle className="w-3 h-3 text-gray-900" />}
                        </div>
                        <div>
                          <p className={clsx('text-sm font-medium', selected ? '' : 'text-gray-400')}>{agent.name}</p>
                          <p className="text-xs text-gray-500 mt-0.5">{agent.description}</p>
                        </div>
                      </button>
                    )
                  })}
                </div>
              </div>

              <button
                onClick={() => runWorkflow.mutate()}
                disabled={runWorkflow.isPending || selectedAgents.length === 0 || !!taskRunning}
                className="btn-primary w-full flex items-center justify-center gap-2 py-2.5"
              >
                {runWorkflow.isPending || taskRunning ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Play className="w-4 h-4" />
                )}
                {taskRunning ? 'Workflow Running...' : 'Run Workflow'}
              </button>
            </div>
          </div>
        </div>

        {/* Status panel */}
        <div className="space-y-4">
          {taskId && taskStatus && (
            <div className="card">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-white text-sm">Execution Status</h3>
                <span className={clsx(
                  'text-xs font-medium px-2 py-0.5 rounded-full',
                  taskStatus.status === 'SUCCESS' ? 'bg-emerald-900/40 text-emerald-400' :
                  taskStatus.status === 'FAILURE' ? 'bg-red-900/40 text-red-400' :
                  'bg-brand-900/40 text-brand-400'
                )}>
                  {taskStatus.status}
                </span>
              </div>
              <div className="space-y-2">
                {AGENTS.filter(a => selectedAgents.includes(a.id)).map((agent, idx) => {
                  const completed = taskStatus.result?.completed_steps?.includes(agent.id)
                  const running = taskRunning && idx === (taskStatus.result?.completed_steps?.length ?? 0)
                  return (
                    <div key={agent.id} className="flex items-center gap-2.5">
                      {completed ? (
                        <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                      ) : running ? (
                        <Loader2 className="w-4 h-4 text-brand-400 animate-spin flex-shrink-0" />
                      ) : (
                        <Clock className="w-4 h-4 text-gray-600 flex-shrink-0" />
                      )}
                      <span className={clsx('text-sm', completed ? 'text-gray-300' : running ? 'text-brand-400' : 'text-gray-600')}>
                        {agent.name}
                      </span>
                    </div>
                  )
                })}
              </div>
              {taskStatus.status === 'SUCCESS' && (
                <div className="mt-3 pt-3 border-t border-gray-800 text-xs text-emerald-400 flex items-center gap-1.5">
                  <Zap className="w-3.5 h-3.5" />
                  Workflow completed successfully
                </div>
              )}
              {taskStatus.status === 'FAILURE' && (
                <div className="mt-3 pt-3 border-t border-gray-800 text-xs text-red-400 flex items-center gap-1.5">
                  <XCircle className="w-3.5 h-3.5" />
                  Workflow failed
                </div>
              )}
            </div>
          )}

          <div className="card">
            <h3 className="font-semibold text-white text-sm mb-3">Agent Architecture</h3>
            <div className="space-y-1.5 text-xs text-gray-500">
              <p className="flex items-center gap-1.5"><Bot className="w-3.5 h-3.5 text-brand-400" />LangGraph Orchestrator</p>
              <p className="pl-5">↳ Data Aggregation</p>
              <p className="pl-5">↳ Project Health Analysis</p>
              <p className="pl-5">↳ Risk Detection</p>
              <p className="pl-5">↳ Executive Reporting</p>
              <p className="pl-5">↳ Action Item Generation</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
