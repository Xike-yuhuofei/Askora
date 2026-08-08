import { lazy, Suspense, useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  ArrowLeft,
  BookOpen,
  CheckCircle2,
  Clock3,
  RefreshCw,
  Route,
  Send,
  ShieldAlert,
  Sparkles,
  Target,
} from 'lucide-react'
import * as bookLearningApi from '../api/bookLearning'
import './BookLearningLaunch.css'

const RichMessage = lazy(() => import('../components/messages/RichMessage'))

const readinessStates = new Set([
  'PROCESSING',
  'CONTENT_PARTIAL',
  'READY_FOR_GOAL',
  'GOAL_CONFIRMATION_REQUIRED',
  'DIAGNOSIS_REQUIRED',
  'DIAGNOSING',
  'PLAN_READY',
  'READY_TO_LEARN',
  'BLOCKED',
])

const stateMeta = {
  PROCESSING: ['资料处理中', '资料仍在安全检查、解析或知识建模中。'],
  CONTENT_PARTIAL: ['资料尚未达到学习条件', '当前资料缺少可执行学习所需的已发布知识或可回放依据。'],
  READY_FOR_GOAL: ['制定学习目标', '用一句可验证的话说明你希望学会什么。'],
  GOAL_CONFIRMATION_REQUIRED: ['确认学习目标', '系统已形成候选目标；确认后才会进入知识映射。'],
  DIAGNOSIS_REQUIRED: ['准备先修诊断', '系统将根据已确认目标建立资料范围并检查必要基础。'],
  DIAGNOSING: ['完成先修诊断', '请独立回答。当前步骤不会把未知状态默认成会或不会。'],
  PLAN_READY: ['生成学习活动', '诊断结果已准备好交给现有学习规划器。'],
  READY_TO_LEARN: ['开始学习', '当前活动已由学习规划器选择，将进入 canonical 教学回合。'],
  BLOCKED: ['当前无法继续', '系统在正确的 owner 边界停下，没有用聊天绕过缺失条件。'],
}

const reasonLabels = {
  CONTENT_PROCESSING_IN_PROGRESS: '资料仍在后台处理中',
  CONTENT_MODEL_PARTIAL: '资料知识模型尚不完整',
  CONTENT_NOT_APPROVED_FOR_LEARNING: '资料尚未通过安全学习条件',
  PUBLISHED_CONTENT_READY_FOR_GOAL: '已有可追溯的已发布知识可用于制定目标',
  LEARNING_GOAL_USER_CONFIRMATION_REQUIRED: '学习目标需要你的明确确认',
  GOAL_KNOWLEDGE_MAPPING_REQUIRED: '目标尚未映射到资料中的知识',
  GOAL_SUBGRAPH_REQUIRED: '目标的先修知识范围尚未建立',
  PREREQUISITE_DIAGNOSTIC_REQUIRED: '需要检查会影响学习路径的先修基础',
  DIAGNOSTIC_ACTIVITY_ACTIVE: '先修诊断正在进行',
  DIAGNOSTIC_COMPLETE_PLAN_GENERATION_REQUIRED: '诊断已完成，可以生成学习计划',
  LEARNING_PLAN_READY: '学习计划已准备好选择下一个活动',
  LEARNING_ACTIVITY_SELECTED: '下一个学习活动已经选定',
  PLAN_NO_FEASIBLE_ACTIVITY: '当前计划没有可执行活动',
  UI02B1_SINGLE_TARGET_REQUIRED: '当前最小版本只支持单一学习目标范围；请把目标写得更聚焦',
}

const activityLabels = {
  learn_new: '学习新内容',
  prerequisite_remediation: '补足先修基础',
  diagnostic: '诊断',
  practice: '练习',
  delayed_review: '延迟复习',
  transfer_check: '迁移检验',
  metacognitive_review: '学习反思',
}

function entityRef(readiness, entityType) {
  return readiness?.owner_refs?.find((item) => item.ref?.entity_type === entityType)?.ref || null
}

function operationKey(documentId, operation, resource = 'current') {
  return `ui02b1:${documentId}:${operation}:${resource}:v1`
}

function teachingSession(activityId) {
  const key = `askora:ui02b1:${activityId}:session-id`
  let value = sessionStorage.getItem(key)
  if (!value) {
    value = globalThis.crypto?.randomUUID?.() || 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(
      /[xy]/g,
      (character) => {
        const random = Math.floor(Math.random() * 16)
        const next = character === 'x' ? random : (random & 0x3) | 0x8
        return next.toString(16)
      },
    )
    sessionStorage.setItem(key, value)
  }
  return value
}

function storedTurn(activityId) {
  const value = Number(sessionStorage.getItem(`askora:ui02b1:${activityId}:next-turn`) || 1)
  return Number.isInteger(value) && value > 0 ? value : 1
}

function responseMessage(error, fallback) {
  if (error?.response?.status === 401) return '登录状态已失效，请重新登录。'
  const code = error?.response?.data?.error?.message
  const known = {
    DIAGNOSTIC_ITEM_UNAVAILABLE: '诊断题暂不可用，系统没有记录为学习者答错。',
    DIAGNOSTIC_NEED_VERSION_CONFLICT: '诊断状态已更新，正在重新读取最新版本。',
    POLICY_RUNTIME_NOT_CONFIGURED: '教学策略运行配置尚未准备好。',
  }
  if (known[code]) return known[code]
  return fallback
}

function assertReadiness(payload) {
  if (String(payload?.schema_version || '').split('.')[0] !== '1') {
    throw new Error('UNSUPPORTED_BOOK_LEARNING_SCHEMA')
  }
  if (!readinessStates.has(payload.state)) throw new Error('UNKNOWN_BOOK_LEARNING_STATE')
  if (!Array.isArray(payload.owner_refs) || !Array.isArray(payload.next_commands)) {
    throw new Error('INVALID_BOOK_LEARNING_READINESS')
  }
  return payload
}

function GoalSummary({ goal }) {
  if (!goal) return <p className="learning-empty">正在读取目标的 owner 版本…</p>
  return (
    <div className="learning-summary">
      <h3>{goal.title}</h3>
      <p>{goal.application_context || `主题：${goal.topic}`}</p>
      <dl>
        <div><dt>目标版本</dt><dd>v{goal.version}</dd></div>
        <div><dt>每周时间</dt><dd>{goal.weekly_time_budget_minutes ? `${goal.weekly_time_budget_minutes} 分钟` : '未设置'}</dd></div>
      </dl>
      <div>
        <strong>希望形成的能力</strong>
        <ul>{goal.target_capabilities?.map((item) => <li key={item}>{item}</li>)}</ul>
      </div>
      <div>
        <strong>成功标准</strong>
        <ul>{goal.success_criteria?.map((item) => <li key={item}>{item}</li>)}</ul>
      </div>
    </div>
  )
}

export default function BookLearningLaunch({ documentId }) {
  const [readiness, setReadiness] = useState(null)
  const [details, setDetails] = useState({})
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [intent, setIntent] = useState('')
  const [applicationContext, setApplicationContext] = useState('')
  const [weeklyBudget, setWeeklyBudget] = useState('60')
  const [deadline, setDeadline] = useState('')
  const [diagnosticAnswer, setDiagnosticAnswer] = useState('')
  const [teachingInput, setTeachingInput] = useState('')
  const [messages, setMessages] = useState([])
  const diagnosticStartedAt = useRef(Date.now())

  const load = useCallback(async ({ quiet = false } = {}) => {
    if (!quiet) setLoading(true)
    setError('')
    try {
      const nextReadiness = assertReadiness(await bookLearningApi.getReadiness(documentId))
      const nextDetails = {}
      const goalRef = entityRef(nextReadiness, 'LearningGoal')
      const goalId = goalRef?.entity_id
      if (goalId) {
        const goalResult = await bookLearningApi.getGoal(goalId)
        nextDetails.goal = goalResult.payload?.goal
      }
      if (
        goalId &&
        nextReadiness.state === 'DIAGNOSIS_REQUIRED' &&
        nextReadiness.next_commands.includes('GeneratePrerequisiteDiagnosis')
      ) {
        nextDetails.mapping = (await bookLearningApi.getMapping(goalId)).payload
      }
      if (
        goalId &&
        (nextReadiness.state === 'DIAGNOSING' ||
          (nextReadiness.state === 'PLAN_READY' && nextReadiness.next_commands.includes('GenerateLearningPlan')))
      ) {
        nextDetails.diagnostic = (await bookLearningApi.getDiagnostic(goalId)).payload
      }
      if (
        goalId &&
        (nextReadiness.state === 'PLAN_READY' || nextReadiness.state === 'READY_TO_LEARN')
      ) {
        nextDetails.plan = (await bookLearningApi.getPlan(goalId)).payload
      }
      if (goalId && nextReadiness.state === 'READY_TO_LEARN') {
        const selectedActivityRef = nextReadiness.owner_refs.find(
          (item) => item.ref?.entity_type === 'LearningActivity' && item.status === 'selected',
        )?.ref
        const activity = nextDetails.plan?.activities?.find(
          (item) => item.activity_id === selectedActivityRef?.entity_id,
        )
        if (!activity || !nextDetails.plan?.plan) {
          throw new Error('SELECTED_ACTIVITY_REF_MISSING')
        }
        nextDetails.selection = { plan: nextDetails.plan.plan, activity }
      }
      setReadiness(nextReadiness)
      setDetails(nextDetails)
    } catch (loadError) {
      setError(responseMessage(loadError, '无法读取这份资料的学习准备状态，请稍后重试。'))
    } finally {
      setLoading(false)
    }
  }, [documentId])

  useEffect(() => { load() }, [load])

  const run = async (command, fallback) => {
    if (busy) return false
    setBusy(true)
    setError('')
    try {
      await command()
      await load({ quiet: true })
      return true
    } catch (commandError) {
      await load({ quiet: true })
      setError(responseMessage(commandError, fallback))
      return false
    } finally {
      setBusy(false)
    }
  }

  const goalRef = entityRef(readiness, 'LearningGoal')
  const goalId = goalRef?.entity_id
  const [stateTitle, stateDescription] = stateMeta[readiness?.state] || ['', '']
  const reasons = useMemo(
    () => readiness?.reason_codes?.map((code) => reasonLabels[code] || code) || [],
    [readiness],
  )

  if (loading) {
    return <div className="page-state" role="status"><div className="spinner" />正在读取资料学习状态…</div>
  }

  if (!readiness) {
    return (
      <div className="page-state page-state--error" role="alert">
        <ShieldAlert size={28} />
        <h1>无法打开资料学习</h1>
        <p>{error}</p>
        <button type="button" className="button button--secondary" onClick={() => load()}><RefreshCw size={16} />重试</button>
      </div>
    )
  }

  const createGoal = () => run(async () => {
    await bookLearningApi.createGoal(documentId, {
      schema_version: '1.0',
      intent: intent.trim(),
      application_context: applicationContext.trim() || null,
      deadline_at: deadline ? new Date(`${deadline}T23:59:59`).toISOString() : null,
      weekly_time_budget_minutes: weeklyBudget ? Number(weeklyBudget) : null,
      idempotency_key: operationKey(documentId, 'goal-create'),
    })
  }, '学习目标没有创建成功，请检查输入后重试。')

  const confirmGoal = () => run(
    () => bookLearningApi.confirmGoal(goalId, {
      schema_version: '1.0',
      confirmed_by_user: true,
      idempotency_key: operationKey(documentId, 'goal-confirm', goalId),
    }),
    '学习目标没有确认成功，请重试。',
  )

  const mapGoal = () => run(
    () => bookLearningApi.mapGoal(goalId, {
      schema_version: '1.0',
      idempotency_key: operationKey(documentId, 'goal-map', goalId),
    }),
    '目标知识范围没有建立成功。',
  )

  const startDiagnostic = () => {
    const mapping = details.mapping?.mapping
    const subgraph = details.mapping?.subgraph
    const targets = mapping?.selected_target_ids || []
    if (targets.length !== 1 || !subgraph) {
      setError(reasonLabels.UI02B1_SINGLE_TARGET_REQUIRED)
      return
    }
    run(
      () => bookLearningApi.startDiagnostic({
        schema_version: '1.0',
        mapping_id: mapping.mapping_id,
        mapping_version: mapping.mapping_version,
        subgraph_id: subgraph.subgraph_id,
        subgraph_version: subgraph.version,
        target_knowledge_unit_id: targets[0],
        max_attempts: 3,
        idempotency_key: operationKey(documentId, 'diagnostic-start', mapping.mapping_id),
      }),
      '先修诊断没有启动；系统没有把这次失败记作答错。',
    )
  }

  const submitDiagnostic = async () => {
    const need = details.diagnostic?.need
    const completed = await run(
      () => bookLearningApi.submitDiagnosticResponse(need.need_id, {
        schema_version: '1.0',
        expected_need_version: need.version,
        response: diagnosticAnswer,
        assistance: {
          hint_level: 0,
          assistance_class: 'none',
          source_visible: false,
          answer_visible: false,
          response_revision: 1,
          response_time_ms: Math.max(1, Date.now() - diagnosticStartedAt.current),
        },
        idempotency_key: operationKey(documentId, 'diagnostic-answer', `${need.need_id}:v${need.version}`),
      }),
      '诊断回答没有提交成功；系统没有把这次故障记作答错。',
    )
    if (completed) {
      setDiagnosticAnswer('')
      diagnosticStartedAt.current = Date.now()
    }
  }

  const generatePlan = () => {
    const need = details.diagnostic?.need
    run(
      () => bookLearningApi.generatePlan({
        schema_version: '1.0',
        need_id: need.need_id,
        idempotency_key: operationKey(documentId, 'plan-generate', need.need_id),
      }),
      '学习计划没有生成成功。',
    )
  }

  const selectActivity = () => run(
    () => bookLearningApi.selectNextActivity({
      schema_version: '1.0',
      goal_id: goalId,
      idempotency_key: operationKey(documentId, 'activity-select', goalId),
    }),
    '下一个学习活动没有选择成功。',
  )

  const sendTeaching = async () => {
    const activity = details.selection?.activity
    const plan = details.selection?.plan
    const text = teachingInput.trim()
    if (!activity || !plan || !text || busy) return
    setBusy(true)
    setError('')
    try {
      const currentTurn = storedTurn(activity.activity_id)
      const result = await bookLearningApi.startTeachingRound(activity.activity_id, {
        schema_version: '1.0',
        goal_id: goalId,
        plan_id: plan.plan_id,
        plan_version: plan.version,
        activity_id: activity.activity_id,
        session_id: teachingSession(activity.activity_id),
        turn_id: `ui02b1-turn-${currentTurn}`,
        learner_text: text,
        idempotency_key: operationKey(documentId, 'teaching', `${activity.activity_id}:turn-${currentTurn}`),
      })
      setMessages((items) => [
        ...items,
        { id: `learner-${currentTurn}`, role: 'learner', text },
        { id: `assistant-${currentTurn}`, role: 'assistant', text: result.reply_text },
      ])
      setTeachingInput('')
      sessionStorage.setItem(
        `askora:ui02b1:${activity.activity_id}:next-turn`,
        String(currentTurn + 1),
      )
    } catch (teachingError) {
      setError(responseMessage(teachingError, '教学回合没有完成；系统没有把这次故障记作学习失败。'))
    } finally {
      setBusy(false)
    }
  }

  const renderStep = () => {
    if (readiness.state === 'PROCESSING' || readiness.state === 'CONTENT_PARTIAL' || readiness.state === 'BLOCKED') {
      return (
        <div className="learning-blocked">
          {readiness.state === 'PROCESSING' ? <Clock3 size={24} /> : <ShieldAlert size={24} />}
          <p>{stateDescription}</p>
          <button type="button" className="button button--secondary" onClick={() => load()}><RefreshCw size={16} />刷新状态</button>
        </div>
      )
    }
    if (readiness.state === 'READY_FOR_GOAL') {
      return (
        <form className="learning-form" onSubmit={(event) => { event.preventDefault(); createGoal() }}>
          <label><span>我希望学会什么</span><textarea value={intent} onChange={(event) => setIntent(event.target.value)} rows={4} maxLength={2000} placeholder="例如：我想掌握本章的核心方法，并能用它分析一个新的案例。" required /></label>
          <label><span>应用场景（可选）</span><input value={applicationContext} onChange={(event) => setApplicationContext(event.target.value)} maxLength={500} placeholder="例如：用于工作中的数据分析" /></label>
          <div className="learning-form__row">
            <label><span>每周学习时间（分钟）</span><input type="number" min="1" max="10080" value={weeklyBudget} onChange={(event) => setWeeklyBudget(event.target.value)} /></label>
            <label><span>目标日期（可选）</span><input type="date" value={deadline} onChange={(event) => setDeadline(event.target.value)} /></label>
          </div>
          <button type="submit" className="button button--primary" disabled={busy || !intent.trim()}><Target size={16} />形成目标候选</button>
        </form>
      )
    }
    if (readiness.state === 'GOAL_CONFIRMATION_REQUIRED') {
      return <><GoalSummary goal={details.goal} /><button type="button" className="button button--primary" onClick={confirmGoal} disabled={busy || !details.goal}><CheckCircle2 size={16} />确认这个学习目标</button></>
    }
    if (readiness.state === 'DIAGNOSIS_REQUIRED') {
      if (readiness.next_commands.includes('MapGoalToKnowledge') || readiness.next_commands.includes('BuildGoalKnowledgeSubgraph')) {
        return <><GoalSummary goal={details.goal} /><button type="button" className="button button--primary" onClick={mapGoal} disabled={busy}><Route size={16} />建立资料学习范围</button></>
      }
      const targets = details.mapping?.mapping?.selected_target_ids || []
      if (targets.length !== 1 && details.mapping) {
        return <div className="learning-blocked"><ShieldAlert size={24} /><p>{reasonLabels.UI02B1_SINGLE_TARGET_REQUIRED}</p></div>
      }
      return <button type="button" className="button button--primary" onClick={startDiagnostic} disabled={busy || !details.mapping}><Sparkles size={16} />开始先修诊断</button>
    }
    if (readiness.state === 'DIAGNOSING') {
      const item = details.diagnostic?.learner_item
      if (!item) return <p className="learning-empty">正在读取学习者可见的诊断题…</p>
      return (
        <form className="diagnostic-card" onSubmit={(event) => { event.preventDefault(); submitDiagnostic() }}>
          <p className="eyebrow">独立回答 · 不显示参考答案</p>
          <h3>{item.prompt}</h3>
          {item.item_type === 'multiple_choice' && item.options?.length ? (
            <fieldset><legend>选择一个答案</legend>{item.options.map((option) => <label key={option}><input type="radio" name="diagnostic-answer" value={option} checked={diagnosticAnswer === option} onChange={(event) => setDiagnosticAnswer(event.target.value)} />{option}</label>)}</fieldset>
          ) : <label><span>你的回答</span><input value={diagnosticAnswer} onChange={(event) => setDiagnosticAnswer(event.target.value)} autoComplete="off" /></label>}
          <button type="submit" className="button button--primary" disabled={busy || !diagnosticAnswer.trim()}>提交独立回答</button>
        </form>
      )
    }
    if (readiness.state === 'PLAN_READY') {
      if (readiness.next_commands.includes('GenerateLearningPlan')) {
        return <button type="button" className="button button--primary" onClick={generatePlan} disabled={busy || !details.diagnostic?.need}><Route size={16} />生成学习计划</button>
      }
      const activities = details.plan?.activities || []
      return <><div className="learning-summary"><h3>计划包含 {activities.length} 个活动</h3><p>活动顺序由 SYS06 学习规划器提供，页面不会重新排序。</p></div><button type="button" className="button button--primary" onClick={selectActivity} disabled={busy}><BookOpen size={16} />选择下一个活动</button></>
    }
    const activity = details.selection?.activity
    return (
      <div className="teaching-panel">
        {activity ? <div className="activity-card"><strong>{activityLabels[activity.type] || activity.type}</strong><span>约 {activity.estimated_duration_minutes} 分钟</span></div> : <p className="learning-empty">正在恢复已选择的学习活动…</p>}
        <div className="teaching-messages" aria-live="polite">
          {messages.length ? messages.map((message) => <article key={message.id} className={`teaching-message teaching-message--${message.role}`}><strong>{message.role === 'learner' ? '你' : 'Askora'}</strong><Suspense fallback={<p>{message.text}</p>}><RichMessage fallbackText={message.text} payload={null} /></Suspense></article>) : <p className="learning-empty">写下你希望先理解的问题，系统会在当前活动与资料证据范围内回应。</p>}
        </div>
        <form className="teaching-composer" onSubmit={(event) => { event.preventDefault(); sendTeaching() }}>
          <label htmlFor="teaching-input" className="visually-hidden">学习问题</label>
          <textarea id="teaching-input" rows={3} value={teachingInput} onChange={(event) => setTeachingInput(event.target.value)} placeholder="例如：请先解释这个概念，并让我尝试举一个例子。" disabled={busy || !activity} />
          <button type="submit" className="button button--primary" disabled={busy || !activity || !teachingInput.trim()}><Send size={16} />发送</button>
        </form>
        <p className="learning-disclosure">当前页面展示本次打开期间的消息；尚无 durable activity↔dialog-session 历史恢复合同。</p>
      </div>
    )
  }

  return (
    <div className="book-learning-page page-stack">
      <header className="page-header page-header--split">
        <div><p className="eyebrow">UI-02B1 · 单份资料学习</p><h1>{stateTitle}</h1><p>{stateDescription}</p></div>
        <a className="button button--secondary" href="#/library"><ArrowLeft size={16} />返回资料库</a>
      </header>
      {error && <p className="inline-error" role="alert">{error}</p>}
      <section className="surface readiness-strip" aria-label="当前学习准备状态">
        <span className={`status-pill readiness-strip__state readiness-strip__state--${readiness.state.toLowerCase()}`}>{readiness.state}</span>
        <ul>{reasons.map((reason) => <li key={reason}>{reason}</li>)}</ul>
        <button type="button" className="button button--ghost" onClick={() => load()} aria-label="刷新学习状态"><RefreshCw size={15} /></button>
      </section>
      <main className="surface learning-step">{renderStep()}</main>
      <details className="surface learning-audit"><summary>查看 owner 引用</summary><ul>{readiness.owner_refs.map((item) => <li key={`${item.owner_system}:${item.ref.entity_type}:${item.ref.entity_id}`}><strong>{item.owner_system}</strong> · {item.ref.entity_type} · v{item.ref.version}</li>)}</ul></details>
    </div>
  )
}
