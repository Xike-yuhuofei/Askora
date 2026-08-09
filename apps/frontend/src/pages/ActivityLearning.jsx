import { useCallback, useEffect, useState } from 'react'
import { ArrowLeft, ArrowRight, CheckCircle2, RefreshCw, Send } from 'lucide-react'
import * as bookLearningApi from '../api/bookLearning'
import * as workspaceApi from '../api/workspace'
import { useNavigate } from '../router'
import './ActivityLearning.css'

function commandKey(activityId, command, version) {
  return `ui02c:${activityId}:${command}:v${version}`
}
function errorMessage(error, fallback) {
  const code = error?.response?.data?.error?.code
  const known = {
    ACTIVITY_STATE_VERSION_CONFLICT: '活动状态刚刚发生变化，已为你刷新。',
    ACTIVITY_NOT_AVAILABLE: '这项活动目前还不能开始。',
    ACTIVITY_NOT_ACTIVE: '这项活动目前不在进行中。',
    ACTIVITY_STALE_OR_SUPERSEDED: '学习计划已经更新，请返回学习路径查看。',
    ACTIVITY_COMPLETION_EVIDENCE_REQUIRED: '需要先完成这项活动要求的学习或评估记录。',
    ACTIVITY_EXECUTION_UNAVAILABLE: '教学服务暂时不可用，活动仍保持原状态。',
    LEGACY_ACTIVITY_STATE_UNMIGRATED: '这项活动尚未完成状态迁移，暂时不能执行。',
  }
  return known[code] || fallback
}

function transcriptRefs(transcript) {
  return (transcript?.turns || []).map((turn) => ({
    entity_type: 'BookLearningTranscriptTurn',
    entity_id: turn.turn_id,
    version: turn.turn_number,
  }))
}

export default function ActivityLearning({ activityId }) {
  const navigate = useNavigate()
  const [state, setState] = useState({ status: 'loading', lifecycle: null, transcript: null, error: '' })
  const [busy, setBusy] = useState(false)
  const [text, setText] = useState('')

  const load = useCallback(async ({ quiet = false } = {}) => {
    if (!quiet) setState((current) => ({ ...current, status: 'loading', error: '' }))
    try {
      const lifecycle = await workspaceApi.getActivityLifecycle(activityId)
      let transcript = null
      if (['available', 'active', 'completed'].includes(lifecycle.data.state.status)) {
        transcript = await bookLearningApi.getTranscript(activityId)
      }
      setState({ status: 'ready', lifecycle, transcript, error: '' })
    } catch (error) {
      setState((current) => ({
        ...current,
        status: 'error',
        error: errorMessage(error, '无法恢复这项学习活动，请稍后重试。'),
      }))
    }
  }, [activityId])

  useEffect(() => { load() }, [load])

  const run = async (operation, fallback) => {
    if (busy) return false
    setBusy(true)
    try {
      await operation()
      await load({ quiet: true })
      return true
    } catch (error) {
      await load({ quiet: true })
      setState((current) => ({ ...current, error: errorMessage(error, fallback) }))
      return false
    } finally {
      setBusy(false)
    }
  }

  if (state.status === 'loading') {
    return <div className="page-state" role="status"><div className="spinner" /><p>正在恢复这项学习活动…</p></div>
  }
  if (!state.lifecycle) {
    return <div className="page-state page-state--error" role="alert"><h1>无法打开学习活动</h1><p>{state.error}</p><button type="button" className="button button--secondary" onClick={() => load()}><RefreshCw size={16} />重试</button></div>
  }

  const lifecycle = state.lifecycle
  const activity = lifecycle.data
  const current = activity.state
  const transcript = state.transcript
  const turns = transcript?.turns || []
  const canStart = activity.execution.can_start
  const canResume = activity.execution.can_resume
  const canComplete = activity.execution.can_complete && turns.length > 0

  const start = () => run(
    () => workspaceApi.startActivity(activityId, {
      schema_version: '1.0',
      activity_id: activityId,
      expected_state_version: current.version,
      idempotency_key: commandKey(activityId, 'start', current.version),
    }),
    '活动暂时没有开始，当前状态已保留。',
  )

  const send = async () => {
    if (!transcript) return
    const learnerText = text.trim()
    const isSystemStart = turns.length === 0
    if (!isSystemStart && !learnerText) return
    const turnNumber = transcript.next_turn_number
    const completed = await run(
      () => bookLearningApi.startTeachingRound(activityId, {
        schema_version: '1.0',
        goal_id: activity.goal_id,
        plan_id: current.plan_id,
        plan_version: current.plan_version,
        activity_id: activityId,
        session_id: transcript.session_id,
        turn_id: isSystemStart ? 'system-start-1' : `learner-turn-${turnNumber}`,
        turn_kind: isSystemStart ? 'system_start' : 'learner',
        learner_text: isSystemStart ? null : learnerText,
        idempotency_key: commandKey(activityId, isSystemStart ? 'system-start' : `turn-${turnNumber}`, current.version),
      }),
      '这次教学回应没有完成；活动仍保持进行中，可以重试。',
    )
    if (completed) setText('')
  }

  const complete = () => run(
    () => workspaceApi.completeActivity(activityId, {
      schema_version: '1.0',
      activity_id: activityId,
      expected_state_version: current.version,
      completion_intent: 'learner_finished',
      transcript_turn_refs: transcriptRefs(transcript),
      idempotency_key: commandKey(activityId, 'complete', current.version),
    }),
    '完成状态没有保存；活动仍保持进行中，可以重试。',
  )

  return (
    <div className="activity-learning page-stack">
      <header className="activity-learning__header">
        <button type="button" className="button button--ghost" onClick={() => navigate('/path')}><ArrowLeft size={16} />学习路径</button>
        <div><p className="eyebrow">Canonical 学习活动</p><h1>{activity.title}</h1><p>预计 {activity.estimated_duration_minutes} 分钟 · 状态 v{current.version}</p></div>
      </header>

      {state.error && <div className="learning-notice learning-notice--error" role="alert">{state.error}<button type="button" className="button button--ghost" onClick={() => load()}><RefreshCw size={15} />刷新</button></div>}

      {canStart && (
        <main className="surface activity-learning__ready">
          <h2>准备开始</h2><p>开始后会固定进入这项计划活动；刷新页面仍可继续。</p>
          <button type="button" className="button button--primary" onClick={start} disabled={busy}>开始学习<ArrowRight size={16} /></button>
        </main>
      )}

      {canResume && transcript && (
        <main className="surface activity-learning__session">
          <div className="activity-learning__messages" aria-live="polite">
            {turns.length ? turns.flatMap((turn) => [
              turn.learner_text ? <article className="activity-message activity-message--learner" key={`${turn.turn_id}:learner`}><strong>你</strong><p>{turn.learner_text}</p></article> : null,
              <article className="activity-message" key={`${turn.turn_id}:askora`}><strong>Askora</strong><p>{turn.reply_text}</p></article>,
            ].filter(Boolean)) : <div className="activity-learning__empty"><h2>从一个聚焦问题开始</h2><p>Askora 会依据当前 TeachingAction 和资料证据开始，不会自行改变计划。</p><button type="button" className="button button--primary" onClick={send} disabled={busy}>进入本次学习</button></div>}
          </div>
          {turns.length > 0 && <form className="activity-learning__composer" onSubmit={(event) => { event.preventDefault(); send() }}><label htmlFor="activity-answer" className="visually-hidden">写下你的想法</label><textarea id="activity-answer" rows={3} value={text} onChange={(event) => setText(event.target.value)} placeholder="写下你的想法或问题…" disabled={busy} /><button type="submit" className="button button--primary" disabled={busy || !text.trim()}><Send size={16} />发送</button></form>}
          <div className="activity-learning__finish"><p>完成本项只表示结束这项计划任务，不等于已掌握。</p>{activity.execution.reason_codes.includes('ACTIVITY_COMPLETION_EVIDENCE_REQUIRED') ? <span>此类型需要评估或复习结果，不能在这里直接完成。</span> : <button type="button" className="button button--secondary" onClick={complete} disabled={busy || !canComplete}><CheckCircle2 size={16} />完成本项</button>}</div>
        </main>
      )}

      {current.status === 'completed' && (
        <main className="surface activity-learning__complete"><CheckCircle2 size={28} /><h2>本项已完成</h2><p>这不会自动更新掌握度或目标达成状态。</p><button type="button" className="button button--primary" onClick={() => lifecycle.next_activity_ref ? navigate(`/learn/${encodeURIComponent(lifecycle.next_activity_ref.entity_id)}`) : navigate('/path')}>{lifecycle.next_activity_ref ? '进入下一项' : '返回学习路径'}<ArrowRight size={16} /></button></main>
      )}

      {!canStart && !canResume && current.status !== 'completed' && <main className="surface activity-learning__blocked"><h2>当前活动不可执行</h2><p>{activity.execution.reason_codes.join(' · ') || '请返回学习路径查看最新安排。'}</p></main>}
    </div>
  )
}
