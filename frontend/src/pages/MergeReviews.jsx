import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import client from '../api/client'
import Loading from '../components/Loading'
import ErrorMessage from '../components/ErrorMessage'
import Badge from '../components/Badge'

export default function MergeReviews() {
  const [reviews, setReviews] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    client.get('/api/merge-reviews?limit=100')
      .then(r => setReviews(r.data))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Loading />

  return (
    <div>
      <h1 className="text-xl font-bold text-slate-100 mb-6">Merge Reviews</h1>
      <ErrorMessage message={error} />
      <div className="bg-slate-800 border border-slate-700 rounded-lg overflow-auto">
        <table className="w-full text-sm">
          <thead><tr className="border-b border-slate-700">
            {['ID', 'Result', 'Status', 'Task', 'Sprint', 'Actor', 'Risk', 'Files', 'Findings', 'Blocking', 'Time'].map(h =>
              <th key={h} className="text-left text-slate-500 px-3 py-2 font-normal whitespace-nowrap">{h}</th>
            )}
          </tr></thead>
          <tbody>
            {reviews.map(r => (
              <tr key={r.id} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                <td className="px-3 py-2"><Link to={`/merge-reviews/${r.id}`} className="text-cyan-400 hover:underline">#{r.id}</Link></td>
                <td className="px-3 py-2"><Badge value={r.result || '—'} /></td>
                <td className="px-3 py-2"><Badge value={r.status} /></td>
                <td className="px-3 py-2 font-mono text-xs text-slate-300">{r.task_key || '—'}</td>
                <td className="px-3 py-2 text-slate-400">{r.sprint_name || '—'}</td>
                <td className="px-3 py-2 text-slate-400">{r.actor_username || '—'}</td>
                <td className="px-3 py-2"><Badge value={r.risk_level} /></td>
                <td className="px-3 py-2 text-slate-400">{r.total_files_analyzed}</td>
                <td className="px-3 py-2 text-slate-400">{r.total_findings}</td>
                <td className="px-3 py-2 text-slate-400">{r.blocking_findings_count}</td>
                <td className="px-3 py-2 text-slate-500 text-xs whitespace-nowrap">{new Date(r.created_at).toLocaleString()}</td>
              </tr>
            ))}
            {reviews.length === 0 && <tr><td colSpan={11} className="px-4 py-6 text-slate-500 text-center">No reviews yet.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}
