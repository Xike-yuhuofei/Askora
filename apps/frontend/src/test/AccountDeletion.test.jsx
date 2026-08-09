import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as accountApi from '../api/account'
import AccountDeletion from '../pages/AccountDeletion'
import { RouterProvider } from '../router'

const clearForDeletion = vi.fn()

vi.mock('../api/account', () => ({
  previewDeletion: vi.fn(),
  requestDeletion: vi.fn(),
  getDeletionStatus: vi.fn(),
  cancelDeletion: vi.fn(),
  retryDeletion: vi.fn(),
}))
vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({ user: { id: 'user-1' }, clearForDeletion }),
}))

const preview = {
  preview_id: '1ec85cbd-14dc-4ab0-9657-4adb1c9fc888',
  policy_version: 'account-deletion-v1',
  preview_digest: `sha256:${'a'.repeat(64)}`,
  counts_by_owner: { SYS01: 2, SYS03: 1 },
  file_count: 1,
  pending_task_count: 1,
  blocking_issues: [],
}

describe('IDP-072 account deletion journey', () => {
  beforeEach(() => {
    window.location.hash = '#/settings/delete-account'
    sessionStorage.clear()
    clearForDeletion.mockReset()
    Object.values(accountApi).forEach((mock) => mock.mockReset())
  })

  it('requires preview, current password and exact typed phrase before pending', async () => {
    accountApi.previewDeletion.mockResolvedValue(preview)
    accountApi.requestDeletion.mockResolvedValue({
      deletion_control_token: 'deletion-control-token-that-is-long-enough',
      status: {
        request_id: 'fbab6d88-1fe8-47cf-875f-6ca645c9d432',
        lifecycle: 'deletion_pending',
        purge_due_at: '2026-08-10T03:00:00Z',
        cancellable: true,
      },
    })
    render(<RouterProvider><AccountDeletion /></RouterProvider>)

    fireEvent.click(screen.getByRole('button', { name: '生成删除清单' }))
    expect(await screen.findByText('3 条记录')).toBeInTheDocument()
    const submit = screen.getByRole('button', { name: '确认进入删除等待期' })
    expect(submit).toBeDisabled()
    fireEvent.change(screen.getByLabelText('当前密码'), {
      target: { value: 'Askora current password 2026' },
    })
    fireEvent.change(screen.getByLabelText(/输入确认短语/), {
      target: { value: '永久删除我的 Askora 账号' },
    })
    expect(submit).toBeEnabled()
    fireEvent.click(submit)

    await waitFor(() => expect(accountApi.requestDeletion).toHaveBeenCalledTimes(1))
    expect(clearForDeletion).toHaveBeenCalledTimes(1)
    expect(sessionStorage.getItem('account_deletion_control')).toBe(
      'deletion-control-token-that-is-long-enough',
    )
    expect(await screen.findByText(/服务端会按计划继续执行清除/)).toBeInTheDocument()
  })

  it('restores status from session-scoped control and never offers cancel while purging', async () => {
    sessionStorage.setItem('account_deletion_control', 'retained-control-token')
    accountApi.getDeletionStatus.mockResolvedValue({
      request_id: 'fbab6d88-1fe8-47cf-875f-6ca645c9d432',
      lifecycle: 'purging',
      purge_due_at: '2026-08-10T03:00:00Z',
      cancellable: false,
    })
    render(<RouterProvider><AccountDeletion /></RouterProvider>)

    expect(await screen.findByText('当前状态：purging')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: '取消删除' })).not.toBeInTheDocument()
  })

  it('retains completed status across refresh until explicit local dismissal', async () => {
    sessionStorage.setItem('account_deletion_control', 'completed-control-token')
    accountApi.getDeletionStatus.mockResolvedValue({
      request_id: 'fbab6d88-1fe8-47cf-875f-6ca645c9d432',
      lifecycle: 'deleted',
      purge_due_at: '2026-08-10T03:00:00Z',
      cancellable: false,
    })
    render(<RouterProvider><AccountDeletion /></RouterProvider>)

    expect(await screen.findByText('当前状态：deleted')).toBeInTheDocument()
    expect(sessionStorage.getItem('account_deletion_control')).toBe('completed-control-token')
    fireEvent.click(screen.getByRole('button', { name: '完成并清除本地状态' }))
    expect(sessionStorage.getItem('account_deletion_control')).toBeNull()
    expect(window.location.hash).toBe('#/login')
  })

  it('reports post-erasure maintenance as server-side automatic while it runs', async () => {
    sessionStorage.setItem('account_deletion_control', 'maintenance-control-token')
    accountApi.getDeletionStatus.mockResolvedValue({
      request_id: 'fbab6d88-1fe8-47cf-875f-6ca645c9d432',
      lifecycle: 'purging',
      purge_due_at: '2026-08-10T03:00:00Z',
      cancellable: false,
      requires_post_erasure_maintenance: true,
    })
    render(<RouterProvider><AccountDeletion /></RouterProvider>)

    expect(await screen.findByText(/完成前不会显示“已删除”/)).toBeInTheDocument()
    expect(screen.getByText(/系统正在自动完成恢复基线失效与删除后恢复基线/)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: '完成防复活维护' })).not.toBeInTheDocument()
  })
})
