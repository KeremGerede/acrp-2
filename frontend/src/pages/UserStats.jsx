import { useEffect, useState } from 'react'
import client from '../api/client'
import Loading from '../components/Loading'
import ErrorMessage from '../components/ErrorMessage'

export default function UserStats() {
  const [stats, setStats] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    client.get('/api/stats/users')
      .then(r => setStats(r.data))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Loading />

  return (
    <div>
      <h1 className="text-xl font-bold text-slate-100 mb-6">User Activity Stats</h1>
      <ErrorMessage message={error} />
      <div className="bg-slate-800 border border-slate-700 rounded-lg overflow-auto">
        <table className="w-full text-sm">
          <thead><tr className="border-b border-slate-700">
            {['Username', 'Email', 'Rev ✓', 'Rev ✗', 'Test ✓', 'Test ✗', 'Promo ✓', 'Promo ✗'].map(h =>
              <th key={h} className="text-left text-slate-500 px-3 py-2 font-normal whitespace-nowrap">{h}</th>
            )}
          </tr></thead>
          <tbody>
            {stats.map(s => (
              <tr key={s.id} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                <td className="px-3 py-2 text-slate-200 font-medium">{s.username}</td>
                <td className="px-3 py-2 text-slate-400">{s.email || '—'}</td>
                <td className="px-3 py-2 text-green-400 font-mono">{s.successful_review_count}</td>
                <td className="px-3 py-2 text-red-400 font-mono">{s.failed_review_count}</td>
                <td className="px-3 py-2 text-green-400 font-mono">{s.successful_test_count}</td>
                <td className="px-3 py-2 text-red-400 font-mono">{s.failed_test_count}</td>
                <td className="px-3 py-2 text-green-400 font-mono">{s.successful_promotion_count}</td>
                <td className="px-3 py-2 text-red-400 font-mono">{s.failed_promotion_count}</td>
              </tr>
            ))}
            {stats.length === 0 && <tr><td colSpan={8} className="px-4 py-6 text-slate-500 text-center">No activity yet.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}
