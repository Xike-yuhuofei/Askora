import { useEffect, useRef, useState } from 'react'
import { NavLink } from '../router'
import {
  CalendarDays,
  GraduationCap,
  FolderOpen,
  Settings,
  Shield,
  Menu,
  X,
  BookOpen,
} from 'lucide-react'
import { WorkspaceContextDisplay } from './WorkspaceContext'
import './WorkspaceContext.css'
import './Sidebar.css'

const productNavItems = [
  { path: '/today', label: '今天', icon: CalendarDays, match: 'exact' },
  { path: '/learning', label: '学习', icon: GraduationCap, match: 'prefix' },
  { path: '/library', label: '资料库', icon: FolderOpen, match: 'prefix' },
]

const utilityNavItems = [
  { path: '/settings', label: '设置', icon: Settings },
  { path: '/settings/recovery', label: '恢复中心', icon: Shield },
]

export default function Sidebar() {
  const [open, setOpen] = useState(false)
  const menuButtonRef = useRef(null)
  const sidebarRef = useRef(null)
  const firstLinkRef = useRef(null)

  useEffect(() => {
    if (!open) return undefined

    const focusTimer = window.setTimeout(() => firstLinkRef.current?.focus(), 50)
    const handleDrawerKeys = (event) => {
      if (event.key === 'Escape') {
        setOpen(false)
        menuButtonRef.current?.focus()
        return
      }
      if (event.key !== 'Tab') return

      const drawerFocusables = Array.from(
        sidebarRef.current?.querySelectorAll('a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])') || [],
      )
      const focusables = [menuButtonRef.current, ...drawerFocusables].filter(Boolean)
      if (!focusables.length) return

      const first = focusables[0]
      const last = focusables[focusables.length - 1]
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    }
    document.addEventListener('keydown', handleDrawerKeys)
    return () => {
      window.clearTimeout(focusTimer)
      document.removeEventListener('keydown', handleDrawerKeys)
    }
  }, [open])

  return (
    <>
      <button
        type="button"
        ref={menuButtonRef}
        className="mobile-menu-button"
        aria-label={open ? '关闭导航菜单' : '打开导航菜单'}
        aria-expanded={open}
        aria-controls="primary-sidebar"
        onClick={() => setOpen((value) => !value)}
      >
        {open ? <X size={22} /> : <Menu size={22} />}
      </button>
      {open && (
        <button
          type="button"
          className="sidebar-overlay"
          aria-label="点击遮罩关闭导航菜单"
          onClick={() => setOpen(false)}
        />
      )}
      <aside
        id="primary-sidebar"
        ref={sidebarRef}
        className={`sidebar ${open ? 'open' : ''}`}
        role={open ? 'dialog' : undefined}
        aria-modal={open ? 'true' : undefined}
        aria-label={open ? '主导航' : undefined}
      >
        <div className="sidebar-logo">
          <div className="logo-icon">
            <BookOpen size={24} />
          </div>
          <div className="logo-text">
            <div className="logo-title">Askora</div>
            <div className="logo-sub">AI 学习伙伴</div>
          </div>
        </div>

        <WorkspaceContextDisplay />

        <nav className="sidebar-nav" aria-label="产品域导航">
          <div className="sidebar-nav-section">
            {productNavItems.map((item, index) => (
              <NavLink
                key={item.path}
                ref={index === 0 ? firstLinkRef : undefined}
                to={item.path}
                match={item.match}
                className="nav-link nav-link--product"
                onClick={() => setOpen(false)}
              >
                <item.icon size={18} />
                <span>{item.label}</span>
              </NavLink>
            ))}
          </div>

          <div className="sidebar-nav-divider" role="presentation" />

          <div className="sidebar-nav-section sidebar-nav-section--utility">
            {utilityNavItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className="nav-link nav-link--utility"
                onClick={() => setOpen(false)}
              >
                <item.icon size={16} />
                <span>{item.label}</span>
              </NavLink>
            ))}
          </div>
        </nav>

        <div className="sidebar-footer">
          <div className="compliance-badge">
            <Shield size={12} />
            <span>私人本地应用</span>
          </div>
        </div>
      </aside>
    </>
  )
}
