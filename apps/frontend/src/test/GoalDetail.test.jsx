import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as goalApi from '../api/goals'
import GoalDetail from '../pages/GoalDetail'
import { RouterProvider } from '../router'

vi.mock('../api/goals', () => ({
  getGoalDetail: vi.fn(), getGoalAchievement: vi.fn(), pauseGoal: vi.fn(),
  resumeGoal: vi.fn(), archiveGoal: vi.fn(), copyArchivedGoal: vi.fn(),
  scheduleGoalAssessments: vi.fn(), submitGoalAssessment: vi.fn(),
  evaluateGoalAchievement: vi.fn(), confirmGoalAchievement: vi.fn(),
}))

const detail = {
  definition: {
    definition_version: 2, title: '热力学迁移', topic: '热力学',
    target_capabilities: ['解释', '应用'], application_context: '分析热机',
    weekly_time_budget_minutes: 90, deadline_at: null,
    success_criteria: [{ criterion_id: 'criterion-1', statement: '独立应用热力学解决新问题', cognitive_process: 'apply', evidence_requirements: ['independent_application', 'novel_context'] }],
  },
  state: { state_version: 3, status: 'active' },
  plan_state: { state_version: 1, status: 'active' },
  focused: true,
}

describe('P1-01B goal lifecycle and achievement workspace', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    goalApi.getGoalDetail.mockResolvedValue(detail)
    goalApi.getGoalAchievement.mockResolvedValue({ policy: {}, objectives: [], assessments: [], latest_evaluation: null })
  })

  it('pauses with both optimistic versions and exposes lifecycle recovery', async () => {
    goalApi.pauseGoal.mockResolvedValue({ state: { ...detail.state, state_version: 4, status: 'paused' }, plan_state: { state_version: 2, status: 'paused' } })
    render(<RouterProvider><GoalDetail goalId="goal-1" /></RouterProvider>)
    expect(await screen.findByRole('heading', { name: /进行中.*当前重点/ })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '暂停' }))
    await waitFor(() => expect(goalApi.pauseGoal).toHaveBeenCalledWith('goal-1', expect.objectContaining({
      expected_state_version: 3, expected_plan_state_version: 1,
    })))
  })

  it('schedules criterion assessment and explains fail-closed scoring', async () => {
    const assessment = {
      assessment_activity_id: 'assessment-1', activity_version: 1,
      prompt: '独立应用热力学解决新问题', cognitive_process: 'apply',
      scoring_method: 'open_response', status: 'available',
    }
    goalApi.scheduleGoalAssessments.mockResolvedValue({ policy: {}, objectives: [], assessments: [assessment], latest_evaluation: null })
    goalApi.submitGoalAssessment.mockResolvedValue({ ...assessment, activity_version: 2, status: 'needs_review' })
    goalApi.getGoalAchievement
      .mockResolvedValueOnce({ policy: {}, objectives: [], assessments: [], latest_evaluation: null })
      .mockResolvedValueOnce({ policy: {}, objectives: [], assessments: [{ ...assessment, activity_version: 2, status: 'needs_review' }], latest_evaluation: null })
    render(<RouterProvider><GoalDetail goalId="goal-1" /></RouterProvider>)
    fireEvent.click(await screen.findByRole('button', { name: '安排成功标准验证' }))
    expect(await screen.findByText(/开放题双重评分/)).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('你的独立回答'), { target: { value: '在新热机情境中分析熵增。' } })
    fireEvent.click(screen.getByRole('button', { name: '提交验证' }))
    await waitFor(() => expect(goalApi.submitGoalAssessment).toHaveBeenCalledWith(
      'goal-1', 'assessment-1', expect.objectContaining({ expected_activity_version: 1 }),
    ))
    expect(await screen.findByText(/系统失败或低置信不会记作学习失败/)).toBeInTheDocument()
  })
})
