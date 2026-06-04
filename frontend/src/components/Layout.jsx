import { NavLink, Outlet } from 'react-router-dom'
import {
  LayoutDashboard,
  Link2,
  ShieldCheck,
  SlidersHorizontal,
  Terminal,
  GitMerge,
  Activity,
  UploadCloud,
  Users,
} from 'lucide-react'

const nav = [
  { to: '/',                label: 'Dashboard',                  icon: LayoutDashboard },
  { to: '/integrations',    label: 'Entegrasyonlar',             icon: Link2 },
  { to: '/review-rules',    label: 'İnceleme Kuralları',         icon: ShieldCheck },
  { to: '/test-configs',    label: 'Test Yapılandırmaları',      icon: SlidersHorizontal },
  { to: '/events',          label: 'Olay Günlükleri',            icon: Terminal },
  { to: '/merge-reviews',   label: 'Birleştirme İncelemeleri',   icon: GitMerge },
  { to: '/functional-tests',label: 'Fonksiyonel Testler',        icon: Activity },
  { to: '/promotions',      label: 'Dağıtımlar (Promotions)',    icon: UploadCloud },
  { to: '/stats',           label: 'Kullanıcı İstatistikleri',   icon: Users },
]

export default function Layout() {
  return (
    <div className="flex h-screen overflow-hidden bg-slate-900">
      <aside className="w-64 flex-shrink-0 bg-slate-800 border-r border-slate-700 flex flex-col">

        {/* Logo */}
        <div className="px-5 py-5 border-b border-slate-700">
          <span className="text-sm font-bold text-cyan-400 uppercase tracking-widest">
            AgentDevOps
          </span>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-0.5">
          {nav.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `group flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-all duration-150 relative ${
                  isActive
                    ? 'bg-slate-700/80 text-cyan-400 border-l-2 border-cyan-400 pl-[10px]'
                    : 'text-slate-400 hover:text-slate-100 hover:bg-slate-700/40 border-l-2 border-transparent pl-[10px]'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <Icon
                    size={17}
                    className={`flex-shrink-0 transition-colors ${
                      isActive ? 'text-cyan-400' : 'text-slate-500 group-hover:text-slate-300'
                    }`}
                  />
                  <span className="truncate">{label}</span>
                </>
              )}
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
