import { useEffect, useState } from 'react'
import { ArrowRight, RefreshCw, Target } from 'lucide-react'
import * as workspaceApi from '../api/workspace'
import SourceStatus from '../components/SourceStatus'
import { useNavigate } from '../router'
import './Goals.css'

const statusLabels = {
  candidate: '待确认',
  confirmed: '已确认',
  active: '进行中',
  achieved: '已达成',
  paused: '已暂停',
  archived: '已归档',
}

function goalIdFromRef(ref) {
  return ref?.split(':')[1] || ''
}

function versionFromRef(ref) {
  return ref?.split(':').at(-1)?.replace(/^v/, '') || '未知'
}

function formatDeadline(value) {
  if (!value) return '未设置截止时间'
  return new Intl.DateTimeFormat('zh-CN', { year: 'numeric', month: 'short', day: 'numeric' })
    .format(new Date(value))
}

export default function Goals() {
  const navigate = useNavigate()
  const [state, setState] = useState({ status: 'loading', payload: null, error: '' })

  const load = async () => {
    setState((current) => ({ ...current, status: 'loading', error: '' }))
    try {
      setState({ status: 'ready', payload: await workspaceApi.getGoalsWorkspace(), error: '' })
    } catch (error) {
      const unauthorized = error.response?.status === 401
      setState({
        status: unauthorized ? 'unauthorized' : 'error',
        payload: null,
        error: unauthorized ? '登录状态已失效，请重新登录。' : '学习目标暂时无法读取。',
      })
    }
  }

  useEffect(() => { load() }, [])

  if (state.status === 'loading') {
    return <div className="page-state" role="status"><div className="spinner" /><p>正在读取学习目标…</p></div>
  }
  if (state.status === 'error' || state.status === 'unauthorized') {
    return (
      <div className="page-state page-state--error" role="alert">
        <h1>学习目标</h1><p>{state.error}</p>
        <button type="button" className="button button--secondary" onClick={load}><RefreshCw size={16} />重试</button>
      </div>
    )
  }

  const { data, source_status: sourceStatus } = state.payload
  return (
    <div className="product-view page-stack">
      <header className="page-header page-header--split">
        <div><p className="eyebrow">只读目标</p><h1>学习目标</h1><p>目标决定学习路径的方向；当前页面只展示已经存在的版本。</p></div>
        <span className="status-pill status-pill--available">{data.goals.length} 个目标</span>
      </header>

      {data.goals.length ? (
        <section className="surface" aria-labelledby="goal-list-title">
          <div className="section-heading"><div><p className="eyebrow">规划数据</p><h2 id="goal-list-title">当前目标</h2></div><Target size={20} /></div>
          <ul className="product-list">
            {data.goals.map((goal) => (
              <li key={goal.goal_ref} className="product-row">
                <div className="product-row__content">
                  <div className="product-row__title"><h3>{goal.title}</h3><span className="status-pill">{statusLabels[goal.status] || goal.status}</span></div>
                  <p>{goal.topic}</p>
                  <dl className="fact-grid">
                    <div><dt>目标能力</dt><dd>{goal.target_capabilities.join('、')}</dd></div>
                    <div><dt>成功标准</dt><dd>{goal.success_criteria.join('；')}</dd></div>
                    <div><dt>时间安排</dt><dd>{goal.weekly_time_budget_minutes ? `每周 ${goal.weekly_time_budget_minutes} 分钟` : '未设置每周时间'} · {formatDeadline(goal.deadline_at)}</dd></div>
                    <div><dt>当前版本</dt><dd>v{versionFromRef(goal.goal_ref)}</dd></div>
                  </dl>
                </div>
                <button type="button" className="button button--secondary" onClick={() => navigate(`/path?goal_id=${goalIdFromRef(goal.goal_ref)}`)}>查看路径<ArrowRight size={16} /></button>
              </li>
            ))}
          </ul>
        </section>
      ) : (
        <section className="surface empty-panel"><Target size={24} /><h2>还没有学习目标</h2><p>当前不会自动生成虚构目标。可先在资料库选择材料并使用已提供的学习入口。</p><button type="button" className="button button--primary" onClick={() => navigate('/library')}>前往资料库</button></section>
      )}
      <SourceStatus items={sourceStatus} />
    </div>
  )
}
