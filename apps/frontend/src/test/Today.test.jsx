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
    expect(screen.getAllByText('函数与导数').length).toBeGreaterThan(0)
    expect(screen.getAllByText('兼容会话').length).toBeGreaterThan(0)
    expect(screen.queryByText('已掌握')).not.toBeInTheDocument()
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
    workspaceApi.getTodayWorkspace.mockResolvedValueOnce({
      ...todayPayload,
      data: {
        ...todayPayload.data,
        view_state: 'READY',
        active_goal: { goal_ref: 'learning_goal:g1:v2', title: '理解函数', status: 'active', target_capabilities: ['解释变化'] },
        current_activity: { activity_ref: 'learning_activity:a1:v1', objective_ref: 'learning_objective:o1:v1', type: 'diagnostic', title: '检查当前基础', estimated_duration_minutes: 5, reason_codes: ['PLAN_TARGET_STATE_UNKNOWN'], status: 'available', launch_state: 'REQUIRES_START_COMMAND' },
      },
      source_status: [
        { source_system: 'SYS06', availability: 'AVAILABLE', source_ref: 'learning_plan:p1:v1', reason_codes: ['CURRENT_PLAN_AVAILABLE'] },
      ],
    })
    render(<RouterProvider><Today /></RouterProvider>)

    expect(await screen.findByRole('heading', { name: '检查当前基础' })).toBeInTheDocument()
    expect(screen.getByText(/完成本项不等于已经掌握/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /开始学习/ }))
    await waitFor(() => expect(window.location.hash).toBe('#/learn/a1'))
  })
})
