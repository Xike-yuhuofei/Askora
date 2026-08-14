import { useState } from 'react'
import { Plus } from 'lucide-react'
import Sidebar from './Sidebar'
import RightRail from './RightRail'
import { useWorkspace, WorkspaceProvider } from './WorkspaceContext'
import { useNavigate } from '../router'
import './AppShell.css'

export default function AppShell({ children, variant = 'standard', hideRightRail = false }) {
  return (
    <WorkspaceProvider>
      <AppShellContent variant={variant} hideRightRail={hideRightRail}>{children}</AppShellContent>
    </WorkspaceProvider>
  )
}

function AppShellContent({ children, variant, hideRightRail }) {
  const isWorkspaceVariant = variant === 'workspace'
  const showRightRail = isWorkspaceVariant && !hideRightRail
  const workspace = useWorkspace()
  const workspaceId = workspace?.current_workspace?.workspace_id
  const [navCollapsed, setNavCollapsed] = useState(false)
  const [railCollapsed, setRailCollapsed] = useState(false)
  const navigate = useNavigate()

  return (
    <div
      className={[
        'app-shell',
        `app-shell--${variant}`,
        isWorkspaceVariant ? 'ds-shell-three-panel' : '',
        navCollapsed ? 'app-shell--nav-collapsed' : '',
        showRightRail && railCollapsed ? 'app-shell--rail-collapsed' : '',
        hideRightRail ? 'app-shell--hide-rail' : '',
      ].filter(Boolean).join(' ')}
      data-workspace-id={workspaceId || undefined}
    >
      {/* TraeWork-style window title bar: traffic dots + panel controls stay
          visible even while a side panel is fully hidden. */}
      <div className="app-titlebar">
        <div className="traffic-dots" aria-label="窗口控制">
          <span className="traffic-dot traffic-dot--close" />
          <span className="traffic-dot traffic-dot--minimize" />
          <span className="traffic-dot traffic-dot--maximize" />
        </div>
        <button
          type="button"
          className="titlebar-button"
          aria-label={navCollapsed ? '展开左侧栏' : '收起左侧栏'}
          aria-expanded={!navCollapsed}
          onClick={() => setNavCollapsed((value) => !value)}
        >
          <PanelGlyph side="left" />
        </button>
        {navCollapsed && (
          <button
            type="button"
            className="titlebar-button"
            aria-label="新建对话"
            onClick={() => navigate('/chat')}
          >
            <Plus size={14} />
          </button>
        )}
        <div className="app-titlebar__spacer" />
        {showRightRail && railCollapsed && (
          <button
            type="button"
            className="titlebar-button"
            aria-label="展开右侧栏"
            aria-expanded={false}
            onClick={() => setRailCollapsed(false)}
          >
            <PanelGlyph side="right" />
          </button>
        )}
      </div>
      <Sidebar
        collapsed={navCollapsed}
        onToggleCollapse={() => setNavCollapsed((value) => !value)}
        onPrimaryActionClick={showRightRail ? () => setRailCollapsed(true) : undefined}
      />
      {isWorkspaceVariant ? (
        <>
          <main className={`app-main app-main--${variant}`} id="main-content">
            <section
              className="app-main--center ds-shell-three-panel__center"
              aria-label="学习画布"
              data-workspace-id={workspaceId || undefined}
            >
              {children}
            </section>
          </main>
          <RightRail
            workspaceId={workspaceId}
            collapsed={railCollapsed}
            onToggleCollapse={() => setRailCollapsed((value) => !value)}
          />
        </>
      ) : (
        <main className={`app-main app-main--${variant}`} id="main-content">
          <div className="app-content-card">{children}</div>
        </main>
      )}
    </div>
  )
}

function PanelGlyph({ side }) {
  // Panel-with-divider glyph matching the sidebars' collapse icons.
  // Left side panel keeps the divider on the right; right side panel mirrors it.
  const dividerX = side === 'right' ? '6.7' : '9.3'
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="13"
      height="13"
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.3"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <rect x="2" y="3" width="12" height="10" rx="2.5" />
      <line x1={dividerX} y1="3.6" x2={dividerX} y2="12.4" />
    </svg>
  )
}
