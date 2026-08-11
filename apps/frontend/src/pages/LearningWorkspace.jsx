import { ArrowRight, BookOpen } from 'lucide-react'
import { useWorkspace } from '../components/WorkspaceContext'
import { useNavigate } from '../router'
import './LearningWorkspace.css'

export default function LearningWorkspace() {
  const navigate = useNavigate()
  const workspace = useWorkspace()
  const current = workspace?.current_workspace

  return (
    <div className="learning-canvas" data-workspace-id={current?.workspace_id}>
      <header className="learning-canvas__header">
        <div className="learning-canvas__title">
          <h1>学习</h1>
          <span className="learning-canvas__workspace">
            {current ? current.display_name : '正在读取当前工作区…'}
          </span>
        </div>
      </header>
      <section className="learning-canvas__empty" aria-labelledby="learning-canvas-empty-title">
        <BookOpen size={28} aria-hidden="true" />
        <h2 id="learning-canvas-empty-title">从当前学习活动继续</h2>
        <p>学习画布不会自行创建会话、目标或计划。请从“今天”进入 canonical 学习活动。</p>
        <button type="button" className="button button--primary" onClick={() => navigate('/today')}>
          查看今天的学习任务
          <ArrowRight size={16} />
        </button>
      </section>
    </div>
  )
}
