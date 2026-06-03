import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import client from '../api/client'
import Loading from '../components/Loading'
import ErrorMessage from '../components/ErrorMessage'
import Badge from '../components/Badge'

export default function FunctionalTests() {
  const [runs, setRuns] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    client.get('/api/functional-tests?limit=100')
      .then(r => setRuns(r.data))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Loading />

  return (
    <div>
      <h1 className="text-xl font-bold text-slate-100 mb-6">Functional Tests</h1>
      <ErrorMessage message={error} />
      <div className="bg-slate-800 border border-slate-700 rounded-lg overflow-auto">
        <table className="w-full text-sm">
          <thead><tr className="border-b border-slate-700">
            {['ID', 'Result', 'Status', 'Task', 'Sprint', 'Total', 'Passed', 'Failed', 'Time'].map(h =>
              <th key={h} className="text-left text-slate-500 px-3 py-2 font-normal whitespace-nowrap">{h}</th>
            )}
          </tr></thead>
          <tbody>
            {runs.map(r => (
              <tr key={r.id} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                <td className="px-3 py-2"><Link to={`/functional-tests/${r.id}`} className="text-cyan-400 hover:underline">#{r.id}</Link></td>
                <td className="px-3 py-2"><Badge value={r.result || '—'} /></td>
                <td className="px-3 py-2"><Badge value={r.status} /></td>
                <td className="px-3 py-2 font-mono text-xs text-slate-300">{r.task_key || '—'}</td>
                <td className="px-3 py-2 text-slate-400">{r.sprint_name || '—'}</td>
                <td className="px-3 py-2 text-slate-400">{r.total_tests}</td>
                <td className="px-3 py-2 text-green-400">{r.passed_tests}</td>
                <td className="px-3 py-2 text-red-400">{r.failed_tests}</td>
                <td className="px-3 py-2 text-slate-500 text-xs whitespace-nowrap">{new Date(r.created_at).toLocaleString()}</td>
              </tr>
            ))}
            {runs.length === 0 && <tr><td colSpan={9} className="px-4 py-6 text-slate-500 text-center">No test runs yet.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}
