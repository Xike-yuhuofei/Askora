import { lazy, Suspense, useState, useEffect, useRef } from 'react'
import { Send, Plus, Sparkles, Clock, Lightbulb, ChevronRight } from 'lucide-react'
import Sidebar from '../components/Sidebar'
import * as dialogApi from '../api/dialog'
import './Chat.css'

const RichMessage = lazy(() => import('../components/messages/RichMessage'))

const subjects = [
  { id: 'math', name: '数学', icon: '📐', kps: ['一元二次方程', '函数与导数', '概率统计', '几何证明'] },
  { id: 'chinese', name: '语文', icon: '📚', kps: ['文言文阅读', '现代文赏析', '写作技巧', '诗词鉴赏'] },
  { id: 'english', name: '英语', icon: '🌍', kps: ['语法时态', '阅读理解', '写作表达', '词汇积累'] },
  { id: 'physics', name: '物理', icon: '⚛️', kps: ['力学运动', '电磁感应', '光学原理', '热力学'] },
]

export default function Chat() {
  const [sessions, setSessions] = useState([])
  const [activeSession, setActiveSession] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [streaming, setStreaming] = useState(false)
  const [showSubjectPicker, setShowSubjectPicker] = useState(true)
  const [selectedSubject, setSelectedSubject] = useState(null)
  const [pageError, setPageError] = useState('')
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    loadSessions()
  }, [])

  const loadSessions = async () => {
    try {
      const data = await dialogApi.getSessions()
      setSessions(data.items || [])
    } catch {
      setPageError('历史会话加载失败，请检查后端服务')
    }
  }

  const startNewSession = async (subject, kp) => {
    try {
      const session = await dialogApi.createSession(subject, kp)
      setActiveSession(session)
      setSessions((current) => [session, ...current])
      setShowSubjectPicker(false)
      setMessages([])
      setPageError('')
    } catch {
      setPageError('创建会话失败，请检查后端服务。')
    }
  }

  const handleSend = async () => {
    if (!input.trim() || loading || streaming) return

    const content = input.trim()
    const clientMessageId = `local-${Date.now()}`
    const userMsg = {
      id: clientMessageId,
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const data = await dialogApi.sendMessage(activeSession.id, content)
      // 兼容后端两种返回结构：
      // 1) 新结构：{ message: { content, ... }, session, ... }
      // 2) 平结构：{ content: string, ... } 或历史兼容层
      const assistantContent =
        data?.message?.content ??
        data?.content ??
        (typeof data?.message === 'string' ? data.message : '')

      const assistantRole = (data?.message?.role === 'assistant' || !data?.message?.role) ? 'assistant' : data?.message?.role

      setMessages((prev) => [
        ...prev,
        {
          role: assistantRole,
          content: assistantContent || '（服务返回为空，请重试）',
          render_payload: data?.message?.render_payload ?? null,
          timestamp: data?.message?.created_at || new Date().toISOString(),
          moderation: data?.moderation,
        },
      ])
    } catch (err) {
      const errData = err.response?.data?.error
      const msgByCode = {
        'BIZ-0003': '这个会话已经结束，请新建会话后继续。',
      }
      setMessages((prev) => prev.filter((message) => message.id !== clientMessageId))
      setInput(content)
      setPageError(msgByCode[errData?.code] || errData?.message || '消息发送失败，请重试。')
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleSelectSubject = (subject) => {
    setSelectedSubject(subject)
  }

  const handleSelectKp = (kp) => {
    startNewSession(selectedSubject.id, kp)
  }

  return (
    <div className="app-container">
      <Sidebar />

      <main className="main-content">
        <div className="page-header">
          <h1 className="page-title">对话学习</h1>
          <p className="page-subtitle">通过苏格拉底式提问，引导你主动思考</p>
        </div>
        {pageError && <div className="error-msg" role="alert">{pageError}</div>}

        {showSubjectPicker ? (
          <div className="subject-picker">
            <div className="picker-header">
              <Sparkles size={20} />
              <h2>选择学科开始学习</h2>
            </div>

            {!selectedSubject ? (
              <div className="subject-grid">
                {subjects.map((subj) => (
                  <button
                    type="button"
                    key={subj.id}
                    className="subject-card"
                    onClick={() => handleSelectSubject(subj)}
                  >
                    <div className="subject-icon">{subj.icon}</div>
                    <div className="subject-name">{subj.name}</div>
                    <ChevronRight size={16} className="subject-arrow" />
                  </button>
                ))}
              </div>
            ) : (
              <div className="kp-picker">
                <button className="back-btn" onClick={() => setSelectedSubject(null)}>
                  ← 返回学科选择
                </button>
                <h3 style={{ marginBottom: 16 }}>{selectedSubject.icon} {selectedSubject.name} - 选择知识点</h3>
                <div className="kp-grid">
                  {selectedSubject.kps.map((kp) => (
                    <button type="button" key={kp} className="kp-card" onClick={() => handleSelectKp(kp)}>
                      <Lightbulb size={18} />
                      <span>{kp}</span>
                      <ChevronRight size={14} />
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div className="recent-sessions">
              <h3><Clock size={16} /> 最近对话</h3>
              {sessions.length > 0 ? (
                <div className="session-list">
                  {sessions.slice(0, 5).map((s) => (
                    <button
                      type="button"
                      key={s.id}
                      className="session-item"
                      onClick={() => {
                        setActiveSession(s)
                        setShowSubjectPicker(false)
                        dialogApi.getMessages(s.id).then((d) => setMessages(d.items || [])).catch(() => {})
                      }}
                    >
                      <div className="session-title">{s.knowledge_point || s.subject}</div>
                      <div className="session-time">{new Date(s.created_at).toLocaleDateString()}</div>
                    </button>
                  ))}
                </div>
              ) : (
                <p className="empty-text">暂无历史对话</p>
              )}
            </div>
          </div>
        ) : (
          <div className="chat-area">
            <div className="chat-header">
              <div>
                <h2>{activeSession?.knowledge_point || activeSession?.subject}</h2>
                <span className="tag tag-info">{activeSession?.subject}</span>
              </div>
              <button className="btn btn-secondary" onClick={() => setShowSubjectPicker(true)}>
                <Plus size={16} />
                新对话
              </button>
            </div>

            <div className="chat-messages">
              {messages.length === 0 && (
                <div className="empty-state">输入你的问题或想法，开始这一轮学习。</div>
              )}
              {messages.map((msg, i) => (
                <div key={i} className={`message ${msg.role}`}>
                  <div className="message-avatar">
                    {msg.role === 'user' ? '我' : '苏'}
                  </div>
                  <div className="message-bubble">
                    {msg.role === 'assistant' ? (
                      <Suspense fallback={<p>{msg.content}</p>}>
                        <RichMessage fallbackText={msg.content} payload={msg.render_payload} />
                      </Suspense>
                    ) : (
                      <p>{msg.content}</p>
                    )}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="message assistant">
                  <div className="message-avatar">苏</div>
                  <div className="message-bubble thinking">
                    <span className="dot" />
                    <span className="dot" />
                    <span className="dot" />
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <div className="chat-input-area">
              <div className="input-wrapper">
                <textarea
                  className="chat-input"
                  placeholder="输入你的想法..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  rows={1}
                  aria-label="对话输入"
                />
                <button
                  className="send-btn"
                  onClick={handleSend}
                  disabled={!input.trim() || loading}
                  aria-label="发送消息"
                >
                  <Send size={18} />
                </button>
              </div>
              <p className="input-hint">
                AI 生成内容仅供学习参考，请独立思考；系统不会声称未经验证的审核结果
              </p>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
