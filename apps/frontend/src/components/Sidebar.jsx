import { useEffect, useRef, useState } from 'react'
import { FolderOpen, Settings, Menu, X, BookOpen, PanelLeftClose, PanelLeftOpen } from 'lucide-react'
import { NavLink, useNavigate } from '../router'
import { WorkspaceContextDisplay } from './WorkspaceContext'
import Button from './ui/Button'
import DsIcon from './ui/DsIcon'
import './WorkspaceContext.css'
import './Sidebar.css'

const utilityNavItems = [
  { path: '/settings', label: '设置', icon: Settings },
]

export default function Sidebar({ collapsed: collapsedProp, onToggleCollapse }) {
  const [open, setOpen] = useState(false)
  const [internalCollapsed, setInternalCollapsed] = useState(false)
  const menuButtonRef = useRef(null)
  const sidebarRef = useRef(null)
  const firstLinkRef = useRef(null)
  const navigate = useNavigate()
  const collapsed = collapsedProp ?? internalCollapsed
  const toggleCollapse = onToggleCollapse ?? (() => setInternalCollapsed((value) => !value))

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
        className={`sidebar ${open ? 'open' : ''} ${collapsed ? 'sidebar--collapsed' : ''}`}
        role={open ? 'dialog' : undefined}
        aria-modal={open ? 'true' : undefined}
        aria-label={open ? '主导航' : '主导航'}
      >
        <div className="sidebar-logo">
          <div className="logo-icon">
            <BookOpen size={24} />
          </div>
          <div className="logo-text">
            <div className="logo-title">Askora</div>
            <div className="logo-sub">个人学习系统</div>
          </div>
          <button
            type="button"
            className="sidebar-collapse"
            aria-label={collapsed ? '展开左侧栏' : '收起左侧栏'}
            aria-expanded={!collapsed}
            aria-controls="primary-sidebar"
            onClick={toggleCollapse}
          >
            {collapsed ? <PanelLeftOpen size={16} /> : <PanelLeftClose size={16} />}
          </button>
        </div>

        <div className="sidebar-primary-action">
          <Button
            variant="brand"
            className="ds-btn--block"
            aria-label="新课程"
            onClick={() => {
              setOpen(false)
              navigate('/courses/new')
            }}
          >
            <DsIcon name="plus" />
            <span className="sidebar-action-label">新课程</span>
          </Button>
        </div>

        <nav className="sidebar-nav" aria-label="产品域导航">
          <div className="sidebar-nav-section">
            <p className="sidebar-nav-label">课程</p>
            <WorkspaceContextDisplay />
            <NavLink
              ref={firstLinkRef}
              to="/library"
              match="prefix"
              className="ds-nav-row"
              onClick={() => setOpen(false)}
            >
              <FolderOpen size={16} />
              <span>资料库</span>
            </NavLink>
          </div>
        </nav>

        <nav className="sidebar-footer" aria-label="工具">
          {utilityNavItems.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className="ds-nav-row ds-nav-row--utility"
              onClick={() => setOpen(false)}
            >
              <item.icon size={16} />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>
      </aside>
    </>
  )
}
