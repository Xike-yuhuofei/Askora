import { useEffect, useRef, useState } from 'react'
import {
  FolderOpen,
  Library,
  Menu,
  MessageSquare,
  Plus,
  X,
} from 'lucide-react'
import { NavLink, useLocation, useNavigate } from '../router'
import { useWorkspace, WorkspaceContextDisplay } from './WorkspaceContext'

import * as workspaceApi from '../api/workspace'
import './WorkspaceContext.css'
import './Sidebar.css'

const MODES = [
  { id: 'learn', label: '资讯' },
  { id: 'library', label: '学习' },
  { id: 'review', label: '笔记' },
]

const PRIMARY_ACTIONS = [
  { id: 'new-chat', label: '新建对话', icon: MessageSquare, href: '/chat', isButton: true },
  { id: 'new-space', label: '空间管理', icon: Plus, href: '/spaces', isButton: true },
  { id: 'library', label: '资料库', icon: Library, href: '/library' },
]

function activityStatusLabel(activity) {
  if (activity.status === 'active' || activity.launch_state === 'RESUMABLE') return '进行中'
  if (activity.status === 'available') return '可开始'
  return null
}

export default function Sidebar({ collapsed: collapsedProp, onToggleCollapse, onPrimaryActionClick }) {
  const [open, setOpen] = useState(false)
  const [internalCollapsed, setInternalCollapsed] = useState(false)
  const [mode, setMode] = useState('learn')
  const [spaces, setSpaces] = useState({ status: 'loading', items: [] })
  const [openFolders, setOpenFolders] = useState({})
  const menuButtonRef = useRef(null)
  const sidebarRef = useRef(null)
  const firstLinkRef = useRef(null)
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const workspace = useWorkspace()
  const collapsed = collapsedProp ?? internalCollapsed

  useEffect(() => {
    let cancelled = false
    setSpaces({ status: 'loading', items: [] })
    workspaceApi.listWorkspaces()
      .then(async (payload) => {
        const items = payload?.data?.workspaces || []
        const enriched = await Promise.all(
          items.map(async (space) => {
            try {
              const response = await workspaceApi.listWorkspaceActivities(space.workspace_id)
              return { ...space, activities: response?.data?.activities || [] }
            } catch {
              return { ...space, activities: [] }
            }
          }),
        )
        if (cancelled) return
        setSpaces({ status: 'ready', items: enriched })
        setOpenFolders(Object.fromEntries(enriched.map((s) => [s.workspace_id, true])))
      })
      .catch(() => {
        if (!cancelled) setSpaces({ status: 'error', items: [] })
      })
    return () => { cancelled = true }
  }, [])

  useEffect(() => {
    if (pathname.startsWith('/library')) setMode('library')
    else if (pathname.startsWith('/learning/history') || pathname.startsWith('/learning/progress')) setMode('review')
    else setMode('learn')
  }, [pathname])

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
        sidebarRef.current?.querySelectorAll('a[href]:not([tabindex="-1"]), button:not([disabled]):not([tabindex="-1"]), [tabindex]:not([tabindex="-1"])') || [],
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

  const toggleFolder = (id) => setOpenFolders((prev) => ({ ...prev, [id]: !prev[id] }))

  const currentWorkspaceId = workspace?.current_workspace?.workspace_id

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
        aria-label="主导航"
      >
        {/* B. Mode switcher */}
        <div className="sidebar-mode-switcher" role="tablist" aria-label="工作模式">
          {MODES.map((m) => (
            <button
              key={m.id}
              type="button"
              role="tab"
              aria-selected={mode === m.id}
              className={`mode-pill ${mode === m.id ? 'is-active' : ''}`}
              onClick={() => {
                setMode(m.id)
                if (m.id === 'library') navigate('/library')
                else if (m.id === 'review') navigate('/learning/history')
                else navigate('/chat')
              }}
            >
              <span>{m.label}</span>
            </button>
          ))}
        </div>

        {/* C. Primary actions */}
        <nav className="sidebar-primary-actions" aria-label="主要功能">
          {PRIMARY_ACTIONS.map((action, index) => {
            const Icon = action.icon
            const isHighlighted = index === 0
            const isButton = action.isButton
            const content = (
              <span className="primary-action__row">
                <Icon size={16} />
                <span className="primary-action__label">{action.label}</span>
              </span>
            )
            if (isButton) {
              return (
                <button
                  key={action.id}
                  type="button"
                  className={`primary-action ${isHighlighted ? 'is-highlighted' : ''}`}
                  onClick={() => {
                    setOpen(false)
                    onPrimaryActionClick?.()
                    navigate(action.href)
                  }}
                >
                  {content}
                </button>
              )
            }
            return (
              <NavLink
                key={action.id}
                ref={action.id === 'library' ? firstLinkRef : undefined}
                to={action.href}
                className={`primary-action ${isHighlighted ? 'is-highlighted' : ''}`}
                onClick={() => {
                  setOpen(false)
                  onPrimaryActionClick?.()
                }}
              >
                {content}
              </NavLink>
            )
          })}
        </nav>

        {/* D. Scroll region */}
        <div className="sidebar-scroll">
          {/* Pinned current workspace */}
          <div className="sidebar-section">
            <WorkspaceContextDisplay />
          </div>

          {/* Workspace / activity tree */}
          <div className="sidebar-section">
            <SectionHeader
              label="空间列表"
              actions={
                <>
                  <button type="button" className="section-action" aria-label="新建空间">
                    <Plus size={14} />
                  </button>
                </>
              }
            />
            {spaces.status === 'loading' && <p className="sidebar-empty">正在读取空间…</p>}
            {spaces.status === 'error' && <p className="sidebar-empty">空间列表暂时不可用。</p>}
            <div className="folder-tree">
              {spaces.items.map((space) => {
                const isOpen = openFolders[space.workspace_id] ?? true
                return (
                  <div key={space.workspace_id} className="folder-group">
                    <button
                      type="button"
                      className="folder-row"
                      onClick={() => toggleFolder(space.workspace_id)}
                    >
                      <FolderOpen size={15} />
                      <span className="folder-row__name">{space.display_name}</span>
                    </button>
                    {isOpen && (
                      <div className="folder-tasks">
                        {space.activities
                          .filter((a) => ['active', 'available'].includes(a.status) || a.launch_state === 'RESUMABLE')
                          .map((activity) => {
                            const href = workspaceApi.conversationHref(space.workspace_id, activity.activity_ref)
                            return (
                              <NavLink
                                key={activity.activity_ref}
                                to={href || `/courses/${encodeURIComponent(space.workspace_id)}`}
                                className="folder-task"
                                onClick={() => setOpen(false)}
                              >
                                <span className="folder-task__title">{activity.display_title}</span>
                                {activityStatusLabel(activity) && (
                                  <span className="folder-task__meta">{activityStatusLabel(activity)}</span>
                                )}
                              </NavLink>
                            )
                          })}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        </div>

        {/* F. Account footer */}
        <NavLink
          to="/settings"
          className="sidebar-account"
          aria-label="账户设置"
          onClick={() => setOpen(false)}
        >
          <span className="account-avatar">稀</span>
          <div className="account-info">
            <span className="account-name">学习者</span>
          </div>
        </NavLink>
      </aside>
    </>
  )
}

function SectionHeader({ label, actions }) {
  return (
    <div className="sidebar-section-header">
      <span className="sidebar-section-header__label">{label}</span>
      {actions && <div className="sidebar-section-header__actions">{actions}</div>}
    </div>
  )
}
