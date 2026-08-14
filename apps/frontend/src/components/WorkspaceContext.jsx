import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { ChevronDown, RefreshCw } from 'lucide-react'
import * as workspaceApi from '../api/workspace'

const WorkspaceContextData = createContext(null)

const INITIAL_STATE = {
  status: 'loading',
  current_workspace: null,
  switch_capability: 'UNAVAILABLE',
  error: null,
}

export function WorkspaceProvider({ children }) {
  const [state, setState] = useState(INITIAL_STATE)
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let cancelled = false
    setState(INITIAL_STATE)
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
  }, [attempt])

  const retry = useCallback(() => setAttempt((value) => value + 1), [])

  return (
    <WorkspaceContextData.Provider value={{ ...state, retry }}>
      {children}
    </WorkspaceContextData.Provider>
  )
}

export function useWorkspace() {
  const ctx = useContext(WorkspaceContextData)
  return ctx
}

/**
 * WC-05 壳层动作降级描述。
 * 返回 { available, reason, guidance }，供壳层（学习/上传/新建等动作）消费。
 * 无空间 → 引导新建；STALE → 提示后仍可操作；不改变既有调用方行为。
 */
export function workspaceActionDegradation(workspace) {
  if (!workspace) return { available: true, reason: null, guidance: null }

  const { status, current_workspace } = workspace

  if (status === 'loading') {
    return { available: false, reason: 'loading', guidance: null }
  }
  if (status === 'error' || status === 'unavailable') {
    return { available: false, reason: 'unavailable', guidance: null }
  }
  if (!current_workspace || status === 'missing' || status === 'empty') {
    return { available: false, reason: 'no_workspace', guidance: '请先新建空间或上传资料。' }
  }
  if (status === 'stale') {
    return { available: true, reason: 'stale', guidance: '空间信息可能已过期，仍可继续操作。' }
  }
  if (status === 'partial') {
    return { available: true, reason: 'partial', guidance: '部分资料信息可用。' }
  }
  return { available: true, reason: null, guidance: null }
}

/** 供壳层消费的降级辅助 hook。 */
export function useWorkspaceActionGuard() {
  const workspace = useWorkspace()
  return workspaceActionDegradation(workspace)
}

export function WorkspaceContextDisplay() {
  const workspace = useWorkspace()
  const [expanded, setExpanded] = useState(true)
  if (!workspace) return null

  const { current_workspace, status } = workspace

  let content = null
  if (status === 'loading') {
    content = (
      <div className="workspace-context workspace-context--loading ds-nav-row" role="status" aria-label="加载空间中" aria-busy="true">
        <span className="workspace-context__name">加载中…</span>
      </div>
    )
  } else if (status === 'error' || status === 'unavailable') {
    content = (
      <div className="workspace-context workspace-context--error ds-nav-row" role="alert">
        <span className="workspace-context__name">暂时不可用</span>
        {typeof workspace.retry === 'function' && (
          <button type="button" className="workspace-context__retry" onClick={workspace.retry}>
            <RefreshCw size={14} aria-hidden="true" />
            <span>重试</span>
          </button>
        )}
      </div>
    )
  } else if (!current_workspace || status === 'missing') {
    content = (
      <div className="workspace-context workspace-context--missing ds-nav-row" role="status">
        <span className="workspace-context__name">尚无可用空间</span>
      </div>
    )
  } else {
    content = (
      <a
        href={`#/courses/${encodeURIComponent(current_workspace.workspace_id)}`}
        className="workspace-context ds-nav-row"
        aria-label={`当前空间：${current_workspace.display_name}`}
        aria-current="page"
        data-workspace-id={current_workspace.workspace_id}
        data-workspace-state={status}
      >
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

  return (
    <div className="workspace-context-group">
      <button
        type="button"
        className="workspace-context-group__toggle"
        aria-expanded={expanded}
        onClick={() => setExpanded((value) => !value)}
      >
        <span>置顶</span>
        <ChevronDown size={12} className={expanded ? 'is-expanded' : ''} aria-hidden="true" />
      </button>
      {expanded ? content : null}
    </div>
  )
}
