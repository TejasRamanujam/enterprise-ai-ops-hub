import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { reportsApi, projectsApi } from '@/services/api'
import { FileText, Bot, Plus, Check, X, Clock, Loader2, ChevronRight } from 'lucide-react'
import type { Report, AIApproval } from '@/types'
import ReactMarkdown from 'react-markdown'
import { format } from 'date-fns'
import toast from 'react-hot-toast'
import clsx from 'clsx'

const REPORT_TYPES = ['weekly', 'monthly', 'quarterly', 'sprint', 'executive', 'risk']
const AUDIENCES = ['engineer', 'manager', 'executive']

export function ReportsPage() {
  const [showGenerate, setShowGenerate] = useState(false)
  const [selectedReport, setSelectedReport] = useState<Report | null>(null)
  const [genForm, setGenForm] = useState({ project_id: '', report_type: 'weekly', audience: 'manager' })
  const queryClient = useQueryClient()

  const { data: reports = [], isLoading } = useQuery({
    queryKey: ['reports'],
    queryFn: () => reportsApi.list({ limit: 20 }),
  })

  const { data: approvals = [] } = useQuery({
    queryKey: ['reports', 'approvals'],
    queryFn: reportsApi.approvals,
  })

  const { data: projects = [] } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.list(),
  })

  const generateMutation = useMutation({
    mutationFn: reportsApi.generate,
    onSuccess: () => {
      toast.success('Report generation started!')
      setShowGenerate(false)
      queryClient.invalidateQueries({ queryKey: ['reports'] })
    },
    onError: () => toast.error('Failed to generate report'),
  })

  const approveMutation = useMutation({
    mutationFn: ({ id, decision }: { id: string; decision: string }) =>
      reportsApi.processApproval(id, decision),
    onSuccess: () => {
      toast.success('Approval processed')
      queryClient.invalidateQueries({ queryKey: ['reports', 'approvals'] })
    },
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">AI Reports</h1>
          <p className="text-sm text-gray-500 mt-0.5">Automated executive and sprint reporting</p>
        </div>
        <button onClick={() => setShowGenerate(true)} className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" />
          Generate Report
        </button>
      </div>

      {/* Pending approvals */}
      {(approvals as AIApproval[]).length > 0 && (
        <div className="card border-amber-800/40">
          <div className="flex items-center gap-2 mb-3">
            <Clock className="w-4 h-4 text-amber-400" />
            <h3 className="font-semibold text-amber-400 text-sm">Pending Approvals ({(approvals as AIApproval[]).length})</h3>
          </div>
          <div className="space-y-2">
            {(approvals as AIApproval[]).map(a => (
              <div key={a.id} className="flex items-start justify-between gap-3 p-3 bg-amber-900/10 border border-amber-800/30 rounded-lg">
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-200">{a.action_type}</p>
                  <p className="text-xs text-gray-500 mt-0.5">{a.description}</p>
                  {a.ai_reasoning && <p className="text-xs text-gray-600 mt-1 italic">AI: {a.ai_reasoning}</p>}
                </div>
                <div className="flex gap-2 flex-shrink-0">
                  <button onClick={() => approveMutation.mutate({ id: a.id, decision: 'approve' })} className="p-1.5 bg-emerald-900/30 hover:bg-emerald-900/60 text-emerald-400 rounded-md transition-colors">
                    <Check className="w-4 h-4" />
                  </button>
                  <button onClick={() => approveMutation.mutate({ id: a.id, decision: 'reject' })} className="p-1.5 bg-red-900/30 hover:bg-red-900/60 text-red-400 rounded-md transition-colors">
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Generate modal */}
      {showGenerate && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
          <div className="card w-full max-w-md">
            <h2 className="font-bold text-white mb-4">Generate AI Report</h2>
            <div className="space-y-3">
              <div>
                <label className="text-xs text-gray-400 block mb-1">Project (optional)</label>
                <select
                  value={genForm.project_id}
                  onChange={e => setGenForm(f => ({ ...f, project_id: e.target.value }))}
                  className="input w-full"
                >
                  <option value="">Portfolio / All Projects</option>
                  {projects.map((p: { id: string; name: string; key: string }) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">Report Type</label>
                <select
                  value={genForm.report_type}
                  onChange={e => setGenForm(f => ({ ...f, report_type: e.target.value }))}
                  className="input w-full capitalize"
                >
                  {REPORT_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">Audience</label>
                <select
                  value={genForm.audience}
                  onChange={e => setGenForm(f => ({ ...f, audience: e.target.value }))}
                  className="input w-full capitalize"
                >
                  {AUDIENCES.map(a => <option key={a} value={a}>{a}</option>)}
                </select>
              </div>
            </div>
            <div className="flex gap-2 mt-4">
              <button
                onClick={() => generateMutation.mutate(genForm)}
                disabled={generateMutation.isPending}
                className="btn-primary flex items-center gap-2 flex-1"
              >
                {generateMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Bot className="w-4 h-4" />}
                Generate
              </button>
              <button onClick={() => setShowGenerate(false)} className="btn-secondary">Cancel</button>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Report list */}
        <div className="space-y-2">
          {isLoading ? (
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="card animate-pulse h-20 bg-gray-800/50" />
              ))}
            </div>
          ) : (
            (reports as Report[]).map(report => (
              <div
                key={report.id}
                onClick={() => setSelectedReport(report)}
                className={clsx(
                  'card cursor-pointer transition-all hover:border-gray-700',
                  selectedReport?.id === report.id && 'border-brand-600/50 bg-brand-900/10'
                )}
              >
                <div className="flex items-start gap-2.5">
                  <FileText className="w-4 h-4 text-gray-400 flex-shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-200 truncate">{report.title}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="badge-blue capitalize">{report.report_type}</span>
                      <span className="text-xs text-gray-500 capitalize">{report.audience}</span>
                    </div>
                    <p className="text-xs text-gray-600 mt-1">{format(new Date(report.created_at), 'MMM d, h:mm a')}</p>
                  </div>
                  <ChevronRight className="w-4 h-4 text-gray-600 flex-shrink-0" />
                </div>
              </div>
            ))
          )}
        </div>

        {/* Report viewer */}
        <div className="lg:col-span-2">
          {selectedReport ? (
            <div className="card sticky top-6">
              <div className="flex items-start justify-between mb-4 pb-4 border-b border-gray-800">
                <div>
                  <h2 className="font-bold text-white">{selectedReport.title}</h2>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="badge-blue capitalize">{selectedReport.report_type}</span>
                    <span className="text-xs text-gray-500">{selectedReport.audience}</span>
                    {selectedReport.model_used && (
                      <span className="text-xs text-gray-600">· {selectedReport.model_used}</span>
                    )}
                  </div>
                </div>
                {selectedReport.token_cost && (
                  <span className="text-xs text-gray-500">{selectedReport.token_cost.toLocaleString()} tokens</span>
                )}
              </div>
              <div className="prose prose-invert prose-sm max-w-none text-gray-200 overflow-y-auto max-h-[70vh]">
                <ReactMarkdown>{selectedReport.content}</ReactMarkdown>
              </div>
            </div>
          ) : (
            <div className="card flex flex-col items-center justify-center py-16 text-center">
              <FileText className="w-10 h-10 text-gray-700 mb-3" />
              <p className="text-gray-400">Select a report to view</p>
              <p className="text-sm text-gray-600 mt-1">Or generate a new AI report above</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
