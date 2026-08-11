import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as bookLearningApi from '../api/bookLearning'
import * as workspaceApi from '../api/workspace'
import ActivityLearning from '../pages/ActivityLearning'
import { RouterProvider } from '../router'

vi.mock('../api/workspace', () => ({
  getActivityLifecycle: vi.fn(),
  getLearningContext: vi.fn(),
  startActivity: vi.fn(),
  completeActivity: vi.fn(),
}))
vi.mock('../api/bookLearning', () => ({
  getTranscript: vi.fn(),
  startTeachingRound: vi.fn(),
  invokeMessageInteraction: vi.fn(),
}))

const activityId = '11111111-1111-4111-8111-111111111111'
const goalId = '22222222-2222-4222-8222-222222222222'
const planId = '33333333-3333-4333-8333-333333333333'

function lifecycle(status = 'available', version = 2) {
  return {
    schema_version: '1.0',
    data: {
      state: { schema_version: '1.0', activity_id: activityId, version, plan_id: planId, plan_version: 1, status, previous_status: status === 'available' ? 'planned' : 'available', transition_reason: 'TEST', source_refs: [], actor_type: 'system', started_at: null, completed_at: null, correlation_id: '44444444-4444-4444-8444-444444444444', created_at: '2026-08-09T00:00:00Z' },
      goal_id: goalId,
      activity_type: 'learn_new',
      title: '学习新内容',
      estimated_duration_minutes: 10,
      knowledge_unit_ids: [],
      execution: { can_start: status === 'available', can_resume: status === 'active', can_complete: status === 'active', product_route: `/learn/${activityId}`, reason_codes: [] },
    },
    next_activity_ref: null,
    plan_status: 'active',
    correlation_id: 'request-1',
  }
}

function transcript(turns = []) {
  return { schema_version: '1.0', session_id: '55555555-5555-4555-8555-555555555555', activity_ref: { entity_type: 'LearningActivity', entity_id: activityId, version: 1 }, turns, next_turn_number: turns.length + 1, correlation_id: 'request-1' }
}

function ownerRef(sourceSystem, entityType, entityId, version) {
  return {
    source_system: sourceSystem,
    entity_type: entityType,
    entity_id: entityId,
    version,
    workspace_id: '66666666-6666-4666-8666-666666666666',
    availability: 'READY',
    freshness_at: '2026-08-11T09:00:00Z',
  }
}

function canonicalTurn() {
  const activityRef = ownerRef('SYS06', 'LearningActivity', activityId, 1)
  const actionRef = ownerRef('SYS05', 'TeachingAction', 'action-1', '3.0')
  const turnRef = ownerRef('SYS08', 'BookLearningTranscriptTurn', 'turn-record-1', 1)
  const workspaceRef = ownerRef('PLATFORM', 'Workspace', '66666666-6666-4666-8666-666666666666', 1)
  const capability = {
    id: 'ask-follow-up',
    capability_id: 'ask-follow-up:message-1',
    semantic_primitive: 'ACTION',
    action_type: 'ASK_FOLLOW_UP',
    label: '继续提问',
    command_contract_ref: 'SYS08.BookLearningAskFollowUpV1',
    input_refs: [activityRef, actionRef, turnRef],
    input_schema_ref: 'LearningInteractionInvocationV1.user_response.text/1.0',
    expected_result_ref_types: ['BookLearningTranscriptTurn', 'LearningMessage'],
    availability: 'AVAILABLE',
    reason_codes: [],
    requires_idempotency_key: true,
    risk: 'LOW_RISK_WRITE',
  }
  return {
    turn_id: 'learner-turn-1',
    turn_number: 1,
    turn_kind: 'learner',
    learner_text: '我的理解',
    reply_text: '继续说明',
    accepted_at: '2026-08-11T09:00:00Z',
    message_envelope: {
      schema_version: '1.0',
      id: 'message-1',
      revision: 1,
      conversation_id: '55555555-5555-4555-8555-555555555555',
      sequence: 1,
      role: 'ASSISTANT',
      timestamp: '2026-08-11T09:00:00Z',
      content: '继续说明',
      blocks: [{
        id: 'explanation',
        type: 'EXPLANATION',
        payload: { title: null, body_markdown: '继续说明', presentation: 'DEFAULT' },
        metadata: {
          schema_version: '1.0',
          semantic_role: 'teaching_explanation',
          provenance: { mode: 'NOT_APPLICABLE', source_refs: [], source_span_refs: [], evidence_bundle_ref: null, generated_by_ref: null },
          owner_refs: [activityRef, actionRef],
          availability: 'READY',
          reason_codes: [],
          accessibility_label: 'Askora 教学回复',
        },
        interactions: [capability],
      }],
      context: {
        workspace_ref: workspaceRef,
        learning_activity_ref: activityRef,
        learning_session_ref: null,
        transcript_turn_ref: turnRef,
        teaching_action_ref: actionRef,
        evidence_bundle_ref: null,
        attempt_ref: null,
        assessment_result_ref: null,
      },
      trace_references: {
        correlation_id: 'message-correlation-1',
        workflow_run_ref: null,
        decision_trace_ref: null,
        model_inference_ref: null,
        learning_event_refs: [],
      },
      compatibility: { source: 'CANONICAL', fidelity: 'FULL', reason_codes: [] },
    },
  }
}

describe('UI02C canonical ActivityLearning', () => {
  beforeEach(() => {
    window.location.hash = `#/learn/${activityId}`
    vi.clearAllMocks()
    workspaceApi.getActivityLifecycle.mockResolvedValue(lifecycle())
    workspaceApi.getLearningContext.mockResolvedValue({
      data: {
        view_state: 'MISSING',
        stage_name: null,
        stage_goal: null,
        next_directions: [],
      },
    })
    bookLearningApi.getTranscript.mockResolvedValue(transcript())
  })

  it('starts with expected lifecycle version and restores active state', async () => {
    workspaceApi.startActivity.mockResolvedValue(lifecycle('active', 3))
    workspaceApi.getActivityLifecycle.mockResolvedValueOnce(lifecycle()).mockResolvedValueOnce(lifecycle('active', 3))
    render(<RouterProvider><ActivityLearning activityId={activityId} /></RouterProvider>)
    fireEvent.click(await screen.findByRole('button', { name: /开始学习/ }))
    await waitFor(() => expect(workspaceApi.startActivity).toHaveBeenCalledWith(activityId, expect.objectContaining({ expected_state_version: 2, activity_id: activityId })))
    expect(await screen.findByRole('button', { name: '进入本次学习' })).toBeInTheDocument()
  })

  it('completes only with accepted transcript refs and preserves the mastery disclaimer', async () => {
    const turn = { turn_id: 'learner-turn-1', turn_number: 1, turn_kind: 'learner', learner_text: '我的理解', reply_text: '继续说明', accepted_at: '2026-08-09T00:01:00Z' }
    workspaceApi.getActivityLifecycle.mockResolvedValue(lifecycle('active', 3))
    bookLearningApi.getTranscript.mockResolvedValue(transcript([turn]))
    workspaceApi.completeActivity.mockResolvedValue(lifecycle('completed', 4))
    render(<RouterProvider><ActivityLearning activityId={activityId} /></RouterProvider>)
    expect(await screen.findByText(/不等于已掌握/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /完成本项/ }))
    await waitFor(() => expect(workspaceApi.completeActivity).toHaveBeenCalledWith(activityId, expect.objectContaining({ transcript_turn_refs: [{ entity_type: 'BookLearningTranscriptTurn', entity_id: 'learner-turn-1', version: 1 }] })))
  })

  it('keeps active state visible when provider execution fails', async () => {
    workspaceApi.getActivityLifecycle.mockResolvedValue(lifecycle('active', 3))
    bookLearningApi.getTranscript.mockResolvedValue(transcript())
    bookLearningApi.startTeachingRound.mockRejectedValue({ response: { data: { error: { code: 'AI_MODEL_UNAVAILABLE' } } } })
    render(<RouterProvider><ActivityLearning activityId={activityId} /></RouterProvider>)
    fireEvent.click(await screen.findByRole('button', { name: '进入本次学习' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('活动仍保持进行中')
  })

  it('keeps the primary composer available when the Drawer query fails', async () => {
    const turn = { turn_id: 'learner-turn-1', turn_number: 1, turn_kind: 'learner', learner_text: '我的理解', reply_text: '继续说明', accepted_at: '2026-08-09T00:01:00Z' }
    workspaceApi.getActivityLifecycle.mockResolvedValue(lifecycle('active', 3))
    workspaceApi.getLearningContext.mockRejectedValue(new Error('drawer unavailable'))
    bookLearningApi.getTranscript.mockResolvedValue(transcript([turn]))

    render(<RouterProvider><ActivityLearning activityId={activityId} /></RouterProvider>)

    expect(await screen.findByText(/当前阶段信息读取失败/)).toBeInTheDocument()
    expect(screen.getByLabelText('写下你的想法')).toBeEnabled()
  })

  it('dispatches the latest server-issued capability with exact owner refs', async () => {
    const turn = canonicalTurn()
    workspaceApi.getActivityLifecycle.mockResolvedValue(lifecycle('active', 3))
    bookLearningApi.getTranscript.mockResolvedValue(transcript([turn]))
    bookLearningApi.invokeMessageInteraction.mockResolvedValue({
      schema_version: '1.0',
      interaction_id: '77777777-7777-4777-8777-777777777777',
      status: 'SUCCEEDED',
      result_refs: [],
      next_transition: { kind: 'REQUERY_OWNER', target_system: 'SYS08', expected_ref_types: ['BookLearningTranscript', 'LearningMessage'] },
      correlation_id: 'message-correlation-1',
    })

    render(<RouterProvider><ActivityLearning activityId={activityId} /></RouterProvider>)

    fireEvent.change(await screen.findByLabelText('写下你的想法'), { target: { value: '请继续解释比例关系' } })
    fireEvent.click(screen.getByRole('button', { name: '继续提问' }))

    await waitFor(() => expect(bookLearningApi.invokeMessageInteraction).toHaveBeenCalledTimes(1))
    expect(bookLearningApi.startTeachingRound).not.toHaveBeenCalled()
    expect(bookLearningApi.invokeMessageInteraction).toHaveBeenCalledWith(
      activityId,
      'message-1',
      expect.objectContaining({
        conversation_id: turn.message_envelope.conversation_id,
        message_id: 'message-1',
        message_revision: 1,
        block_id: 'explanation',
        capability_id: 'ask-follow-up:message-1',
        action_type: 'ASK_FOLLOW_UP',
        expected_owner_versions: turn.message_envelope.blocks[0].interactions[0].input_refs,
        user_response: { payload: { text: '请继续解释比例关系' }, accepted_response_ref: null },
      }),
    )
  })
})
