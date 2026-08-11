import { useState, useRef } from 'react'
import { Send, Sparkles, ChevronRight } from 'lucide-react'
import { useLocation } from '../router'
import { useWorkspaceScoped } from '../components/AppShell'
import LearningContextDrawer from '../components/LearningContextDrawer'
import './LearningWorkspace.css'

const MOCK_RESOURCES = [
  {
    id: 'res-001',
    type: 'reference',
    title: 'Askora 学习手册 · 快速入门',
    source: 'workspace-default',
    added_at: '2025-01-15T10:00:00Z',
  },
  {
    id: 'res-002',
    type: 'snippet',
    title: '关于一元二次方程的笔记摘录',
    source: 'manual',
    added_at: '2025-02-20T14:30:00Z',
  },
  {
    id: 'res-003',
    type: 'reference',
    title: '函数图像分析要点',
    source: 'workspace-default',
    added_at: '2025-03-01T09:00:00Z',
  },
]

const STARTER_SUGGESTIONS = [
  '请帮我理解这个知识点',
  '给我一道例题',
  '我卡住了，给点提示',
  '这和我的薄弱点有什么关系？',
]

export default function LearningWorkspace() {
  const { pathname } = useLocation()
  const workspaceId = pathname.split('/')[2] || 'default'
  const { currentMaterial, onSetCurrentMaterial } = useWorkspaceScoped() || {}

  const [drawerOpen, setDrawerOpen] = useState(false)
  const [learningContext, setLearningContext] = useState([])
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content: '你好！我是 Askora AI，正在为你讲解「一元二次方程」。有什么问题可以直接问我。',
      created_at: new Date().toISOString(),
    },
  ])
  const [input, setInput] = useState('')
  const messagesRef = useRef(null)
  const textareaRef = useRef(null)

  const handleAddResource = (resource) => {
    setLearningContext((prev) => {
      if (prev.find((item) => item.id === resource.id)) return prev
      return [...prev, resource]
    })
  }

  const handleRemoveResource = (resourceId) => {
    setLearningContext((prev) => prev.filter((item) => item.id !== resourceId))
  }

  const handleSetCurrentMaterial = (resourceId) => {
    const resource = learningContext.find((item) => item.id === resourceId)
    if (resource && onSetCurrentMaterial) {
      onSetCurrentMaterial(resource)
    }
  }

  const handleSend = (contentOverride) => {
    const content = (typeof contentOverride === 'string' ? contentOverride : input).trim()
    if (!content) return

    setMessages((prev) => [
      ...prev,
      { id: `user-${Date.now()}`, role: 'user', content, created_at: new Date().toISOString() },
    ])
    setInput('')

    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          id: `assistant-${Date.now()}`,
          role: 'assistant',
          content: `收到你的问题：「${content}」。这是一个很好的切入点，让我来帮你分析…`,
          created_at: new Date().toISOString(),
        },
      ])
    }, 600)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="learning-canvas" data-workspace-id={workspaceId}>
      <header className="learning-canvas__header">
        <div className="learning-canvas__title">
          <h1>学习画布</h1>
          <span className="learning-canvas__workspace">Workspace: {workspaceId}</span>
        </div>
        <button
          type="button"
          className="learning-canvas__drawer-toggle"
          onClick={() => setDrawerOpen((v) => !v)}
          aria-expanded={drawerOpen}
          aria-controls="learning-context-drawer"
        >
          <Sparkles size={14} />
          学习上下文
          <ChevronRight
            size={14}
            style={{ transform: drawerOpen ? 'rotate(90deg)' : 'none', transition: 'transform .16s' }}
          />
        </button>
      </header>

      {drawerOpen && (
        <div className="learning-canvas__drawer-bar" role="region" aria-label="学习上下文概览">
          {learningContext.length === 0 ? (
            <span>当前阶段：开始学习 · 尚未添加材料</span>
          ) : (
            <span>
              当前阶段：进行中 · {learningContext.length} 项材料
              {currentMaterial && ` · 当前：${currentMaterial.title}`}
            </span>
          )}
          <button
            type="button"
            className="learning-canvas__manage-btn"
            onClick={() => setDrawerOpen(true)}
          >
            管理
          </button>
        </div>
      )}

      <div ref={messagesRef} className="learning-canvas__messages" aria-live="polite">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`learning-message learning-message--${msg.role}`}
          >
            {msg.role === 'assistant' && (
              <div className="learning-message__avatar" aria-hidden="true">
                <Sparkles size={16} />
              </div>
            )}
            <div className="learning-message__bubble">
              {msg.content}
            </div>
            {msg.role === 'user' && (
              <div className="learning-message__avatar learning-message__avatar--user" aria-hidden="true">
                你
              </div>
            )}
          </div>
        ))}
      </div>

      {messages.length <= 1 && (
        <div className="learning-canvas__suggestions" aria-label="建议起始问题">
          <span className="learning-canvas__suggestions-label">试试这样开始</span>
          <div className="learning-canvas__suggestions-chips">
            {STARTER_SUGGESTIONS.map((text) => (
              <button
                key={text}
                type="button"
                className="suggestion-chip"
                onClick={() => handleSend(text)}
              >
                {text}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="learning-canvas__composer">
        <div className="composer-box">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="写下你的问题或思路…"
            aria-label="学习输入"
            rows={1}
          />
          <button
            type="button"
            className="composer-send"
            aria-label="发送消息"
            onClick={() => handleSend()}
            disabled={!input.trim()}
          >
            <Send size={18} />
          </button>
        </div>
        <p className="composer-hint">在对话中引用的材料会出现在右侧参考面板。</p>
      </div>

      <LearningContextDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        resources={MOCK_RESOURCES}
        learningContext={learningContext}
        currentMaterialId={currentMaterial?.id || null}
        onAdd={handleAddResource}
        onRemove={handleRemoveResource}
        onSetCurrentMaterial={handleSetCurrentMaterial}
      />
    </div>
  )
}
