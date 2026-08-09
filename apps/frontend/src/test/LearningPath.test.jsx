import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as workspaceApi from '../api/workspace'
import LearningPath from '../pages/LearningPath'
import { RouterProvider } from '../router'

vi.mock('../api/workspace', () => ({ getLearningPath: vi.fn(), getGoalsWorkspace: vi.fn() }))

const pathPayload = { schema_version: '1.0', data: { view_state: 'PARTIAL', selected_goal_ref: 'learning_goal:g1:v2', available_goal_refs: ['learning_goal:g1:v2'], reason_codes: ['CURRENT_PLAN_AVAILABLE', 'OBJECTIVE_METADATA_UNAVAILABLE'], learning_path: { plan_ref: 'learning_plan:p1:v1', goal_ref: 'learning_goal:g1:v2', status: 'active', created_from_learner_state_version: 3, knowledge_graph_version: 'graph:1', review_schedule_version: null, assumptions: {}, reason_codes: ['PLAN_INITIAL_GENERATION'], objectives: [{ objective_ref: 'learning_objective:o1:v1', capability: null, cognitive_process: null, status: null, activity_refs: ['learning_activity:a2:v1'], reason_codes: ['OBJECTIVE_METADATA_UNAVAILABLE'] }], activities: [{ activity_ref: 'learning_activity:a2:v1', objective_ref: 'learning_objective:o1:v1', type: 'diagnostic', title: '检查当前基础', estimated_duration_minutes: 5, priority: 1, reason_codes: ['PLAN_TARGET_STATE_UNKNOWN'], status: 'available', launch_state: 'REQUIRES_START_COMMAND' }, { activity_ref: 'learning_activity:a1:v1', objective_ref: 'learning_objective:o1:v1', type: 'learn_new', title: '学习新内容', estimated_duration_minutes: 15, priority: 10, reason_codes: ['PLAN_MASTERY_GAP'], status: 'planned', launch_state: 'UNAVAILABLE' }] } }, source_status: [{ source_system: 'SYS06', availability: 'AVAILABLE', reason_codes: [] }] }

describe('UI02B-VSLICE-AC-003/004/008 LearningPath', () => {
  beforeEach(() => { window.location.hash = '#/path'; workspaceApi.getLearningPath.mockReset() })

  it('preserves server activity order and keeps objective metadata missing', async () => {
    workspaceApi.getLearningPath.mockResolvedValue(pathPayload)
    render(<RouterProvider><LearningPath /></RouterProvider>)
    await screen.findByRole('heading', { name: '学习活动' })
    const headings = screen.getAllByRole('heading', { level: 3 })
    expect(headings.map((item) => item.textContent)).toEqual(['检查当前基础', '学习新内容'])
    expect(screen.getByText(/不做推断/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /开始学习/ }))
    await waitFor(() => expect(window.location.hash).toBe('#/learn/a2'))
  })

  it('requires explicit scope when multiple current plans exist', async () => {
    workspaceApi.getLearningPath.mockResolvedValueOnce({ schema_version: '1.0', data: { view_state: 'PARTIAL', selected_goal_ref: null, available_goal_refs: ['learning_goal:g1:v1', 'learning_goal:g2:v1'], learning_path: null, reason_codes: ['MULTIPLE_CURRENT_PLANS_REQUIRE_GOAL_SCOPE'] }, source_status: [] }).mockResolvedValueOnce(pathPayload)
    workspaceApi.getGoalsWorkspace.mockResolvedValue({ data: { goals: [{ goal_ref: 'learning_goal:g1:v1', title: '目标一' }, { goal_ref: 'learning_goal:g2:v1', title: '目标二' }] } })
    render(<RouterProvider><LearningPath /></RouterProvider>)
    const select = await screen.findByLabelText('学习目标')
    expect(screen.getByRole('option', { name: '目标一' })).toBeInTheDocument()
    fireEvent.change(select, { target: { value: 'g1' } })
    await waitFor(() => expect(workspaceApi.getLearningPath).toHaveBeenLastCalledWith('g1'))
  })
})
