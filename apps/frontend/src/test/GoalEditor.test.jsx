import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as goalApi from '../api/goals'
import * as workspaceApi from '../api/workspace'
import GoalEditor from '../pages/GoalEditor'
import { RouterProvider } from '../router'

vi.mock('../api/goals', () => ({
  suggestSuccessCriteria: vi.fn(), createGoalDraft: vi.fn(), getGoalDraft: vi.fn(),
  updateGoalDraft: vi.fn(), getGoalTargets: vi.fn(), previewGoalDraft: vi.fn(),
  applyGoalDraft: vi.fn(), getGoalDetail: vi.fn(), createEditGoalDraft: vi.fn(),
}))
vi.mock('../api/workspace', () => ({ getLibraryWorkspace: vi.fn() }))

const criterion = {
  criterion_id: '10000000-0000-4000-8000-000000000001',
  cognitive_process: 'explain',
  statement: '独立解释热力学并回应追问',
  evidence_requirements: ['independent_explanation'],
}

const document = {
  document_id: '20000000-0000-4000-8000-000000000001', title: '热力学讲义',
  processing_status: 'completed', knowledge_status: 'PUBLISHED',
}

describe('P1-01A goal editor', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    workspaceApi.getLibraryWorkspace.mockResolvedValue({ data: { documents: [document] } })
  })

  it('creates a multi-source-capable draft with measurable generated criteria', async () => {
    goalApi.suggestSuccessCriteria.mockResolvedValue({ criteria: [criterion] })
    goalApi.createGoalDraft.mockResolvedValue({ draft_id: 'draft-1' })
    render(<RouterProvider><GoalEditor /></RouterProvider>)

    expect(await screen.findByRole('heading', { name: '创建学习目标' })).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('目标名称'), { target: { value: '理解热力学' } })
    fireEvent.change(screen.getByLabelText('学习主题'), { target: { value: '热力学' } })
    fireEvent.change(screen.getByLabelText(/目标能力/), { target: { value: '解释、应用' } })
    fireEvent.click(screen.getByText('热力学讲义'))
    fireEvent.click(screen.getByRole('button', { name: /生成候选/ }))
    expect(await screen.findByDisplayValue('独立解释热力学并回应追问')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '保存为草稿' }))

    await waitFor(() => expect(goalApi.createGoalDraft).toHaveBeenCalledWith(expect.objectContaining({
      source_document_ids: [document.document_id],
      target_capabilities: ['解释', '应用'],
      success_criteria: [criterion],
    })))
  })

  it('shows source evidence cards, requires explicit target selection and previews replan', async () => {
    const draft = {
      draft_id: 'draft-1', draft_version: 1, status: 'draft', title: '热力学', topic: '热力学',
      target_capabilities: ['解释'], application_context: null, deadline_at: null,
      weekly_time_budget_minutes: 70, success_criteria: [criterion],
      source_document_ids: [document.document_id], selected_target_ids: [], targets_confirmed: false,
    }
    const target = { target_id: '30000000-0000-4000-8000-000000000001', name: '熵增', source_name: '热力学讲义', evidence_excerpt: '孤立系统的熵不会减少', recommended_reason: '来自已发布知识' }
    goalApi.getGoalDraft.mockResolvedValue(draft)
    goalApi.getGoalTargets.mockResolvedValue({ targets: [target] })
    goalApi.updateGoalDraft.mockResolvedValue({ ...draft, draft_version: 2, selected_target_ids: [target.target_id], targets_confirmed: true })
    goalApi.previewGoalDraft.mockResolvedValue({ preview_id: 'preview-1', preview_version: 1, draft_version: 2, effective_timing: 'immediate', active_activity_ref: null, target_cards: [target], field_diffs: [], plan_impact: {} })
    render(<RouterProvider><GoalEditor draftId="draft-1" /></RouterProvider>)

    expect(await screen.findByText('孤立系统的熵不会减少')).toBeInTheDocument()
    expect(screen.queryByText(target.target_id)).not.toBeInTheDocument()
    fireEvent.click(screen.getByText('熵增'))
    fireEvent.click(screen.getByRole('button', { name: '确认所选重点' }))
    await waitFor(() => expect(goalApi.updateGoalDraft).toHaveBeenCalledWith('draft-1', expect.objectContaining({ targets_confirmed: true })))
    fireEvent.click(screen.getByRole('button', { name: '生成变更预览' }))
    expect(await screen.findByRole('heading', { name: '目标与计划影响' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '确认并启用目标' })).toBeInTheDocument()
  })
})
