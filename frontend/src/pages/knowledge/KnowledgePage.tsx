import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { knowledgeApi } from '@/services/api'
import { Brain, Send, ExternalLink, Loader2, Database, RefreshCw } from 'lucide-react'
import type { KnowledgeQueryResult, Citation } from '@/types'
import ReactMarkdown from 'react-markdown'
import toast from 'react-hot-toast'

const SUGGESTED_QUERIES = [
  "What are the current blockers for the Customer Identity Platform?",
  "Which teams are impacted by the database migration delays?",
  "What architecture decisions were made in the last sprint?",
  "What are the highest priority risks across all projects?",
  "Summarize the key action items from this week's meetings",
]

export function KnowledgePage() {
  const [query, setQuery] = useState('')
  const [history, setHistory] = useState<Array<{ query: string; result: KnowledgeQueryResult }>>([])

  const { data: sources = [] } = useQuery({
    queryKey: ['knowledge', 'sources'],
    queryFn: knowledgeApi.sources,
  })

  const { data: integrations = [] } = useQuery({
    queryKey: ['knowledge', 'integrations'],
    queryFn: knowledgeApi.integrations,
  })

  const askMutation = useMutation({
    mutationFn: (q: string) => knowledgeApi.query(q, { include_citations: true }),
    onSuccess: (data: KnowledgeQueryResult) => {
      setHistory(prev => [{ query, result: data }, ...prev])
      setQuery('')
    },
    onError: () => toast.error('Failed to query knowledge base'),
  })

  const syncMutation = useMutation({
    mutationFn: (id: string) => knowledgeApi.triggerSync(id),
    onSuccess: () => toast.success('Sync started!'),
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) askMutation.mutate(query.trim())
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Knowledge Assistant</h1>
          <p className="text-sm text-gray-500 mt-0.5">RAG-powered enterprise knowledge retrieval</p>
        </div>
        <span className="badge-purple inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-purple-900/40 text-purple-400 border border-purple-800">
          <Database className="w-3 h-3 mr-1.5" />
          {sources.length} Knowledge Sources
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Chat area */}
        <div className="lg:col-span-2 space-y-4">
          {/* Input */}
          <div className="card">
            <form onSubmit={handleSubmit} className="flex gap-3">
              <div className="flex-1 relative">
                <Brain className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                <input
                  type="text"
                  value={query}
                  onChange={e => setQuery(e.target.value)}
                  placeholder="Ask anything about your projects, blockers, decisions..."
                  className="input w-full pl-9"
                  disabled={askMutation.isPending}
                />
              </div>
              <button
                type="submit"
                disabled={!query.trim() || askMutation.isPending}
                className="btn-primary flex items-center gap-2 px-4"
              >
                {askMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
              </button>
            </form>
            {/* Suggestions */}
            <div className="mt-3 flex flex-wrap gap-2">
              {SUGGESTED_QUERIES.map((q, i) => (
                <button
                  key={i}
                  onClick={() => setQuery(q)}
                  className="text-xs px-2.5 py-1 bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-gray-200 rounded-full transition-colors"
                >
                  {q.length > 50 ? q.slice(0, 50) + '...' : q}
                </button>
              ))}
            </div>
          </div>

          {/* Loading */}
          {askMutation.isPending && (
            <div className="card flex items-center gap-3 text-gray-400">
              <Loader2 className="w-4 h-4 animate-spin text-brand-400" />
              <span className="text-sm">AI is searching across {sources.length} knowledge sources...</span>
            </div>
          )}

          {/* Conversation history */}
          {history.map(({ query: q, result }, i) => (
            <div key={i} className="space-y-3 animate-fade-in">
              {/* User query */}
              <div className="flex justify-end">
                <div className="max-w-lg px-4 py-2.5 bg-brand-600/20 border border-brand-600/30 rounded-2xl rounded-tr-sm text-sm text-gray-200">
                  {q}
                </div>
              </div>
              {/* AI answer */}
              <div className="card">
                <div className="flex items-center gap-2 mb-3">
                  <Brain className="w-4 h-4 text-brand-400" />
                  <span className="text-xs font-medium text-brand-400">AI Knowledge Assistant</span>
                  <span className="text-xs text-gray-600">{result.response_time_ms}ms · {result.token_count} tokens</span>
                  <div className="ml-auto text-xs text-gray-500">
                    Confidence: {Math.round(result.confidence * 100)}%
                  </div>
                </div>
                <div className="prose prose-invert prose-sm max-w-none text-gray-200">
                  <ReactMarkdown>{result.answer}</ReactMarkdown>
                </div>
                {/* Citations */}
                {result.citations.length > 0 && (
                  <div className="mt-4 pt-3 border-t border-gray-800">
                    <p className="text-xs font-medium text-gray-500 mb-2">Sources</p>
                    <div className="space-y-1.5">
                      {result.citations.slice(0, 4).map((c: Citation, ci) => (
                        <div key={ci} className="flex items-start gap-2 text-xs">
                          <span className="w-4 h-4 rounded bg-gray-800 flex items-center justify-center text-gray-500 font-mono flex-shrink-0">{ci + 1}</span>
                          <div className="flex-1">
                            <span className="text-gray-300">{c.title}</span>
                            <span className="text-gray-600 mx-1">·</span>
                            <span className="text-gray-500 capitalize">{c.source_type}</span>
                            <span className="text-gray-600 mx-1">·</span>
                            <span className="text-brand-400">{Math.round(c.relevance_score * 100)}% relevant</span>
                          </div>
                          {c.url && (
                            <a href={c.url} target="_blank" rel="noopener" className="text-gray-600 hover:text-gray-400">
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}

          {history.length === 0 && !askMutation.isPending && (
            <div className="card flex flex-col items-center justify-center py-12 text-center">
              <Brain className="w-10 h-10 text-gray-700 mb-3" />
              <p className="text-gray-400 font-medium">Ask your knowledge base anything</p>
              <p className="text-sm text-gray-600 mt-1">Query across Jira, GitHub, Confluence, and Slack</p>
            </div>
          )}
        </div>

        {/* Sidebar: sources */}
        <div className="space-y-4">
          <div className="card">
            <h3 className="font-semibold text-white text-sm mb-3">Knowledge Sources</h3>
            <div className="space-y-2">
              {sources.map((s: { id: string; name: string; source_type: string; document_count: number; last_synced_at?: string }) => (
                <div key={s.id} className="flex items-center gap-2.5 p-2.5 bg-gray-800/50 rounded-lg">
                  <div className="w-7 h-7 rounded-md bg-brand-900/40 flex items-center justify-center text-xs font-bold text-brand-400">
                    {s.source_type[0].toUpperCase()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-gray-200 truncate">{s.name}</p>
                    <p className="text-xs text-gray-500">{s.document_count} docs</p>
                  </div>
                  <span className="badge-green text-xs">Active</span>
                </div>
              ))}
            </div>
          </div>

          <div className="card">
            <h3 className="font-semibold text-white text-sm mb-3">Integrations</h3>
            <div className="space-y-2">
              {integrations.map((i: { id: string; name: string; integration_type: string; is_enabled: boolean; sync_count: number }) => (
                <div key={i.id} className="flex items-center justify-between p-2.5 bg-gray-800/50 rounded-lg">
                  <div>
                    <p className="text-xs font-medium text-gray-200">{i.name}</p>
                    <p className="text-xs text-gray-500 capitalize">{i.integration_type}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={i.is_enabled ? 'badge-green' : 'badge-yellow'}>
                      {i.is_enabled ? 'On' : 'Off'}
                    </span>
                    <button
                      onClick={() => syncMutation.mutate(i.id)}
                      className="text-gray-600 hover:text-gray-400 transition-colors"
                    >
                      <RefreshCw className={`w-3.5 h-3.5 ${syncMutation.isPending ? 'animate-spin' : ''}`} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
