import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as bookLearningApi from '../api/bookLearning'
import * as workspaceApi from '../api/workspace'
import ActivityLearning from '../pages/ActivityLearning'
import { RouterProvider } from '../router'

vi.mock('../api/workspace', () => ({
  getActivityLifecycle: vi.fn(),
  startActivity: vi.fn(),
  completeActivity: vi.fn(),
}))
vi.mock('../api/bookLearning', () => ({
  getTranscript: vi.fn(),
  startTeachingRound: vi.fn(),
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

describe('UI02C canonical ActivityLearning', () => {
  beforeEach(() => {
    window.location.hash = `#/learn/${activityId}`
    vi.clearAllMocks()
    workspaceApi.getActivityLifecycle.mockResolvedValue(lifecycle())
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
})
