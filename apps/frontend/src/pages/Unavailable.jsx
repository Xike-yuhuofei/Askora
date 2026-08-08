import { ArrowLeft, BookOpen, FileQuestion, Route, Target } from 'lucide-react'
import { useNavigate } from '../router'
import './Unavailable.css'

const pageContent = {
  goals: {
    icon: Target,
    eyebrow: 'UI-02',
    title: '学习目标',
    description: '目标只读 Query 尚未进入当前 Slice。这里不会提供没有后端合同的创建或确认按钮。',
  },
  path: {
    icon: Route,
    eyebrow: 'UI-02',
    title: '学习路径',
    description: 'LearningPlan 的 current-user Query 尚未实现，因此不会用会话或前端排序伪造计划。',
  },
  library: {
    icon: BookOpen,
    eyebrow: 'UI-02',
    title: '资料库',
    description: '文档与 KnowledgeUnit 结构化视图将在 UI-02 实现；当前不会把占位数据展示为知识地图。',
  },
  evidence: {
    icon: BookOpen,
    eyebrow: 'UI-02',
    title: '学习证据',
    description: 'canonical SYS03 证据视图将在 UI-02 实现；当前不会回退显示 legacy mastery 指标。',
  },
  activity: {
    icon: Route,
    eyebrow: '需要活动启动合同',
    title: '该学习活动暂不可启动',
    description: '当前没有已冻结的 activity↔session link 与 StartLearningActivity command。系统不会创建兼容会话来冒充该活动。',
  },
  'not-found': {
    icon: FileQuestion,
    eyebrow: '页面不存在',
    title: '没有找到这个页面',
    description: '地址可能已变更。返回“今天”不会创建新会话或改变学习状态。',
  },
}

export default function Unavailable({ kind, resourceId }) {
  const navigate = useNavigate()
  const content = pageContent[kind] || pageContent['not-found']
  const Icon = content.icon
  return (
    <div className="unavailable-page">
      <div className="unavailable-icon"><Icon size={24} /></div>
      <p className="eyebrow">{content.eyebrow}</p>
      <h1>{content.title}</h1>
      <p>{content.description}</p>
      {kind === 'activity' && resourceId && <code>activity ref: {resourceId}</code>}
      <button type="button" className="button button--secondary" onClick={() => navigate('/today')}>
        <ArrowLeft size={16} />
        返回今天
      </button>
    </div>
  )
}
