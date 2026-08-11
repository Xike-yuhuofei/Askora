import { useState } from 'react'

const commandByAction = {
  ASK_FOLLOW_UP: 'SYS08.BookLearningAskFollowUpV1',
  INSPECT_SOURCE: 'SYS02.InspectSourceV1',
  SUBMIT_ATTEMPT: 'SYS04.SubmitAttemptV1',
  REQUEST_HINT: 'SYS08.RequestHintV1',
  REQUEST_EXPLANATION: 'SYS08.RequestExplanationV1',
  START_ACTIVITY: 'SYS06.StartLearningActivityV1',
}

export function isDispatchableInteraction(interaction) {
  return Boolean(
    interaction &&
    typeof interaction.id === 'string' &&
    typeof interaction.capability_id === 'string' &&
    Object.hasOwn(commandByAction, interaction.action_type) &&
    interaction.command_contract_ref === commandByAction[interaction.action_type] &&
    interaction.availability === 'AVAILABLE' &&
    typeof interaction.label === 'string' && interaction.label.length > 0 &&
    Array.isArray(interaction.input_refs) &&
    interaction.requires_idempotency_key === true,
  )
}

export default function InteractiveElement({ interaction, inputPayload, onInvoke, onRequestInput }) {
  const [status, setStatus] = useState('idle')
  if (!isDispatchableInteraction(interaction)) return null
  if (!onInvoke && !onRequestInput) return null

  const requiresText = interaction.action_type === 'ASK_FOLLOW_UP'
  const hasText = typeof inputPayload?.text === 'string' && inputPayload.text.trim().length > 0

  const activate = async () => {
    if (status === 'submitting') return
    if (requiresText && !hasText) {
      onRequestInput?.(interaction)
      return
    }
    if (!onInvoke) return
    setStatus('submitting')
    try {
      const result = await onInvoke(interaction, inputPayload || null)
      if (result === false || (result?.status && !['ACCEPTED', 'SUCCEEDED'].includes(result.status))) {
        throw new Error('owner interaction did not succeed')
      }
      setStatus('succeeded')
    } catch {
      setStatus('failed')
    }
  }

  return (
    <>
      <button
        type="button"
        className="learning-message-action"
        onClick={activate}
        disabled={status === 'submitting' || status === 'succeeded'}
        aria-busy={status === 'submitting'}
      >
        {status === 'submitting' && '正在提交…'}
        {status === 'succeeded' && `已完成：${interaction.label}`}
        {status === 'failed' && `重试：${interaction.label}`}
        {status === 'idle' && interaction.label}
      </button>
      {status === 'failed' && (
        <span className="learning-message-action-status" role="status">
          操作未完成，内容与学习状态均未改变。
        </span>
      )}
    </>
  )
}
