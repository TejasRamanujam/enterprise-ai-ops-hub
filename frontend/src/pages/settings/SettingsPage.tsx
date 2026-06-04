import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { agentsApi, analyticsApi } from '@/services/api'
import { useAuthStore } from '@/store/auth'
import { Settings, Key, Users, Database, Brain, Shield, ChevronRight } from 'lucide-react'
import { format } from 'date-fns'
import clsx from 'clsx'

type Tab = 'profile' | 'integrations' | 'token-usage' | 'prompts' | 'audit'

export function SettingsPage() {
  const [tab, setTab] = useState<Tab>('profile')
  const { user } = useAuthStore()

  const { data: tokenUsage = [] } = useQuery({
    queryKey: ['agents', 'token-usage-all'],
    queryFn: () => agentsApi.tokenUsage(90),
    enabled: tab === 'token-usage',
  })

  const { data: promptVersions = [] } = useQuery({
    queryKey: ['agents', 'prompt-versions'],
    queryFn: agentsApi.promptVersions,
    enabled: tab === 'prompts',
  })

  const { data: auditLogs = [] } = useQuery({
    queryKey: ['analytics', 'audit-logs'],
    queryFn: () => analyticsApi.auditLogs({ limit: 30 }),
    enabled: tab === 'audit',
  })

  const TABS = [
    { id: 'profile', label: 'Profile', icon: Users },
    { id: 'integrations', label: 'Integrations', icon: Database },
    { id: 'token-usage', label: 'Token Usage', icon: Brain },
    { id: 'prompts', label: 'Prompt Versions', icon: Key },
    { id: 'audit', label: 'Audit Log', icon: Shield },
  ] as const

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-white">Settings</h1>
        <p className="text-sm text-gray-500 mt-0.5">Platform configuration and administration</p>
      </div>

      <div className="flex gap-1 p-1 bg-gray-900 rounded-xl border border-gray-800 w-fit">
        {TABS.map(t => {
          const Icon = t.icon
          return (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={clsx(
                'flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all',
                tab === t.id
                  ? 'bg-gray-800 text-white'
                  : 'text-gray-500 hover:text-gray-300'
              )}
            >
              <Icon className="w-3.5 h-3.5" />
              {t.label}
            </button>
          )
        })}
      </div>

      {tab === 'profile' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="card">
            <h3 className="font-semibold text-white text-sm mb-4">User Profile</h3>
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <div className="w-16 h-16 rounded-2xl bg-brand-900/50 border border-brand-800/50 flex items-center justify-center text-2xl font-bold text-brand-400">
                  {user?.full_name?.[0] ?? user?.username?.[0] ?? 'U'}
                </div>
                <div>
                  <p className="font-semibold text-white">{user?.full_name ?? user?.username}</p>
                  <p className="text-sm text-gray-500">{user?.email}</p>
                  <span className="text-xs bg-brand-900/40 text-brand-400 border border-brand-800/40 px-2 py-0.5 rounded-full capitalize mt-1 inline-block">
                    {user?.role}
                  </span>
                </div>
              </div>
              <div className="space-y-3">
                <div>
                  <label className="text-xs text-gray-400 block mb-1">Full Name</label>
                  <input defaultValue={user?.full_name ?? ''} className="input w-full" />
                </div>
                <div>
                  <label className="text-xs text-gray-400 block mb-1">Email</label>
                  <input defaultValue={user?.email} className="input w-full" readOnly />
                </div>
                <div>
                  <label className="text-xs text-gray-400 block mb-1">Department</label>
                  <input defaultValue={user?.department ?? ''} className="input w-full" placeholder="e.g. Engineering" />
                </div>
              </div>
              <button className="btn-primary w-full">Save Changes</button>
            </div>
          </div>

          <div className="card">
            <h3 className="font-semibold text-white text-sm mb-4">Change Password</h3>
            <div className="space-y-3">
              <div>
                <label className="text-xs text-gray-400 block mb-1">Current Password</label>
                <input type="password" className="input w-full" />
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">New Password</label>
                <input type="password" className="input w-full" />
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">Confirm Password</label>
                <input type="password" className="input w-full" />
              </div>
              <button className="btn-secondary w-full">Update Password</button>
            </div>
          </div>
        </div>
      )}

      {tab === 'integrations' && (
        <div className="card">
          <h3 className="font-semibold text-white text-sm mb-4">Integration Configuration</h3>
          <div className="space-y-4">
            {[
              { name: 'Jira', icon: '🔵', desc: 'Project management & issue tracking', fields: ['Jira URL', 'Email', 'API Token', 'Project Key'] },
              { name: 'GitHub', icon: '⬛', desc: 'Code repository & PR tracking', fields: ['Personal Access Token', 'Organization', 'Repository'] },
              { name: 'Confluence', icon: '🔷', desc: 'Documentation & knowledge base', fields: ['Confluence URL', 'Email', 'API Token', 'Space Key'] },
              { name: 'Slack', icon: '🟪', desc: 'Team communication & notifications', fields: ['Bot Token', 'Webhook URL', 'Channel ID'] },
            ].map(integration => (
              <div key={integration.name} className="border border-gray-800 rounded-xl p-4">
                <div className="flex items-center gap-3 mb-3">
                  <span className="text-2xl">{integration.icon}</span>
                  <div>
                    <p className="font-semibold text-white text-sm">{integration.name}</p>
                    <p className="text-xs text-gray-500">{integration.desc}</p>
                  </div>
                  <div className="ml-auto">
                    <span className="text-xs bg-gray-800 text-gray-400 px-2 py-0.5 rounded-full">Not configured</span>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  {integration.fields.map(field => (
                    <div key={field}>
                      <label className="text-xs text-gray-500 block mb-1">{field}</label>
                      <input type={field.toLowerCase().includes('token') || field.toLowerCase().includes('key') ? 'password' : 'text'}
                        placeholder={`Enter ${field.toLowerCase()}`}
                        className="input w-full text-sm" />
                    </div>
                  ))}
                </div>
                <button className="btn-secondary mt-3 text-sm">Save Integration</button>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === 'token-usage' && (
        <div className="card">
          <h3 className="font-semibold text-white text-sm mb-4">AI Token Usage (90 days)</h3>
          {tokenUsage.length === 0 ? (
            <p className="text-gray-500 text-sm">No token usage data available.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-800 text-left">
                    <th className="pb-3 text-xs font-medium text-gray-500 uppercase">Agent</th>
                    <th className="pb-3 text-xs font-medium text-gray-500 uppercase">Model</th>
                    <th className="pb-3 text-xs font-medium text-gray-500 uppercase">Calls</th>
                    <th className="pb-3 text-xs font-medium text-gray-500 uppercase">Prompt Tokens</th>
                    <th className="pb-3 text-xs font-medium text-gray-500 uppercase">Completion</th>
                    <th className="pb-3 text-xs font-medium text-gray-500 uppercase">Cost (USD)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                  {tokenUsage.map((u: { agent_name: string; model: string; call_count: number; total_prompt_tokens: number; total_completion_tokens: number; total_cost_usd: number }) => (
                    <tr key={`${u.agent_name}-${u.model}`} className="hover:bg-gray-800/30">
                      <td className="py-3 text-gray-300 capitalize">{u.agent_name.replace('_', ' ')}</td>
                      <td className="py-3 text-gray-400 font-mono text-xs">{u.model}</td>
                      <td className="py-3 text-gray-300">{u.call_count}</td>
                      <td className="py-3 text-gray-300">{u.total_prompt_tokens?.toLocaleString()}</td>
                      <td className="py-3 text-gray-300">{u.total_completion_tokens?.toLocaleString()}</td>
                      <td className="py-3 text-emerald-400 font-medium">${u.total_cost_usd?.toFixed(4)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {tab === 'prompts' && (
        <div className="card">
          <h3 className="font-semibold text-white text-sm mb-4">Prompt Version History</h3>
          {promptVersions.length === 0 ? (
            <p className="text-gray-500 text-sm">No prompt versions recorded yet.</p>
          ) : (
            <div className="space-y-3">
              {promptVersions.map((pv: { id: string; agent_name: string; version: number; created_at: string; change_summary?: string; is_active: boolean }) => (
                <div key={pv.id} className="flex items-start gap-3 p-3 bg-gray-800/50 border border-gray-800 rounded-lg">
                  <div className="w-8 h-8 rounded-lg bg-purple-900/40 flex items-center justify-center text-xs font-bold text-purple-400 flex-shrink-0">
                    v{pv.version}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium text-gray-200 capitalize">{pv.agent_name.replace('_', ' ')}</p>
                      {pv.is_active && <span className="text-xs bg-emerald-900/40 text-emerald-400 px-2 py-0.5 rounded-full">Active</span>}
                    </div>
                    <p className="text-xs text-gray-500 mt-0.5">{pv.change_summary ?? 'No summary'}</p>
                    <p className="text-xs text-gray-600 mt-1">{format(new Date(pv.created_at), 'MMM d, yyyy HH:mm')}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {tab === 'audit' && (
        <div className="card">
          <h3 className="font-semibold text-white text-sm mb-4">Audit Log</h3>
          {auditLogs.length === 0 ? (
            <p className="text-gray-500 text-sm">No audit events recorded.</p>
          ) : (
            <div className="space-y-2">
              {auditLogs.map((log: { id: string; action: string; resource_type: string; resource_id?: string; created_at: string; user_id?: string; ip_address?: string; details?: Record<string, unknown> }) => (
                <div key={log.id} className="flex items-start gap-3 p-3 bg-gray-800/30 border border-gray-800/50 rounded-lg">
                  <div className="w-2 h-2 rounded-full bg-brand-500 mt-1.5 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-medium text-gray-200">{log.action}</span>
                      <span className="text-xs bg-gray-800 text-gray-400 px-1.5 py-0.5 rounded capitalize">{log.resource_type}</span>
                      {log.resource_id && <span className="text-xs text-gray-600 font-mono">{log.resource_id.slice(0, 8)}</span>}
                    </div>
                    <div className="flex items-center gap-3 mt-0.5 text-xs text-gray-500">
                      <span>{format(new Date(log.created_at), 'MMM d, HH:mm:ss')}</span>
                      {log.ip_address && <span>{log.ip_address}</span>}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
