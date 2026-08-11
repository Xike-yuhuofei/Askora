import { useCallback, useRef, useState } from 'react'
import { X, BookOpen, FileText } from 'lucide-react'

export default function RightRail({
  defaultOpen = true,
  userNote = '',
  onUserNoteChange,
  currentMaterial = null,
  onClearCurrentMaterial,
}) {
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
          <UserNotePanel value={userNote} onChange={onUserNoteChange} />
        ) : (
          <CurrentMaterialPanel material={currentMaterial} onClear={onClearCurrentMaterial} />
        )}
      </div>
    </aside>
  )
}

function UserNotePanel({ value, onChange }) {
  return (
    <div className="notes-panel">
      <div className="notes-panel__header">
        <h3>学习笔记</h3>
        <span className="notes-panel__meta">Workspace-scoped · 本地保存</span>
      </div>
      <label htmlFor="right-rail-note" className="visually-hidden">学习笔记</label>
      <textarea
        id="right-rail-note"
        className="notes-panel__textarea"
        placeholder="记录你的学习心得、疑问或想法…&#10;&#10;笔记内容仅在本地保存，不会影响 AI 教学决策。"
        value={value}
        onChange={(e) => onChange?.(e.target.value)}
        aria-label="学习笔记"
      />
    </div>
  )
}

function CurrentMaterialPanel({ material, onClear }) {
  if (!material) {
    return (
      <div className="current-material-panel current-material-panel--empty">
        <BookOpen size={20} />
        <p>没有选择当前材料。</p>
        <span>在学习对话中引用材料时，会自动显示在此处。</span>
      </div>
    )
  }

  return (
    <div className="current-material-panel" aria-label="当前材料预览">
      <div className="current-material-panel__header">
        <span className="current-material-panel__label">当前材料</span>
        {onClear && (
          <button
            type="button"
            className="current-material-panel__close"
            onClick={onClear}
            aria-label="取消当前材料"
          >
            <X size={14} />
          </button>
        )}
      </div>
      <div className="current-material-panel__content">
        <h3>{material.title}</h3>
        <p className="current-material-panel__meta">
          {material.type === 'reference' ? '参考文献' : '摘录'}
          {material.source ? ` · ${material.source}` : ''}
        </p>
        <div className="current-material-panel__body">
          <p>此区域为只读模式，用于对照参考。</p>
          {material.snippet && (
            <blockquote className="current-material-panel__snippet">
              {material.snippet}
            </blockquote>
          )}
        </div>
      </div>
      <div className="current-material-panel__footer">
        <span>原材料编辑请前往库页面。</span>
      </div>
    </div>
  )
}
