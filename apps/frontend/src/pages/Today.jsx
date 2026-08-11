import { useEffect, useMemo, useState } from 'react'
import { ArrowRight, BookOpen, Clock3, ChevronDown, ChevronUp, RefreshCw } from 'lucide-react'
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
const activityTypeLabels = {
  learn_new: '学习新内容',
  prerequisite_remediation: '补齐前置知识',
  diagnostic: '诊断活动',
  practice: '练习活动',
  delayed_review: '计划内复习',
  transfer_check: '迁移应用检查',
  metacognitive_review: '学习反思',
}
const activityReasonLabels = {
  PLAN_TARGET_STATE_UNKNOWN: '需要先了解当前基础',
  PLAN_MASTERY_GAP: '当前学习证据显示仍需练习',
  PLAN_PREREQUISITE_UNKNOWN: '前置知识状态尚不明确',
  PLAN_HARD_PREREQUISITE_UNMET: '需要先补齐前置知识',
  PLAN_REVIEW_DUE: '已到建议复习时间',
  PLAN_REVIEW_OVERDUE: '复习建议已到期',
  PLAN_TRANSFER_EVIDENCE_NEEDED: '需要新的迁移应用证据',
}
const viewStateLabels = {
  READY: '计划可用',
  PARTIAL: '部分信息可用',
  EMPTY: '暂无安排',
}

function formatActivityReasons(reasonCodes = []) {
  const mapped = reasonCodes
    .map((reason) => activityReasonLabels[reason])
    .filter(Boolean)
  return mapped.length > 0 ? [...new Set(mapped)].join(' · ') : '推荐依据暂未提供可读说明'
}

function validationCopy(summary) {
  if (!summary) return null
  if (summary.validation_obligation === 'INDEPENDENT_VALIDATION_REQUIRED') {
    return '后续需要一次不依赖提示的独立验证'
  }
  if (summary.validation_obligation === 'NONE') return '当前没有待独立验证要求'
  return '待独立验证状态暂不可用'
}

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
  const [quickStartOpen, setQuickStartOpen] = useState(null)

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
      setState({
        status: 'error',
        payload: null,
        error: '今日学习信息暂时无法读取。',
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

  if (state.status === 'error') {
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
  const plannedActivities = (data.planned_activities || []).slice(0, 3)
  const activeGoal = data.active_goal
  const currentActivity = data.current_activity
  const currentValidationCopy = validationCopy(data.current_evidence_summary)
  const planSource = sourceStatus.find((item) => item.source_system === 'SYS06')
  const multiplePlans = planSource?.reason_codes?.includes('MULTIPLE_CURRENT_PLANS_REQUIRE_GOAL_SCOPE')
  const currentActivityId = currentActivity?.activity_ref?.split(':')[1]
  const activityAction = ['ACTIVE', 'RESUMABLE'].includes(currentActivity?.launch_state)
    ? '继续学习'
    : currentActivity?.launch_state === 'REQUIRES_START_COMMAND'
      ? '开始学习'
      : ''
  const hasCanonicalActivity = Boolean(currentActivity)
  const isQuickStartOpen = quickStartOpen ?? !hasCanonicalActivity

  return (
    <div className="today-page page-stack">
      <header className="page-header page-header--split">
        <div>
          <p className="eyebrow">{data.local_date}</p>
          <h1>今天</h1>
          <p>先看清当前可用信息，再决定下一步学习。</p>
        </div>
        <span className={`status-pill status-pill--${data.view_state.toLowerCase()}`}>
          {viewStateLabels[data.view_state] || '状态未知'}
        </span>
      </header>

      {hasCanonicalActivity ? (
        <section className="surface canonical-next" aria-labelledby="canonical-next-title">
          <div className="canonical-next__content">
            <p className="eyebrow">
              {activeGoal ? `当前目标 · ${activeGoal.title}` : '当前学习活动'}
            </p>
            <h2 id="canonical-next-title">{currentActivity.title}</h2>
            <dl className="today-supporting">
              <div>
                <dt>活动</dt>
                <dd>
                  {activityTypeLabels[currentActivity.type] || '学习活动'}
                  {' · '}
                  {currentActivity.estimated_duration_minutes
                    ? `预计 ${currentActivity.estimated_duration_minutes} 分钟`
                    : '预计时间尚未提供'}
                  {' · '}
                  {activityStatusLabels[currentActivity.status] || currentActivity.status}
                </dd>
              </div>
              <div>
                <dt>安排原因</dt>
                <dd>{formatActivityReasons(currentActivity.reason_codes)}</dd>
              </div>
              {currentValidationCopy && (
                <div>
                  <dt>验证要求</dt>
                  <dd>{currentValidationCopy}</dd>
                </div>
              )}
            </dl>
            <small>活动状态来自 SYS06；完成本项不等于已经掌握。</small>
          </div>
          {activityAction && currentActivityId ? (
            <button
              type="button"
              className="button button--primary"
              onClick={() => navigate(`/learn/${encodeURIComponent(currentActivityId)}`)}
            >
              {activityAction}
              <ArrowRight size={16} />
            </button>
          ) : (
            <div className="canonical-next__unavailable">
              <strong>当前活动暂不可启动</strong>
              <small>请查看当前学习安排或稍后重试。</small>
              <button type="button" className="button button--secondary" onClick={() => navigate('/learning/plan')}>
                查看学习安排
                <ArrowRight size={16} />
              </button>
            </div>
          )}
        </section>
      ) : (
        <section className="surface plan-notice" aria-labelledby="plan-notice-title">
          <div className="plan-notice__icon">
            <BookOpen size={20} />
          </div>
          <div>
            <h2 id="plan-notice-title">
              {multiplePlans
                ? '请选择一个学习目标'
                : data.view_state === 'EMPTY'
                  ? '今天还没有学习安排'
                  : '还没有可展示的当前计划'}
            </h2>
            <p>
              {multiplePlans
                ? '存在多个当前计划，Askora 不会按时间替你猜选。请在学习路径中明确选择目标。'
                : '当前版本不会伪造目标、进度或今日任务。你仍可使用下方兼容入口开始学习。'}
            </p>
          </div>
          {multiplePlans && (
            <button
              type="button"
              className="button button--secondary"
              onClick={() => navigate('/learning/plan')}
            >
              选择目标
            </button>
          )}
        </section>
      )}

      {(plannedActivities.length > 0 || reviews.length > 0) && (
        <div className="today-secondary-grid">
          {plannedActivities.length > 0 && (
            <section className="surface today-upcoming" aria-labelledby="upcoming-title">
              <div className="section-heading section-heading--compact">
                <div>
                  <p className="eyebrow">后续安排</p>
                  <h2 id="upcoming-title">接下来的学习活动</h2>
                </div>
              </div>
              <ol className="upcoming-list">
                {plannedActivities.map((activity) => (
                  <li key={activity.activity_ref}>
                    <div>
                      <strong>{activity.title}</strong>
                      <span className="status-pill">
                        {activityStatusLabels[activity.status] || activity.status}
                      </span>
                    </div>
                    <span>
                      {activityTypeLabels[activity.type] || '学习活动'}
                      {activity.estimated_duration_minutes
                        ? ` · 预计 ${activity.estimated_duration_minutes} 分钟`
                        : ''}
                    </span>
                    <small>{formatActivityReasons(activity.reason_codes)}</small>
                  </li>
                ))}
              </ol>
            </section>
          )}

          {reviews.length > 0 && (
            <section className="surface today-reviews" aria-labelledby="review-title">
              <div className="section-heading section-heading--compact">
                <div>
                  <p className="eyebrow">候选信息</p>
                  <h2 id="review-title">复习建议</h2>
                </div>
                <Clock3 size={18} />
              </div>
              <ul className="review-list">
                {reviews.map((review) => (
                  <li key={review.schedule_ref}>
                    <strong>{review.included_activity_ref ? '已计划的复习建议' : '待复习知识单元'}</strong>
                    <span>建议时间：{formatDue(review.next_due_at)}</span>
                    <small>
                      {review.included_activity_ref ? '已纳入学习计划' : '尚未纳入学习计划'}
                    </small>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>
      )}

      <section
        className={`surface today-quick${hasCanonicalActivity ? '' : ' today-quick--fallback'}`}
        aria-labelledby="quick-title"
      >
        <button
          type="button"
          className="today-quick__toggle"
          aria-expanded={isQuickStartOpen}
          aria-controls="quick-start-content"
          onClick={() => setQuickStartOpen(!isQuickStartOpen)}
        >
          <div>
            <p className="eyebrow">兼容入口</p>
            <h2 id="quick-title">快速学习</h2>
            <small className="today-quick__hint">非计划活动 · 不会生成学习目标或计划</small>
          </div>
          {isQuickStartOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        </button>

        {isQuickStartOpen && (
          <div className="today-quick__body" id="quick-start-content">
            <div className="quick-form">
              <label>
                <span>学科</span>
                <select value={subjectId} onChange={changeSubject}>
                  {quickSubjects.map((subject) => (
                    <option key={subject.id} value={subject.id}>
                      {subject.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                <span>学习主题</span>
                <select value={topic} onChange={(event) => setTopic(event.target.value)}>
                  {selectedSubject.topics.map((item) => (
                    <option key={item} value={item}>
                      {item}
                    </option>
                  ))}
                </select>
              </label>
              <button
                type="button"
                className={`button ${hasCanonicalActivity ? 'button--secondary' : 'button--primary'}`}
                onClick={startCompatibilitySession}
                disabled={creating}
              >
                {creating ? '正在创建…' : '开始兼容学习'}
                {!creating && <ArrowRight size={16} />}
              </button>
            </div>
            {actionError && <p className="inline-error" role="alert">{actionError}</p>}

            {sessions.length > 0 && (
              <div className="recent-block">
                <h3>最近会话</h3>
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
              </div>
            )}
          </div>
        )}
      </section>

      <SourceStatus items={sourceStatus} />
    </div>
  )
}
