import { useEffect, useState } from 'react'
import client from '../api/client'
import Loading from '../components/Loading'
import ErrorMessage from '../components/ErrorMessage'
import Badge from '../components/Badge'

const empty = {
  tenant_id: '',
  provider: 'github',
  name: '',
  repository_full_name: '',   // owner/repo — tek alan, backend auto-split yapar
  sprint_branch_pattern: 'sprint/*',
  task_branch_pattern: 'task/*',
  development_branch: 'development',
  test_branch: 'test',
  manager_email: '',
  notification_recipients: '',
  is_active: true,
}

function Field({ label, children }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs text-slate-400">{label}</label>
      {children}
    </div>
  )
}

export default function Integrations() {
  const [items, setItems]       = useState([])
  const [loading, setLoading]   = useState(true)
  const [error, setError]       = useState('')
  const [form, setForm]         = useState(empty)
  const [editing, setEditing]   = useState(null)
  const [saving, setSaving]     = useState(false)
  const [webhookInfo, setWebhookInfo] = useState(null)
  const [showForm, setShowForm] = useState(false)

  const load = () =>
    client.get('/api/integrations')
      .then(r => setItems(r.data))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))

  useEffect(() => { load() }, [])

  const f = field => e => setForm({ ...form, [field]: e.target.value })

  const submit = async e => {
    e.preventDefault(); setSaving(true); setError('')
    const payload = {
      ...form,
      tenant_id: parseInt(form.tenant_id),
      notification_recipients: form.notification_recipients
        ? form.notification_recipients.split(',').map(s => s.trim()).filter(Boolean)
        : [],
    }
    try {
      if (editing) await client.patch(`/api/integrations/${editing}`, payload)
      else         await client.post('/api/integrations', payload)
      setForm(empty); setEditing(null); setShowForm(false); load()
    } catch (err) { setError(err.message) }
    finally { setSaving(false) }
  }

  const startEdit = item => {
    setForm({
      ...empty,
      ...item,
      notification_recipients: (item.notification_recipients || []).join(', '),
    })
    setEditing(item.id)
    setShowForm(true)
    setWebhookInfo(null)
  }

  const cancelForm = () => { setForm(empty); setEditing(null); setShowForm(false) }

  const deleteItem = async id => {
    if (!confirm('Bu integration silinsin mi?')) return
    await client.delete(`/api/integrations/${id}`).catch(e => setError(e.message))
    load()
  }

  const showWebhook = async id => {
    try {
      const r = await client.get(`/api/integrations/${id}/webhook-info`)
      setWebhookInfo(r.data)
    } catch (err) { setError(err.message) }
  }

  if (loading) return <Loading />

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-slate-100">Integrations</h1>
        {!showForm && (
          <button className="btn-p" onClick={() => setShowForm(true)}>+ New Integration</button>
        )}
      </div>

      <ErrorMessage message={error} />

      {/* ── Form ── */}
      {showForm && (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-5 mb-6">
          <h2 className="text-sm font-semibold text-slate-300 mb-4">
            {editing ? 'Edit Integration' : 'New Integration'}
          </h2>

          <form onSubmit={submit} className="space-y-5">

            {/* Row 1 — identity */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <Field label="Tenant ID *">
                <input className="inp" placeholder="1" value={form.tenant_id} onChange={f('tenant_id')} required />
              </Field>
              <Field label="Provider">
                <select className="inp" value={form.provider} onChange={f('provider')}>
                  <option value="github">GitHub</option>
                  <option value="gitlab">GitLab (stub)</option>
                  <option value="azure_devops">Azure DevOps (stub)</option>
                </select>
              </Field>
              <Field label="Name *">
                <input className="inp" placeholder="My Project" value={form.name} onChange={f('name')} required />
              </Field>
            </div>

            {/* Row 2 — repo */}
            <Field label="Repository Full Name (owner/repo) *">
              <input
                className="inp"
                placeholder="KeremGerede/acrp-2"
                value={form.repository_full_name}
                onChange={f('repository_full_name')}
                required
              />
              <p className="text-xs text-slate-500 mt-1">
                Owner ve repo URL otomatik türetilir.
              </p>
            </Field>

            {/* Row 3 — branch patterns */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <Field label="Sprint Branch Pattern">
                <input className="inp" placeholder="sprint/*" value={form.sprint_branch_pattern} onChange={f('sprint_branch_pattern')} />
              </Field>
              <Field label="Task Branch Pattern">
                <input className="inp" placeholder="task/*" value={form.task_branch_pattern} onChange={f('task_branch_pattern')} />
              </Field>
              <Field label="Dev Branch">
                <input className="inp" placeholder="development" value={form.development_branch} onChange={f('development_branch')} />
              </Field>
              <Field label="Test Branch">
                <input className="inp" placeholder="test" value={form.test_branch} onChange={f('test_branch')} />
              </Field>
            </div>

            {/* Row 4 — hints */}
            <div className="bg-slate-900/60 border border-slate-700 rounded p-3 text-xs text-slate-400 space-y-1">
              <p className="font-medium text-slate-300">Branch pattern örnekleri</p>
              <p><code className="text-cyan-300">sprint/*</code> → sprint/sprint-1, sprint/sprint-2</p>
              <p><code className="text-cyan-300">sprint*/*</code> → sprint1/task-6, sprint2/task-9</p>
              <p><code className="text-cyan-300">task/*</code> → task/sprint-1/TASK-42-feature</p>
              <p className="text-slate-500 pt-1">
                Pattern eşleşmese bile sistem, merge eventlerini otomatik detect eder.
              </p>
            </div>

            {/* Row 5 — notifications */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <Field label="Manager Email">
                <input className="inp" type="email" placeholder="manager@company.com" value={form.manager_email} onChange={f('manager_email')} />
              </Field>
              <Field label="Notification Recipients (virgülle ayır)">
                <input className="inp" placeholder="dev1@co.com, dev2@co.com" value={form.notification_recipients} onChange={f('notification_recipients')} />
              </Field>
            </div>

            <div className="flex gap-2 pt-1">
              <button className="btn-p" disabled={saving}>{saving ? 'Kaydediliyor...' : editing ? 'Güncelle' : 'Oluştur'}</button>
              <button type="button" className="btn-s" onClick={cancelForm}>İptal</button>
            </div>
          </form>
        </div>
      )}

      {/* ── Webhook info panel ── */}
      {webhookInfo && (
        <div className="bg-slate-800 border border-cyan-800 rounded-lg p-4 mb-6">
          <div className="flex justify-between items-start mb-3">
            <h3 className="text-sm font-semibold text-cyan-400">Webhook Kurulum</h3>
            <button className="text-slate-500 hover:text-slate-300 text-xs" onClick={() => setWebhookInfo(null)}>Kapat</button>
          </div>
          <div className="mb-3 p-2 bg-slate-900 rounded font-mono text-xs text-cyan-300 break-all">
            {`https://YOUR-NGROK.ngrok.io/api/webhooks/${webhookInfo.provider}/${webhookInfo.integration_id}`}
          </div>
          <p className="text-xs text-slate-400 mb-2">
            <span className="text-slate-300 font-medium">Secret:</span>{' '}
            <code className="font-mono text-yellow-300">{webhookInfo.webhook_secret}</code>
          </p>
          <ol className="text-xs text-slate-400 list-decimal list-inside space-y-1">
            {webhookInfo.instructions?.map((line, i) => <li key={i}>{line}</li>)}
          </ol>
        </div>
      )}

      {/* ── Table ── */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700">
              {['ID', 'Name', 'Provider', 'Repository', 'Sprint Pattern', 'Task Pattern', 'Status', 'Actions'].map(h => (
                <th key={h} className="text-left text-slate-500 px-4 py-2 font-normal whitespace-nowrap">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {items.map(item => (
              <tr key={item.id} className="border-b border-slate-700/50 hover:bg-slate-700/20">
                <td className="px-4 py-2 text-slate-500">{item.id}</td>
                <td className="px-4 py-2 text-slate-200 font-medium">{item.name}</td>
                <td className="px-4 py-2"><Badge value={item.provider} /></td>
                <td className="px-4 py-2 font-mono text-xs text-slate-400">{item.repository_full_name || '—'}</td>
                <td className="px-4 py-2 font-mono text-xs text-slate-500">{item.sprint_branch_pattern || '—'}</td>
                <td className="px-4 py-2 font-mono text-xs text-slate-500">{item.task_branch_pattern || '—'}</td>
                <td className="px-4 py-2">
                  <Badge
                    value={item.is_active ? 'success' : 'skipped'}
                    label={item.is_active ? 'Active' : 'Inactive'}
                  />
                </td>
                <td className="px-4 py-2">
                  <div className="flex gap-3">
                    <button className="text-cyan-400 hover:text-cyan-300 text-xs" onClick={() => startEdit(item)}>Düzenle</button>
                    <button className="text-slate-400 hover:text-slate-200 text-xs" onClick={() => showWebhook(item.id)}>Webhook</button>
                    <button className="text-red-400 hover:text-red-300 text-xs" onClick={() => deleteItem(item.id)}>Sil</button>
                  </div>
                </td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr><td colSpan={8} className="px-4 py-8 text-slate-500 text-center">Henüz integration yok.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      <style>{`
        .inp {
          background: #1e293b;
          border: 1px solid #334155;
          border-radius: 6px;
          padding: 7px 11px;
          color: #e2e8f0;
          font-size: 13px;
          outline: none;
          width: 100%;
        }
        .inp:focus { border-color: #22d3ee; }
        .btn-p {
          background: #0e7490; color: #fff;
          border: none; border-radius: 6px;
          padding: 8px 18px; font-size: 13px; cursor: pointer;
        }
        .btn-p:hover { background: #0891b2; }
        .btn-s {
          background: #334155; color: #e2e8f0;
          border: none; border-radius: 6px;
          padding: 8px 18px; font-size: 13px; cursor: pointer;
        }
      `}</style>
    </div>
  )
}
