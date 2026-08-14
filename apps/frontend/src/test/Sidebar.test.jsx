import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as workspaceApi from '../api/workspace'
import Sidebar from '../components/Sidebar'
import { RouterProvider } from '../router'

vi.mock('../api/workspace', () => ({
  listWorkspaces: vi.fn(),
  listWorkspaceActivities: vi.fn(),
  conversationHref: vi.fn((workspaceId, activityRef) => `/courses/${workspaceId}/activities/${activityRef}`),
}))

describe('UI01-VSLICE-AC-001 responsive navigation', () => {
  beforeEach(() => {
    workspaceApi.listWorkspaces.mockReset()
    workspaceApi.listWorkspaceActivities.mockReset()
    workspaceApi.listWorkspaces.mockResolvedValue({ data: { workspaces: [] } })
    workspaceApi.listWorkspaceActivities.mockResolvedValue({ data: { activities: [] } })
  })

  it('exposes space management, library and account settings without a Welcome nav item or empty conversation area', async () => {
    render(<RouterProvider><Sidebar /></RouterProvider>)

    expect(screen.getByRole('button', { name: '空间管理' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: '资料库' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: '账户设置' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: '资讯' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: '学习' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: '笔记' })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: '欢迎' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: '新课程' })).not.toBeInTheDocument()
    expect(screen.queryByText('课程')).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: '今天' })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: '学习' })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: '学习目标' })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: '学习历史' })).not.toBeInTheDocument()
    expect(screen.queryByText('Local')).not.toBeInTheDocument()
    expect(screen.queryByText('对话学习')).not.toBeInTheDocument()
    expect(screen.queryByText('私人本地应用')).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: '恢复中心' })).not.toBeInTheDocument()
    await waitFor(() => expect(screen.queryByText('已有对话')).not.toBeInTheDocument())
    expect(screen.queryByText('还没有对话。先上传资料或新建空间。')).not.toBeInTheDocument()
  })

  it('applies the collapsed class from the collapsed prop (toggle lives in the title bar)', () => {
    const { container, rerender } = render(<RouterProvider><Sidebar collapsed={false} /></RouterProvider>)
    expect(container.querySelector('#primary-sidebar')).not.toHaveClass('sidebar--collapsed')
    rerender(<RouterProvider><Sidebar collapsed /></RouterProvider>)
    expect(container.querySelector('#primary-sidebar')).toHaveClass('sidebar--collapsed')
  })

  it('contains focus in the open drawer and returns it on Escape', async () => {
    render(<RouterProvider><Sidebar /></RouterProvider>)
    const trigger = screen.getByRole('button', { name: '打开导航菜单' })
    fireEvent.click(trigger)

    const drawer = screen.getByRole('dialog', { name: '主导航' })
    await waitFor(() => expect(screen.getByRole('link', { name: '资料库' })).toHaveFocus())

    const lastLink = screen.getByRole('link', { name: '账户设置' })
    lastLink.focus()
    fireEvent.keyDown(document, { key: 'Tab' })
    expect(trigger).toHaveFocus()

    fireEvent.keyDown(document, { key: 'Escape' })
    expect(drawer).not.toHaveClass('open')
    expect(trigger).toHaveFocus()
  })
})
