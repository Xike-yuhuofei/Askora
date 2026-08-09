import { useCallback, useEffect, useMemo, useState } from 'react'
import { ArrowLeft, Check, RefreshCw, Sparkles, Target } from 'lucide-react'
import * as goalApi from '../api/goals'
import * as workspaceApi from '../api/workspace'
import { useNavigate } from '../router'
import './GoalEditor.css'

const commandKey = (prefix) => `${prefix}-${globalThis.crypto?.randomUUID?.() || Date.now()}`

const criterionLabels = {
  recall: '回忆', understand: '理解', explain: '解释', apply: '应用', transfer: '迁移',
}

function errorMessage(error, fallback) {
  const payload = error?.response?.data
  return payload?.error?.message || payload?.detail || fallback
}

function sourceAvailability(document) {
  if (document.archived_at || document.is_archived) return { disabled: true, label: '已归档' }
  if (['failed', 'rejected', 'quarantined'].includes(document.processing_status)) {
    return { disabled: true, label: '不可用于新目标' }
  }
  if (['pending', 'processing'].includes(document.processing_status)) {
    return { disabled: false, label: '可存草稿，暂不能确认' }
  }
  if (document.knowledge_status !== 'PUBLISHED') {
    return { disabled: false, label: '尚无已发布知识，暂不能确认' }
  }
  return { disabled: false, label: '可用于目标' }
}

function draftToForm(draft) {
  return {
    title: draft.title,
    topic: draft.topic,
    targetCapabilities: draft.target_capabilities.join('、'),
    applicationContext: draft.application_context || '',
    deadline: draft.deadline_at?.slice(0, 10) || '',
    weeklyBudget: draft.weekly_time_budget_minutes || '',
    sourceIds: draft.source_document_ids,
    criteria: draft.success_criteria,
  }
}

function shortcutDefaults() {
  const query = window.location.hash.split('?')[1] || ''
  const params = new URLSearchParams(query)
  return {
    sourceId: params.get('source_document_id'),
    title: params.get('title') || '',
    topic: params.get('topic') || '',
    applicationContext: params.get('application_context') || '',
    weeklyBudget: params.get('weekly_time_budget_minutes') || 70,
    deadline: params.get('deadline') || '',
  }
}

export default function GoalEditor({ draftId = null, editGoalId = null }) {
  const navigate = useNavigate()
  const [draft, setDraft] = useState(null)
  const [form, setForm] = useState({
    title: '', topic: '', targetCapabilities: '', applicationContext: '', deadline: '',
    weeklyBudget: 70, sourceIds: [], criteria: [],
  })
  const [documents, setDocuments] = useState([])
  const [targets, setTargets] = useState([])
  const [selectedTargets, setSelectedTargets] = useState([])
  const [preview, setPreview] = useState(null)
  const [status, setStatus] = useState('loading')
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)

  const load = useCallback(async () => {
    setStatus('loading')
    setMessage('')
    try {
      const library = await workspaceApi.getLibraryWorkspace({ pageSize: 100 })
      setDocuments(library.data?.documents || [])
      if (draftId) {
        const current = await goalApi.getGoalDraft(draftId)
        setDraft(current)
        setForm(draftToForm(current))
        setSelectedTargets(current.selected_target_ids || [])
        if (current.source_document_ids.length) {
          const response = await goalApi.getGoalTargets(draftId)
          setTargets(response.targets || [])
        }
      } else {
        const shortcut = shortcutDefaults()
        const validSource = library.data?.documents?.some(
          (item) => item.document_id === shortcut.sourceId && !sourceAvailability(item).disabled,
        )
        setForm((current) => ({
          ...current,
          title: shortcut.title,
          topic: shortcut.topic,
          applicationContext: shortcut.applicationContext,
          weeklyBudget: shortcut.weeklyBudget,
          deadline: shortcut.deadline,
          sourceIds: validSource ? [shortcut.sourceId] : [],
        }))
      }
      setStatus('ready')
    } catch (error) {
      setStatus('error')
      setMessage(errorMessage(error, '目标编辑器暂时无法读取。'))
    }
  }, [draftId])

  useEffect(() => { load() }, [load])

  useEffect(() => {
    if (!editGoalId || draftId) return
    let active = true
    const openEdit = async () => {
      try {
        const detail = await goalApi.getGoalDetail(editGoalId)
        const created = await goalApi.createEditGoalDraft(editGoalId, {
          expected_state_version: detail.state.state_version,
          idempotency_key: commandKey('goal-edit'),
        })
        if (active) navigate(`/goals/drafts/${created.draft_id}`, { replace: true })
      } catch (error) {
        if (active) { setStatus('error'); setMessage(errorMessage(error, '无法创建修订草稿。')) }
      }
    }
    openEdit()
    return () => { active = false }
  }, [draftId, editGoalId, navigate])

  const selectedDocuments = useMemo(
    () => documents.filter((item) => form.sourceIds.includes(item.document_id)),
    [documents, form.sourceIds],
  )

  const generateCriteria = async () => {
    if (!form.topic.trim()) { setMessage('请先填写学习主题。'); return }
    setBusy(true); setMessage('')
    try {
      const result = await goalApi.suggestSuccessCriteria({
        topic: form.topic.trim(), cognitive_processes: ['recall', 'explain', 'apply', 'transfer'],
      })
      setForm((current) => ({ ...current, criteria: result.criteria }))
    } catch (error) { setMessage(errorMessage(error, '成功标准候选生成失败。')) }
    finally { setBusy(false) }
  }

  const payload = () => ({
    source_document_ids: form.sourceIds,
    title: form.title.trim(),
    topic: form.topic.trim(),
    target_capabilities: form.targetCapabilities.split(/[、,，]/).map((item) => item.trim()).filter(Boolean),
    application_context: form.applicationContext.trim() || null,
    deadline_at: form.deadline ? new Date(`${form.deadline}T23:59:59`).toISOString() : null,
    weekly_time_budget_minutes: form.weeklyBudget ? Number(form.weeklyBudget) : null,
    success_criteria: form.criteria,
  })

  const save = async () => {
    if (!form.sourceIds.length || !form.criteria.length) {
      setMessage('至少选择一份资料并生成一条可测成功标准。'); return
    }
    setBusy(true); setMessage('')
    try {
      let saved
      if (!draft) {
        saved = await goalApi.createGoalDraft({ ...payload(), idempotency_key: commandKey('goal-create') })
        navigate(`/goals/drafts/${saved.draft_id}`, { replace: true })
        return
      }
      saved = await goalApi.updateGoalDraft(draft.draft_id, {
        expected_draft_version: draft.draft_version,
        ...payload(),
        idempotency_key: commandKey('goal-save'),
      })
      setDraft(saved); setForm(draftToForm(saved)); setPreview(null)
      const response = await goalApi.getGoalTargets(saved.draft_id)
      setTargets(response.targets || [])
      setSelectedTargets(saved.selected_target_ids || [])
      setMessage('草稿已保存。请明确勾选学习重点。')
    } catch (error) { setMessage(errorMessage(error, '草稿保存失败。')) }
    finally { setBusy(false) }
  }

  const confirmTargets = async () => {
    if (!selectedTargets.length) { setMessage('请至少勾选一个学习重点。'); return }
    setBusy(true); setMessage('')
    try {
      const saved = await goalApi.updateGoalDraft(draft.draft_id, {
        expected_draft_version: draft.draft_version,
        selected_target_ids: selectedTargets,
        targets_confirmed: true,
        idempotency_key: commandKey('goal-targets'),
      })
      setDraft(saved)
      setMessage('学习重点已明确确认。')
    } catch (error) { setMessage(errorMessage(error, '学习重点确认失败。')) }
    finally { setBusy(false) }
  }

  const buildPreview = async () => {
    setBusy(true); setMessage('')
    try {
      const result = await goalApi.previewGoalDraft(draft.draft_id, {
        expected_draft_version: draft.draft_version,
        idempotency_key: commandKey('goal-preview'),
      })
      setPreview(result)
      setDraft((current) => ({ ...current, draft_version: current.draft_version + 1, status: 'preview_ready' }))
    } catch (error) { setMessage(errorMessage(error, '变更预览生成失败。')) }
    finally { setBusy(false) }
  }

  const apply = async (boundaryMode) => {
    setBusy(true); setMessage('')
    try {
      const result = await goalApi.applyGoalDraft(draft.draft_id, {
        expected_draft_version: preview.draft_version,
        expected_preview_version: preview.preview_version,
        preview_id: preview.preview_id,
        boundary_mode: boundaryMode,
        set_focused: true,
        idempotency_key: commandKey('goal-apply'),
      })
      if (result.status === 'applied') navigate(`/goals/${result.goal_id}`, { replace: true })
      else { setMessage('变更已批准，将在当前活动正常完成后切换。'); setPreview(null) }
    } catch (error) { setMessage(errorMessage(error, '目标应用失败，请重新预览。')) }
    finally { setBusy(false) }
  }

  const updateCriterion = (criterionId, statement) => setForm((current) => ({
    ...current,
    criteria: current.criteria.map((item) => item.criterion_id === criterionId ? { ...item, statement } : item),
  }))

  if (status === 'loading') return <div className="page-state" role="status"><div className="spinner" /><p>正在准备目标编辑器…</p></div>
  if (status === 'error') return <div className="page-state page-state--error" role="alert"><h1>目标编辑器</h1><p>{message}</p><button className="button button--secondary" onClick={load}><RefreshCw size={16} />重试</button></div>

  return (
    <div className="goal-editor page-stack">
      <header className="page-header page-header--split">
        <div><p className="eyebrow">P1-01 · 目标定义</p><h1>{draft ? '编辑目标草稿' : '创建学习目标'}</h1><p>先保存草稿，再明确选择学习重点并审阅计划影响。</p></div>
        <button type="button" className="button button--secondary" onClick={() => navigate('/goals')}><ArrowLeft size={16} />返回目标</button>
      </header>

      <section className="surface goal-form" aria-labelledby="goal-definition-title">
        <div className="section-heading"><div><p className="eyebrow">目标内容</p><h2 id="goal-definition-title">定义你要获得的能力</h2></div><Target size={20} /></div>
        <div className="goal-form__grid">
          <label>目标名称<input value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} /></label>
          <label>学习主题<input value={form.topic} onChange={(event) => setForm({ ...form, topic: event.target.value })} /></label>
          <label className="goal-form__wide">目标能力（用顿号分隔）<input value={form.targetCapabilities} onChange={(event) => setForm({ ...form, targetCapabilities: event.target.value })} /></label>
          <label className="goal-form__wide">应用场景<textarea rows="3" value={form.applicationContext} onChange={(event) => setForm({ ...form, applicationContext: event.target.value })} /></label>
          <label>截止日期<input type="date" value={form.deadline} onChange={(event) => setForm({ ...form, deadline: event.target.value })} /></label>
          <label>每周预算（分钟）<input type="number" min="1" max="10080" value={form.weeklyBudget} onChange={(event) => setForm({ ...form, weeklyBudget: event.target.value })} /></label>
        </div>
      </section>

      <section className="surface" aria-labelledby="goal-sources-title">
        <div className="section-heading"><div><p className="eyebrow">资料范围</p><h2 id="goal-sources-title">选择一份或多份资料</h2></div><span>{form.sourceIds.length} 已选</span></div>
        <div className="goal-choice-list">
          {documents.map((document) => {
            const availability = sourceAvailability(document)
            return <label key={document.document_id} className={`goal-choice ${availability.disabled ? 'goal-choice--disabled' : ''}`}>
              <input type="checkbox" disabled={availability.disabled} checked={form.sourceIds.includes(document.document_id)} onChange={(event) => setForm({ ...form, sourceIds: event.target.checked ? [...form.sourceIds, document.document_id] : form.sourceIds.filter((id) => id !== document.document_id) })} />
              <span><strong>{document.title || document.filename || '未命名资料'}</strong><small>{availability.label}</small></span>
            </label>
          })}
          {!documents.length && <p>资料库为空，请先上传资料。</p>}
        </div>
      </section>

      <section className="surface" aria-labelledby="criteria-title">
        <div className="section-heading"><div><p className="eyebrow">可测标准</p><h2 id="criteria-title">成功标准</h2></div><button type="button" className="button button--secondary" disabled={busy} onClick={generateCriteria}><Sparkles size={16} />生成候选</button></div>
        <div className="goal-criteria">
          {form.criteria.map((criterion) => <label key={criterion.criterion_id}><span>{criterionLabels[criterion.cognitive_process] || criterion.cognitive_process}</span><textarea rows="2" value={criterion.statement} onChange={(event) => updateCriterion(criterion.criterion_id, event.target.value)} /><small>证据要求：{criterion.evidence_requirements.join('、')}</small></label>)}
          {!form.criteria.length && <p>生成后可以逐条修改；含“了解、熟悉、看完”等不可测表述时无法确认。</p>}
        </div>
        <button type="button" className="button button--primary" disabled={busy} onClick={save}>{draft ? '保存草稿更改' : '保存为草稿'}</button>
      </section>

      {draft && <section className="surface" aria-labelledby="targets-title">
        <div className="section-heading"><div><p className="eyebrow">必须显式确认</p><h2 id="targets-title">学习重点卡片</h2></div><Check size={20} /></div>
        <div className="goal-target-grid">
          {targets.map((target) => <label key={target.target_id} className="goal-target-card">
            <input type="checkbox" checked={selectedTargets.includes(target.target_id)} onChange={(event) => setSelectedTargets(event.target.checked ? [...selectedTargets, target.target_id] : selectedTargets.filter((id) => id !== target.target_id))} />
            <span><strong>{target.name}</strong><small>来源：{target.source_name}</small><q>{target.evidence_excerpt}</q><em>{target.recommended_reason}</em></span>
          </label>)}
          {!targets.length && <p>所选资料尚无可执行的已发布知识，草稿可以保留，但现在不能确认。</p>}
        </div>
        <div className="goal-actions"><button className="button button--secondary" disabled={busy || !targets.length} onClick={confirmTargets}>确认所选重点</button><button className="button button--primary" disabled={busy || !draft.targets_confirmed} onClick={buildPreview}>生成变更预览</button></div>
      </section>}

      {preview && <section className="surface goal-preview" aria-labelledby="preview-title">
        <div className="section-heading"><div><p className="eyebrow">切换前检查</p><h2 id="preview-title">目标与计划影响</h2></div><span className="status-pill">{preview.effective_timing === 'immediate' ? '立即生效' : '活动边界生效'}</span></div>
        <dl className="fact-grid">
          <div><dt>资料</dt><dd>{selectedDocuments.map((item) => item.title || item.filename).join('、')}</dd></div>
          <div><dt>学习重点</dt><dd>{preview.target_cards.map((item) => item.name).join('、')}</dd></div>
          <div><dt>计划影响</dt><dd>创建新 mapping 与新 plan；新计划准备好后旧计划才会 supersede。</dd></div>
          <div><dt>字段变更</dt><dd>{preview.field_diffs.map((item) => item.field).join('、') || '首次定义'}</dd></div>
        </dl>
        <div className="goal-actions"><button className="button button--primary" disabled={busy} onClick={() => apply('normal_boundary')}>{preview.active_activity_ref ? '当前活动完成后切换' : '确认并启用目标'}</button>{preview.active_activity_ref && <button className="button button--danger" disabled={busy} onClick={() => apply('supersede_active')}>结束本项并切换</button>}</div>
      </section>}

      {message && <p className="goal-message" role="status">{message}</p>}
    </div>
  )
}
