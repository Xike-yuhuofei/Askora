import { useEffect, useState } from 'react'
import { normalizeApiError } from '../api/client'
import * as workspaceApi from '../api/workspace'
import Alert from '../components/ui/Alert'
import Button from '../components/ui/Button'
import { useNavigate } from '../router'

const emptyForm = { name: '', error: '', submitting: false }

export default function CourseCreate() {
  const navigate = useNavigate()
  const [form, setForm] = useState(emptyForm)
  const [selectionVersion, setSelectionVersion] = useState(null)
  const [listError, setListError] = useState('')

  useEffect(() => {
    let cancelled = false
    workspaceApi.listWorkspaces()
      .then((payload) => {
        if (!cancelled) setSelectionVersion(payload?.data?.selection_version ?? null)
      })
      .catch((err) => {
        if (!cancelled) setListError(normalizeApiError(err).message || '无法读取当前空间列表')
      })
    return () => { cancelled = true }
  }, [])

  const submit = async (event) => {
    event.preventDefault()
    const displayName = form.name.trim()
    if (!displayName || form.submitting) return
    setForm((current) => ({ ...current, submitting: true, error: '' }))
    try {
      const result = await workspaceApi.createWorkspace({
        schema_version: '1.0',
        display_name: displayName,
        expected_selection_version: selectionVersion,
        transition_guard: workspaceApi.clearTransitionGuard(),
        idempotency_key: globalThis.crypto?.randomUUID?.() || `space-${Date.now()}`,
      })
      const workspaceId = result?.workspace?.workspace_id
      if (!workspaceId) {
        setForm((current) => ({
          ...current,
          submitting: false,
          error: '创建已提交，但还没有返回空间。不会显示占位空间。',
        }))
        return
      }
      navigate(`/courses/${encodeURIComponent(workspaceId)}`)
    } catch (err) {
      setForm((current) => ({
        ...current,
        submitting: false,
        error: normalizeApiError(err).message || '无法创建空间',
      }))
    }
  }

  return (
    <section className="surface page-stack" aria-labelledby="space-create-title">
      <header className="page-header">
        <p className="eyebrow">空间</p>
        <h1 id="space-create-title">新建空间</h1>
      </header>
      <Alert tone="info" title="打开此页不会创建空间">
        只有提交正式的 Workspace create command 才会产生真实空间。成功后进入空空间，不会自动开对话。
      </Alert>
      {listError && <p className="inline-error" role="alert">{listError}</p>}
      <form className="page-stack" onSubmit={submit}>
        <label htmlFor="space-name">空间名称</label>
        <input
          id="space-name"
          name="display_name"
          placeholder="例如：我的学习空间"
          value={form.name}
          onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
          maxLength={120}
          required
          autoComplete="off"
        />
        {form.error && <p className="inline-error" role="alert">{form.error}</p>}
        <Button type="submit" variant="brand" disabled={!form.name.trim() || form.submitting}>
          {form.submitting ? '正在创建…' : '创建空间'}
        </Button>
      </form>
    </section>
  )
}
