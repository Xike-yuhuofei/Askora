import { useEffect, useState } from 'react'
import { ArrowLeft, Edit3, RefreshCw, Target } from 'lucide-react'
import * as goalApi from '../api/goals'
import { useNavigate } from '../router'
import './GoalEditor.css'

const statusLabels = { confirmed: '已确认', active: '进行中', paused: '已暂停', achieved: '已达成', archived: '已归档' }

export default function GoalDetail({ goalId }) {
  const navigate = useNavigate()
  const [state, setState] = useState({ status: 'loading', data: null, error: '' })
  const load = async () => {
    setState({ status: 'loading', data: null, error: '' })
    try { setState({ status: 'ready', data: await goalApi.getGoalDetail(goalId), error: '' }) }
    catch (error) { setState({ status: 'error', data: null, error: error?.response?.data?.error?.message || '目标详情暂时无法读取。' }) }
  }
  useEffect(() => { load() }, [goalId])
  if (state.status === 'loading') return <div className="page-state" role="status"><div className="spinner" /><p>正在读取目标…</p></div>
  if (state.status === 'error') return <div className="page-state page-state--error" role="alert"><p>{state.error}</p><button className="button button--secondary" onClick={load}><RefreshCw size={16} />重试</button></div>
  const { definition, state: goalState, focused } = state.data
  return <div className="goal-editor page-stack">
    <header className="page-header page-header--split"><div><p className="eyebrow">目标定义 v{definition.definition_version}</p><h1>{definition.title}</h1><p>{definition.topic}</p></div><div className="goal-actions"><button className="button button--secondary" onClick={() => navigate('/goals')}><ArrowLeft size={16} />返回</button>{!['achieved', 'archived'].includes(goalState.status) && <button className="button button--primary" onClick={() => navigate(`/goals/${goalId}/edit`)}><Edit3 size={16} />修订目标</button>}</div></header>
    <section className="surface"><div className="section-heading"><div><p className="eyebrow">当前状态</p><h2>{statusLabels[goalState.status] || goalState.status}{focused ? ' · 当前重点' : ''}</h2></div><Target size={20} /></div><dl className="fact-grid"><div><dt>目标能力</dt><dd>{definition.target_capabilities.join('、')}</dd></div><div><dt>应用场景</dt><dd>{definition.application_context || '未设置'}</dd></div><div><dt>每周预算</dt><dd>{definition.weekly_time_budget_minutes ? `${definition.weekly_time_budget_minutes} 分钟` : '未设置'}</dd></div><div><dt>截止时间</dt><dd>{definition.deadline_at ? new Date(definition.deadline_at).toLocaleDateString('zh-CN') : '未设置'}</dd></div></dl></section>
    <section className="surface"><div className="section-heading"><div><p className="eyebrow">证据门禁输入</p><h2>成功标准</h2></div></div><ol className="goal-detail-criteria">{definition.success_criteria.map((item) => <li key={item.criterion_id}><strong>{item.statement}</strong><span>{item.cognitive_process} · {item.evidence_requirements.join('、')}</span></li>)}</ol></section>
  </div>
}
