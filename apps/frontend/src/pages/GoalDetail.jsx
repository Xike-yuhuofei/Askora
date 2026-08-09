import { useEffect, useState } from 'react'
import { Archive, ArrowLeft, Copy, Edit3, Pause, Play, RefreshCw, ShieldCheck, Target } from 'lucide-react'
import * as goalApi from '../api/goals'
import { useNavigate } from '../router'
import './GoalEditor.css'

const statusLabels = { confirmed: '已确认', active: '进行中', paused: '已暂停', achieved: '已达成', archived: '已归档' }
const assessmentLabels = { scheduled: '等待延迟验证', available: '可以作答', accepted: '评分已接纳', needs_review: '等待复核', scoring_failed: '评分服务失败', cancelled: '已取消' }
const key = (scope) => `${scope}-${Date.now()}-${Math.random().toString(16).slice(2)}`

export default function GoalDetail({ goalId }) {
  const navigate = useNavigate()
  const [state, setState] = useState({ status: 'loading', data: null, error: '' })
  const [workspace, setWorkspace] = useState(null)
  const [responses, setResponses] = useState({})
  const [notice, setNotice] = useState('')
  const [busy, setBusy] = useState(false)
  const load = async () => {
    setState({ status: 'loading', data: null, error: '' })
    try {
      const data = await goalApi.getGoalDetail(goalId)
      setState({ status: 'ready', data, error: '' })
      try { setWorkspace(await goalApi.getGoalAchievement(goalId)) } catch { setWorkspace(null) }
    } catch (error) {
      setState({ status: 'error', data: null, error: error?.response?.data?.error?.message || '目标详情暂时无法读取。' })
    }
  }
  useEffect(() => { load() }, [goalId])

  const lifecycle = async (action) => {
    const current = state.data
    setBusy(true); setNotice('')
    try {
      const body = {
        expected_state_version: current.state.state_version,
        expected_plan_state_version: current.plan_state?.state_version || null,
        idempotency_key: key(`goal-${action}`),
      }
      const result = await goalApi[`${action}Goal`](goalId, body)
      if (result.copied_draft) navigate(`/goals/drafts/${result.copied_draft.draft_id}`)
      else { setNotice(action === 'archive' ? '目标已归档，可复制为新目标。' : '目标状态已更新。'); await load() }
    } catch (error) { setNotice(error?.response?.data?.error?.message || '目标状态更新失败，请刷新后重试。') }
    finally { setBusy(false) }
  }

  const schedule = async () => {
    setBusy(true); setNotice('')
    try {
      const result = await goalApi.scheduleGoalAssessments(goalId, {
        expected_state_version: state.data.state.state_version,
        idempotency_key: key('goal-assessments'),
      })
      setWorkspace(result); setNotice('验证任务已按规则版本安排。')
    } catch (error) { setNotice(error?.response?.data?.error?.message || '暂时无法安排验证。') }
    finally { setBusy(false) }
  }

  const submit = async (item) => {
    setBusy(true); setNotice('')
    try {
      await goalApi.submitGoalAssessment(goalId, item.assessment_activity_id, {
        expected_state_version: state.data.state.state_version,
        expected_activity_version: item.activity_version,
        response: responses[item.assessment_activity_id] || '',
        idempotency_key: key('goal-assessment-submit'),
      })
      setWorkspace(await goalApi.getGoalAchievement(goalId)); setNotice('回答已提交。系统失败或低置信不会记作学习失败。')
    } catch (error) { setNotice(error?.response?.data?.error?.message || '回答提交失败，可稍后重试。') }
    finally { setBusy(false) }
  }

  const evaluate = async () => {
    setBusy(true); setNotice('')
    try {
      const evaluation = await goalApi.evaluateGoalAchievement(goalId, {
        expected_state_version: state.data.state.state_version,
        idempotency_key: key('goal-evaluate'),
      })
      setWorkspace((current) => ({ ...current, latest_evaluation: evaluation }))
      setNotice(evaluation.eligible_for_achievement ? '证据门禁已满足，请由你最终确认达成。' : '仍有成功标准或独立验证义务未满足。')
    } catch (error) { setNotice(error?.response?.data?.error?.message || '证据评估失败。') }
    finally { setBusy(false) }
  }

  const achieve = async () => {
    const evaluation = workspace?.latest_evaluation
    if (!evaluation?.eligible_for_achievement) return
    setBusy(true); setNotice('')
    try {
      await goalApi.confirmGoalAchievement(goalId, {
        expected_state_version: state.data.state.state_version,
        expected_plan_state_version: state.data.plan_state?.state_version || null,
        evaluation_id: evaluation.evaluation_id,
        expected_evaluation_version: evaluation.evaluation_version,
        idempotency_key: key('goal-achieve'),
      })
      setNotice('目标已由你确认达成。该状态不等于一般化 mastery 或真人学习效果证明。'); await load()
    } catch (error) { setNotice(error?.response?.data?.error?.message || '达成确认失败，请重新评估证据。') }
    finally { setBusy(false) }
  }

  if (state.status === 'loading') return <div className="page-state" role="status"><div className="spinner" /><p>正在读取目标…</p></div>
  if (state.status === 'error') return <div className="page-state page-state--error" role="alert"><p>{state.error}</p><button className="button button--secondary" onClick={load}><RefreshCw size={16} />重试</button></div>
  const { definition, state: goalState, focused } = state.data
  return <div className="goal-editor page-stack">
    <header className="page-header page-header--split"><div><p className="eyebrow">目标定义 v{definition.definition_version}</p><h1>{definition.title}</h1><p>{definition.topic}</p></div><div className="goal-actions"><button className="button button--secondary" onClick={() => navigate('/goals')}><ArrowLeft size={16} />返回</button>{!['achieved', 'archived'].includes(goalState.status) && <button className="button button--primary" onClick={() => navigate(`/goals/${goalId}/edit`)}><Edit3 size={16} />修订目标</button>}</div></header>
    {notice && <p className="goal-notice" role="status">{notice}</p>}
    <section className="surface"><div className="section-heading"><div><p className="eyebrow">当前状态</p><h2>{statusLabels[goalState.status] || goalState.status}{focused ? ' · 当前重点' : ''}</h2></div><Target size={20} /></div><dl className="fact-grid"><div><dt>目标能力</dt><dd>{definition.target_capabilities.join('、')}</dd></div><div><dt>应用场景</dt><dd>{definition.application_context || '未设置'}</dd></div><div><dt>每周预算</dt><dd>{definition.weekly_time_budget_minutes ? `${definition.weekly_time_budget_minutes} 分钟` : '未设置'}</dd></div><div><dt>截止时间</dt><dd>{definition.deadline_at ? new Date(definition.deadline_at).toLocaleDateString('zh-CN') : '未设置'}</dd></div></dl>
      <div className="goal-actions goal-lifecycle-actions">{goalState.status === 'active' && <button disabled={busy} className="button button--secondary" onClick={() => lifecycle('pause')}><Pause size={16} />暂停</button>}{goalState.status === 'paused' && <button disabled={busy} className="button button--primary" onClick={() => lifecycle('resume')}><Play size={16} />恢复</button>}{['confirmed', 'active', 'paused'].includes(goalState.status) && <button disabled={busy} className="button button--secondary" onClick={() => lifecycle('archive')}><Archive size={16} />归档</button>}{goalState.status === 'archived' && <button disabled={busy} className="button button--primary" onClick={() => lifecycle('copyArchived')}><Copy size={16} />复制为新目标</button>}</div>
    </section>
    <section className="surface"><div className="section-heading"><div><p className="eyebrow">证据门禁输入</p><h2>成功标准</h2></div></div><ol className="goal-detail-criteria">{definition.success_criteria.map((item) => <li key={item.criterion_id}><strong>{item.statement}</strong><span>{item.cognitive_process} · {item.evidence_requirements.join('、')}</span></li>)}</ol></section>
    {goalState.status === 'active' && <section className="surface"><div className="section-heading"><div><p className="eyebrow">版本化验证</p><h2>达成证据</h2></div><ShieldCheck size={20} /></div><p>评分绑定当前目标、资料、rubric 和 policy；低置信、评分分歧或模型失败只会进入复核/失败状态。</p>{!workspace?.assessments?.length && <button disabled={busy} className="button button--primary" onClick={schedule}>安排成功标准验证</button>}<div className="goal-assessments">{workspace?.assessments?.map((item) => <article className="goal-assessment-card" key={item.assessment_activity_id}><div><strong>{item.prompt}</strong><span>{assessmentLabels[item.status] || item.status} · {item.scoring_method === 'structured' ? '确定性评分' : '开放题双重评分'}</span></div>{['available', 'needs_review', 'scoring_failed'].includes(item.status) && <><label htmlFor={`answer-${item.assessment_activity_id}`}>你的独立回答</label><textarea id={`answer-${item.assessment_activity_id}`} value={responses[item.assessment_activity_id] || ''} onChange={(event) => setResponses((current) => ({ ...current, [item.assessment_activity_id]: event.target.value }))} /><button disabled={busy || !(responses[item.assessment_activity_id] || '').trim()} className="button button--secondary" onClick={() => submit(item)}>提交验证</button></>}</article>)}</div>{workspace?.assessments?.length > 0 && <button disabled={busy} className="button button--secondary" onClick={evaluate}>检查达成门禁</button>}{workspace?.latest_evaluation?.eligible_for_achievement && <button disabled={busy} className="button button--primary" onClick={achieve}>由我确认目标达成</button>}</section>}
  </div>
}
