import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as usersApi from '../api/users'
import * as authApi from '../api/auth'
import Settings from '../pages/Settings'
import { RouterProvider } from '../router'

const logout = vi.fn()
const replaceSessionTokens = vi.fn()

vi.mock('../api/users', () => ({ getSystemConfig: vi.fn() }))
vi.mock('../api/auth', () => ({
  changePassword: vi.fn(),
  getRecoveryStatus: vi.fn(),
  issueRecoveryKit: vi.fn(),
  listSessions: vi.fn(),
  revokeOtherSessions: vi.fn(),
  revokeSession: vi.fn(),
}))
vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({ user: { nickname: '测试用户', status: 'active' }, logout, replaceSessionTokens }),
}))

describe('UI-SCREEN-094 / IDP-AC-001 settings identity controls', () => {
  beforeEach(() => {
    window.location.hash = '#/settings'
    logout.mockReset()
    replaceSessionTokens.mockReset()
    usersApi.getSystemConfig.mockReset()
    usersApi.getSystemConfig.mockResolvedValue({ mode: 'private', llm_ready: false })
    authApi.listSessions.mockReset()
    authApi.getRecoveryStatus.mockReset()
    authApi.issueRecoveryKit.mockReset()
    authApi.changePassword.mockReset()
    authApi.revokeOtherSessions.mockReset()
    authApi.revokeSession.mockReset()
    authApi.listSessions.mockResolvedValue({
      sessions: [
        {
          session_id: 'session-current',
          version: 1,
          client_label: 'Askora App 实例 · current',
          current: true,
          revoked: false,
          last_seen_at: '2026-08-09T01:00:00Z',
        },
        {
          session_id: 'session-other',
          version: 1,
          client_label: 'Askora App 实例 · other',
          current: false,
          revoked: false,
          last_seen_at: '2026-08-08T01:00:00Z',
        },
      ],
    })
    authApi.getRecoveryStatus.mockResolvedValue({
      configured: true,
      credential_version: 1,
      created_at: '2026-08-09T01:00:00Z',
    })
  })

  it('states the private runtime boundary without exposing credentials', async () => {
    render(<RouterProvider><Settings /></RouterProvider>)

    expect(await screen.findByText('私人使用')).toBeInTheDocument()
    expect(screen.getByText('未配置，将使用模拟回复')).toBeInTheDocument()
    expect(screen.queryByText(/api[_ -]?key/i)).not.toBeInTheDocument()
  })

  it('describes logout as server-side session revocation and returns to login', async () => {
    logout.mockResolvedValue(undefined)
    render(<RouterProvider><Settings /></RouterProvider>)

    expect(await screen.findByText(/不会删除学习数据/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /退出当前会话/ }))
    await waitFor(() => expect(logout).toHaveBeenCalledTimes(1))
    await waitFor(() => expect(window.location.hash).toBe('#/login'))
  })

  it('changes password, rotates tokens and reports revoked sessions', async () => {
    authApi.changePassword.mockResolvedValue({
      changed: true,
      revoked_other_sessions: 1,
      tokens: { access_token: 'new-access', refresh_token: 'new-refresh' },
    })
    render(<RouterProvider><Settings /></RouterProvider>)

    await screen.findByText('Askora App 实例 · current（当前）')
    fireEvent.change(screen.getByLabelText('当前密码'), { target: { value: 'correct horse battery staple' } })
    fireEvent.change(screen.getByLabelText('新密码'), { target: { value: '新的 Askora 密码 足够长 2026' } })
    fireEvent.change(screen.getByLabelText('确认新密码'), { target: { value: '新的 Askora 密码 足够长 2026' } })
    fireEvent.click(screen.getByRole('button', { name: '修改密码并轮换会话' }))

    await waitFor(() => expect(authApi.changePassword).toHaveBeenCalledTimes(1))
    expect(replaceSessionTokens).toHaveBeenCalledWith({ access_token: 'new-access', refresh_token: 'new-refresh' })
    expect(await screen.findByText(/已撤销 1 个其他会话/)).toBeInTheDocument()
  })

  it('labels instances as untrusted display data and can revoke another session', async () => {
    authApi.revokeSession.mockResolvedValue({ success: true, revoked_sessions: 1 })
    render(<RouterProvider><Settings /></RouterProvider>)

    expect(await screen.findByText(/不代表可信硬件身份/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '撤销' }))
    await waitFor(() => expect(authApi.revokeSession).toHaveBeenCalledWith(
      'session-other', expect.stringMatching(/^revoke-session-/),
    ))
  })

  it('rotates the offline recovery kit and requires explicit storage confirmation', async () => {
    authApi.issueRecoveryKit.mockResolvedValue({
      issued: true,
      replayed: false,
      recovery_secret: 'askora-recovery-new-secret-value',
      credential_version: 2,
      created_at: '2026-08-09T02:00:00Z',
      storage_warning: '请立即离线保存；此恢复套件不会再次显示',
    })
    render(<RouterProvider><Settings /></RouterProvider>)

    expect(await screen.findByText('当前套件版本 1')).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('验证当前密码以轮换恢复套件'), {
      target: { value: 'correct horse battery staple' },
    })
    fireEvent.click(screen.getByRole('button', { name: '轮换恢复套件' }))

    expect(await screen.findByLabelText('新的离线恢复套件')).toHaveTextContent(
      'askora-recovery-new-secret-value',
    )
    const dismiss = screen.getByRole('button', { name: '确认保存并关闭' })
    expect(dismiss).toBeDisabled()
    fireEvent.click(screen.getByRole('checkbox', { name: /已将新套件保存在离线安全位置/ }))
    expect(dismiss).toBeEnabled()
    fireEvent.click(dismiss)
    expect(screen.queryByText('askora-recovery-new-secret-value')).not.toBeInTheDocument()
    expect(window.localStorage.getItem('recovery_secret')).toBeNull()
  })

  it('keeps a recovery rotation error visible after refreshing status', async () => {
    authApi.issueRecoveryKit.mockRejectedValue({
      response: { data: { error: { code: 'AUTH_CURRENT_PASSWORD_INVALID' } } },
    })
    render(<RouterProvider><Settings /></RouterProvider>)

    await screen.findByText('当前套件版本 1')
    fireEvent.change(screen.getByLabelText('验证当前密码以轮换恢复套件'), {
      target: { value: 'wrong current password' },
    })
    fireEvent.click(screen.getByRole('button', { name: '轮换恢复套件' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('当前密码不正确，请重新输入。')
  })

  it('exposes account deletion as a distinct danger operation', async () => {
    render(<RouterProvider><Settings /></RouterProvider>)
    await screen.findByText('私人使用')
    fireEvent.click(screen.getByRole('button', { name: '查看删除范围' }))
    await waitFor(() => expect(window.location.hash).toBe('#/settings/delete-account'))
  })
})
