import { useEffect, useState } from 'react'
import { ArrowRight, History as HistoryIcon, Library, RefreshCw } from 'lucide-react'
import * as dialogApi from '../api/dialog'
import { useNavigate } from '../router'
import './History.css'

const statusLabels = {
  completed: '已完成',
  ended: '已结束',
  abandoned: '已放弃',
  active: '进行中',
  archived: '已放弃',
}

const FILTERS = [
  { key: 'all', label: '全部' },
  { key: 'activity', label: '学习活动' },
  { key: 'dialog', label: '对话' },
]

export default function History() {
  const navigate = useNavigate()
  const [filter, setFilter] = useState('all')
  const [state, setState] = useState({ status: 'loading', items: [], error: '' })

  const load = async () => {
    setState((current) => ({ ...current, status: 'loading', error: '' }))
    try {
      const data = await dialogApi.getSessions(1, 100)
      setState({ status: 'ready', items: data.items || [], error: '' })
    } catch {
      setState({
        status: 'error',
        items: [],
        error: '历史记录暂时无法读取。',
      })
    }
  }

  useEffect(() => { load() }, [])

  // 当前仅能聚合 dialog session；「学习活动」尚无逐条数据，诚实显示空态。
  const visibleItems = filter === 'activity' ? [] : state.items

  return (
    <div className="history-page page-stack">
      <header className="page-header">
        <p className="eyebrow">只读历史</p>
        <h1>历史记录</h1>
        <p>这里是只读历史，不会显示计划或未来安排。</p>
      </header>

      <section className="surface history-surface" aria-labelledby="history-list-title">
        <div className="section-heading">
          <div>
            <h2 id="history-list-title">学习会话</h2>
            <p>当前仅聚合 dialog session；activity 和 episode 关联尚不可用。</p>
          </div>
          <HistoryIcon size={19} />
        </div>

        <div className="history-filters" role="group" aria-label="历史记录过滤">
          {FILTERS.map((item) => (
            <button
              key={item.key}
              type="button"
              className={`history-filter${filter === item.key ? ' history-filter--active' : ''}`}
              aria-pressed={filter === item.key}
              onClick={() => setFilter(item.key)}
            >
              {item.label}
            </button>
          ))}
        </div>

        {state.status === 'loading' && <div className="inline-state" role="status"><div className="spinner" /> 正在读取…</div>}
        {(state.status === 'error') && (
          <div className="inline-state inline-state--error" role="alert">
            <span>{state.error}</span>
            <button type="button" className="button button--secondary" onClick={load}>
              <RefreshCw size={15} /> 重试
            </button>
          </div>
        )}
        {state.status === 'ready' && visibleItems.length === 0 && (
          <div className="empty-copy history-empty" role="status">
            <p>还没有历史记录{filter === 'activity' ? '（学习活动）' : ''}</p>
            {filter !== 'activity' && <p>完成学习活动后，这里会记录过程。</p>}
            <button type="button" className="button button--secondary" onClick={() => navigate('/library')}>
              <Library size={16} /> 开始学习
            </button>
          </div>
        )}
        {state.status === 'ready' && visibleItems.length > 0 && (
          <ul className="history-list">
            {visibleItems.map((session) => (
              <li key={session.id} className="history-item">
                <button type="button" className="history-item__main" onClick={() => navigate(`/quick/${encodeURIComponent(session.id)}`)}>
                  <strong>{session.knowledge_point || session.title || session.subject}</strong>
                  <small>{session.subject} · {new Date(session.updated_at || session.created_at).toLocaleString('zh-CN')}</small>
                </button>
                <div className="history-item__end">
                  <span className={`status-pill status-pill--${session.status === 'active' ? 'available' : 'neutral'}`}>
                    {statusLabels[session.status] || session.status}
                  </span>
                  <button type="button" className="button button--secondary" onClick={() => navigate(`/quick/${encodeURIComponent(session.id)}`)}>
                    回看<ArrowRight size={16} />
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}