const variants = {
  success: 'bg-green-900/60 text-green-400 border border-green-700',
  failed: 'bg-red-900/60 text-red-400 border border-red-700',
  pending: 'bg-yellow-900/60 text-yellow-400 border border-yellow-700',
  running: 'bg-blue-900/60 text-blue-400 border border-blue-700',
  skipped: 'bg-slate-700 text-slate-400 border border-slate-600',
  completed: 'bg-green-900/60 text-green-400 border border-green-700',
  critical: 'bg-red-900/60 text-red-400 border border-red-700',
  high: 'bg-orange-900/60 text-orange-400 border border-orange-700',
  warning: 'bg-yellow-900/60 text-yellow-400 border border-yellow-700',
  info: 'bg-blue-900/60 text-blue-400 border border-blue-700',
  default: 'bg-slate-700 text-slate-300 border border-slate-600',
}

export default function Badge({ value, label }) {
  const key = (value || '').toLowerCase()
  const cls = variants[key] || variants.default
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${cls}`}>
      {label || value || '—'}
    </span>
  )
}
