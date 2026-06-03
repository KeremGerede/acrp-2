import { NavLink, Outlet } from 'react-router-dom'

const nav = [
  { to: '/', label: 'Dashboard' },
  { to: '/tenants', label: 'Tenants' },
  { to: '/integrations', label: 'Integrations' },
  { to: '/review-rules', label: 'Review Rules' },
  { to: '/test-configs', label: 'Test Configs' },
  { to: '/events', label: 'Event Logs' },
  { to: '/merge-reviews', label: 'Merge Reviews' },
  { to: '/functional-tests', label: 'Functional Tests' },
  { to: '/promotions', label: 'Promotions' },
  { to: '/stats', label: 'User Stats' },
]

export default function Layout() {
  return (
    <div className="flex h-screen overflow-hidden bg-slate-900">
      <aside className="w-56 flex-shrink-0 bg-slate-800 border-r border-slate-700 flex flex-col">
        <div className="px-4 py-5 border-b border-slate-700">
          <span className="text-sm font-bold text-cyan-400 uppercase tracking-widest">AgentDevOps</span>
        </div>
        <nav className="flex-1 overflow-y-auto py-3">
          {nav.map(({ to, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `block px-4 py-2 text-sm transition-colors ${
                  isActive
                    ? 'bg-slate-700 text-cyan-400 font-semibold'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-700/50'
                }`
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="flex-1 overflow-y-auto p-6">
        <Outlet />
      </main>
    </div>
  )
}
