import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as workspaceApi from '../api/workspace'
import CourseCreate from '../pages/CourseCreate'
import { RouterProvider } from '../router'

vi.mock('../api/workspace', () => ({
  listWorkspaces: vi.fn(),
  createWorkspace: vi.fn(),
  clearTransitionGuard: vi.fn(() => ({
    composer_draft: 'CLEAR',
    stream: 'CLEAR',
    user_note: 'CLEAR',
    material_position: 'PRESERVED',
  })),
}))

const navigate = vi.fn()
vi.mock('../router', async () => {
  const mod = await vi.importActual('../router')
  return { ...mod, useNavigate: () => navigate }
})

describe('UI-COURSE-005 create space', () => {
  beforeEach(() => {
    navigate.mockReset()
    workspaceApi.listWorkspaces.mockReset()
    workspaceApi.createWorkspace.mockReset()
    workspaceApi.listWorkspaces.mockResolvedValue({ data: { selection_version: 1, workspaces: [] } })
  })

  it('does not create a space until the form is submitted', async () => {
    render(<RouterProvider><CourseCreate /></RouterProvider>)
    expect(await screen.findByRole('heading', { name: '新建空间' })).toBeInTheDocument()
    expect(workspaceApi.createWorkspace).not.toHaveBeenCalled()
    expect(screen.getByText(/打开此页不会创建空间/)).toBeInTheDocument()
    expect(screen.getByPlaceholderText('例如：我的学习空间')).toBeInTheDocument()
  })

  it('submits the Workspace create command and opens the new space', async () => {
    workspaceApi.createWorkspace.mockResolvedValue({
      outcome: 'CREATED_AND_SELECTED',
      workspace: { workspace_id: 'ws-created' },
    })
    render(<RouterProvider><CourseCreate /></RouterProvider>)
    fireEvent.change(await screen.findByLabelText('空间名称'), { target: { value: '线性代数' } })
    fireEvent.click(screen.getByRole('button', { name: '创建空间' }))
    await waitFor(() => expect(workspaceApi.createWorkspace).toHaveBeenCalled())
    expect(workspaceApi.createWorkspace.mock.calls[0][0]).toMatchObject({
      display_name: '线性代数',
      expected_selection_version: 1,
    })
    expect(navigate).toHaveBeenCalledWith('/courses/ws-created')
  })
})
