import { NavLink, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard, AlertTriangle, Package,
  ArrowLeftRight, DoorOpen, Tag,
  LogOut, User, ShieldCheck, Upload,
  UserCircle, Users, ScrollText
} from 'lucide-react'
import { useAuthStore } from '../../store/auth'
import { Logo } from '../ui/Logo'

const NAV_ITEMS = [
  // Seccion principal
  { to: '/dashboard',   icon: LayoutDashboard, label: 'Dashboard',   roles: ['admin', 'operador', 'visor'] },
  { to: '/alertas',     icon: AlertTriangle,   label: 'Alertas',     roles: ['admin', 'operador', 'visor'] },
  { to: '/insumos',     icon: Package,         label: 'Insumos',     roles: ['admin', 'operador', 'visor'] },
  { to: '/movimientos', icon: ArrowLeftRight,  label: 'Movimientos', roles: ['admin', 'operador', 'visor'] },
  // Seccion gestion
  { to: '/salas',       icon: DoorOpen,        label: 'Salas',       roles: ['admin', 'operador', 'visor'], divider: true },
  { to: '/categorias',  icon: Tag,             label: 'Categorias',  roles: ['admin', 'operador', 'visor'] },
  // Seccion operaciones
  { to: '/importar',    icon: Upload,          label: 'Importar',    roles: ['admin'], divider: true },
  // Seccion administracion (solo admin)
  { to: '/usuarios',    icon: Users,           label: 'Usuarios',    roles: ['admin'], divider: true },
  { to: '/audit-log',   icon: ScrollText,      label: 'Audit Log',   roles: ['admin'] },
]

export function Sidebar() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  function handleLogout() { logout(); navigate('/login') }

  const navLinkCls = ({ isActive }: { isActive: boolean }) => `
    flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-semibold
    transition-colors duration-150
    ${isActive
      ? 'bg-teal-600 text-white'
      : 'text-slate-400 hover:bg-slate-800 hover:text-white'
    }
  `

  const itemsVisibles = NAV_ITEMS.filter(
    item => user?.rol && item.roles.includes(user.rol)
  )

  return (
    <aside className="w-60 min-h-screen bg-slate-900 flex flex-col border-r border-slate-800 flex-shrink-0">
      {/* Logo */}
      <div className="px-5 pt-7 pb-6 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <Logo className="w-9 h-9" light />
          <div>
            <p className="text-white font-bold text-base leading-tight">Hestia</p>
            <p className="text-slate-400 text-xs">Escuela de Salud</p>
          </div>
        </div>
      </div>

      {/* Navegacion */}
      <nav className="flex-1 px-3 py-5 space-y-1">
        {itemsVisibles.map(({ to, icon: Icon, label, divider }) => (
          <div key={to}>
            {divider && <div className="border-t border-slate-800 my-2" />}
            <NavLink to={to} className={navLinkCls}>
              <Icon size={17} />
              {label}
            </NavLink>
          </div>
        ))}
      </nav>

      {/* Pie: perfil, seguridad, usuario, logout */}
      <div className="px-3 pb-5 border-t border-slate-800 pt-4 space-y-1">
        <NavLink to="/perfil" className={navLinkCls}>
          <UserCircle size={17} />
          Mi perfil
        </NavLink>
        <NavLink to="/seguridad" className={navLinkCls}>
          <ShieldCheck size={17} />
          Seguridad
        </NavLink>
        <div className="flex items-center gap-3 px-3 py-2.5 mt-1">
          <div className="w-7 h-7 rounded-full bg-slate-700 flex items-center justify-center">
            <User size={14} className="text-slate-300" />
          </div>
          <div className="min-w-0">
            <p className="text-white text-xs font-semibold truncate">{user?.nombre ?? 'Usuario'}</p>
            <p className="text-slate-400 text-xs capitalize">{user?.rol}</p>
          </div>
        </div>
        <button onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-slate-400
                     hover:bg-slate-800 hover:text-rose-400 text-sm font-semibold
                     transition-colors duration-150">
          <LogOut size={17} /> Cerrar sesion
        </button>
      </div>
    </aside>
  )
}
