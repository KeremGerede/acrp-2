import { useEffect, useState } from 'react'
import client from '../api/client'
import Loading from '../components/Loading'
import ErrorMessage from '../components/ErrorMessage'
import Badge from '../components/Badge'

export default function Promotions() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    client.get('/api/promotions?limit=100')
      .then(r => setItems(r.data))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Loading />

  return (
    <div>
      <h1 className="text-xl font-bold text-slate-100 mb-6">Environment Promotions</h1>
      <ErrorMessage message={error} />
      <div className="bg-slate-800 border border-slate-700 rounded-lg overflow-auto">
        <table className="w-full text-sm">
          <thead><tr className="border-b border-slate-700">
            {['ID', 'From', 'To', 'Status', 'Review #', 'Test #', 'Message', 'Time'].map(h =>
              <th key={h} className="text-left text-slate-500 px-3 py-2 font-normal whitespace-nowrap">{h}</th>
            )}
          </tr></thead>
          <tbody>
            {items.map(p => (
              <tr key={p.id} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                <td className="px-3 py-2 text-slate-500">{p.id}</td>
                <td className="px-3 py-2 font-mono text-xs text-slate-400">{p.from_stage || '—'}</td>
                <td className="px-3 py-2 font-mono text-xs text-slate-300">{p.to_stage || '—'}</td>
                <td className="px-3 py-2"><Badge value={p.status === 'ready_for_test_environment' ? 'success' : p.status} label={p.status} /></td>
                <td className="px-3 py-2 text-slate-400">{p.merge_review_run_id || '—'}</td>
                <td className="px-3 py-2 text-slate-400">{p.functional_test_run_id || '—'}</td>
                <td className="px-3 py-2 text-slate-400 text-xs max-w-[200px] truncate">{p.message || '—'}</td>
                <td className="px-3 py-2 text-slate-500 text-xs whitespace-nowrap">{new Date(p.created_at).toLocaleString()}</td>
              </tr>
            ))}
            {items.length === 0 && <tr><td colSpan={8} className="px-4 py-6 text-slate-500 text-center">No promotions yet.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}
