import { useEffect, useRef, useState } from 'react'
import { normalizeApiError } from '../api/client'
import * as documentApi from '../api/documents'
import * as onboardingApi from '../api/onboarding'
import * as workspaceApi from '../api/workspace'
import Alert from './ui/Alert'
import Button from './ui/Button'
import './MaterialDestination.css'

const processingCopy = {
  pending: '资料已保存，正在等待处理。',
  processing: '资料正在处理，还不能加入空间。',
  completed: '处理完成。选择加入已有空间，或马上开始学习。',
  failed: '处理失败，不能开始有依据的学习。',
  rejected: '资料未通过检查，不能加入空间。',
  quarantined: '资料已隔离，不能加入空间。',
  local_only: '已完成本机解析。模型可用时可「用模型再解析」。',
}

export default function MaterialDestination({ material, onDismiss, onAssigned }) {
  const [spaces, setSpaces] = useState({ status: 'loading', items: [], selectionVersion: null })
  const [selectedId, setSelectedId] = useState('')
  const [newName, setNewName] = useState('')
  const [busy, setBusy] = useState('')
  const [error, setError] = useState('')
  const [modelReady, setModelReady] = useState(true)
  const titleRef = useRef(null)
  const previousFocusRef = useRef(null)

  useEffect(() => {
    previousFocusRef.current = document.activeElement
    titleRef.current?.focus()
    const onKey = (event) => {
      if (event.key === 'Escape') onDismiss?.()
    }
    window.addEventListener('keydown', onKey)
    return () => {
      window.removeEventListener('keydown', onKey)
      previousFocusRef.current?.focus?.()
    }
  }, [onDismiss])

  useEffect(() => {
    let cancelled = false
    workspaceApi.listWorkspaces()
      .then((payload) => {
        if (cancelled) return
        const items = payload?.data?.workspaces || []
        setSpaces({
          status: 'ready',
          items,
          selectionVersion: payload?.data?.selection_version ?? null,
        })
      })
      .catch((err) => {
        if (!cancelled) {
          setSpaces({ status: 'error', items: [], selectionVersion: null })
          setError(normalizeApiError(err).message || '无法读取空间')
        }
      })
    return () => { cancelled = true }
  }, [])

  useEffect(() => {
    let cancelled = false
    onboardingApi.getOnboardingJourney()
      .then((journey) => {
        if (cancelled) return
        const step = journey?.steps?.find((item) => item.step === 'MODEL')
        setModelReady(!step || step.state === 'COMPLETE')
      })
      .catch(() => { /* 读取失败时按就绪处理，避免误阻塞；如模型缺失会进入诚实空态 */ })
    return () => { cancelled = true }
  }, [])

  const ready = material.processing_status === 'completed'
  const blocked = ['failed', 'rejected', 'quarantined'].includes(material.processing_status)

  const assignTo = async (workspaceId, meta) => {
    const result = await documentApi.assignMaterial(material.document_id, {
      workspace_id: workspaceId,
      expected_lifecycle_version: material.lifecycle_version,
      idempotency_key: globalThis.crypto?.randomUUID?.() || `assign-${Date.now()}`,
    })
    onAssigned?.(result.workspace_id, meta)
    return result.workspace_id
  }

  const createSpace = async (displayName, meta) => {
    const created = await workspaceApi.createWorkspace({
      schema_version: '1.0',
      display_name: displayName,
      expected_selection_version: spaces.selectionVersion,
      transition_guard: workspaceApi.clearTransitionGuard(),
      idempotency_key: globalThis.crypto?.randomUUID?.() || `space-${Date.now()}`,
    })
    const workspaceId = created?.workspace?.workspace_id
    if (!workspaceId) throw new Error('空间已提交，但还没有返回身份')
    await assignTo(workspaceId, meta)
    return workspaceId
  }

  const joinExisting = async () => {
    if (!ready || !selectedId || busy) return
    setBusy('join')
    setError('')
    try {
      await assignTo(selectedId)
    } catch (err) {
      setError(normalizeApiError(err).message || '无法加入空间')
      setBusy('')
    }
  }

  const startNow = async () => {
    if (!ready || !modelReady || busy) return
    setBusy('start')
    setError('')
    try {
      const name = newName.trim() || material.title || '新空间'
      await createSpace(name, { startNow: true, documentId: material.document_id })
    } catch (err) {
      setError(normalizeApiError(err).message || '无法马上开始学习')
      setBusy('')
    }
  }

  const joinNew = async () => {
    if (!ready || !newName.trim() || busy) return
    setBusy('create')
    setError('')
    try {
      await createSpace(newName.trim())
    } catch (err) {
      setError(normalizeApiError(err).message || '无法创建并加入空间')
      setBusy('')
    }
  }

  const retrySpaces = () => {
    setError('')
    setSpaces({ status: 'loading', items: [], selectionVersion: null })
    workspaceApi.listWorkspaces()
      .then((payload) => {
        const items = payload?.data?.workspaces || []
        setSpaces({ status: 'ready', items, selectionVersion: payload?.data?.selection_version ?? null })
      })
      .catch((err) => {
        setSpaces({ status: 'error', items: [], selectionVersion: null })
        setError(normalizeApiError(err).message || '无法读取空间')
      })
  }

  return (
    <div className="material-destination" role="dialog" aria-modal="true" aria-labelledby="material-destination-title">
      <div className="material-destination__panel surface">
        <header>
          <p className="eyebrow">资料去向</p>
          <h2 id="material-destination-title" tabIndex={-1} ref={titleRef}>{material.title || '未命名资料'}</h2>
        </header>
        <Alert
          tone={blocked ? 'danger' : ready ? 'info' : 'warning'}
          title={ready ? '选择下一步' : '处理尚未完成'}
          role={blocked ? 'alert' : 'status'}
        >
          {processingCopy[material.processing_status] || '正在读取处理状态。'}
        </Alert>
        {error && <p className="inline-error" role="alert">{error}</p>}

        <section aria-label="加入学习空间">
          <h3>加入学习空间</h3>
          {spaces.status === 'loading' ? (
            <p role="status">正在读取空间…</p>
          ) : spaces.status === 'error' ? (
            <div className="material-destination__space-error">
              <p>无法读取空间</p>
              <Button variant="ghost" onClick={retrySpaces}>重试</Button>
            </div>
          ) : spaces.items.length === 0 ? (
            <p>还没有空间。可以当场新建，或使用马上开始学习。</p>
          ) : (
            <label>
              已有空间
              <select
                value={selectedId}
                onChange={(event) => setSelectedId(event.target.value)}
                disabled={!ready}
              >
                <option value="">请选择空间</option>
                {spaces.items.map((space) => (
                  <option key={space.workspace_id} value={space.workspace_id}>{space.display_name}</option>
                ))}
              </select>
            </label>
          )}
          <label>
            或新建空间名称
            <input value={newName} onChange={(event) => setNewName(event.target.value)} maxLength={120} disabled={!ready} />
          </label>
          <div className="material-destination__actions">
            <Button variant="secondary" disabled={!ready || !selectedId || Boolean(busy)} onClick={joinExisting}>
              {busy === 'join' ? '正在加入…' : '加入所选空间'}
            </Button>
            <Button variant="secondary" disabled={!ready || !newName.trim() || Boolean(busy)} onClick={joinNew}>
              {busy === 'create' ? '正在创建…' : '新建并加入'}
            </Button>
          </div>
        </section>

        <section aria-label="马上开始学习">
          <h3>马上开始学习</h3>
          <p>系统会自动建一个空间并放入这份资料。若还没有可启动的对话，会进入该空间的诚实空态。</p>
          {!modelReady && (
            <p className="material-destination__model-note" role="note">
              还缺可用模型：先建好空间并放入资料；请在设置中配置并验证模型后，才能开始有依据的对话。
            </p>
          )}
          <Button variant="brand" disabled={!ready || !modelReady || Boolean(busy)} onClick={startNow}>
            {busy === 'start' ? '正在开始…' : '马上开始学习'}
          </Button>
        </section>

        <Button variant="ghost" onClick={onDismiss}>稍后决定</Button>
      </div>
    </div>
  )
}