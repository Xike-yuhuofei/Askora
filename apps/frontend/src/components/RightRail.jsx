import { useCallback, useRef, useState } from 'react'
import { BookOpen, FileText } from 'lucide-react'

export default function RightRail({ defaultOpen = true, workspaceId }) {
  const [isOpen, setIsOpen] = useState(defaultOpen)
  const [activeTab, setActiveTab] = useState('note')
  const toggleRef = useRef(null)

  const toggle = useCallback(() => {
    setIsOpen((prev) => {
      if (prev && toggleRef.current) {
        setTimeout(() => toggleRef.current?.focus(), 0)
      }
      return !prev
    })
  }, [])

  if (!isOpen) {
    return (
      <aside
        className="right-rail right-rail--collapsed"
        aria-label="参考资料与笔记（已折叠）"
      >
        <button
          ref={toggleRef}
          type="button"
          className="right-rail-toggle right-rail-toggle--open"
          aria-label="展开笔记与参考"
          aria-expanded={false}
          onClick={toggle}
        >
          笔记 &amp; 参考
        </button>
      </aside>
    )
  }

  return (
    <aside
      className="right-rail"
      aria-label="参考资料与笔记"
      aria-expanded={true}
      data-workspace-id={workspaceId || undefined}
    >
      <header className="right-rail__header">
        <span className="right-rail__title">参考 &amp; 笔记</span>
        <button
          ref={toggleRef}
          type="button"
          className="right-rail-toggle right-rail-toggle--close"
          aria-label="收起右侧面板"
          onClick={toggle}
        >
          收起
        </button>
      </header>
      <div className="right-rail__tabs" role="tablist" aria-label="右侧面板标签">
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'note'}
          className={`right-rail__tab ${activeTab === 'note' ? 'is-active' : ''}`}
          onClick={() => setActiveTab('note')}
        >
          <FileText size={14} />
          User Note
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'material'}
          className={`right-rail__tab ${activeTab === 'material' ? 'is-active' : ''}`}
          onClick={() => setActiveTab('material')}
        >
          <BookOpen size={14} />
          Current Material
        </button>
      </div>
      <div className="right-rail__content">
        {activeTab === 'note' ? (
          <UserNotePanel />
        ) : (
          <CurrentMaterialPanel />
        )}
      </div>
    </aside>
  )
}

function UserNotePanel() {
  return (
    <div className="notes-panel">
      <div className="notes-panel__header">
        <h3>学习笔记</h3>
        <span className="notes-panel__meta">Workspace-scoped</span>
      </div>
      <p className="right-rail__honest-state" role="status">
        笔记读取与保存尚未接入，本面板不会把浏览器内容冒充已保存笔记。
      </p>
    </div>
  )
}

function CurrentMaterialPanel() {
  return (
    <div className="current-material-panel current-material-panel--empty">
      <BookOpen size={20} />
      <p>当前没有可验证的资料引用。</p>
      <span>只有 canonical Current Material query 接入后才会在这里显示资料。</span>
    </div>
  )
}
