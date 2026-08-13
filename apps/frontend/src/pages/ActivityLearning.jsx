import { Fragment, memo, useCallback, useEffect, useRef, useState } from 'react'
import { ArrowLeft, ArrowRight, Check, CheckCircle2, Copy, Info, RefreshCw } from 'lucide-react'
import * as bookLearningApi from '../api/bookLearning'
import * as workspaceApi from '../api/workspace'
import LearningContextDrawer from '../components/LearningContextDrawer'
import ConversationView from '../components/messages/ConversationView'
import Composer from '../components/ui/Composer'
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

const maxComposerHeight = 168 // ≈ 6 行

function messageForTurn(turn) {
  return turn.message_envelope || {
    schema_version: '1.0',
    id: `legacy-${turn.turn_id}`,
    revision: 1,
    conversation_id: 'legacy-book-transcript',
    sequence: turn.turn_number,
    role: 'ASSISTANT',
    timestamp: turn.accepted_at,
    content: turn.reply_text,
    blocks: [],
  }
}

function askFollowUpCapability(turn) {
  const message = turn?.message_envelope
  if (!message || !Array.isArray(message.blocks)) return null
  for (const block of message.blocks) {
    const capability = (block.interactions || []).find(
      (item) => item.action_type === 'ASK_FOLLOW_UP' && item.availability === 'AVAILABLE',
    )
    if (capability) return capability
  }
  return null
}

const AskoraMessage = memo(function AskoraMessage({ turn, copied, onCopy, isFirst, interactionInput, onInvoke, onRequestInput }) {
  return (
    <article className="activity-message activity-message--askora">
      <div className="activity-message__avatar" aria-hidden="true">A</div>
      <div className="activity-message__body">
        <div className="activity-message__meta">
          {isFirst && <span className="activity-message__role">Askora</span>}
          <button
            type="button"
            className="activity-message__copy"
            onClick={() => onCopy(turn)}
            aria-label={copied ? '已复制本条回复' : '复制本条回复'}
          >
            {copied ? <Check size={13} /> : <Copy size={13} />}
            <span>{copied ? '已复制' : '复制'}</span>
          </button>
        </div>
        <div className="activity-message__bubble">
          <ConversationView
            messages={[messageForTurn(turn)]}
            interactionInput={interactionInput}
            onInvoke={onInvoke}
            onRequestInput={onRequestInput}
          />
        </div>
      </div>
    </article>
  )
})

const LearnerMessage = memo(function LearnerMessage({ text }) {
  return (
    <article className="activity-message activity-message--learner">
      <div className="activity-message__body">
        <div className="activity-message__bubble"><p>{text}</p></div>
      </div>
    </article>
  )
})

export default function ActivityLearning({ activityId }) {
  const navigate = useNavigate()
  const [state, setState] = useState({ status: 'loading', lifecycle: null, transcript: null, error: '' })
  const [busy, setBusy] = useState(false)
  const [sending, setSending] = useState(false)
  const [text, setText] = useState('')
  const [pendingText, setPendingText] = useState('')
  const [copiedTurn, setCopiedTurn] = useState('')
  const messagesRef = useRef(null)
  const composerRef = useRef(null)

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

  // 新消息、乐观回显或打字指示器出现时自动滚动到底部。（放在提前 return 之前，保证 Hook 顺序稳定。）
  useEffect(() => {
    const region = messagesRef.current
    if (region) region.scrollTop = region.scrollHeight
  }, [state.transcript?.turns, sending, pendingText])

  // 输入框随内容自动增高（1–6 行）。
  useEffect(() => {
    const el = composerRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${Math.min(el.scrollHeight, maxComposerHeight)}px`
  }, [text])

  const run = async (operation, fallback) => {
    if (busy) return false
    setBusy(true)
    try {
      const result = await operation()
      await load({ quiet: true })
      return result ?? true
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

  const send = async (overrideText, explicitInteraction = null) => {
    if (!transcript) return
    const learnerText = (overrideText != null ? overrideText : text).trim()
    const isSystemStart = turns.length === 0
    if (!isSystemStart && !learnerText) return
    const turnNumber = transcript.next_turn_number
    const lastTurn = turns.length ? turns[turns.length - 1] : null
    const interaction = explicitInteraction || askFollowUpCapability(lastTurn)
    const interactionBlock = interaction && lastTurn?.message_envelope?.blocks.find(
      (block) => (block.interactions || []).some(
        (item) => item.capability_id === interaction.capability_id,
      ),
    )
    if (!isSystemStart) setPendingText(learnerText)
    setSending(true)
    let completed = false
    let operationResult = false
    try {
      operationResult = await run(
        () => {
          if (!isSystemStart && interaction && interactionBlock && lastTurn?.message_envelope) {
            const interactionId = window.crypto?.randomUUID?.()
              || `07500000-0000-4000-8000-${String(turnNumber).padStart(12, '0')}`
            return bookLearningApi.invokeMessageInteraction(
              activityId,
              lastTurn.message_envelope.id,
              {
                schema_version: '1.0',
                interaction_id: interactionId,
                conversation_id: lastTurn.message_envelope.conversation_id,
                message_id: lastTurn.message_envelope.id,
                message_revision: lastTurn.message_envelope.revision,
                block_id: interactionBlock.id,
                capability_id: interaction.capability_id,
                action_type: interaction.action_type,
                expected_owner_versions: interaction.input_refs,
                user_response: { payload: { text: learnerText }, accepted_response_ref: null },
                idempotency_key: commandKey(activityId, `message-interaction-${turnNumber}`, current.version),
                requested_at: new Date().toISOString(),
                correlation_id: lastTurn.message_envelope.trace_references.correlation_id,
              },
            )
          }
          return bookLearningApi.startTeachingRound(activityId, {
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
          })
        },
        '这次教学回应没有完成；活动仍保持进行中，可以重试。',
      )
      completed = operationResult !== false && (
        !interaction || ['ACCEPTED', 'SUCCEEDED'].includes(operationResult?.status)
      )
      if (completed) setText('')
    } finally {
      setSending(false)
      setPendingText('')
    }
    return completed ? operationResult : false
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

  const copyTurn = async (turn) => {
    try {
      await navigator.clipboard.writeText(turn.reply_text)
      setCopiedTurn(turn.turn_id)
      setTimeout(() => setCopiedTurn((id) => (id === turn.turn_id ? '' : id)), 1400)
    } catch { /* 剪贴板不可用时静默忽略 */ }
  }

  const handleComposerKeyDown = (event) => {
    // 中文输入法回车确认候选词时不触发发送。
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault()
      send()
    }
  }

  const inlineError = state.error && (
    <div className="activity-learning__error" role="alert">
      <span>{state.error}</span>
      <button type="button" className="button button--ghost" onClick={() => load()}><RefreshCw size={14} />刷新</button>
    </div>
  )

  return (
    <div className="activity-learning page-stack">
      <header className="activity-learning__header">
        <button type="button" className="button button--ghost" onClick={() => navigate('/learning/plan')}><ArrowLeft size={16} />学习路径</button>
        <div className="activity-learning__header-title">
          <p className="eyebrow">学习活动</p>
          <h1>{activity.title}</h1>
          <p className="activity-learning__header-meta">约 {activity.estimated_duration_minutes} 分钟</p>
        </div>
      </header>

      {!canResume && state.error && <div className="learning-notice learning-notice--error" role="alert">{state.error}<button type="button" className="button button--ghost" onClick={() => load()}><RefreshCw size={15} />刷新</button></div>}

      {canStart && (
        <main className="surface activity-learning__ready">
          <h2>准备开始</h2><p>开始后会固定进入这项计划活动；刷新页面仍可继续。</p>
          <button type="button" className="button button--primary" onClick={start} disabled={busy}>开始学习<ArrowRight size={16} /></button>
        </main>
      )}

      {canResume && transcript && (
        <main className="activity-learning__session">
          <div className="activity-learning__messages" role="log" aria-live="polite" aria-relevant="additions" ref={messagesRef}>
            {inlineError}
            {turns.length ? turns.map((turn, index) => (
              <Fragment key={turn.turn_id}>
                {turn.learner_text ? <LearnerMessage text={turn.learner_text} /> : null}
                <AskoraMessage
                  turn={turn}
                  isFirst={index === 0}
                  copied={copiedTurn === turn.turn_id}
                  onCopy={copyTurn}
                  interactionInput={index === turns.length - 1 ? { text } : null}
                  onInvoke={index === turns.length - 1
                    ? (interaction, payload) => send(payload?.text, interaction)
                    : undefined}
                  onRequestInput={index === turns.length - 1
                    ? () => composerRef.current?.focus()
                    : undefined}
                />
              </Fragment>
            )) : <div className="activity-learning__empty"><h2>从一个聚焦问题开始</h2><p>Askora 会依据当前 TeachingAction 和资料证据开始，不会自行改变计划。</p><button type="button" className="button button--primary" onClick={() => send()} disabled={busy}>进入本次学习<ArrowRight size={16} /></button></div>}
            {sending && pendingText && <LearnerMessage text={pendingText} />}
            {sending && (
              <article className="activity-message activity-message--askora activity-message--typing" aria-label="Askora 正在思考">
                <div className="activity-message__avatar" aria-hidden="true">A</div>
                <div className="activity-message__body">
                  <div className="activity-message__bubble"><span className="typing-dots"><span /><span /><span /></span></div>
                </div>
              </article>
            )}
          </div>
          {turns.length > 0 && (
            <>
              <LearningContextDrawer activityId={activityId} />
              <form className="activity-learning__composer" onSubmit={(event) => { event.preventDefault(); send() }}>
                <Composer
                  id="activity-answer"
                  label="写下你的想法"
                  ref={composerRef}
                  value={text}
                  onChange={(event) => setText(event.target.value)}
                  onKeyDown={handleComposerKeyDown}
                  placeholder="写下你的理解…"
                  disabled={busy}
                  sendDisabled={busy || !text.trim()}
                />
              </form>
            </>
          )}
          {turns.length === 0 && <LearningContextDrawer activityId={activityId} />}
          <div className="activity-learning__finish"><p className="activity-learning__disclaimer"><Info size={14} aria-hidden="true" />完成本项不等于已掌握</p><button type="button" className="button button--secondary" onClick={complete} disabled={busy || !canComplete}><CheckCircle2 size={16} />完成本项</button></div>
        </main>
      )}

      {current.status === 'completed' && (
        <main className="surface activity-learning__complete"><CheckCircle2 size={28} /><h2>本项已完成</h2><p>这不会自动更新掌握度或目标达成状态。</p><button type="button" className="button button--primary" onClick={() => lifecycle.next_activity_ref ? navigate(`/learn/${encodeURIComponent(lifecycle.next_activity_ref.entity_id)}`) : navigate('/learning/plan')}>{lifecycle.next_activity_ref ? '进入下一项' : '返回学习路径'}<ArrowRight size={16} /></button></main>
      )}

      {!canStart && !canResume && current.status !== 'completed' && <main className="surface activity-learning__blocked"><h2>当前活动不可执行</h2><p>{activity.execution.reason_codes.join(' · ') || '请返回学习路径查看最新安排。'}</p></main>}
    </div>
  )
}
