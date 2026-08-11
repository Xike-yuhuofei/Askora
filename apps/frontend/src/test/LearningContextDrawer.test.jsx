import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as workspaceApi from '../api/workspace'
import LearningContextDrawer from '../components/LearningContextDrawer'

vi.mock('../api/workspace', () => ({
  getLearningContext: vi.fn(),
}))

const activityId = '11111111-1111-4111-8111-111111111111'

function response(viewState = 'READY', overrides = {}) {
  return {
    schema_version: '1.0',
    generated_at: '2026-08-11T08:30:00Z',
    correlation_id: 'request-1',
    data: {
      view_state: viewState,
      stage_ref: 'teaching_action:action-1:v0.3',
      stage_name: '引导练习',
      stage_goal: '在引导下完成当前任务',
      stage_source: { source_system: 'SYS05', source_ref: 'teaching_action:action-1:v0.3' },
      stage_goal_source: { source_system: 'SYS05', source_ref: 'teaching_action:action-1:v0.3', presentation_version: 'ui-stage-copy/1.0' },
      next_directions: [
        { kind: 'TEACHING_DIRECTION', ref: 'activity:a1:v1', label: '练习与巩固', source_system: 'SYS06', source_ref: 'activity:a1:v1' },
        { kind: 'TEACHING_DIRECTION', ref: 'activity:a2:v1', label: '迁移应用', source_system: 'SYS06', source_ref: 'activity:a2:v1' },
        { kind: 'TEACHING_DIRECTION', ref: 'activity:a3:v1', label: '复盘学习方法', source_system: 'SYS06', source_ref: 'activity:a3:v1' },
      ],
      reason_codes: ['EXACT_SYS05_SYS06_CONTEXT_AVAILABLE'],
      ...overrides,
    },
    source_status: [],
  }
}

describe('EXEC-069 Learning Context Drawer', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    workspaceApi.getLearningContext.mockResolvedValue(response())
  })

  it('defaults to one collapsed stage and next-direction line', async () => {
    render(<LearningContextDrawer activityId={activityId} />)

    const trigger = await screen.findByRole('button', { name: /展开学习上下文：引导练习/ })
    expect(trigger).toHaveAttribute('aria-expanded', 'false')
    expect(trigger).toHaveTextContent('引导练习 · 接下来：练习与巩固')
    expect(screen.queryByText('阶段目标')).not.toBeInTheDocument()
    expect(workspaceApi.getLearningContext).toHaveBeenCalledWith(activityId)
  })

  it('expands to stage, stage goal, and at most three canonical directions only', async () => {
    render(<LearningContextDrawer activityId={activityId} />)
    const trigger = await screen.findByRole('button', { name: /展开学习上下文：引导练习/ })
    fireEvent.click(trigger)

    expect(trigger).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByText('当前阶段')).toBeInTheDocument()
    expect(screen.getByText('阶段目标')).toBeInTheDocument()
    expect(screen.getByText('接下来')).toBeInTheDocument()
    expect(screen.getByText('在引导下完成当前任务')).toBeInTheDocument()
    expect(screen.getAllByRole('listitem')).toHaveLength(3)
    expect(workspaceApi.getLearningContext).toHaveBeenCalledTimes(1)
  })

  it.each([
    ['MISSING', { stage_name: null, stage_goal: null, next_directions: [] }, '当前阶段信息不可用'],
    ['PARTIAL', { stage_name: null, stage_goal: null }, '部分信息'],
    ['STALE', {}, '信息可能已过期'],
  ])('presents %s honestly without inferring replacement content', async (viewState, overrides, expected) => {
    workspaceApi.getLearningContext.mockResolvedValue(response(viewState, overrides))
    const { container } = render(<LearningContextDrawer activityId={activityId} />)

    expect(await screen.findByText(new RegExp(expected))).toBeInTheDocument()
    expect(container.querySelector('.learning-context-disclosure')).toHaveAttribute('data-state', viewState)
  })

  it('presents transport failure as ERROR without throwing', async () => {
    workspaceApi.getLearningContext.mockRejectedValue(new Error('network down'))
    const { container } = render(<LearningContextDrawer activityId={activityId} />)

    expect(await screen.findByText(/当前阶段信息读取失败/)).toBeInTheDocument()
    expect(container.querySelector('.learning-context-disclosure')).toHaveAttribute('data-state', 'ERROR')
  })

  it('exposes LOADING while the canonical query is pending', () => {
    workspaceApi.getLearningContext.mockReturnValue(new Promise(() => {}))
    const { container } = render(<LearningContextDrawer activityId={activityId} />)

    expect(screen.getByText('正在读取当前阶段 · 接下来')).toBeInTheDocument()
    expect(container.querySelector('.learning-context-disclosure')).toHaveAttribute('data-state', 'LOADING')
  })

  it('collapses on Escape and returns focus to the disclosure trigger', async () => {
    render(<LearningContextDrawer activityId={activityId} />)
    const trigger = await screen.findByRole('button', { name: /展开学习上下文：引导练习/ })
    fireEvent.click(trigger)
    const panel = screen.getByRole('group', { name: '学习上下文详情' })
    fireEvent.keyDown(panel, { key: 'Escape' })

    await waitFor(() => expect(trigger).toHaveFocus())
    expect(trigger).toHaveAttribute('aria-expanded', 'false')
  })
})
