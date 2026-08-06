import { useEffect, useRef, useState } from 'react'
import { NavLink, useNavigate } from '../router'
import {
  MessageSquare,
  BookOpen,
  User,
  Shield,
  LogOut,
  GraduationCap,
  Menu,
  X,
} from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import './Sidebar.css'

const navItems = [
  { path: '/', label: '对话学习', icon: MessageSquare },
  { path: '/knowledge', label: '知识点', icon: BookOpen },
  { path: '/profile', label: '学习画像', icon: GraduationCap },
  { path: '/account', label: '账号管理', icon: User },
]

export default function Sidebar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const menuButtonRef = useRef(null)
  const firstLinkRef = useRef(null)

  useEffect(() => {
    if (!open) return undefined

    const focusTimer = window.setTimeout(() => firstLinkRef.current?.focus(), 50)
    const closeOnEscape = (event) => {
      if (event.key === 'Escape') {
        setOpen(false)
        menuButtonRef.current?.focus()
      }
    }
    document.addEventListener('keydown', closeOnEscape)
    return () => {
      window.clearTimeout(focusTimer)
      document.removeEventListener('keydown', closeOnEscape)
    }
  }, [open])

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

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
      <aside id="primary-sidebar" className={`sidebar ${open ? 'open' : ''}`}>
      <div className="sidebar-logo">
        <div className="logo-icon">
          <BookOpen size={24} />
        </div>
        <div className="logo-text">
          <div className="logo-title">Askora</div>
          <div className="logo-sub">AI 学习伙伴</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item, index) => (
          <NavLink
            key={item.path}
            ref={index === 0 ? firstLinkRef : undefined}
            to={item.path}
            className="nav-link"
            onClick={() => setOpen(false)}
          >
            <item.icon size={18} />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        {user && (
          <div className="user-info">
            <div className="user-avatar">
              {user.nickname?.[0] || user.phone?.slice(-4) || 'U'}
            </div>
            <div className="user-detail">
              <div className="user-name">{user.nickname || '用户'}</div>
              <div className="user-role">
                私人用户
              </div>
            </div>
          </div>
        )}
        <button className="logout-btn" onClick={handleLogout}>
          <LogOut size={16} />
          <span>退出登录</span>
        </button>

        <div className="compliance-badge">
          <Shield size={12} />
          <span>私人本地应用</span>
        </div>
      </div>
      </aside>
    </>
  )
}
