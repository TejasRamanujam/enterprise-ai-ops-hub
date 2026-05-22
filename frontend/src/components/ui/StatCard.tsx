import clsx from 'clsx'
import type { LucideIcon } from 'lucide-react'

interface Props {
  label: string
  value: string | number
  subtitle?: string
  icon: LucideIcon
  trend?: 'up' | 'down' | 'neutral'
  trendValue?: string
  color?: 'blue' | 'green' | 'yellow' | 'red' | 'purple'
}

const COLOR_MAP = {
  blue: { icon: 'text-blue-400 bg-blue-900/30', border: 'border-blue-800/30' },
  green: { icon: 'text-emerald-400 bg-emerald-900/30', border: 'border-emerald-800/30' },
  yellow: { icon: 'text-amber-400 bg-amber-900/30', border: 'border-amber-800/30' },
  red: { icon: 'text-red-400 bg-red-900/30', border: 'border-red-800/30' },
  purple: { icon: 'text-purple-400 bg-purple-900/30', border: 'border-purple-800/30' },
}

export function StatCard({ label, value, subtitle, icon: Icon, trend, trendValue, color = 'blue' }: Props) {
  const colors = COLOR_MAP[color]
  return (
    <div className={clsx('stat-card border', colors.border)}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-gray-500 font-medium uppercase tracking-wider">{label}</p>
          <p className="text-2xl font-bold text-white mt-1">{value}</p>
          {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
        </div>
        <div className={clsx('p-2.5 rounded-lg', colors.icon)}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
      {trendValue && (
        <div className="mt-2 flex items-center gap-1">
          <span className={clsx(
            'text-xs font-medium',
            trend === 'up' ? 'text-emerald-400' : trend === 'down' ? 'text-red-400' : 'text-gray-400'
          )}>
            {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'} {trendValue}
          </span>
          <span className="text-xs text-gray-600">vs last sprint</span>
        </div>
      )}
    </div>
  )
}
