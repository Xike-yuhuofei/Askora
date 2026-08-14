import { useCallback, useEffect, useRef, useState } from 'react'
import {
  Plus,
  FolderOpen,
  Pencil,
  ArrowRight,
  Loader2,
  X,
} from 'lucide-react'

import * as workspaceApi from '../api/workspace'
import { normalizeApiError } from '../api/client'
import { useNavigate } from '../router'
import Button from '../components/ui/Button'
import Alert from '../components/ui/Alert'
import './WorkspaceManage.css'

function formatLastActive(value) {
  if (!value) return '暂无活动'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '暂无活动'
  const now = new Date()
  const diffMs = now - date
  const diffSec = Math.floor(diffMs / 1000)
  if (diffSec < 60) return '刚刚'
  const diffMin = Math.floor(diffSec / 60)
  if (diffMin < 60) return `${diffMin} 分钟前`
  const diffHour = Math.floor(diffMin / 60)
  if (diffHour < 24) return `${diffHour} 小时前`
  const diffDay = Math.floor(diffHour / 24)
  if (diffDay < 30) return `${diffDay} 天前`
  return date.toLocaleDateString('zh-CN')
}

export default function WorkspaceManage() {
  const navigate = useNavigate()
  const [workspaces, setWorkspaces] = useState({ status: 'loading', items: [], error: null })
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newName, setNewName] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [createError, setCreateError] = useState('')
  const [renamingId, setRenamingId] = useState(null)
  const [renameValue, setRenameValue] = useState('')
  const [renameError, setRenameError] = useState('')
  const [savingRename, setSavingRename] = useState(false)
  const renameInputRef = useRef(null)
  const createInputRef = useRef(null)

  const load = useCallback(async () => {
    setWorkspaces((prev) => ({ ...prev, status: 'loading', error: null }))
    try {
      const data = await workspaceApi.listWorkspaces()
      setWorkspaces({
        status: 'ready',
        items: data?.data?.workspaces || [],
        error: null,
      })
    } catch (err) {
      const info = normalizeApiError(err)
      setWorkspaces({ status: 'error', items: [], error: info })
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  useEffect(() => {
    if (renamingId && renameInputRef.current) {
      renameInputRef.current.focus()
      renameInputRef.current.select()
    }
  }, [renamingId])

  useEffect(() => {
    if (showCreateForm && createInputRef.current) {
      createInputRef.current.focus()
    }
  }, [showCreateForm])

  const openCreateModal = () => {
    setNewName('')
    setCreateError('')
    setShowCreateForm(true)
  }

  const closeCreateModal = () => {
    if (submitting) return
    setShowCreateForm(false)
    setNewName('')
    setCreateError('')
  }

  const handleCreateSubmit = async (event) => {
    event.preventDefault()
    const name = newName.trim()
    if (!name) {
      setCreateError('空间名称不能为空')
      return
    }
    setSubmitting(true)
    setCreateError('')
    try {
      await workspaceApi.createWorkspace({ display_name: name })
      setShowCreateForm(false)
      setNewName('')
      await load()
    } catch (err) {
      const info = normalizeApiError(err)
      setCreateError(info.message || '创建空间失败')
    } finally {
      setSubmitting(false)
    }
  }

  const startRename = (ws) => {
    setRenamingId(ws.workspace_id)
    setRenameValue(ws.display_name || '')
    setRenameError('')
  }

  const cancelRename = () => {
    setRenamingId(null)
    setRenameValue('')
    setRenameError('')
    setSavingRename(false)
  }

  const handleRenameSubmit = async () => {
    const name = renameValue.trim()
    if (!name) {
      setRenameError('名称不能为空')
      return
    }
    if (savingRename) return
    setSavingRename(true)
    setRenameError('')
    try {
      await workspaceApi.renameWorkspace(renamingId, { display_name: name })
      cancelRename()
      await load()
    } catch (err) {
      const info = normalizeApiError(err)
      setRenameError(info.message || '重命名失败')
    } finally {
      setSavingRename(false)
    }
  }

  const handleRenameKeyDown = (event) => {
    if (event.key === 'Enter') {
      event.preventDefault()
      handleRenameSubmit()
    } else if (event.key === 'Escape') {
      event.preventDefault()
      cancelRename()
    }
  }

  const handleCreateKeyDown = (event) => {
    if (event.key === 'Escape') {
      event.preventDefault()
      closeCreateModal()
    }
  }

  const handleEnter = (workspaceId) => {
    navigate(`/courses/${encodeURIComponent(workspaceId)}`)
  }

  return (
    <section className="surface page-stack" aria-labelledby="workspace-manage-title">
      <header className="page-header">
        <h1 id="workspace-manage-title">空间管理</h1>
      </header>

      <div className="workspace-manage__toolbar">
        <Button variant="brand" onClick={openCreateModal}>
          <Plus size={16} /> 新建空间
        </Button>
      </div>

      {showCreateForm && (
        <div className="workspace-create-form surface" role="dialog" aria-label="新建空间">
          <form onSubmit={handleCreateSubmit}>
            <div className="workspace-create-form__row">
              <input
                ref={createInputRef}
                type="text"
                className="workspace-create-form__input"
                placeholder="输入空间名称…"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                onKeyDown={handleCreateKeyDown}
                disabled={submitting}
                aria-label="空间名称"
              />
            </div>
            {createError && (
              <p className="workspace-create-form__error" role="alert">{createError}</p>
            )}
            <div className="workspace-create-form__actions">
              <Button
                type="submit"
                variant="brand"
                disabled={submitting}
              >
                {submitting ? <Loader2 size={16} /> : null}
                {submitting ? '创建中…' : '创建'}
              </Button>
              <Button
                type="button"
                variant="secondary"
                onClick={closeCreateModal}
                disabled={submitting}
              >
                取消
              </Button>
            </div>
          </form>
        </div>
      )}

      {workspaces.status === 'loading' && (
        <div className="inline-state" role="status">
          <Loader2 size={16} className="spinner" />
          <span>正在加载空间列表…</span>
        </div>
      )}

      {workspaces.status === 'error' && (
        <section className="workspace-error" role="alert">
          <Alert tone="error" title="加载失败">
            {workspaces.error?.message || '无法读取空间列表'}
          </Alert>
          <Button variant="secondary" onClick={load}>重新加载</Button>
        </section>
      )}

      {workspaces.status === 'ready' && workspaces.items.length === 0 && (
        <div className="workspace-empty">
          <FolderOpen size={40} className="workspace-empty__icon" />
          <h2 className="workspace-empty__title">还没有空间</h2>
          <p className="workspace-empty__desc">
            点击上方 "新建空间" 按钮，创建你的第一个学习空间。
          </p>
          <Button variant="brand" onClick={openCreateModal}>
            <Plus size={16} /> 新建空间
          </Button>
        </div>
      )}

      {workspaces.status === 'ready' && workspaces.items.length > 0 && (
        <ul className="workspace-list">
          {workspaces.items.map((ws) => (
            <li key={ws.workspace_id} className="workspace-item">
              <div className="workspace-item__main">
                <div className="workspace-item__name-wrapper">
                  {renamingId === ws.workspace_id ? (
                    <div className="workspace-rename">
                      <input
                        ref={renameInputRef}
                        type="text"
                        className="workspace-rename__input"
                        value={renameValue}
                        onChange={(e) => setRenameValue(e.target.value)}
                        onKeyDown={handleRenameKeyDown}
                        onBlur={handleRenameSubmit}
                        disabled={savingRename}
                        aria-label="重命名空间"
                      />
                      {savingRename && (
                        <Loader2 size={14} className="workspace-rename__spinner" />
                      )}
                    </div>
                  ) : (
                    <span className="workspace-item__name" title={ws.display_name}>
                      {ws.display_name}
                    </span>
                  )}
                  {renamingId === ws.workspace_id && renameError && (
                    <span className="workspace-rename__error" role="alert">{renameError}</span>
                  )}
                </div>
                <div className="workspace-item__meta">
                  <span className="workspace-item__count">
                    {ws.activity_count || 0} 项活动
                  </span>
                  <span className="workspace-item__dot" aria-hidden="true">·</span>
                  <span className="workspace-item__last-active">
                    {formatLastActive(ws.last_active_at)}
                  </span>
                </div>
              </div>
              <div className="workspace-item__actions">
                {renamingId === ws.workspace_id ? (
                  <button
                    type="button"
                    className="workspace-action-btn workspace-action-btn--cancel"
                    onClick={cancelRename}
                    disabled={savingRename}
                    aria-label="取消重命名"
                  >
                    <X size={16} />
                  </button>
                ) : (
                  <button
                    type="button"
                    className="workspace-action-btn"
                    onClick={() => startRename(ws)}
                    aria-label={`重命名 ${ws.display_name}`}
                    title="重命名"
                  >
                    <Pencil size={16} />
                  </button>
                )}
                <button
                  type="button"
                  className="workspace-action-btn workspace-action-btn--enter"
                  onClick={() => handleEnter(ws.workspace_id)}
                  aria-label={`进入 ${ws.display_name}`}
                  title="进入空间"
                >
                  进入
                  <ArrowRight size={16} />
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}