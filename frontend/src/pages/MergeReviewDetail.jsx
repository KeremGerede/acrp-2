import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import client from '../api/client'
import Loading from '../components/Loading'
import ErrorMessage from '../components/ErrorMessage'
import Badge from '../components/Badge'

const SEV_COLOR = { critical: 'border-red-700', high: 'border-orange-700', warning: 'border-yellow-700', info: 'border-blue-700' }

const FA_STATUS = {
  passed:               { label: 'Geçti',            cls: 'bg-green-900/40 text-green-300 border border-green-700' },
  passed_with_warnings: { label: 'Uyarı ile Geçti',  cls: 'bg-yellow-900/40 text-yellow-300 border border-yellow-700' },
  failed:               { label: 'Başarısız',         cls: 'bg-red-900/40 text-red-300 border border-red-700' },
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export default function MergeReviewDetail() {
  const { id } = useParams()
  const [review, setReview] = useState(null)
  const [findings, setFindings] = useState([])
  const [steps, setSteps] = useState([])
  const [notifications, setNotifications] = useState([])
  const [reportData, setReportData] = useState({ passed_checks: [], file_assessments: [] })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([
      client.get(`/api/merge-reviews/${id}`),
      client.get(`/api/merge-reviews/${id}/findings`),
      client.get(`/api/merge-reviews/${id}/steps`),
      client.get(`/api/notifications/merge-reviews/${id}`),
      client.get(`/api/merge-reviews/${id}/report-data`).catch(() => ({ data: {} })),
    ]).then(([r, f, s, n, rd]) => {
      setReview(r.data)
      setFindings(f.data)
      setSteps(s.data)
      setNotifications(n.data)
      setReportData(rd.data || {})
    }).catch(e => setError(e.message)).finally(() => setLoading(false))
  }, [id])

  if (loading) return <Loading />
  if (!review) return <ErrorMessage message={error || 'Not found'} />

  const fileAssessments = reportData.file_assessments || []
  const passedChecks = reportData.passed_checks || []
  const pdfUrl = `${API_BASE}/api/merge-reviews/${id}/pdf`

  return (
    <div>
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <Link to="/merge-reviews" className="text-slate-500 hover:text-slate-300 text-sm">← Reviews</Link>
        <h1 className="text-xl font-bold text-slate-100">Review #{review.id}</h1>
        <Badge value={review.result || review.status} />
        <Badge value={review.risk_level} />
        <div className="ml-auto">
          <a
            href={pdfUrl}
            download
            className="flex items-center gap-2 px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-slate-200 text-sm rounded-lg border border-slate-600 transition-colors"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            PDF İndir
          </a>
        </div>
      </div>
      <ErrorMessage message={error} />

      {/* Metadata */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        {[
          ['Task', review.task_key], ['Sprint', review.sprint_name],
          ['Actor', review.actor_username], ['Status', review.status],
          ['Files Analyzed', review.total_files_analyzed], ['Total Findings', review.total_findings],
          ['Blocking', review.blocking_findings_count], ['Completed', review.completed_at ? new Date(review.completed_at).toLocaleString() : '—'],
        ].map(([label, val]) => (
          <div key={label} className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2">
            <div className="text-xs text-slate-500">{label}</div>
            <div className="text-sm text-slate-200 font-mono mt-0.5">{val || '—'}</div>
          </div>
        ))}
      </div>

      {/* Branches */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 mb-6 text-sm">
        <p className="text-slate-400"><span className="text-slate-500">Source:</span> <code className="font-mono text-cyan-300">{review.source_branch || '—'}</code></p>
        <p className="text-slate-400 mt-1"><span className="text-slate-500">Target:</span> <code className="font-mono text-cyan-300">{review.target_branch || '—'}</code></p>
        <p className="text-slate-400 mt-1"><span className="text-slate-500">Commit:</span> <code className="font-mono text-xs text-slate-300">{review.commit_sha || '—'}</code></p>
      </div>

      {/* Summary */}
      {review.report_summary && (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 mb-6">
          <h2 className="text-sm font-semibold text-slate-300 mb-2">Summary</h2>
          <p className="text-slate-400 text-sm">{review.report_summary}</p>
          {review.decision_reason && <p className="text-slate-500 text-xs mt-2 italic">{review.decision_reason}</p>}
        </div>
      )}

      {/* Dosya Bazlı İnceleme Sonucu */}
      {fileAssessments.length > 0 && (
        <div className="mb-6">
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">
            Dosya Bazlı İnceleme Sonucu
          </h2>
          <div className="flex flex-col gap-3">
            {fileAssessments.map((fa, i) => {
              const st = FA_STATUS[fa.status] || FA_STATUS.passed
              return (
                <div key={i} className="bg-slate-800 border border-slate-700 rounded-lg p-4">
                  <div className="flex items-center gap-3 mb-2">
                    <code className="text-cyan-300 text-xs font-mono">{fa.file_path}</code>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${st.cls}`}>{st.label}</span>
                  </div>
                  {fa.passed_points?.length > 0 && (
                    <div className="mt-2">
                      <p className="text-xs text-green-400 font-semibold mb-1">Geçen noktalar</p>
                      <ul className="list-disc list-inside space-y-0.5">
                        {fa.passed_points.map((pt, j) => (
                          <li key={j} className="text-slate-400 text-xs">{pt}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {fa.remaining_points?.length > 0 && (
                    <div className="mt-2">
                      <p className="text-xs text-yellow-400 font-semibold mb-1">Kalan noktalar</p>
                      <ul className="list-disc list-inside space-y-0.5">
                        {fa.remaining_points.map((pt, j) => (
                          <li key={j} className="text-slate-400 text-xs">{pt}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Başarıyla Geçen Kontroller */}
      {passedChecks.length > 0 && (
        <div className="mb-6">
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">
            Başarıyla Geçen Kontroller ({passedChecks.length})
          </h2>
          <div className="flex flex-col gap-2">
            {passedChecks.map((pc, i) => (
              <div key={i} className="bg-slate-800 border border-green-800/60 rounded-lg p-3">
                <div className="flex items-start gap-2">
                  <span className="text-green-400 mt-0.5 shrink-0">✓</span>
                  <div>
                    <p className="text-slate-200 text-sm font-medium">{pc.check_title}</p>
                    <code className="text-slate-500 text-xs font-mono">{pc.file_path}</code>
                    {pc.evidence && (
                      <p className="text-slate-400 text-xs mt-1">
                        <span className="text-slate-500">Kanıt:</span> {pc.evidence}
                      </p>
                    )}
                    {pc.reason && <p className="text-slate-500 text-xs mt-0.5">{pc.reason}</p>}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Findings */}
      {findings.length > 0 && (
        <div className="mb-6">
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Findings ({findings.length})</h2>
          <div className="flex flex-col gap-3">
            {findings.map(f => (
              <div key={f.id} className={`bg-slate-800 border rounded-lg p-4 ${SEV_COLOR[f.severity] || 'border-slate-700'}`}>
                <div className="flex items-center gap-2 mb-1">
                  <Badge value={f.severity} />
                  <Badge value={f.category} />
                  <span className="text-slate-300 text-sm font-medium">{f.rule_title}</span>
                </div>
                <p className="text-slate-400 text-xs font-mono mb-2">{f.file_path}{f.line_number ? `:${f.line_number}` : ''}</p>
                <p className="text-slate-300 text-sm font-medium">{f.issue}</p>
                <p className="text-slate-400 text-sm mt-1">{f.explanation}</p>
                <p className="text-cyan-400 text-sm mt-1 italic">{f.suggestion}</p>
                {f.code_snippet && <pre className="bg-slate-900 rounded text-xs text-slate-300 p-2 mt-2 overflow-x-auto">{f.code_snippet}</pre>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Agent Steps */}
      {steps.length > 0 && (
        <div className="mb-6">
          <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">Agent Steps</h2>
          <div className="bg-slate-800 border border-slate-700 rounded-lg overflow-hidden">
            <table className="w-full text-xs">
              <thead><tr className="border-b border-slate-700">
                {['Agent', 'Tool', 'Step', 'Status', 'Output'].map(h => <th key={h} className="text-left text-slate-500 px-3 py-2 font-normal">{h}</th>)}
              </tr></thead>
              <tbody>
                {steps.map(s => (
                  <tr key={s.id} className="border-b border-slate-700/50">
                    <td className="px-3 py-2 text-slate-400">{s.agent_name}</td>
                    <td className="px-3 py-2 text-slate-400 font-mono">{s.tool_name}</td>
                    <td className="px-3 py-2 text-slate-300">{s.step_name}</td>
                    <td className="px-3 py-2"><Badge value={s.status} /></td>
                    <td className="px-3 py-2 text-slate-500 truncate max-w-[200px]">{s.output_summary || s.error_message || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Notifications */}
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
