import { useEffect, useMemo, useState } from 'react'
import { ArrowRight, ListTree, RefreshCw } from 'lucide-react'
import * as workspaceApi from '../api/workspace'
import SourceStatus from '../components/SourceStatus'
import { useNavigate } from '../router'
import './Goals.css'
import './LearningPath.css'

const activityStatus = { planned: '已规划', available: '可开始', active: '进行中', completed: '已完成', skipped: '已跳过', superseded: '已替代' }
const planStatus = { active: '进行中', paused: '已暂停', completed: '已完成', superseded: '已替代' }
const activityTypes = { learn_new: '新知识学习', prerequisite_remediation: '前置知识补强', diagnostic: '基础检查', practice: '练习巩固', delayed_review: '延迟复习', transfer_check: '迁移应用', metacognitive_review: '学习复盘' }
const reasonLabels = { PLAN_TARGET_STATE_UNKNOWN: '需要先了解当前基础', PLAN_MASTERY_GAP: '当前证据显示仍需学习', PLAN_PREREQUISITE_UNKNOWN: '前置知识状态尚不明确', PLAN_HARD_PREREQUISITE_UNMET: '需要先补齐前置知识', PLAN_REVIEW_DUE: '已到建议复习时间', PLAN_REVIEW_OVERDUE: '复习建议已到期', PLAN_TRANSFER_EVIDENCE_NEEDED: '需要新的迁移应用证据' }

function initialGoalId() {
  const query = window.location.hash.split('?')[1] || ''
  return new URLSearchParams(query).get('goal_id') || ''
}

function goalIdFromRef(ref) { return ref?.split(':')[1] || '' }

export default function LearningPath() {
  const navigate = useNavigate()
  const [goalId, setGoalId] = useState(initialGoalId)
  const [state, setState] = useState({ status: 'loading', payload: null, goalOptions: [], error: '' })

  const load = async (scope = goalId) => {
    setState((current) => ({ ...current, status: 'loading', error: '' }))
    try {
      const payload = await workspaceApi.getLearningPath(scope)
      let goalOptions = []
      if (payload.data.reason_codes.includes('MULTIPLE_CURRENT_PLANS_REQUIRE_GOAL_SCOPE')) {
        try {
          const goals = await workspaceApi.getGoalsWorkspace()
          const allowed = new Set(payload.data.available_goal_refs)
          goalOptions = goals.data.goals.filter((goal) => allowed.has(goal.goal_ref))
        } catch {
          goalOptions = payload.data.available_goal_refs.map((goalRef, index) => ({ goal_ref: goalRef, title: `学习目标 ${index + 1}` }))
        }
      }
      setState({ status: 'ready', payload, goalOptions, error: '' })
    } catch (error) {
      const unauthorized = error.response?.status === 401
      setState({ status: unauthorized ? 'unauthorized' : 'error', payload: null, goalOptions: [], error: unauthorized ? '登录状态已失效，请重新登录。' : '学习路径暂时无法读取。' })
    }
  }

  useEffect(() => { load(goalId) }, [])
  const path = state.payload?.data?.learning_path
  const goalOptions = state.goalOptions
  const selected = useMemo(() => goalId || goalIdFromRef(state.payload?.data?.selected_goal_ref), [goalId, state.payload])

  const chooseGoal = (event) => {
    const next = event.target.value
    setGoalId(next)
    load(next)
  }

  if (state.status === 'loading') return <div className="page-state" role="status"><div className="spinner" /><p>正在读取学习路径…</p></div>
  if (state.status === 'error' || state.status === 'unauthorized') return <div className="page-state page-state--error" role="alert"><h1>学习路径</h1><p>{state.error}</p><button type="button" className="button button--secondary" onClick={() => load()}><RefreshCw size={16} />重试</button></div>

  const { data, source_status: sourceStatus } = state.payload
  return (
    <div className="product-view page-stack">
      <header className="page-header page-header--split"><div><p className="eyebrow">当前计划</p><h1>学习路径</h1><p>按规划器发布的顺序查看活动；这里不会在前端重新规划。</p></div><span className={`status-pill status-pill--${data.view_state.toLowerCase()}`}>{data.view_state === 'READY' ? '路径可用' : data.view_state === 'PARTIAL' ? '部分信息可用' : '暂无路径'}</span></header>

      {!path && data.reason_codes.includes('MULTIPLE_CURRENT_PLANS_REQUIRE_GOAL_SCOPE') && (
        <section className="surface path-scope" aria-labelledby="path-scope-title"><div><h2 id="path-scope-title">请选择要查看的目标</h2><p>存在多个当前计划，Askora 不会替你猜选其中一个。</p></div><label><span>学习目标</span><select value={selected} onChange={chooseGoal}><option value="">选择目标</option>{goalOptions.map((goal) => <option key={goal.goal_ref} value={goalIdFromRef(goal.goal_ref)}>{goal.title}</option>)}</select></label></section>
      )}

      {path ? (
        <>
          <section className="surface path-summary" aria-labelledby="path-summary-title"><div className="section-heading"><div><p className="eyebrow">计划输入</p><h2 id="path-summary-title">路径依据</h2></div><ListTree size={20} /></div><dl className="fact-grid"><div><dt>计划状态</dt><dd>{planStatus[path.status] || path.status}</dd></div><div><dt>学习者状态版本</dt><dd>v{path.created_from_learner_state_version}</dd></div><div><dt>知识图谱版本</dt><dd>{path.knowledge_graph_version}</dd></div><div><dt>复习计划版本</dt><dd>{path.review_schedule_version || '未纳入'}</dd></div></dl>{path.objectives.some((item) => item.capability == null) && <p className="data-note">学习目标的细分能力与认知过程尚未由规划系统发布；当前保留可追踪关系，不做推断。</p>}</section>
          <section className="surface" aria-labelledby="activity-list-title"><div className="section-heading"><div><p className="eyebrow">规划顺序</p><h2 id="activity-list-title">学习活动</h2></div><span className="status-pill">{path.activities.length} 项</span></div>{path.activities.length ? <ol className="path-list">{path.activities.map((activity, index) => <li key={activity.activity_ref}><span className="path-list__index">{index + 1}</span><div><div className="product-row__title"><h3>{activity.title}</h3><span className="status-pill">{activityStatus[activity.status] || activity.status}</span></div><p>{activity.estimated_duration_minutes} 分钟 · {activityTypes[activity.type] || '学习活动'}</p><small>{activity.reason_codes.map((reason) => reasonLabels[reason] || '由当前学习计划安排').join(' · ')}</small></div></li>)}</ol> : <p className="empty-copy">计划存在，但当前没有可展示的活动。</p>}</section>
        </>
      ) : !data.reason_codes.includes('MULTIPLE_CURRENT_PLANS_REQUIRE_GOAL_SCOPE') && (
        <section className="surface empty-panel"><ListTree size={24} /><h2>还没有可展示的学习路径</h2><p>这不表示目标已完成；当前没有 owner 发布的活动计划。</p><button type="button" className="button button--secondary" onClick={() => navigate('/goals')}>查看学习目标<ArrowRight size={16} /></button></section>
      )}
      <SourceStatus items={sourceStatus} />
    </div>
  )
}
