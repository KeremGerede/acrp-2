import { useEffect, useState } from 'react'
import client from '../api/client'
import Loading from '../components/Loading'
import ErrorMessage from '../components/ErrorMessage'
import Badge from '../components/Badge'

const empty = {
  tenant_id: '', provider: 'github', name: '', repository_owner: '', repository_name: '',
  repository_full_name: '', repository_url: '', default_branch: 'main',
  sprint_branch_pattern: 'sprint/*', task_branch_pattern: 'task/*',
  development_branch: 'development', test_branch: 'test',
  manager_email: '', notification_recipients: '', is_active: true,
}

export default function Integrations() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [form, setForm] = useState(empty)
  const [editing, setEditing] = useState(null)
  const [saving, setSaving] = useState(false)
  const [webhookInfo, setWebhookInfo] = useState(null)

  const load = () => client.get('/api/integrations').then(r => setItems(r.data)).catch(e => setError(e.message)).finally(() => setLoading(false))
  useEffect(() => { load() }, [])

  const f = (field) => (e) => setForm({ ...form, [field]: e.target.value })

  const submit = async (e) => {
    e.preventDefault(); setSaving(true); setError('')
    const payload = {
      ...form,
      tenant_id: parseInt(form.tenant_id),
      notification_recipients: form.notification_recipients ? form.notification_recipients.split(',').map(s => s.trim()).filter(Boolean) : [],
    }
    try {
      if (editing) { await client.patch(`/api/integrations/${editing}`, payload) }
      else { await client.post('/api/integrations', payload) }
      setForm(empty); setEditing(null); load()
    } catch (err) { setError(err.message) } finally { setSaving(false) }
  }

  const startEdit = (item) => {
    setForm({ ...item, notification_recipients: (item.notification_recipients || []).join(', ') })
    setEditing(item.id)
  }

  const deleteItem = async (id) => {
    if (!confirm('Delete this integration?')) return
    await client.delete(`/api/integrations/${id}`).catch(e => setError(e.message))
    load()
  }

  const showWebhook = async (id) => {
    const r = await client.get(`/api/integrations/${id}/webhook-info`)
    setWebhookInfo(r.data)
  }

  if (loading) return <Loading />

  return (
    <div>
      <h1 className="text-xl font-bold text-slate-100 mb-6">Integrations</h1>
      <ErrorMessage message={error} />

      <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 mb-6">
        <h2 className="text-sm font-semibold text-slate-300 mb-3">{editing ? 'Edit Integration' : 'New Integration'}</h2>
        <form onSubmit={submit} className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <input className="inp" placeholder="Tenant ID *" value={form.tenant_id} onChange={f('tenant_id')} required />
          <select className="inp" value={form.provider} onChange={f('provider')}>
            <option value="github">GitHub</option>
            <option value="gitlab">GitLab (stub)</option>
            <option value="azure_devops">Azure DevOps (stub)</option>
          </select>
          <input className="inp" placeholder="Name *" value={form.name} onChange={f('name')} required />
          <input className="inp" placeholder="Repo Owner" value={form.repository_owner} onChange={f('repository_owner')} />
          <input className="inp" placeholder="Repo Name" value={form.repository_name} onChange={f('repository_name')} />
          <input className="inp" placeholder="Repo Full Name (owner/name)" value={form.repository_full_name} onChange={f('repository_full_name')} />
          <input className="inp" placeholder="Sprint Branch Pattern (sprint/*)" value={form.sprint_branch_pattern} onChange={f('sprint_branch_pattern')} />
          <input className="inp" placeholder="Task Branch Pattern (task/*)" value={form.task_branch_pattern} onChange={f('task_branch_pattern')} />
          <input className="inp" placeholder="Development Branch" value={form.development_branch} onChange={f('development_branch')} />
          <input className="inp" placeholder="Test Branch" value={form.test_branch} onChange={f('test_branch')} />
          <input className="inp" placeholder="Manager Email" type="email" value={form.manager_email} onChange={f('manager_email')} />
          <input className="inp" placeholder="Notification Recipients (comma-separated)" value={form.notification_recipients} onChange={f('notification_recipients')} />
          <div className="md:col-span-2 flex gap-2">
            <button className="btn-p" disabled={saving}>{saving ? 'Saving...' : editing ? 'Update' : 'Create'}</button>
            {editing && <button type="button" className="btn-s" onClick={() => { setForm(empty); setEditing(null) }}>Cancel</button>}
          </div>
        </form>
      </div>

      {webhookInfo && (
        <div className="bg-slate-800 border border-cyan-700 rounded-lg p-4 mb-6">
          <div className="flex justify-between items-start">
            <h3 className="text-sm font-semibold text-cyan-400 mb-2">Webhook Setup</h3>
            <button className="text-slate-500 hover:text-slate-300 text-xs" onClick={() => setWebhookInfo(null)}>Close</button>
          </div>
          <p className="text-xs text-slate-400 mb-1"><strong className="text-slate-300">Secret:</strong> <code className="font-mono text-cyan-300">{webhookInfo.webhook_secret}</code></p>
          <ul className="text-xs text-slate-400 list-disc list-inside space-y-1">
            {webhookInfo.instructions?.map((line, i) => <li key={i}>{line}</li>)}
          </ul>
        </div>
      )}

      <div className="bg-slate-800 border border-slate-700 rounded-lg overflow-x-auto">
        <table className="w-full text-sm">
          <thead><tr className="border-b border-slate-700">
            {['ID', 'Name', 'Provider', 'Repo', 'Status', 'Actions'].map(h => (
              <th key={h} className="text-left text-slate-500 px-4 py-2 font-normal">{h}</th>
            ))}
          </tr></thead>
          <tbody>
            {items.map(item => (
              <tr key={item.id} className="border-b border-slate-700/50">
                <td className="px-4 py-2 text-slate-500">{item.id}</td>
                <td className="px-4 py-2 text-slate-200">{item.name}</td>
                <td className="px-4 py-2"><Badge value={item.provider} /></td>
                <td className="px-4 py-2 text-slate-400 font-mono text-xs">{item.repository_full_name || '—'}</td>
                <td className="px-4 py-2"><Badge value={item.is_active ? 'success' : 'skipped'} label={item.is_active ? 'Active' : 'Inactive'} /></td>
                <td className="px-4 py-2 flex gap-3">
                  <button className="text-cyan-400 hover:text-cyan-300 text-xs" onClick={() => startEdit(item)}>Edit</button>
                  <button className="text-slate-400 hover:text-slate-200 text-xs" onClick={() => showWebhook(item.id)}>Webhook</button>
                  <button className="text-red-400 hover:text-red-300 text-xs" onClick={() => deleteItem(item.id)}>Delete</button>
                </td>
              </tr>
            ))}
            {items.length === 0 && <tr><td colSpan={6} className="px-4 py-6 text-slate-500 text-center">No integrations yet.</td></tr>}
          </tbody>
        </table>
      </div>

      <style>{`.inp{background:#1e293b;border:1px solid #334155;border-radius:6px;padding:8px 12px;color:#e2e8f0;font-size:14px;outline:none;width:100%}.inp:focus{border-color:#22d3ee}.btn-p{background:#0e7490;color:#fff;border:none;border-radius:6px;padding:8px 16px;font-size:14px;cursor:pointer}.btn-p:hover{background:#0891b2}.btn-s{background:#334155;color:#e2e8f0;border:none;border-radius:6px;padding:8px 16px;font-size:14px;cursor:pointer}`}</style>
    </div>
  )
}
