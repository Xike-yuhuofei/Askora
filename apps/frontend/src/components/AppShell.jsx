import { useState } from 'react'
import Sidebar from './Sidebar'
import RightRail from './RightRail'
import RecoveryIndicator from './RecoveryIndicator'
import { useWorkspace, WorkspaceProvider } from './WorkspaceContext'
import './AppShell.css'

export default function AppShell({ children, variant = 'standard' }) {
  return (
    <WorkspaceProvider>
      <AppShellContent variant={variant}>{children}</AppShellContent>
    </WorkspaceProvider>
  )
}

function AppShellContent({ children, variant }) {
  const isWorkspaceVariant = variant === 'workspace'
  const workspace = useWorkspace()
  const workspaceId = workspace?.current_workspace?.workspace_id
  const [navCollapsed, setNavCollapsed] = useState(false)
  const [railCollapsed, setRailCollapsed] = useState(false)

  return (
    <div
      className={[
        'app-shell',
        `app-shell--${variant}`,
        isWorkspaceVariant ? 'ds-shell-three-panel' : '',
        navCollapsed ? 'app-shell--nav-collapsed' : '',
        isWorkspaceVariant && railCollapsed ? 'app-shell--rail-collapsed' : '',
      ].filter(Boolean).join(' ')}
      data-workspace-id={workspaceId || undefined}
    >
      <Sidebar
        collapsed={navCollapsed}
        onToggleCollapse={() => setNavCollapsed((value) => !value)}
      />
      <main className={`app-main app-main--${variant}`} id="main-content">
        <RecoveryIndicator />
        {isWorkspaceVariant ? (
          <section
            className="app-main--center ds-shell-three-panel__center"
            aria-label="学习画布"
            data-workspace-id={workspaceId || undefined}
          >
            {children}
          </section>
        ) : children}
      </main>
      {isWorkspaceVariant ? (
        <RightRail
          workspaceId={workspaceId}
          collapsed={railCollapsed}
          onToggleCollapse={() => setRailCollapsed((value) => !value)}
        />
      ) : null}
    </div>
  )
}
