import clsx from 'clsx'

interface Props {
  score: 'green' | 'yellow' | 'red' | string
  showLabel?: boolean
  size?: 'sm' | 'md'
}

const LABELS = { green: 'Healthy', yellow: 'At Risk', red: 'Critical' }
const CLASSES = {
  green: 'badge-green',
  yellow: 'badge-yellow',
  red: 'badge-red',
}

export function HealthBadge({ score, showLabel = true, size = 'md' }: Props) {
  const cls = CLASSES[score as keyof typeof CLASSES] ?? 'badge-blue'
  const label = LABELS[score as keyof typeof LABELS] ?? score
  return (
    <span className={clsx(cls, size === 'sm' && 'text-xs')}>
      <span className="w-1.5 h-1.5 rounded-full bg-current mr-1.5 inline-block" />
      {showLabel && label}
    </span>
  )
}
