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

  return (
    <div
      className={`app-shell app-shell--${variant}`}
      data-workspace-id={workspaceId || undefined}
    >
      <Sidebar />
      <main className={`app-main app-main--${variant}`} id="main-content">
        <RecoveryIndicator />
        {isWorkspaceVariant ? (
          <div className="app-main--workspace-content" data-workspace-id={workspaceId || undefined}>
            <section
              className="app-main--center"
              aria-label="学习画布"
              data-workspace-id={workspaceId || undefined}
            >
              {children}
            </section>
            <RightRail workspaceId={workspaceId} />
          </div>
        ) : children}
      </main>
    </div>
  )
}
