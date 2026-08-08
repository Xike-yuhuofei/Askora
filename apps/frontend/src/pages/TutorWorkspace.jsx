import { lazy, Suspense, useEffect, useRef, useState } from 'react'
import { ArrowLeft, BookOpen, History as HistoryIcon, Send } from 'lucide-react'
import * as dialogApi from '../api/dialog'
import { useNavigate } from '../router'
import './TutorWorkspace.css'

const RichMessage = lazy(() => import('../components/messages/RichMessage'))

export default function TutorWorkspace({ sessionId }) {
  const navigate = useNavigate()
  const [view, setView] = useState({ status: 'loading', session: null, messages: [], sessions: [], error: '' })
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const messagesRef = useRef(null)

  useEffect(() => {
    let cancelled = false
    setView({ status: 'loading', session: null, messages: [], sessions: [], error: '' })
    Promise.all([
      dialogApi.getSession(sessionId),
      dialogApi.getMessages(sessionId),
      dialogApi.getSessions(1, 20),
    ])
      .then(([session, messages, sessions]) => {
        if (!cancelled) {
          const sessionItems = sessions.items || []
          const listItem = sessionItems.find((item) => item.id === sessionId)
          setView({
            status: 'ready',
            session: {
              ...session,
              knowledge_point: session.knowledge_point
                || session.knowledge_point_id
                || listItem?.knowledge_point
                || listItem?.knowledge_point_id,
            },
            messages: messages.items || [],
            sessions: sessionItems,
            error: '',
          })
        }
      })
      .catch((error) => {
        if (!cancelled) {
          const status = error.response?.status
          setView({
            status: status === 401 ? 'unauthorized' : 'error',
            session: null,
            messages: [],
            sessions: [],
            error: status === 404
              ? '这个兼容会话不存在或已经被删除。'
              : status === 403
                ? '你无权访问这个会话。'
                : status === 401
                  ? '登录状态已失效，请重新登录。'
                  : '工作台暂时无法读取，请检查后端服务。',
          })
        }
      })
    return () => { cancelled = true }
  }, [sessionId])

  useEffect(() => {
    const messageRegion = messagesRef.current
    if (messageRegion) messageRegion.scrollTop = messageRegion.scrollHeight
  }, [view.messages, sending])

  const send = async () => {
    const content = input.trim()
    if (!content || sending || view.session?.status !== 'active') return
    const localId = `local-${Date.now()}`
    setSending(true)
    setInput('')
    setView((current) => ({
      ...current,
      error: '',
      messages: [...current.messages, {
        id: localId,
        role: 'user',
        content,
        created_at: new Date().toISOString(),
      }],
    }))
    try {
      const result = await dialogApi.sendMessage(sessionId, content)
      const message = result.message || {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: result.content || '（服务返回为空，请重试）',
        render_payload: null,
        created_at: new Date().toISOString(),
      }
      setView((current) => ({ ...current, messages: [...current.messages, message] }))
    } catch (error) {
      const apiError = error.response?.data?.error
      setInput(content)
      setView((current) => ({
        ...current,
        messages: current.messages.filter((message) => message.id !== localId),
        error: apiError?.message || '消息发送失败，请重试。',
      }))
    } finally {
      setSending(false)
    }
  }

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      send()
    }
  }

  if (view.status === 'loading') {
    return <div className="page-state" role="status"><div className="spinner" /><p>正在打开学习工作台…</p></div>
  }

  if (view.status !== 'ready') {
    return (
      <div className="page-state page-state--error" role="alert">
        <h1>学习工作台</h1>
        <p>{view.error}</p>
        <button type="button" className="button button--secondary" onClick={() => navigate('/history')}>
          返回历史记录
        </button>
      </div>
    )
  }

  const session = view.session
  const isActive = session.status === 'active'

  return (
    <div className="workspace-layout">
      <aside className="workspace-rail" aria-label="会话历史">
        <button type="button" className="workspace-back" onClick={() => navigate('/today')}>
          <ArrowLeft size={16} />
          今天
        </button>
        <div className="workspace-rail__heading">
          <HistoryIcon size={16} />
          <span>最近会话</span>
        </div>
        <nav className="workspace-session-nav">
          {view.sessions.slice(0, 5).map((item) => (
            <button
              type="button"
              key={item.id}
              className={item.id === sessionId ? 'is-active' : ''}
              onClick={() => navigate(`/quick/${encodeURIComponent(item.id)}`)}
            >
              <strong>{item.knowledge_point || item.title || item.subject}</strong>
              <small>{item.status === 'active' ? '进行中' : '只读历史'}</small>
            </button>
          ))}
        </nav>
      </aside>

      <section className="workspace-canvas" aria-labelledby="workspace-title">
        <header className="workspace-header">
          <div>
            <div className="workspace-kicker">
              <span className="status-pill status-pill--compatibility">兼容快速学习</span>
              <span>{session.subject}</span>
            </div>
            <h1 id="workspace-title">{session.knowledge_point || session.topic || session.subject || '学习会话'}</h1>
          </div>
          <button type="button" className="button button--ghost" onClick={() => navigate('/history')}>
            查看历史
          </button>
        </header>

        {view.error && <p className="inline-error" role="alert">{view.error}</p>}

        <div ref={messagesRef} className="workspace-messages" aria-live="polite">
          {view.messages.length === 0 && (
            <div className="workspace-empty">
              <BookOpen size={22} />
              <p>输入你的问题或想法，开始这一轮兼容学习。</p>
            </div>
          )}
          {view.messages.map((message, index) => (
            <article
              key={message.id || `${message.role}-${message.turn_number || index}`}
              className={`workspace-message workspace-message--${message.role}`}
            >
              <div className="workspace-message__meta">{message.role === 'user' ? '你' : 'Askora'}</div>
              <div className="workspace-message__content">
                {message.role === 'assistant' ? (
                  <Suspense fallback={<p>{message.content}</p>}>
                    <RichMessage fallbackText={message.content} payload={message.render_payload} />
                  </Suspense>
                ) : <p>{message.content}</p>}
              </div>
            </article>
          ))}
          {sending && <div className="workspace-thinking" role="status">Askora 正在回应…</div>}
        </div>

        <div className="workspace-composer">
          {!isActive && <p className="inline-notice">该会话已结束，仅可查看历史内容。</p>}
          <div className="composer-box">
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={isActive ? '写下你的问题或思路…' : '会话已结束'}
              aria-label="学习输入"
              rows={2}
              disabled={!isActive || sending}
            />
            <button
              type="button"
              className="composer-send"
              aria-label="发送消息"
              onClick={send}
              disabled={!input.trim() || !isActive || sending}
            >
              <Send size={18} />
            </button>
          </div>
          <p className="composer-hint">兼容会话不等于 LearningActivity；不会生成学习计划或掌握结论。</p>
        </div>
      </section>

      <aside className="workspace-inspector" aria-labelledby="workspace-context-title">
        <p className="eyebrow">只读上下文</p>
        <h2 id="workspace-context-title">学习状态</h2>
        <dl>
          <div><dt>来源</dt><dd>兼容会话</dd></div>
          <div><dt>计划关联</dt><dd>当前不可用</dd></div>
          <div><dt>帮助状态</dt><dd>当前记录不可用</dd></div>
          <div><dt>独立验证</dt><dd>当前记录不可用</dd></div>
        </dl>
        <p className="inspector-note">这里不会从旧 hint level、strategy 或会话轮数推断 canonical TeachingAction、证据或掌握状态。</p>
      </aside>
    </div>
  )
}
