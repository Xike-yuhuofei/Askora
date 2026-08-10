import { useEffect, useState } from 'react'
import { ArrowRight, History as HistoryIcon, RefreshCw } from 'lucide-react'
import * as dialogApi from '../api/dialog'
import { useNavigate } from '../router'
import './History.css'

const statusLabels = {
  active: '进行中',
  ended: '已结束',
  archived: '已归档',
}

export default function History() {
  const navigate = useNavigate()
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

  return (
    <div className="history-page page-stack">
      <header className="page-header">
        <p className="eyebrow">只读历史</p>
        <h1>历史记录</h1>
        <p>查看已有兼容会话。历史内容不会调用在线模型重新生成。</p>
      </header>

      <section className="surface history-surface" aria-labelledby="history-list-title">
        <div className="section-heading">
          <div>
            <h2 id="history-list-title">学习会话</h2>
            <p>当前仅聚合 dialog session；activity 和 episode 关联尚不可用。</p>
          </div>
          <HistoryIcon size={19} />
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
        {state.status === 'ready' && state.items.length === 0 && (
          <p className="empty-copy">暂无历史会话。你可以从“今天”的兼容入口开始。</p>
        )}
        {state.status === 'ready' && state.items.length > 0 && (
          <ul className="history-list">
            {state.items.map((session) => (
              <li key={session.id}>
                <button type="button" onClick={() => navigate(`/quick/${encodeURIComponent(session.id)}`)}>
                  <span className="history-list__main">
                    <strong>{session.knowledge_point || session.title || session.subject}</strong>
                    <small>{session.subject} · {new Date(session.updated_at || session.created_at).toLocaleString('zh-CN')}</small>
                  </span>
                  <span className="history-list__end">
                    <span className={`status-pill status-pill--${session.status === 'active' ? 'available' : 'neutral'}`}>
                      {statusLabels[session.status] || session.status}
                    </span>
                    <ArrowRight size={16} />
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
