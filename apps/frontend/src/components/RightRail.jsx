import { useState } from 'react'
import { BookOpen, FileText, PanelRightClose, PanelRightOpen } from 'lucide-react'
import './RightRail.css'

export default function RightRail({ workspaceId, collapsed: collapsedProp, onToggleCollapse }) {
  const [activeTab, setActiveTab] = useState('note')
  const [internalCollapsed, setInternalCollapsed] = useState(false)
  const collapsed = collapsedProp ?? internalCollapsed
  const toggleCollapse = onToggleCollapse ?? (() => setInternalCollapsed((value) => !value))

  return (
    <aside
      className={`right-rail ds-shell-three-panel__right ${collapsed ? 'right-rail--collapsed' : ''}`}
      aria-label={collapsed ? '参考资料与笔记（已收起）' : '参考资料与笔记'}
      data-workspace-id={workspaceId || undefined}
    >
      <header className="right-rail__header">
        <button
          type="button"
          className="right-rail-collapse"
          aria-label={collapsed ? '展开右侧栏' : '收起右侧栏'}
          aria-expanded={!collapsed}
          onClick={toggleCollapse}
        >
          {collapsed ? <PanelRightOpen size={16} /> : <PanelRightClose size={16} />}
        </button>
        <span className="right-rail__title">参考 &amp; 笔记</span>
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
          学习笔记
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={activeTab === 'material'}
          className={`right-rail__tab ${activeTab === 'material' ? 'is-active' : ''}`}
          onClick={() => setActiveTab('material')}
        >
          <BookOpen size={14} />
          当前资料
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
