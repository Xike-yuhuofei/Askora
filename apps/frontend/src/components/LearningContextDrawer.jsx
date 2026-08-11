import { useEffect, useRef } from 'react'
import { X, Plus, Minus, FolderOpen, Sparkles, BookOpen } from 'lucide-react'
import './LearningContextDrawer.css'

function formatDate(dateString) {
  if (!dateString) return ''
  try {
    return new Date(dateString).toLocaleDateString('zh-CN', {
      month: 'short',
      day: 'numeric',
    })
  } catch {
    return ''
  }
}

export default function LearningContextDrawer({
  open,
  onClose,
  resources = [],
  learningContext = [],
  currentMaterialId = null,
  onAdd,
  onRemove,
  onSetCurrentMaterial,
}) {
  const drawerRef = useRef(null)
  const firstFocusableRef = useRef(null)
  const previousFocusRef = useRef(null)

  useEffect(() => {
    if (!open) return undefined

    previousFocusRef.current = document.activeElement
    const focusTimer = window.setTimeout(() => {
      const firstFocusable = drawerRef.current?.querySelector('button, [tabindex]:not([tabindex="-1"])')
      if (firstFocusable) {
        firstFocusableRef.current = firstFocusable
        firstFocusable.focus()
      }
    }, 50)

    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        event.preventDefault()
        onClose()
        previousFocusRef.current?.focus()
        return
      }
      if (event.key !== 'Tab') return

      const focusables = Array.from(
        drawerRef.current?.querySelectorAll('button, [tabindex]:not([tabindex="-1"])') || [],
      )
      if (!focusables.length) return

      const first = focusables[0]
      const last = focusables[focusables.length - 1]

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => {
      window.clearTimeout(focusTimer)
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [open, onClose])

  if (!open) return null

  const inContextIds = new Set(learningContext.map((item) => item.id))

  return (
    <>
      <button
        type="button"
        className="drawer-overlay"
        aria-label="关闭学习上下文抽屉"
        onClick={() => {
          onClose()
          previousFocusRef.current?.focus()
        }}
      />
      <aside
        ref={drawerRef}
        className="learning-context-drawer"
        role="dialog"
        aria-modal="true"
        aria-label="学习上下文抽屉"
      >
        <header className="learning-context-drawer__header">
          <div>
            <h2>学习上下文</h2>
            <p>选择当前学习要使用的材料</p>
          </div>
          <button
            type="button"
            className="learning-context-drawer__close"
            onClick={() => {
              onClose()
              previousFocusRef.current?.focus()
            }}
            aria-label="关闭抽屉"
          >
            <X size={18} />
          </button>
        </header>

        <section className="learning-context-drawer__section" aria-labelledby="recent-heading">
          <h3 id="recent-heading" className="learning-context-drawer__section-title">
            <FolderOpen size={16} />
            最近资源
          </h3>
          <ul className="learning-context-list">
            {resources.length === 0 ? (
              <li className="learning-context-list__empty">暂无资源</li>
            ) : (
              resources.map((resource) => {
                const inContext = inContextIds.has(resource.id)
                const isCurrent = resource.id === currentMaterialId
                return (
                  <li
                    key={resource.id}
                    className={`learning-context-item ${inContext ? 'is-in-context' : ''} ${isCurrent ? 'is-current' : ''}`}
                  >
                    <div className="learning-context-item__info">
                      <strong>{resource.title}</strong>
                      <span>
                        {resource.type === 'reference' ? '参考文献' : '摘录'}
                        {resource.added_at ? ` · ${formatDate(resource.added_at)}` : ''}
                      </span>
                    </div>
                    <div className="learning-context-item__actions">
                      {inContext ? (
                        <>
                          {!isCurrent && (
                            <button
                              type="button"
                              className="btn btn--ghost btn--small"
                              onClick={() => onSetCurrentMaterial(resource.id)}
                              title="设为当前材料"
                            >
                              <Sparkles size={14} />
                              设为当前
                            </button>
                          )}
                          <button
                            type="button"
                            className="btn btn--ghost btn--small"
                            onClick={() => onRemove(resource.id)}
                            aria-label={`从上下文移除 ${resource.title}`}
                          >
                            <Minus size={14} />
                            移除
                          </button>
                        </>
                      ) : (
                        <button
                          type="button"
                          className="btn btn--ghost btn--small"
                          onClick={() => onAdd(resource)}
                          aria-label={`添加 ${resource.title} 到上下文`}
                        >
                          <Plus size={14} />
                          添加
                        </button>
                      )}
                    </div>
                  </li>
                )
              })
            )}
          </ul>
        </section>

        <section className="learning-context-drawer__section" aria-labelledby="context-heading">
          <h3 id="context-heading" className="learning-context-drawer__section-title">
            <BookOpen size={16} />
            当前学习上下文
            <span className="learning-context-drawer__count">{learningContext.length}</span>
          </h3>
          {learningContext.length === 0 ? (
            <p className="learning-context-drawer__empty">
              还没有添加材料。请从上方最近资源中选择。
            </p>
          ) : (
            <ul className="learning-context-list">
              {learningContext.map((resource) => {
                const isCurrent = resource.id === currentMaterialId
                return (
                  <li
                    key={resource.id}
                    className={`learning-context-item ${isCurrent ? 'is-current' : ''}`}
                  >
                    <div className="learning-context-item__info">
                      <strong>{resource.title}</strong>
                      <span>{resource.type === 'reference' ? '参考文献' : '摘录'}</span>
                    </div>
                    <div className="learning-context-item__actions">
                      {!isCurrent && (
                        <button
                          type="button"
                          className="btn btn--primary btn--small"
                          onClick={() => onSetCurrentMaterial(resource.id)}
                        >
                          <Sparkles size={14} />
                          设为当前
                        </button>
                      )}
                      <button
                        type="button"
                        className="btn btn--ghost btn--small"
                        onClick={() => onRemove(resource.id)}
                        aria-label={`从上下文移除 ${resource.title}`}
                      >
                        <Minus size={14} />
                        移除
                      </button>
                    </div>
                  </li>
                )
              })}
            </ul>
          )}
        </section>

        <footer className="learning-context-drawer__footer">
          <p className="learning-context-drawer__hint">
            同一时刻只能有一个当前材料。当前材料不会被后端自动修改。
          </p>
        </footer>
      </aside>
    </>
  )
}
