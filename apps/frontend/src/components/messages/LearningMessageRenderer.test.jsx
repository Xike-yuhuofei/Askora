import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import MessageRenderer from './MessageRenderer'

const metadata = {
  schema_version: '1.0',
  semantic_role: 'test',
  provenance: {
    mode: 'NOT_APPLICABLE', source_refs: [], source_span_refs: [],
    evidence_bundle_ref: null, generated_by_ref: null,
  },
  owner_refs: [], availability: 'READY', reason_codes: [], accessibility_label: null,
}

const interaction = {
  id: 'ask-follow-up', capability_id: 'ask-follow-up-v1', semantic_primitive: 'ACTION',
  action_type: 'ASK_FOLLOW_UP', label: '继续提问',
  command_contract_ref: 'SYS08.BookLearningAskFollowUpV1', input_refs: [],
  input_schema_ref: 'LearningInteractionInvocationV1.user_response.text/1.0',
  expected_result_ref_types: ['BookLearningTranscriptTurn', 'LearningMessage'],
  availability: 'AVAILABLE', reason_codes: [], requires_idempotency_key: true,
  risk: 'LOW_RISK_WRITE',
}

function message(blocks) {
  return {
    schema_version: '1.0', id: 'message-1', revision: 1, conversation_id: 'conversation-1',
    sequence: 1, role: 'ASSISTANT', timestamp: '2026-08-11T09:00:00Z',
    content: '可读降级内容', blocks,
    context: {
      workspace_ref: {}, learning_activity_ref: {}, learning_session_ref: null,
      transcript_turn_ref: {}, teaching_action_ref: null, evidence_bundle_ref: null,
      attempt_ref: null, assessment_result_ref: null,
    },
    trace_references: { correlation_id: 'test', workflow_run_ref: null, decision_trace_ref: null, model_inference_ref: null, learning_event_refs: [] },
    compatibility: { source: 'CANONICAL', fidelity: 'FULL', reason_codes: [] },
  }
}

describe('LearningMessage renderer LCMS-AC-001..005', () => {
  it('renders all six typed blocks through the stable dispatcher', () => {
    render(<MessageRenderer message={message([
      { id: 'b1', type: 'EXPLANATION', payload: { title: null, body_markdown: '解释', presentation: 'DEFAULT' }, metadata, interactions: [] },
      { id: 'b2', type: 'KNOWLEDGE', payload: { title: '概念', body_markdown: '定义', knowledge_status: 'PRESENTATION_ONLY', qualifier: null }, metadata, interactions: [] },
      { id: 'b3', type: 'EVIDENCE', payload: { excerpt: '原文', source_label: '资料', locator: '1.1', citation_label: null }, metadata, interactions: [] },
      { id: 'b4', type: 'LEARNING_ACTIVITY', payload: { prompt_markdown: '请作答', response_mode: 'TEXT', options: [], response_constraints: {} }, metadata, interactions: [] },
      { id: 'b5', type: 'FEEDBACK', payload: { feedback_basis: 'NON_ASSESSMENT_EXECUTION_FEEDBACK', heading: '状态', body_markdown: '已记录', correctness: null, assessment_confidence: null, diagnostic_summary: null }, metadata, interactions: [] },
      { id: 'b6', type: 'REVIEW_APPLY', payload: { mode: 'APPLY', title: '应用', description_markdown: '迁移练习', timing_label: null }, metadata, interactions: [] },
    ])} />)

    for (const text of ['解释', '概念', '原文', '请作答', '状态']) {
      expect(screen.getByText(text)).toBeInTheDocument()
    }
    expect(screen.getByRole('heading', { name: '应用' })).toBeInTheDocument()
  })

  it('falls back safely for an unknown block type', () => {
    render(<MessageRenderer message={message([
      { id: 'unknown', type: 'EXECUTE_TOOL', payload: {}, metadata, interactions: [] },
    ])} />)
    expect(screen.getByText('可读降级内容')).toBeInTheDocument()
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('dispatches only a server-issued capability and remains single-flight', async () => {
    let resolveInvocation
    const onInvoke = vi.fn(() => new Promise((resolve) => { resolveInvocation = resolve }))
    render(<MessageRenderer message={message([
      { id: 'b1', type: 'EXPLANATION', payload: { title: null, body_markdown: '解释', presentation: 'DEFAULT' }, metadata, interactions: [interaction] },
    ])} interactionInput={{ text: '请继续解释' }} onInvoke={onInvoke} />)

    const button = screen.getByRole('button', { name: '继续提问' })
    fireEvent.click(button)
    fireEvent.click(button)
    expect(onInvoke).toHaveBeenCalledTimes(1)
    expect(button).toBeDisabled()
    resolveInvocation({ status: 'SUCCEEDED' })
    await waitFor(() => expect(screen.getByRole('button', { name: '已完成：继续提问' })).toBeDisabled())
  })

  it('keeps owner failure visible and retryable without claiming success', async () => {
    const onInvoke = vi.fn().mockRejectedValue(new Error('owner unavailable'))
    render(<MessageRenderer message={message([
      { id: 'b1', type: 'EXPLANATION', payload: { title: null, body_markdown: '解释', presentation: 'DEFAULT' }, metadata, interactions: [interaction] },
    ])} interactionInput={{ text: '请继续解释' }} onInvoke={onInvoke} />)

    fireEvent.click(screen.getByRole('button', { name: '继续提问' }))

    expect(await screen.findByRole('status')).toHaveTextContent('内容与学习状态均未改变')
    expect(screen.getByRole('button', { name: '重试：继续提问' })).toBeEnabled()
  })
})
