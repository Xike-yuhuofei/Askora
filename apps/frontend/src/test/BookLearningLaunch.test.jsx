import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as bookLearningApi from '../api/bookLearning'
import BookLearningLaunch from '../pages/BookLearningLaunch'

vi.mock('../api/bookLearning', () => ({
  getReadiness: vi.fn(),
  getGoal: vi.fn(),
  getMapping: vi.fn(),
  getDiagnostic: vi.fn(),
  getPlan: vi.fn(),
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
const mappingId = '33333333-3333-4333-8333-333333333333'
const subgraphId = '44444444-4444-4444-8444-444444444444'
const targetId = '55555555-5555-4555-8555-555555555555'
const needId = '66666666-6666-4666-8666-666666666666'
const planId = '77777777-7777-4777-8777-777777777777'
const activityId = '88888888-8888-4888-8888-888888888888'

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

const mappingPayload = {
  mapping: {
    mapping_id: mappingId,
    mapping_version: 1,
    selected_target_ids: [targetId],
  },
  subgraph: { subgraph_id: subgraphId, version: 1 },
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

const terminalDiagnostic = {
  need: { need_id: needId, version: 2, status: 'resolved' },
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

const selectionPayload = {
  goal,
  plan: planPayload.plan,
  activity: planPayload.activities[0],
}

function operation(payload = {}) {
  return { schema_version: '1.0', operation: 'test', owner_refs: [], payload, correlation_id: 'op' }
}

describe('UI02B1 material-to-learning launch', () => {
  beforeEach(() => {
    sessionStorage.clear()
    for (const value of Object.values(bookLearningApi)) {
      value.mockReset()
      value.mockResolvedValue(operation())
    }
    bookLearningApi.getGoal.mockResolvedValue(operation({ goal }))
    bookLearningApi.getMapping.mockResolvedValue(operation(mappingPayload))
    bookLearningApi.getPlan.mockResolvedValue(operation(planPayload))
    bookLearningApi.selectNextActivity.mockResolvedValue(operation(selectionPayload))
  })

  it('UI02B1-AC-001..009 closes the real command sequence to a canonical teaching response', async () => {
    bookLearningApi.getReadiness
      .mockResolvedValueOnce(readiness('READY_FOR_GOAL', ['CreateLearningGoalCandidate'], ['PUBLISHED_CONTENT_READY_FOR_GOAL']))
      .mockResolvedValueOnce(readiness('GOAL_CONFIRMATION_REQUIRED', ['ConfirmLearningGoal'], ['LEARNING_GOAL_USER_CONFIRMATION_REQUIRED'], [goalRef]))
      .mockResolvedValueOnce(readiness('DIAGNOSIS_REQUIRED', ['MapGoalToKnowledge'], ['GOAL_KNOWLEDGE_MAPPING_REQUIRED'], [goalRef]))
      .mockResolvedValueOnce(readiness('DIAGNOSIS_REQUIRED', ['GeneratePrerequisiteDiagnosis'], ['PREREQUISITE_DIAGNOSTIC_REQUIRED'], [goalRef]))
      .mockResolvedValueOnce(readiness('DIAGNOSING', ['ContinuePrerequisiteDiagnosis'], ['DIAGNOSTIC_ACTIVITY_ACTIVE'], [goalRef]))
      .mockResolvedValueOnce(readiness('PLAN_READY', ['GenerateLearningPlan'], ['DIAGNOSTIC_COMPLETE_PLAN_GENERATION_REQUIRED'], [goalRef]))
      .mockResolvedValueOnce(readiness('PLAN_READY', ['SelectNextLearningActivity'], ['LEARNING_PLAN_READY'], [goalRef]))
      .mockResolvedValueOnce(readiness('READY_TO_LEARN', ['StartCanonicalTeachingRound'], ['LEARNING_ACTIVITY_SELECTED'], [goalRef, selectedActivityRef]))
    bookLearningApi.getDiagnostic
      .mockResolvedValueOnce(operation(activeDiagnostic))
      .mockResolvedValueOnce(operation(terminalDiagnostic))
    bookLearningApi.startTeachingRound.mockResolvedValue({ reply_text: '我们先从资料中的比例定义开始。' })

    render(<BookLearningLaunch documentId={documentId} />)
    expect(await screen.findByRole('heading', { name: '制定学习目标' })).toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('我希望学会什么'), { target: { value: '掌握比例并应用到新案例' } })
    fireEvent.click(screen.getByRole('button', { name: '形成目标候选' }))
    expect(await screen.findByRole('heading', { name: '确认学习目标' })).toBeInTheDocument()
    expect(screen.getByText('独立解决一道新题')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: '确认这个学习目标' }))
    expect(await screen.findByRole('button', { name: '建立资料学习范围' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '建立资料学习范围' }))
    expect(await screen.findByRole('button', { name: '开始先修诊断' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '开始先修诊断' }))

    expect(await screen.findByText('请写出比例的定义')).toBeInTheDocument()
    expect(screen.queryByText('grader-only')).not.toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('你的回答'), { target: { value: '两个量之间的相对关系' } })
    fireEvent.click(screen.getByRole('button', { name: '提交独立回答' }))

    expect(await screen.findByRole('button', { name: '生成学习计划' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '生成学习计划' }))
    expect(await screen.findByRole('button', { name: '选择下一个活动' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '选择下一个活动' }))

    expect(await screen.findByText('学习新内容')).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('学习问题'), { target: { value: '请用资料解释比例。' } })
    fireEvent.click(screen.getByRole('button', { name: '发送' }))
    expect(await screen.findByText('我们先从资料中的比例定义开始。')).toBeInTheDocument()

    expect(bookLearningApi.createGoal).toHaveBeenCalledTimes(1)
    expect(bookLearningApi.confirmGoal).toHaveBeenCalledTimes(1)
    expect(bookLearningApi.mapGoal).toHaveBeenCalledTimes(1)
    expect(bookLearningApi.startDiagnostic).toHaveBeenCalledTimes(1)
    expect(bookLearningApi.submitDiagnosticResponse).toHaveBeenCalledWith(
      needId,
      expect.objectContaining({
        expected_need_version: 1,
        response: '两个量之间的相对关系',
        assistance: expect.objectContaining({ assistance_class: 'none', answer_visible: false }),
      }),
    )
    expect(bookLearningApi.startTeachingRound).toHaveBeenCalledWith(
      activityId,
      expect.objectContaining({ activity_id: activityId, learner_text: '请用资料解释比例。' }),
    )
    expect(bookLearningApi.selectNextActivity).toHaveBeenCalledTimes(1)
  })

  it('UI02B1-AC-004 refuses to choose among multiple mapped targets', async () => {
    bookLearningApi.getReadiness.mockResolvedValue(
      readiness('DIAGNOSIS_REQUIRED', ['GeneratePrerequisiteDiagnosis'], ['PREREQUISITE_DIAGNOSTIC_REQUIRED'], [goalRef]),
    )
    bookLearningApi.getMapping.mockResolvedValue(operation({
      ...mappingPayload,
      mapping: { ...mappingPayload.mapping, selected_target_ids: [targetId, '99999999-9999-4999-8999-999999999999'] },
    }))

    render(<BookLearningLaunch documentId={documentId} />)

    expect(await screen.findByText(/只支持单一学习目标范围/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: '开始先修诊断' })).not.toBeInTheDocument()
    expect(bookLearningApi.startDiagnostic).not.toHaveBeenCalled()
  })

  it('UI02B1-AC-010 fails closed for an unknown readiness state', async () => {
    bookLearningApi.getReadiness.mockResolvedValue({
      ...readiness('READY_FOR_GOAL', [], ['UNKNOWN']),
      state: 'FUTURE_STATE',
    })

    render(<BookLearningLaunch documentId={documentId} />)

    expect(await screen.findByRole('heading', { name: '无法打开资料学习' })).toBeInTheDocument()
    expect(bookLearningApi.createGoal).not.toHaveBeenCalled()
  })
})
