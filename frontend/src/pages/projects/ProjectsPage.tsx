import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Plus, Search, Filter, TrendingUp, Users, Calendar } from 'lucide-react'
import { projectsApi } from '@/services/api'
import { HealthBadge } from '@/components/ui/HealthBadge'
import { format } from 'date-fns'
import type { Project } from '@/types'
import { useState } from 'react'
import clsx from 'clsx'

export function ProjectsPage() {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')

  const { data: projects = [], isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.list(),
  })

  const filtered = (projects as Project[]).filter(p => {
    const matchesSearch = p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.key.toLowerCase().includes(search.toLowerCase())
    const matchesStatus = statusFilter === 'all' || p.status === statusFilter
    return matchesSearch && matchesStatus
  })

  const statusCounts = (projects as Project[]).reduce((acc, p) => {
    acc[p.status] = (acc[p.status] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Projects</h1>
          <p className="text-sm text-gray-500 mt-0.5">{(projects as Project[]).length} projects total</p>
        </div>
        <button className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" />
          New Project
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            placeholder="Search projects..."
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="input w-full pl-9"
          />
        </div>
        <div className="flex items-center gap-2">
          {['all', 'active', 'at_risk', 'on_hold', 'completed'].map(status => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={clsx(
                'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors capitalize',
                statusFilter === status
                  ? 'bg-brand-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:text-gray-200'
              )}
            >
              {status === 'all' ? `All (${(projects as Project[]).length})` : `${status.replace('_', ' ')} (${statusCounts[status] || 0})`}
            </button>
          ))}
        </div>
      </div>

      {/* Project grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="card animate-pulse h-48 bg-gray-800/50" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {filtered.map(project => (
            <Link key={project.id} to={`/projects/${project.id}`}>
              <div className="card hover:border-gray-700 hover:bg-gray-800/50 transition-all cursor-pointer group">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2.5">
                    <div className="w-9 h-9 rounded-lg bg-brand-900/50 border border-brand-800/50 flex items-center justify-center text-sm font-bold text-brand-400">
                      {project.key.substring(0, 2)}
                    </div>
                    <div>
                      <p className="font-semibold text-white text-sm group-hover:text-brand-300 transition-colors">{project.name}</p>
                      <p className="text-xs text-gray-500">{project.key}</p>
                    </div>
                  </div>
                  <HealthBadge score={project.health_score ?? 'yellow'} />
                </div>

                {project.description && (
                  <p className="text-xs text-gray-500 mb-3 line-clamp-2">{project.description}</p>
                )}

                <div className="grid grid-cols-3 gap-3 py-3 border-t border-gray-800">
                  <div className="text-center">
                    <p className="text-sm font-semibold text-white">{project.team_size}</p>
                    <p className="text-xs text-gray-600">Engineers</p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm font-semibold text-white">
                      {project.confidence_score ? `${Math.round(project.confidence_score * 100)}%` : 'N/A'}
                    </p>
                    <p className="text-xs text-gray-600">Confidence</p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm font-semibold text-white capitalize">{project.status.replace('_', ' ')}</p>
                    <p className="text-xs text-gray-600">Status</p>
                  </div>
                </div>

                {project.target_end_date && (
                  <div className="flex items-center gap-1.5 mt-2 text-xs text-gray-500">
                    <Calendar className="w-3 h-3" />
                    Target: {format(new Date(project.target_end_date), 'MMM d, yyyy')}
                  </div>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
