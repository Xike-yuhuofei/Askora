import { createContext, useContext, useEffect, useState } from 'react'
import * as workspaceApi from '../api/workspace'

const WorkspaceContextData = createContext(null)

export function WorkspaceProvider({ children }) {
  const [state, setState] = useState({
    status: 'loading',
    current_workspace: null,
    switch_capability: 'UNAVAILABLE',
    error: null,
  })

  useEffect(() => {
    let cancelled = false
    workspaceApi.getWorkspaceContext()
      .then((payload) => {
        if (cancelled) return
        const viewState = payload?.data?.view_state
        setState({
          status: viewState?.toLowerCase() || 'missing',
          current_workspace: payload?.data?.current_workspace || null,
          switch_capability: payload?.data?.switch_capability || 'UNAVAILABLE',
          source_status: payload?.source_status || [],
          error: null,
        })
      })
      .catch(() => {
        if (!cancelled) {
          setState({
            status: 'error',
            current_workspace: null,
            switch_capability: 'UNAVAILABLE',
            source_status: [],
            error: '当前工作区暂时无法读取。',
          })
        }
      })
    return () => { cancelled = true }
  }, [])

  return <WorkspaceContextData.Provider value={state}>{children}</WorkspaceContextData.Provider>
}

export function useWorkspace() {
  const ctx = useContext(WorkspaceContextData)
  return ctx
}

export function WorkspaceContextDisplay() {
  const workspace = useWorkspace()
  if (!workspace) return null

  const { current_workspace, status } = workspace

  if (status === 'loading') {
    return (
      <div className="workspace-context workspace-context--loading ds-nav-row" role="status" aria-label="加载课程中">
        <span className="workspace-context__label">课程</span>
        <span className="workspace-context__name skeleton">加载中…</span>
      </div>
    )
  }

  if (status === 'error') {
    return (
      <div className="workspace-context workspace-context--error ds-nav-row" role="alert">
        <span className="workspace-context__label">课程</span>
        <span className="workspace-context__name">暂时不可用</span>
      </div>
    )
  }

  if (!current_workspace || status === 'missing') {
    return (
      <div className="workspace-context workspace-context--missing ds-nav-row" role="status">
        <span className="workspace-context__label">当前课程</span>
        <span className="workspace-context__name">尚无可用课程</span>
      </div>
    )
  }

  return (
    <a
      href={`#/courses/${encodeURIComponent(current_workspace.workspace_id)}`}
      className="workspace-context ds-nav-row"
      aria-label={`当前课程：${current_workspace.display_name}`}
      data-workspace-id={current_workspace.workspace_id}
      data-workspace-state={status}
    >
      <span className="workspace-context__label">当前课程</span>
      <span className="workspace-context__name" title={current_workspace.display_name}>
        {current_workspace.display_name}
      </span>
      {status !== 'ready' && (
        <span className="workspace-context__meta" role="status">
          {status === 'partial' ? '部分信息可用' : '信息可能已过期'}
        </span>
      )}
    </a>
  )
}
