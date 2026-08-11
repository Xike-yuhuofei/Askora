import { createContext, useContext, useState, useCallback } from 'react'
import Sidebar from './Sidebar'
import RightRail from './RightRail'
import RecoveryIndicator from './RecoveryIndicator'
import { WorkspaceProvider } from './WorkspaceContext'
import './AppShell.css'

const WorkspaceScopedContext = createContext(null)

export function useWorkspaceScoped() {
  const ctx = useContext(WorkspaceScopedContext)
  if (!ctx) return null
  return ctx
}

function WorkspaceScopedProvider({ children }) {
  const [userNote, setUserNote] = useState('')
  const [currentMaterial, setCurrentMaterial] = useState(null)

  const value = {
    userNote,
    onUserNoteChange: setUserNote,
    currentMaterial,
    onSetCurrentMaterial: setCurrentMaterial,
    onClearCurrentMaterial: useCallback(() => setCurrentMaterial(null), []),
  }

  return (
    <WorkspaceScopedContext.Provider value={value}>
      {children}
    </WorkspaceScopedContext.Provider>
  )
}

export default function AppShell({ children, variant = 'standard' }) {
  const isWorkspaceVariant = variant === 'workspace'

  return (
    <WorkspaceProvider>
      <div className={`app-shell app-shell--${variant}`}>
        <Sidebar />
        <main className={`app-main app-main--${variant}`} id="main-content">
          <RecoveryIndicator />
          {isWorkspaceVariant ? (
            <WorkspaceScopedProvider>
              <div className="app-main--workspace-content">
                <section className="app-main--center" aria-label="学习画布">
                  {children}
                </section>
                <WorkspaceScopedRightRail />
              </div>
            </WorkspaceScopedProvider>
          ) : (
            children
          )}
        </main>
      </div>
    </WorkspaceProvider>
  )
}

function WorkspaceScopedRightRail() {
  const { userNote, onUserNoteChange, currentMaterial, onClearCurrentMaterial } = useWorkspaceScoped()
  return (
    <RightRail
      userNote={userNote}
      onUserNoteChange={onUserNoteChange}
      currentMaterial={currentMaterial}
      onClearCurrentMaterial={onClearCurrentMaterial}
    />
  )
}
