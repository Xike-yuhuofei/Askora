import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as workspaceApi from '../api/workspace'
import AppShell from '../components/AppShell'
import { RouterProvider } from '../router'

vi.mock('../api/workspace', () => ({
  getWorkspaceContext: vi.fn(),
  listWorkspaces: vi.fn(),
  listWorkspaceActivities: vi.fn(),
  conversationHref: vi.fn(),
}))

const payload = {
  schema_version: '1.0',
  generated_at: '2026-08-11T08:00:00Z',
  data: {
    view_state: 'READY',
    current_workspace: {
      workspace_id: '5c9d33f4-e565-4bf9-8a62-d235a1cb4168',
      workspace_ref: 'workspace:5c9d33f4-e565-4bf9-8a62-d235a1cb4168:v2',
      display_name: '高等数学',
      version: 2,
      lifecycle: 'active',
      is_default: true,
    },
    switch_capability: 'SINGLE_WORKSPACE',
  },
  source_status: [{
    source_system: 'PLATFORM_WORKSPACE',
    availability: 'AVAILABLE',
    source_ref: 'workspace:5c9d33f4-e565-4bf9-8a62-d235a1cb4168:v2',
    reason_codes: ['CANONICAL_DEFAULT_WORKSPACE'],
  }],
  correlation_id: 'exec068-test',
}

describe('EXEC068 canonical Workspace context', () => {
  beforeEach(() => {
    workspaceApi.getWorkspaceContext.mockReset()
    workspaceApi.listWorkspaces.mockReset()
    workspaceApi.listWorkspaceActivities.mockReset()
    workspaceApi.listWorkspaces.mockResolvedValue({ data: { workspaces: [] } })
    workspaceApi.listWorkspaceActivities.mockResolvedValue({ data: { activities: [] } })
  })

  it('shares the exact owner-provided workspace id across all three columns', async () => {
    workspaceApi.getWorkspaceContext.mockResolvedValue(payload)
    const { container } = render(
      <RouterProvider>
        <AppShell variant="workspace"><div>Primary Learning Canvas</div></AppShell>
      </RouterProvider>,
    )

    expect(screen.getByRole('status', { name: '加载空间中' })).toBeInTheDocument()
    await screen.findByText('高等数学')

    const scopedRegions = container.querySelectorAll('[data-workspace-id="5c9d33f4-e565-4bf9-8a62-d235a1cb4168"]')
    expect(scopedRegions.length).toBeGreaterThanOrEqual(4)
    expect(screen.getByLabelText('当前空间：高等数学')).toBeInTheDocument()
    expect(container.querySelector('.ds-shell-three-panel')).not.toBeNull()
    expect(container.querySelector('.ds-shell-three-panel__center')).not.toBeNull()
    const notes = screen.getByLabelText('参考资料与笔记')
    expect(notes.className).toContain('right-rail')
    expect(notes.className).toContain('ds-shell-three-panel__right')
    expect(notes.closest('#main-content')).toBeNull()
    expect(container.querySelector('.app-shell > .right-rail')).toBe(notes)
    // TraeWork-style window title bar keeps traffic dots + panel controls
    // visible regardless of collapse state.
    const titlebar = container.querySelector('.app-titlebar')
    expect(titlebar).not.toBeNull()
    expect(titlebar.querySelector('.traffic-dots')).not.toBeNull()
    expect(screen.getByRole('button', { name: '收起左侧栏' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '收起右侧栏' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '收起左侧栏' }))
    fireEvent.click(screen.getByRole('button', { name: '收起右侧栏' }))
    expect(container.querySelector('.app-shell')).toHaveClass('app-shell--nav-collapsed')
    expect(container.querySelector('.app-shell')).toHaveClass('app-shell--rail-collapsed')
    // While collapsed, expand controls live in the title bar and a
    // "new chat" shortcut appears next to the search button.
    expect(titlebar.querySelector('.traffic-dots')).not.toBeNull()
    expect(titlebar.querySelector('button[aria-label="新建对话"]')).not.toBeNull()
    fireEvent.click(screen.getByRole('button', { name: '展开左侧栏' }))
    fireEvent.click(screen.getAllByRole('button', { name: '展开右侧栏' })[0])
    expect(container.querySelector('.app-shell')).not.toHaveClass('app-shell--nav-collapsed')
    expect(container.querySelector('.app-shell')).not.toHaveClass('app-shell--rail-collapsed')
    expect(titlebar.querySelector('button[aria-label="新建对话"]')).toBeNull()
    expect(screen.queryByRole('combobox')).not.toBeInTheDocument()
    expect(screen.queryByText('点击切换')).not.toBeInTheDocument()
    expect(workspaceApi.getWorkspaceContext).toHaveBeenCalledTimes(1)
  })

  it('shows an honest error without inventing a default Workspace', async () => {
    workspaceApi.getWorkspaceContext.mockRejectedValue(new Error('offline'))
    render(
      <RouterProvider>
        <AppShell variant="workspace"><div>Primary Learning Canvas</div></AppShell>
      </RouterProvider>,
    )

    await waitFor(() => expect(screen.getByText('暂时不可用')).toBeInTheDocument())
    expect(screen.queryByText('默认工作区')).not.toBeInTheDocument()
    expect(screen.getByText('Primary Learning Canvas')).toBeInTheDocument()
  })
})
