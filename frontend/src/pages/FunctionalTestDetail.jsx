import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import client from '../api/client'
import Loading from '../components/Loading'
import ErrorMessage from '../components/ErrorMessage'
import Badge from '../components/Badge'

export default function FunctionalTestDetail() {
  const { id } = useParams()
  const [run, setRun] = useState(null)
  const [notifications, setNotifications] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      client.get(`/api/functional-tests/${id}`),
      client.get(`/api/notifications/functional-tests/${id}`),
    ]).then(([r, n]) => { setRun(r.data); setNotifications(n.data) })
      .catch(e => setError(e.message)).finally(() => setLoading(false))
  }, [id])

  if (loading) return <Loading />
  if (!run) return <ErrorMessage message={error || 'Not found'} />

  return (
    <div>
      <div className="flex items-center gap-3 mb-6">
        <Link to="/functional-tests" className="text-slate-500 hover:text-slate-300 text-sm">← Tests</Link>
        <h1 className="text-xl font-bold text-slate-100">Test Run #{run.id}</h1>
        <Badge value={run.result || run.status} />
      </div>
      <ErrorMessage message={error} />

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        {[
          ['Task', run.task_key], ['Sprint', run.sprint_name],
          ['Status', run.status], ['Result', run.result],
          ['Total Tests', run.total_tests], ['Passed', run.passed_tests],
          ['Failed', run.failed_tests], ['Completed', run.completed_at ? new Date(run.completed_at).toLocaleString() : '—'],
        ].map(([label, val]) => (
          <div key={label} className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2">
            <div className="text-xs text-slate-500">{label}</div>
            <div className={`text-sm font-mono mt-0.5 ${label === 'Passed' ? 'text-green-400' : label === 'Failed' ? 'text-red-400' : 'text-slate-200'}`}>{val ?? '—'}</div>
          </div>
        ))}
      </div>

      {run.report_summary && (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 mb-6">
          <h2 className="text-sm font-semibold text-slate-300 mb-2">Summary</h2>
          <p className="text-slate-400 text-sm">{run.report_summary}</p>
        </div>
      )}

      {run.raw_output && (
        <div className="mb-6">
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Raw Output</h2>
          <pre className="bg-slate-900 border border-slate-700 rounded-lg p-4 text-xs text-slate-300 overflow-x-auto whitespace-pre-wrap max-h-96">{run.raw_output}</pre>
        </div>
      )}

      {notifications.length > 0 && (
        <div className="mb-6">
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Notifications</h2>
          <div className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
            <table className="w-full text-xs">
              <thead><tr className="border-b border-slate-700">
                {['Type', 'Subject', 'Status', 'Sent At'].map(h => <th key={h} className="text-left text-slate-500 px-3 py-2 font-normal">{h}</th>)}
              </tr></thead>
              <tbody>
                {notifications.map(n => (
                  <tr key={n.id} className="border-b border-slate-700/50">
                    <td className="px-3 py-2 text-slate-400">{n.notification_type}</td>
                    <td className="px-3 py-2 text-slate-300 max-w-[300px] truncate">{n.subject}</td>
                    <td className="px-3 py-2"><Badge value={n.status} /></td>
                    <td className="px-3 py-2 text-slate-500">{n.sent_at ? new Date(n.sent_at).toLocaleString() : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
