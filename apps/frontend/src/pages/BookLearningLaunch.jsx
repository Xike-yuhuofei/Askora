import { lazy, Suspense, useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  ArrowLeft,
  BookOpen,
  Check,
  CheckCircle2,
  Clock3,
  RefreshCw,
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

const automaticCommands = new Set([
  'MapGoalToKnowledge',
  'BuildGoalKnowledgeSubgraph',
  'GeneratePrerequisiteDiagnosis',
  'GenerateLearningPlan',
  'SelectNextLearningActivity',
])

const stateMeta = {
  PROCESSING: ['正在准备这份资料', '完成安全检查和内容整理后，就可以开始制定目标。'],
  CONTENT_PARTIAL: ['这份资料还不能开始学习', '资料中的可用内容仍不完整。你的文件已经保留，可以稍后再试。'],
  READY_FOR_GOAL: ['你想从这份资料中学会什么？', '一句清楚的目标，能帮助 Askora 安排更合适的起点。'],
  GOAL_CONFIRMATION_REQUIRED: ['确认你的学习目标', '看看系统的理解是否准确。确认后，余下准备会自动完成。'],
  DIAGNOSIS_REQUIRED: ['正在安排学习起点', 'Askora 正在整理学习范围，并准备必要的基础检查。'],
  DIAGNOSING: ['先看看你的起点', '这不是考试，也不计分；回答会用来减少不必要的重复学习。'],
  PLAN_READY: ['正在安排第一节学习', 'Askora 正在从计划中选择现在最值得做的一小步。'],
  READY_TO_LEARN: ['本次学习已经准备好', '从一个聚焦的问题开始，预计十几分钟完成。'],
  BLOCKED: ['暂时无法继续', '系统没有绕过缺失条件。你的资料和已完成进度仍然保留。'],
}

const activityLabels = {
  learn_new: '理解一个新概念',
  prerequisite_remediation: '补足一个必要基础',
  diagnostic: '确认学习起点',
  practice: '做一次应用练习',
  delayed_review: '完成一次延迟复习',
  transfer_check: '把知识用到新情境',
  metacognitive_review: '回顾自己的学习方法',
}

function entityRef(readiness, entityType) {
  return readiness?.owner_refs?.find((item) => item.ref?.entity_type === entityType)?.ref || null
}

function selectedActivityRef(readiness) {
  return readiness?.owner_refs?.find(
    (item) => item.ref?.entity_type === 'LearningActivity' && item.status === 'selected',
  )?.ref || null
}

function operationKey(documentId, operation, resource = 'current') {
  return `ui02b2:${documentId}:${operation}:${resource}:v1`
}

function readinessFingerprint(readiness, command) {
  const preferredType = {
    MapGoalToKnowledge: 'LearningGoal',
    BuildGoalKnowledgeSubgraph: 'GoalKnowledgeMapping',
    GeneratePrerequisiteDiagnosis: 'GoalKnowledgeMapping',
    GenerateLearningPlan: 'DiagnosticNeed',
    SelectNextLearningActivity: 'LearningPlan',
  }[command]
  const item = readiness.owner_refs.find((value) => value.ref.entity_type === preferredType)
  if (!item) return `${readiness.state}:${command}:missing-owner-ref`
  return `${readiness.state}:${command}:${item.ref.entity_id}:v${item.ref.version}`
}

function responseMessage(error, fallback) {
  const code = error?.response?.data?.error?.message
  const known = {
    DIAGNOSTIC_ITEM_UNAVAILABLE: '基础检查题暂时不可用。这次故障不会被记录成你的错误。',
    DIAGNOSTIC_NEED_VERSION_CONFLICT: '学习起点刚刚发生变化，已为你读取最新进度。',
    POLICY_RUNTIME_NOT_CONFIGURED: '教学服务尚未准备好，你的学习进度已经保留。',
    BOOK_LEARNING_USER_INPUT_REQUIRED: '现在需要你的输入，系统没有替你作答。',
    BOOK_SYSTEM_START_ALREADY_ACCEPTED: '本次学习已经开始，正在恢复已有内容。',
  }
  return known[code] || fallback
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

function assertTranscript(payload) {
  if (String(payload?.schema_version || '').split('.')[0] !== '1') {
    throw new Error('UNSUPPORTED_BOOK_TRANSCRIPT_SCHEMA')
  }
  if (!payload?.session_id || !Array.isArray(payload.turns) || !payload.activity_ref) {
    throw new Error('INVALID_BOOK_TRANSCRIPT')
  }
  return payload
}

function GoalSummary({ goal }) {
  if (!goal) return <p className="learning-empty">正在恢复你的目标…</p>
  return (
    <div className="learning-summary learning-summary--goal">
      <div className="learning-summary__icon"><Target size={20} /></div>
      <div>
        <h3>{goal.title}</h3>
        {goal.application_context && <p>{goal.application_context}</p>}
        <ul>
          {goal.target_capabilities?.slice(0, 3).map((item) => <li key={item}>{item}</li>)}
        </ul>
        <p className="learning-summary__meta">
          {goal.weekly_time_budget_minutes ? `每周约 ${goal.weekly_time_budget_minutes} 分钟` : '按你的节奏学习'}
        </p>
      </div>
    </div>
  )
}

function LearningProgress({ state }) {
  const activeIndex = state === 'READY_FOR_GOAL' || state === 'GOAL_CONFIRMATION_REQUIRED'
    ? 0
    : state === 'DIAGNOSIS_REQUIRED' || state === 'DIAGNOSING'
      ? 1
      : 2
  const labels = ['目标', '起点', '本次学习']
  return (
    <ol className="learning-progress" aria-label="学习准备进度">
      {labels.map((label, index) => (
        <li
          className={index < activeIndex ? 'is-complete' : index === activeIndex ? 'is-current' : ''}
          key={label}
          aria-current={index === activeIndex ? 'step' : undefined}
        >
          <span>{index < activeIndex ? <Check size={14} /> : index + 1}</span>
          {label}
        </li>
      ))}
    </ol>
  )
}

function EvidenceDisclosure({ evidence }) {
  if (!evidence?.length) return null
  return (
    <details className="turn-evidence">
      <summary>依据资料 · {evidence.length} 处</summary>
      <ol>
        {evidence.map((item) => (
          <li key={item.evidence_id}>
            <p>{item.excerpt}</p>
            <small>{item.pedagogical_role} · 已连接到原文位置</small>
          </li>
        ))}
      </ol>
    </details>
  )
}

export default function BookLearningLaunch({ documentId }) {
  const [readiness, setReadiness] = useState(null)
  const [details, setDetails] = useState({})
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [advancing, setAdvancing] = useState(false)
  const [error, setError] = useState('')
  const [intent, setIntent] = useState('')
  const [applicationContext, setApplicationContext] = useState('')
  const [weeklyBudget, setWeeklyBudget] = useState('60')
  const [deadline, setDeadline] = useState('')
  const [diagnosticAnswer, setDiagnosticAnswer] = useState('')
  const [teachingInput, setTeachingInput] = useState('')
  const diagnosticStartedAt = useRef(Date.now())
  const advanceAttempts = useRef(new Set())

  const load = useCallback(async ({ quiet = false } = {}) => {
    if (!quiet) setLoading(true)
    try {
      const nextReadiness = assertReadiness(await bookLearningApi.getReadiness(documentId))
      const nextDetails = {}
      const goalId = entityRef(nextReadiness, 'LearningGoal')?.entity_id
      if (goalId) {
        nextDetails.goal = (await bookLearningApi.getGoal(goalId)).payload?.goal
      }
      if (goalId && nextReadiness.state === 'DIAGNOSING') {
        nextDetails.diagnostic = (await bookLearningApi.getDiagnostic(goalId)).payload
      }
      if (goalId && (nextReadiness.state === 'PLAN_READY' || nextReadiness.state === 'READY_TO_LEARN')) {
        nextDetails.plan = (await bookLearningApi.getPlan(goalId)).payload
      }
      if (goalId && nextReadiness.state === 'READY_TO_LEARN') {
        const activityRef = selectedActivityRef(nextReadiness)
        const activity = nextDetails.plan?.activities?.find(
          (item) => item.activity_id === activityRef?.entity_id,
        )
        if (!activity || !nextDetails.plan?.plan) throw new Error('SELECTED_ACTIVITY_REF_MISSING')
        nextDetails.selection = { plan: nextDetails.plan.plan, activity }
        nextDetails.transcript = assertTranscript(
          await bookLearningApi.getTranscript(activity.activity_id),
        )
      }
      setReadiness(nextReadiness)
      setDetails(nextDetails)
      setError('')
    } catch (loadError) {
      setError(responseMessage(loadError, '无法恢复这份资料的学习进度，请稍后重试。'))
    } finally {
      setLoading(false)
    }
  }, [documentId])

  useEffect(() => { load() }, [load])

  useEffect(() => {
    if (!readiness || loading || busy || advancing) return
    const commands = readiness.next_commands.filter((command) => automaticCommands.has(command))
    if (commands.length !== 1) return
    const command = commands[0]
    const fingerprint = readinessFingerprint(readiness, command)
    if (advanceAttempts.current.has(fingerprint)) return
    if (advanceAttempts.current.size >= 6) {
      setError('准备步骤没有在预期范围内完成。你的进度已经保留，请重试。')
      return
    }
    advanceAttempts.current.add(fingerprint)
    setAdvancing(true)
    setError('')
    bookLearningApi.advance(documentId, {
      schema_version: '1.0',
      idempotency_key: operationKey(documentId, 'advance', fingerprint),
    }).then(
      () => load({ quiet: true }),
      async (advanceError) => {
        await load({ quiet: true })
        setError(responseMessage(advanceError, '学习准备暂时没有完成。已完成的进度不会丢失。'))
      },
    ).finally(() => setAdvancing(false))
  }, [advancing, busy, documentId, load, loading, readiness])

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

  const retry = () => {
    advanceAttempts.current.clear()
    load()
  }

  const goalId = entityRef(readiness, 'LearningGoal')?.entity_id
  const [stateTitle, stateDescription] = stateMeta[readiness?.state] || ['', '']
  const reasons = useMemo(() => readiness?.reason_codes || [], [readiness])
  const lastModelExecution = details.transcript?.turns?.at(-1)?.model_execution || null

  if (loading) {
    return <div className="page-state" role="status"><div className="spinner" />正在恢复你的学习进度…</div>
  }

  if (!readiness) {
    return (
      <div className="page-state page-state--error" role="alert">
        <ShieldAlert size={28} />
        <h1>暂时无法打开这份资料</h1>
        <p>{error}</p>
        <button type="button" className="button button--secondary" onClick={retry}><RefreshCw size={16} />重试</button>
      </div>
    )
  }

  const openCanonicalGoalDraft = (goal = null) => {
    const params = new URLSearchParams({ source_document_id: documentId })
    const title = goal?.title || intent.trim()
    if (title) params.set('title', title)
    if (title) params.set('topic', goal?.topic || title)
    const context = goal?.application_context || applicationContext.trim()
    if (context) params.set('application_context', context)
    const budget = goal?.weekly_time_budget_minutes || weeklyBudget
    if (budget) params.set('weekly_time_budget_minutes', String(budget))
    if (deadline) params.set('deadline', deadline)
    window.location.hash = `#/goals/new?${params.toString()}`
  }

  const confirmLegacyGoal = () => run(
    () => bookLearningApi.confirmGoal(goalId, {
      schema_version: '1.0',
      confirmed_by_user: true,
      idempotency_key: operationKey(documentId, 'goal-confirm', goalId),
    }),
    '旧版学习目标没有确认成功，请迁移到新版草稿后重试。',
  )

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
      '回答没有提交成功。这次故障不会被记录成你的错误。',
    )
    if (completed) {
      setDiagnosticAnswer('')
      diagnosticStartedAt.current = Date.now()
    }
  }

  const startLesson = () => {
    const activity = details.selection?.activity
    if (!activity) return
    window.location.hash = `#/learn/${encodeURIComponent(activity.activity_id)}`
  }

  const sendTeaching = async () => {
    const activity = details.selection?.activity
    const plan = details.selection?.plan
    const transcript = details.transcript
    const text = teachingInput.trim()
    if (!activity || !plan || !transcript || !text) return
    const turnNumber = transcript.next_turn_number
    const completed = await run(
      () => bookLearningApi.startTeachingRound(activity.activity_id, {
        schema_version: '1.0',
        goal_id: goalId,
        plan_id: plan.plan_id,
        plan_version: plan.version,
        activity_id: activity.activity_id,
        session_id: transcript.session_id,
        turn_id: `learner-turn-${turnNumber}`,
        turn_kind: 'learner',
        learner_text: text,
        idempotency_key: operationKey(documentId, 'teaching', `${activity.activity_id}:turn-${turnNumber}`),
      }),
      '这次回应没有完成。你的已有学习记录已经保留。',
    )
    if (completed) setTeachingInput('')
  }

  const renderPreparation = () => (
    <div className="learning-preparing" role="status" aria-live="polite">
      <span className="learning-preparing__orb"><Sparkles size={23} /></span>
      <h2>{stateTitle}</h2>
      <p>{stateDescription}</p>
      <div className="learning-preparing__line" aria-hidden="true"><span /></div>
    </div>
  )

  const renderTeaching = () => {
    const activity = details.selection?.activity
    const transcript = details.transcript
    if (!activity || !transcript) return <p className="learning-empty">正在恢复本次学习…</p>
    if (!transcript.turns.length) {
      return (
        <div className="lesson-ready">
          <span className="lesson-ready__icon"><BookOpen size={26} /></span>
          <p className="eyebrow">为你安排的下一步</p>
          <h2>{activityLabels[activity.type] || '继续学习'}</h2>
          <p>Askora 会先提出一个聚焦的问题，再根据你的回答继续。</p>
          <div className="lesson-ready__time"><Clock3 size={16} />约 {activity.estimated_duration_minutes} 分钟</div>
          <button type="button" className="button button--primary button--prominent" onClick={startLesson} disabled={busy}>
            <BookOpen size={17} />开始本次学习
          </button>
        </div>
      )
    }
    return (
      <div className="teaching-panel">
        <div className="activity-card">
          <div><small>本次学习</small><strong>{activityLabels[activity.type] || activity.type}</strong></div>
          <span><Clock3 size={14} />约 {activity.estimated_duration_minutes} 分钟</span>
        </div>
        <div className="teaching-messages" aria-live="polite">
          {transcript.turns.flatMap((turn) => {
            const items = []
            if (turn.learner_text) {
              items.push(
                <article key={`${turn.turn_id}:learner`} className="teaching-message teaching-message--learner">
                  <strong>你</strong><p>{turn.learner_text}</p>
                </article>,
              )
            }
            items.push(
              <article key={`${turn.turn_id}:assistant`} className="teaching-message teaching-message--assistant">
                <strong>Askora</strong>
                <Suspense fallback={<p>{turn.reply_text}</p>}>
                  <RichMessage fallbackText={turn.reply_text} payload={null} />
                </Suspense>
                <EvidenceDisclosure evidence={turn.evidence} />
              </article>,
            )
            return items
          })}
        </div>
        <form className="teaching-composer" onSubmit={(event) => { event.preventDefault(); sendTeaching() }}>
          <label htmlFor="teaching-input" className="visually-hidden">写下你的想法或问题</label>
          <textarea
            id="teaching-input"
            rows={3}
            value={teachingInput}
            onChange={(event) => setTeachingInput(event.target.value)}
            placeholder="写下你的想法或问题…"
            disabled={busy}
          />
          <button type="submit" className="button button--primary" disabled={busy || !teachingInput.trim()} aria-label="发送学习回答">
            <Send size={16} />发送
          </button>
        </form>
        <p className="learning-disclosure"><CheckCircle2 size={14} />学习记录已保存，刷新页面也可以继续。</p>
      </div>
    )
  }

  const renderStep = () => {
    if (readiness.state === 'PROCESSING' || readiness.state === 'CONTENT_PARTIAL' || readiness.state === 'BLOCKED') {
      return (
        <div className="learning-blocked">
          {readiness.state === 'PROCESSING' ? <Clock3 size={25} /> : <ShieldAlert size={25} />}
          <h2>{stateTitle}</h2><p>{stateDescription}</p>
          <button type="button" className="button button--secondary" onClick={retry}><RefreshCw size={16} />重新检查</button>
        </div>
      )
    }
    if (readiness.state === 'READY_FOR_GOAL') {
      return (
        <form className="learning-form" onSubmit={(event) => { event.preventDefault(); openCanonicalGoalDraft() }}>
          <div className="learning-form__intro"><h2>{stateTitle}</h2><p>{stateDescription}</p></div>
          <label><span>我的学习目标</span><textarea value={intent} onChange={(event) => setIntent(event.target.value)} rows={4} maxLength={2000} placeholder="例如：掌握这本书的核心方法，并能用它分析一个新的案例。" required autoFocus /></label>
          <label><span>我准备用在（可选）</span><input value={applicationContext} onChange={(event) => setApplicationContext(event.target.value)} maxLength={500} placeholder="例如：工作中的数据分析" /></label>
          <details className="learning-form__more">
            <summary>更多选项</summary>
            <div className="learning-form__row">
              <label><span>每周学习时间</span><div className="input-with-suffix"><input type="number" min="1" max="10080" value={weeklyBudget} onChange={(event) => setWeeklyBudget(event.target.value)} /><span>分钟</span></div></label>
              <label><span>希望完成的日期</span><input type="date" value={deadline} onChange={(event) => setDeadline(event.target.value)} /></label>
            </div>
          </details>
          <button type="submit" className="button button--primary button--prominent" disabled={busy || !intent.trim()}><Sparkles size={16} />继续</button>
        </form>
      )
    }
    if (readiness.state === 'GOAL_CONFIRMATION_REQUIRED') {
      return (
        <div className="goal-confirmation">
          <div><h2>{stateTitle}</h2><p>{stateDescription}</p></div>
          <GoalSummary goal={details.goal} />
          <button type="button" className="button button--primary button--prominent" onClick={confirmLegacyGoal} disabled={busy || !details.goal}><CheckCircle2 size={17} />确认并准备学习</button>
          <button type="button" className="button button--secondary" onClick={() => openCanonicalGoalDraft(details.goal)} disabled={busy || !details.goal}>迁移到新版目标草稿</button>
          <p className="goal-confirmation__note">新目标默认进入新版草稿；这里仅保留已有旧候选的兼容确认。</p>
        </div>
      )
    }
    if (readiness.state === 'DIAGNOSIS_REQUIRED' || readiness.state === 'PLAN_READY') {
      return renderPreparation()
    }
    if (readiness.state === 'DIAGNOSING') {
      const item = details.diagnostic?.learner_item
      if (!item) return <p className="learning-empty">正在恢复基础检查…</p>
      return (
        <form className="diagnostic-card" onSubmit={(event) => { event.preventDefault(); submitDiagnostic() }}>
          <div><p className="eyebrow">不计分 · 用于调整学习起点</p><h2>{item.prompt}</h2></div>
          {item.item_type === 'multiple_choice' && item.options?.length ? (
            <fieldset><legend>选择一个答案</legend>{item.options.map((option) => <label key={option}><input type="radio" name="diagnostic-answer" value={option} checked={diagnosticAnswer === option} onChange={(event) => setDiagnosticAnswer(event.target.value)} />{option}</label>)}</fieldset>
          ) : <label><span>你的回答</span><input value={diagnosticAnswer} onChange={(event) => setDiagnosticAnswer(event.target.value)} autoComplete="off" autoFocus /></label>}
          <button type="submit" className="button button--primary button--prominent" disabled={busy || !diagnosticAnswer.trim()}>提交并继续</button>
        </form>
      )
    }
    return renderTeaching()
  }

  return (
    <div className="book-learning-page page-stack">
      <header className="book-learning-header">
        <a className="book-learning-back" href="#/library" aria-label="返回资料库"><ArrowLeft size={18} />资料库</a>
        <div><p className="eyebrow">资料学习</p><h1>{details.goal?.title || '开始一段有目标的学习'}</h1></div>
      </header>
      <LearningProgress state={readiness.state} />
      {(error || advancing) && (
        <div className={error ? 'learning-notice learning-notice--error' : 'learning-notice'} role={error ? 'alert' : 'status'}>
          {error || '正在为你准备下一步…'}
          {error && <button type="button" className="button button--ghost" onClick={retry}><RefreshCw size={15} />重试</button>}
        </div>
      )}
      <main className="surface learning-step">{renderStep()}</main>
      <details className="learning-technical">
        <summary>技术详情</summary>
        <p>状态：{readiness.state}</p>
        {lastModelExecution && (
          <p>
            模型执行：{lastModelExecution.mode} · {lastModelExecution.provider || 'local'} · {lastModelExecution.model || 'template'} · {lastModelExecution.prompt_version}
          </p>
        )}
        <ul>{reasons.map((reason) => <li key={reason}>{reason}</li>)}</ul>
        <ul>{readiness.owner_refs.map((item, index) => (
          <li key={`${item.owner_system}:${item.ref.entity_type}:${item.ref.entity_id}:${item.ref.version}:${item.status}:${index}`}>
            {item.owner_system} · {item.ref.entity_type} · v{item.ref.version}
          </li>
        ))}</ul>
      </details>
    </div>
  )
}
