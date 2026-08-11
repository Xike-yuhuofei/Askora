import { createContext, useCallback, useContext, useEffect, useState } from 'react'

const WorkspaceContextData = createContext(null)

const SINGLE_WORKSPACE = {
  workspace_id: 'default',
  name: '默认工作区',
  status: 'ready',
}

export function WorkspaceProvider({ children }) {
  const [state, setState] = useState({
    status: 'ready',
    current_workspace_id: SINGLE_WORKSPACE.workspace_id,
    workspaces: [SINGLE_WORKSPACE],
    error: null,
  })

  const value = {
    ...state,
    current_workspace: state.workspaces.find((w) => w.workspace_id === state.current_workspace_id) || null,
    has_multiple_workspaces: state.workspaces.length > 1,
  }

  return <WorkspaceContextData.Provider value={value}>{children}</WorkspaceContextData.Provider>
}

export function useWorkspace() {
  const ctx = useContext(WorkspaceContextData)
  return ctx
}

export function WorkspaceContextDisplay() {
  const workspace = useWorkspace()
  if (!workspace) return null

  const { current_workspace, status, has_multiple_workspaces } = workspace

  if (status === 'loading') {
    return (
      <div className="workspace-context workspace-context--loading" role="status" aria-label="加载工作区中">
        <span className="workspace-context__label">工作区</span>
        <span className="workspace-context__name skeleton">加载中…</span>
      </div>
    )
  }

  if (!current_workspace || status === 'error') {
    return (
      <div className="workspace-context workspace-context--error" role="alert">
        <span className="workspace-context__label">工作区</span>
        <span className="workspace-context__name">不可用</span>
      </div>
    )
  }

  return (
    <div
      className="workspace-context"
      aria-label={
        has_multiple_workspaces
          ? `当前工作区：${current_workspace.name}，点击切换`
          : `当前工作区：${current_workspace.name}（单一工作区）`
      }
    >
      <span className="workspace-context__label">当前工作区</span>
      <span className="workspace-context__name" title={current_workspace.name}>
        {current_workspace.name}
      </span>
      {has_multiple_workspaces && (
        <span className="workspace-context__hint">点击切换</span>
      )}
      {!has_multiple_workspaces && (
        <span className="workspace-context__single" aria-hidden="true">单一工作区</span>
      )}
    </div>
  )
}
