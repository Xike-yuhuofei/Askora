import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as bookLearningApi from '../api/bookLearning'
import BookLearningLaunch from '../pages/BookLearningLaunch'

vi.mock('../api/bookLearning', () => ({
  getReadiness: vi.fn(),
  advance: vi.fn(),
  getGoal: vi.fn(),
  getMapping: vi.fn(),
  getDiagnostic: vi.fn(),
  getPlan: vi.fn(),
  getTranscript: vi.fn(),
  createGoal: vi.fn(),
  confirmGoal: vi.fn(),
  mapGoal: vi.fn(),
  startDiagnostic: vi.fn(),
  submitDiagnosticResponse: vi.fn(),
  generatePlan: vi.fn(),
  selectNextActivity: vi.fn(),
  startTeachingRound: vi.fn(),
}))

const documentId = '11111111-1111-4111-8111-111111111111'
const goalId = '22222222-2222-4222-8222-222222222222'
const needId = '66666666-6666-4666-8666-666666666666'
const planId = '77777777-7777-4777-8777-777777777777'
const activityId = '88888888-8888-4888-8888-888888888888'
const sessionId = '99999999-9999-4999-8999-999999999999'

const goalRef = {
  owner_system: 'SYS06',
  ref: { entity_type: 'LearningGoal', entity_id: goalId, version: 1 },
  status: 'candidate',
  reason_codes: [],
}

const selectedActivityRef = {
  owner_system: 'SYS06',
  ref: { entity_type: 'LearningActivity', entity_id: activityId, version: 1 },
  status: 'selected',
  reason_codes: ['ACTIVITY_SELECTED'],
}

const readiness = (state, nextCommands, reasonCodes, ownerRefs = []) => ({
  schema_version: '1.0',
  document_id: documentId,
  state,
  owner_refs: ownerRefs,
  reason_codes: reasonCodes,
  next_commands: nextCommands,
  generated_at: '2026-08-08T12:00:00Z',
  correlation_id: `test-${state}`,
})

const goal = {
  goal_id: goalId,
  version: 1,
  title: '掌握资料中的比例方法',
  topic: '比例',
  target_capabilities: ['能解释比例关系', '能应用到新案例'],
  application_context: null,
  success_criteria: ['独立解决一道新题'],
  weekly_time_budget_minutes: 60,
}

const activeDiagnostic = {
  need: { need_id: needId, version: 1, status: 'active' },
  learner_item: {
    item_ref: { entity_type: 'AssessmentItem', entity_id: 'item-1', version: '1.0' },
    need_id: needId,
    need_version: 1,
    item_type: 'exact',
    prompt: '请写出比例的定义',
    options: [],
  },
}

const planPayload = {
  plan: { plan_id: planId, version: 1, status: 'active' },
  activities: [{
    activity_id: activityId,
    plan_id: planId,
    plan_version: 1,
    type: 'learn_new',
    estimated_duration_minutes: 15,
    status: 'available',
  }],
}

const assistantTurn = {
  turn_id: 'system-start-1',
  turn_number: 1,
  turn_kind: 'system_start',
  learner_text: null,
  reply_text: '先想一想：比例中的两个量表达了什么关系？',
  teaching_action_ref: { entity_type: 'TeachingAction', entity_id: 'action-1', version: '3.0' },
  evidence_bundle_ref: { entity_type: 'EvidenceBundle', entity_id: 'bundle-1', version: '3.0' },
  evidence: [{
    evidence_id: 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa',
    source_span_ids: ['bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb'],
    pedagogical_role: 'definition',
    excerpt: '比例表示两个量之间的相对关系。',
  }],
  accepted_at: '2026-08-08T12:00:00Z',
  model_execution: {
    schema_version: '1.0',
    mode: 'real_model',
    provider: 'deepseek',
    model: 'deepseek-chat',
    prompt_version: 'v03-policy-bound-real-render/1.0',
    inference_id: 'cccccccc-cccc-4ccc-8ccc-cccccccccccc',
    latency_ms: 320,
    input_tokens: 120,
    output_tokens: 40,
    total_tokens: 160,
  },
}

const transcript = (turns = []) => ({
  schema_version: '1.0',
  session_id: sessionId,
  activity_ref: { entity_type: 'LearningActivity', entity_id: activityId, version: 1 },
  turns,
  next_turn_number: turns.length + 1,
  correlation_id: 'transcript-test',
})

function operation(payload = {}) {
  return { schema_version: '1.0', operation: 'test', owner_refs: [], payload, correlation_id: 'op' }
}

describe('UI02B2 guided book learning', () => {
  beforeEach(() => {
    for (const value of Object.values(bookLearningApi)) {
      value.mockReset()
      value.mockResolvedValue(operation())
    }
    bookLearningApi.getGoal.mockResolvedValue(operation({ goal }))
    bookLearningApi.getDiagnostic.mockResolvedValue(operation(activeDiagnostic))
    bookLearningApi.getPlan.mockResolvedValue(operation(planPayload))
    bookLearningApi.getTranscript.mockResolvedValue(transcript())
  })

  it('automatically advances owner-only preparation and stops for the learner diagnostic', async () => {
    bookLearningApi.getReadiness
      .mockResolvedValueOnce(readiness('GOAL_CONFIRMATION_REQUIRED', ['ConfirmLearningGoal'], ['LEARNING_GOAL_USER_CONFIRMATION_REQUIRED'], [goalRef]))
      .mockResolvedValueOnce(readiness('DIAGNOSIS_REQUIRED', ['MapGoalToKnowledge'], ['GOAL_KNOWLEDGE_MAPPING_REQUIRED'], [goalRef]))
      .mockResolvedValueOnce(readiness('DIAGNOSIS_REQUIRED', ['GeneratePrerequisiteDiagnosis'], ['PREREQUISITE_DIAGNOSTIC_REQUIRED'], [goalRef]))
      .mockResolvedValue(readiness('DIAGNOSING', ['ContinuePrerequisiteDiagnosis'], ['DIAGNOSTIC_ACTIVITY_ACTIVE'], [goalRef]))

    render(<BookLearningLaunch documentId={documentId} />)

    expect(await screen.findByRole('heading', { name: '确认你的学习目标' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '确认并准备学习' }))

    expect(await screen.findByText('请写出比例的定义')).toBeInTheDocument()
    await waitFor(() => expect(bookLearningApi.advance).toHaveBeenCalledTimes(2))
    expect(bookLearningApi.advance.mock.calls[0][1].idempotency_key).toContain('MapGoalToKnowledge')
    expect(bookLearningApi.advance.mock.calls[1][1].idempotency_key).toContain('GeneratePrerequisiteDiagnosis')
    expect(screen.queryByRole('button', { name: /建立资料学习范围|开始先修诊断|生成学习计划|选择下一个活动/ })).not.toBeInTheDocument()
    expect(screen.getByText('不计分 · 用于调整学习起点')).toBeInTheDocument()
  })

  it('starts with a server-owned system turn and restores the accepted reply with evidence', async () => {
    bookLearningApi.getReadiness.mockResolvedValue(
      readiness('READY_TO_LEARN', ['StartCanonicalTeachingRound'], ['LEARNING_ACTIVITY_SELECTED'], [goalRef, selectedActivityRef]),
    )
    bookLearningApi.getTranscript
      .mockResolvedValueOnce(transcript())
      .mockResolvedValue(transcript([assistantTurn]))

    render(<BookLearningLaunch documentId={documentId} />)

    fireEvent.click(await screen.findByRole('button', { name: '开始本次学习' }))

    expect(await screen.findByText('先想一想：比例中的两个量表达了什么关系？')).toBeInTheDocument()
    fireEvent.click(screen.getByText('技术详情'))
    expect(screen.getByText(/模型执行：real_model · deepseek · deepseek-chat/)).toBeInTheDocument()
    expect(bookLearningApi.startTeachingRound).toHaveBeenCalledWith(
      activityId,
      expect.objectContaining({
        turn_kind: 'system_start',
        learner_text: null,
        session_id: sessionId,
      }),
    )
    expect(screen.getByText('依据资料 · 1 处')).toBeInTheDocument()
    expect(screen.getByText(/刷新页面也可以继续/)).toBeInTheDocument()
    expect(within(screen.getByRole('main')).queryByText(/canonical|SYS08|READY_TO_LEARN/)).not.toBeInTheDocument()
  })

  it('submits the next learner turn against the durable transcript number', async () => {
    bookLearningApi.getReadiness.mockResolvedValue(
      readiness('READY_TO_LEARN', ['StartCanonicalTeachingRound'], ['LEARNING_ACTIVITY_SELECTED'], [goalRef, selectedActivityRef]),
    )
    bookLearningApi.getTranscript.mockResolvedValue(transcript([assistantTurn]))

    render(<BookLearningLaunch documentId={documentId} />)

    fireEvent.change(await screen.findByLabelText('写下你的想法或问题'), {
      target: { value: '两个量之间的相对关系。' },
    })
    fireEvent.click(screen.getByRole('button', { name: '发送学习回答' }))

    await waitFor(() => expect(bookLearningApi.startTeachingRound).toHaveBeenCalledWith(
      activityId,
      expect.objectContaining({
        turn_id: 'learner-turn-2',
        turn_kind: 'learner',
        learner_text: '两个量之间的相对关系。',
      }),
    ))
  })

  it('fails closed for an unknown readiness state', async () => {
    bookLearningApi.getReadiness.mockResolvedValue({
      ...readiness('READY_FOR_GOAL', [], ['UNKNOWN']),
      state: 'FUTURE_STATE',
    })

    render(<BookLearningLaunch documentId={documentId} />)

    expect(await screen.findByRole('heading', { name: '暂时无法打开这份资料' })).toBeInTheDocument()
    expect(bookLearningApi.createGoal).not.toHaveBeenCalled()
  })

  it('renders distinct lifecycle refs without duplicate React keys', async () => {
    const activityRef = { ...selectedActivityRef, status: 'available' }
    bookLearningApi.getReadiness.mockResolvedValue(
      readiness('READY_TO_LEARN', ['StartCanonicalTeachingRound'], ['LEARNING_ACTIVITY_SELECTED'], [goalRef, activityRef, selectedActivityRef]),
    )
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})

    try {
      render(<BookLearningLaunch documentId={documentId} />)
      expect(await screen.findByRole('button', { name: '开始本次学习' })).toBeInTheDocument()
      await waitFor(() => {
        expect(consoleError.mock.calls.some((items) => String(items[0]).includes('same key'))).toBe(false)
      })
    } finally {
      consoleError.mockRestore()
    }
  })
})
