import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as dialogApi from '../api/dialog'
import * as workspaceApi from '../api/workspace'
import Today from '../pages/Today'
import { RouterProvider } from '../router'

vi.mock('../api/dialog', () => ({ createSession: vi.fn() }))
vi.mock('../api/workspace', () => ({ getTodayWorkspace: vi.fn() }))

const todayPayload = {
  schema_version: '1.0',
  generated_at: '2026-08-08T01:30:00Z',
  correlation_id: 'request-1',
  data: {
    local_date: '2026-08-08',
    timezone: 'Asia/Shanghai',
    view_state: 'PARTIAL',
    active_goal: null,
    current_activity: null,
    planned_activities: [],
    review_due_candidates: [
      {
        knowledge_unit_ref: 'knowledge_unit:unit-1',
        schedule_ref: 'review_schedule:schedule-1:v1',
        next_due_at: '2026-08-08T00:30:00Z',
        review_priority: 0.8,
        evidence_quality: 0.7,
        included_activity_ref: null,
      },
    ],
    current_evidence_summary: null,
    compatibility_quick_start: {
      source_label: 'LEGACY_COMPATIBILITY',
      recent_sessions: [
        {
          session_id: '11111111-1111-4111-8111-111111111111',
          title: null,
          subject: 'math',
          knowledge_point_id: '函数与导数',
          status: 'active',
          updated_at: '2026-08-08T01:00:00Z',
        },
      ],
    },
  },
  source_status: [
    { source_system: 'SYS06', availability: 'MISSING', source_ref: null, reason_codes: ['OWNER_QUERY_UNAVAILABLE'] },
    { source_system: 'SYS07', availability: 'AVAILABLE', source_ref: null, reason_codes: ['LATEST_USER_SCHEDULES'] },
    { source_system: 'SYS03', availability: 'NOT_APPLICABLE', source_ref: null, reason_codes: ['NO_CURRENT_ACTIVITY'] },
    { source_system: 'LEGACY_COMPATIBILITY', availability: 'AVAILABLE', source_ref: null, reason_codes: ['DIALOG_SESSION_COMPATIBILITY'] },
  ],
}

const canonicalActivity = {
  activity_ref: 'learning_activity:a1:v1',
  objective_ref: 'learning_objective:o1:v1',
  type: 'diagnostic',
  title: '检查当前基础',
  estimated_duration_minutes: 5,
  reason_codes: ['PLAN_TARGET_STATE_UNKNOWN'],
  status: 'available',
  launch_state: 'REQUIRES_START_COMMAND',
}

function canonicalTodayPayload(overrides = {}) {
  return {
    ...todayPayload,
    data: {
      ...todayPayload.data,
      view_state: 'READY',
      active_goal: {
        goal_ref: 'learning_goal:g1:v2',
        title: '理解函数',
        status: 'active',
        target_capabilities: ['解释变化'],
      },
      current_activity: canonicalActivity,
      planned_activities: [
        {
          activity_ref: 'learning_activity:a2:v1',
          objective_ref: 'learning_objective:o2:v1',
          type: 'practice',
          title: '练习函数变化判断',
          estimated_duration_minutes: 8,
          reason_codes: ['PLAN_MASTERY_GAP'],
          status: 'planned',
          launch_state: 'UNAVAILABLE',
        },
      ],
      current_evidence_summary: {
        knowledge_unit_ref: 'knowledge_unit:unit-1',
        confidence: 0.6,
        independent_success_count: 0,
        delayed_recall_evidence_count: 0,
        transfer_evidence_count: 0,
        validation_obligation: 'INDEPENDENT_VALIDATION_REQUIRED',
      },
      ...overrides,
    },
    source_status: [
      {
        source_system: 'SYS06',
        availability: 'AVAILABLE',
        source_ref: 'learning_plan:p1:v1',
        reason_codes: ['CURRENT_PLAN_AVAILABLE'],
      },
    ],
  }
}

describe('UI-SCREEN-AC-002 / UI01 Today page', () => {
  beforeEach(() => {
    window.location.hash = '#/today'
    workspaceApi.getTodayWorkspace.mockReset()
    dialogApi.createSession.mockReset()
    workspaceApi.getTodayWorkspace.mockResolvedValue(todayPayload)
  })

  it('shows partial source truth without inventing a goal or plan', async () => {
    render(<RouterProvider><Today /></RouterProvider>)

    expect(await screen.findByRole('heading', { name: '今天' })).toBeInTheDocument()
    expect(screen.getByText('还没有可展示的当前计划')).toBeInTheDocument()
    expect(screen.getByText('尚未纳入学习计划')).toBeInTheDocument()
    expect(screen.queryByText('已掌握')).not.toBeInTheDocument()

    expect(screen.getByRole('button', { name: /快速学习/ })).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getAllByText('函数与导数').length).toBeGreaterThan(0)
    expect(screen.getAllByText('兼容会话').length).toBeGreaterThan(0)
  })

  it('creates only an explicitly labelled compatibility session', async () => {
    dialogApi.createSession.mockResolvedValue({ id: 'session-new' })
    render(<RouterProvider><Today /></RouterProvider>)
    await screen.findByRole('heading', { name: '快速学习' })

    fireEvent.click(screen.getByRole('button', { name: /开始兼容学习/ }))
    await waitFor(() => expect(dialogApi.createSession).toHaveBeenCalledWith('math', '一元二次方程'))
    await waitFor(() => expect(window.location.hash).toBe('#/quick/session-new'))
  })

  it('renders a truthful retry state when the owner query fails', async () => {
    workspaceApi.getTodayWorkspace.mockRejectedValueOnce({ response: { status: 503 } })
    render(<RouterProvider><Today /></RouterProvider>)

    expect(await screen.findByRole('alert')).toHaveTextContent('今日学习信息暂时无法读取')
    expect(screen.getByRole('button', { name: /重试/ })).toBeInTheDocument()
    expect(screen.queryByText('已掌握')).not.toBeInTheDocument()
  })

  it('launches the exact canonical activity from its lifecycle capability', async () => {
    workspaceApi.getTodayWorkspace.mockResolvedValueOnce(canonicalTodayPayload())
    render(<RouterProvider><Today /></RouterProvider>)

    expect(await screen.findByRole('heading', { name: '检查当前基础' })).toBeInTheDocument()
    expect(screen.getByText(/完成本项不等于已经掌握/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /开始学习/ }))
    await waitFor(() => expect(window.location.hash).toBe('#/learn/a1'))
  })

  it('keeps the canonical activity as the sole primary action and supporting facts secondary', async () => {
    workspaceApi.getTodayWorkspace.mockResolvedValueOnce(canonicalTodayPayload())
    const { container } = render(<RouterProvider><Today /></RouterProvider>)

    expect(await screen.findByRole('heading', { name: '检查当前基础' })).toBeInTheDocument()
    expect(screen.getByText('需要先了解当前基础')).toBeInTheDocument()
    expect(screen.getByText(/后续需要一次不依赖提示的独立验证/)).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: '接下来的学习活动' })).toBeInTheDocument()
    expect(screen.getByText('练习函数变化判断')).toBeInTheDocument()
    expect(container.querySelectorAll('.button--primary')).toHaveLength(1)

    const quickStart = screen.getByRole('button', { name: /快速学习/ })
    expect(quickStart).toHaveAttribute('aria-expanded', 'false')
    quickStart.focus()
    expect(quickStart).toHaveFocus()
    fireEvent.click(quickStart)
    expect(screen.getByRole('button', { name: /开始兼容学习/ })).toHaveClass('button--secondary')
    expect(container.querySelectorAll('.button--primary')).toHaveLength(1)
  })

  it('distinguishes planned review activities from ReviewDue candidates', async () => {
    workspaceApi.getTodayWorkspace.mockResolvedValueOnce(canonicalTodayPayload({
      planned_activities: [
        {
          ...canonicalActivity,
          activity_ref: 'learning_activity:review-a1:v1',
          type: 'delayed_review',
          title: '复习函数定义',
          status: 'planned',
          launch_state: 'UNAVAILABLE',
        },
      ],
      review_due_candidates: [
        {
          ...todayPayload.data.review_due_candidates[0],
          included_activity_ref: 'learning_activity:review-a1:v1',
        },
        {
          ...todayPayload.data.review_due_candidates[0],
          schedule_ref: 'review_schedule:schedule-2:v1',
          knowledge_unit_ref: 'knowledge_unit:unit-2',
          included_activity_ref: null,
        },
      ],
    }))
    render(<RouterProvider><Today /></RouterProvider>)

    expect(await screen.findByText(/计划内复习/)).toBeInTheDocument()
    expect(screen.getByText('已纳入学习计划')).toBeInTheDocument()
    expect(screen.getByText('尚未纳入学习计划')).toBeInTheDocument()
  })

  it.each([
    ['ACTIVE', '继续学习'],
    ['RESUMABLE', '继续学习'],
    ['REQUIRES_START_COMMAND', '开始学习'],
  ])('maps %s launch state to the canonical action', async (launchState, actionLabel) => {
    workspaceApi.getTodayWorkspace.mockResolvedValueOnce(canonicalTodayPayload({
      current_activity: { ...canonicalActivity, launch_state: launchState },
    }))
    render(<RouterProvider><Today /></RouterProvider>)

    expect(await screen.findByRole('button', { name: new RegExp(actionLabel) })).toBeInTheDocument()
  })

  it('fails closed when the canonical activity launch state is unavailable', async () => {
    workspaceApi.getTodayWorkspace.mockResolvedValueOnce(canonicalTodayPayload({
      current_activity: { ...canonicalActivity, launch_state: 'UNAVAILABLE' },
    }))
    render(<RouterProvider><Today /></RouterProvider>)

    expect(await screen.findByText('当前活动暂不可启动')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /开始学习|继续学习/ })).not.toBeInTheDocument()
  })

  it('does not require a Goal or Project to render an owner-provided direct-material activity', async () => {
    workspaceApi.getTodayWorkspace.mockResolvedValueOnce(canonicalTodayPayload({
      active_goal: null,
      current_activity: {
        ...canonicalActivity,
        title: '直接学习当前资料',
      },
    }))
    render(<RouterProvider><Today /></RouterProvider>)

    expect(await screen.findByRole('heading', { name: '直接学习当前资料' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /开始学习/ })).toBeInTheDocument()
    expect(screen.queryByText(/必须.*项目|Project/)).not.toBeInTheDocument()
  })

  it('renders the EMPTY state as an honest fallback without a fabricated plan', async () => {
    workspaceApi.getTodayWorkspace.mockResolvedValueOnce({
      ...todayPayload,
      data: {
        ...todayPayload.data,
        view_state: 'EMPTY',
        review_due_candidates: [],
        compatibility_quick_start: {
          source_label: 'LEGACY_COMPATIBILITY',
          recent_sessions: [],
        },
      },
    })
    render(<RouterProvider><Today /></RouterProvider>)

    expect(await screen.findByText('今天还没有学习安排')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /快速学习/ })).toHaveAttribute('aria-expanded', 'true')
    expect(screen.queryByText('已掌握')).not.toBeInTheDocument()
  })

  it('keeps multiple plans scoped and asks for an explicit goal selection', async () => {
    workspaceApi.getTodayWorkspace.mockResolvedValueOnce({
      ...todayPayload,
      source_status: [
        {
          source_system: 'SYS06',
          availability: 'AVAILABLE',
          source_ref: null,
          reason_codes: ['MULTIPLE_CURRENT_PLANS_REQUIRE_GOAL_SCOPE'],
        },
      ],
    })
    render(<RouterProvider><Today /></RouterProvider>)

    expect(await screen.findByText('请选择一个学习目标')).toBeInTheDocument()
    expect(screen.getByText(/不会按时间替你猜选/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /开始学习|继续学习/ })).not.toBeInTheDocument()
  })
})
