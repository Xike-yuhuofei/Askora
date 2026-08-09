import { useEffect, useMemo, useState } from 'react'
import { ArrowRight, BookOpen, Clock3, RefreshCw } from 'lucide-react'
import * as dialogApi from '../api/dialog'
import * as workspaceApi from '../api/workspace'
import SourceStatus from '../components/SourceStatus'
import { useNavigate } from '../router'
import './Today.css'

const quickSubjects = [
  { id: 'math', label: '数学', topics: ['一元二次方程', '函数与导数', '概率统计', '几何证明'] },
  { id: 'chinese', label: '语文', topics: ['文言文阅读', '现代文赏析', '写作技巧', '诗词鉴赏'] },
  { id: 'english', label: '英语', topics: ['语法时态', '阅读理解', '写作表达', '词汇积累'] },
  { id: 'physics', label: '物理', topics: ['力学运动', '电磁感应', '光学原理', '热力学'] },
]

const activityStatusLabels = { planned: '已规划', available: '可开始', active: '进行中', completed: '已完成', skipped: '已跳过', superseded: '已替代' }

function formatDue(value) {
  if (!value) return '时间未知'
  return new Intl.DateTimeFormat('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

export default function Today() {
  const navigate = useNavigate()
  const [state, setState] = useState({ status: 'loading', payload: null, error: '' })
  const [subjectId, setSubjectId] = useState(quickSubjects[0].id)
  const [topic, setTopic] = useState(quickSubjects[0].topics[0])
  const [creating, setCreating] = useState(false)
  const [actionError, setActionError] = useState('')

  const selectedSubject = useMemo(
    () => quickSubjects.find((subject) => subject.id === subjectId) || quickSubjects[0],
    [subjectId],
  )

  const loadToday = async () => {
    setState((current) => ({ ...current, status: 'loading', error: '' }))
    try {
      const payload = await workspaceApi.getTodayWorkspace()
      setState({ status: 'ready', payload, error: '' })
    } catch (error) {
      const unauthorized = error.response?.status === 401
      setState({
        status: unauthorized ? 'unauthorized' : 'error',
        payload: null,
        error: unauthorized ? '登录状态已失效，请重新登录。' : '今日学习信息暂时无法读取。',
      })
    }
  }

  useEffect(() => {
    loadToday()
  }, [])

  const changeSubject = (event) => {
    const nextId = event.target.value
    const nextSubject = quickSubjects.find((subject) => subject.id === nextId) || quickSubjects[0]
    setSubjectId(nextId)
    setTopic(nextSubject.topics[0])
  }

  const startCompatibilitySession = async () => {
    if (creating) return
    setCreating(true)
    setActionError('')
    try {
      const session = await dialogApi.createSession(subjectId, topic)
      navigate(`/quick/${encodeURIComponent(session.id)}`)
    } catch {
      setActionError('兼容会话创建失败，请检查后端服务后重试。')
    } finally {
      setCreating(false)
    }
  }

  if (state.status === 'loading') {
    return (
      <div className="page-state" role="status" aria-live="polite">
        <div className="spinner" />
        <p>正在整理今天的学习信息…</p>
      </div>
    )
  }

  if (state.status === 'error' || state.status === 'unauthorized') {
    return (
      <div className="page-state page-state--error" role="alert">
        <h1>今天</h1>
        <p>{state.error}</p>
        <button type="button" className="button button--secondary" onClick={loadToday}>
          <RefreshCw size={16} />
          重试
        </button>
      </div>
    )
  }

  const { data, source_status: sourceStatus } = state.payload
  const sessions = data.compatibility_quick_start?.recent_sessions || []
  const reviews = data.review_due_candidates || []
  const activeGoal = data.active_goal
  const currentActivity = data.current_activity
  const planSource = sourceStatus.find((item) => item.source_system === 'SYS06')
  const multiplePlans = planSource?.reason_codes?.includes('MULTIPLE_CURRENT_PLANS_REQUIRE_GOAL_SCOPE')

  return (
    <div className="today-page page-stack">
      <header className="page-header page-header--split">
        <div>
          <p className="eyebrow">{data.local_date}</p>
          <h1>今天</h1>
          <p>先看清当前可用信息，再决定下一步学习。</p>
        </div>
        <span className={`status-pill status-pill--${data.view_state.toLowerCase()}`}>
          {data.view_state === 'READY' ? '计划可用' : '部分信息可用'}
        </span>
      </header>

      {activeGoal && currentActivity ? (
        <section className="surface canonical-next" aria-labelledby="canonical-next-title">
          <div className="canonical-next__content">
            <p className="eyebrow">当前目标 · {activeGoal.title}</p>
            <h2 id="canonical-next-title">{currentActivity.title}</h2>
            <p>{currentActivity.estimated_duration_minutes ? `预计 ${currentActivity.estimated_duration_minutes} 分钟` : '预计时间尚未提供'} · {activityStatusLabels[currentActivity.status] || currentActivity.status}</p>
            <small>活动已进入 canonical 计划；启动/恢复关联仍未冻结，因此这里不提供虚假的“继续学习”。</small>
          </div>
          <button type="button" className="button button--primary" onClick={() => navigate('/path')}>查看路径<ArrowRight size={16} /></button>
        </section>
      ) : (
        <section className="plan-notice" aria-labelledby="plan-notice-title">
          <div className="plan-notice__icon"><BookOpen size={20} /></div>
          <div>
            <h2 id="plan-notice-title">{multiplePlans ? '请选择一个学习目标' : '还没有可展示的当前计划'}</h2>
            <p>{multiplePlans ? '存在多个当前计划，Askora 不会按时间替你猜选。请在学习路径中明确选择目标。' : '当前版本不会伪造目标、进度或今日任务。你仍可恢复已有会话，或使用明确标记的兼容入口开始学习。'}</p>
          </div>
          {multiplePlans && <button type="button" className="button button--secondary" onClick={() => navigate('/path')}>选择目标</button>}
        </section>
      )}

      <div className="today-grid">
        <section className="surface today-primary" aria-labelledby="quick-title">
          <div className="section-heading">
            <div>
              <p className="eyebrow">兼容入口</p>
              <h2 id="quick-title">快速学习</h2>
            </div>
            <span className="status-pill status-pill--compatibility">非计划活动</span>
          </div>

          <div className="quick-form">
            <label>
              <span>学科</span>
              <select value={subjectId} onChange={changeSubject}>
                {quickSubjects.map((subject) => (
                  <option key={subject.id} value={subject.id}>{subject.label}</option>
                ))}
              </select>
            </label>
            <label>
              <span>学习主题</span>
              <select value={topic} onChange={(event) => setTopic(event.target.value)}>
                {selectedSubject.topics.map((item) => (
                  <option key={item} value={item}>{item}</option>
                ))}
              </select>
            </label>
            <button
              type="button"
              className="button button--primary"
              onClick={startCompatibilitySession}
              disabled={creating}
            >
              {creating ? '正在创建…' : '开始兼容学习'}
              {!creating && <ArrowRight size={16} />}
            </button>
          </div>
          {actionError && <p className="inline-error" role="alert">{actionError}</p>}

          <div className="recent-block">
            <h3>最近会话</h3>
            {sessions.length ? (
              <ul className="row-list">
                {sessions.map((session) => (
                  <li key={session.session_id}>
                    <button
                      type="button"
                      className="session-row"
                      onClick={() => navigate(`/quick/${encodeURIComponent(session.session_id)}`)}
                    >
                      <span>
                        <strong>{session.knowledge_point_id || session.title || session.subject}</strong>
                        <small>{session.subject} · 兼容会话</small>
                      </span>
                      <ArrowRight size={16} />
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="empty-copy">暂无历史会话。创建兼容会话不会生成学习目标或计划。</p>
            )}
          </div>
        </section>

        <aside className="today-aside">
          <section className="surface" aria-labelledby="review-title">
            <div className="section-heading section-heading--compact">
              <div>
                <p className="eyebrow">复习安排</p>
                <h2 id="review-title">到期复习</h2>
              </div>
              <Clock3 size={18} />
            </div>
            {reviews.length ? (
              <ul className="review-list">
                {reviews.map((review) => (
                  <li key={review.schedule_ref}>
                    <strong>待复习知识单元</strong>
                    <span>建议时间：{formatDue(review.next_due_at)}</span>
                    <small>尚未纳入学习计划</small>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="empty-copy">暂无到期复习。这不表示相关知识已经掌握。</p>
            )}
          </section>
          <SourceStatus items={sourceStatus} />
        </aside>
      </div>
    </div>
  )
}
