import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import Login from '../pages/Login'
import { RouterProvider } from '../router'

const login = vi.fn()
const register = vi.fn()
const recover = vi.fn()

vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({ login, register, recover }),
}))

describe('UI-SCREEN-092 / UI01-VSLICE-AC-007 login', () => {
  beforeEach(() => {
    login.mockReset()
    register.mockReset()
    recover.mockReset()
    window.location.hash = '#/login'
  })

  it('renders the login icon/tab instead of crashing', () => {
    render(<RouterProvider><Login /></RouterProvider>)
    expect(screen.getByRole('heading', { name: 'Askora' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '登录' })).toBeInTheDocument()
    expect(screen.getByLabelText('手机号')).toBeInTheDocument()
  })

  it('validates phone input and navigates to today after a real auth call', async () => {
    login.mockResolvedValue({})
    render(<RouterProvider><Login /></RouterProvider>)

    fireEvent.change(screen.getByLabelText('手机号'), { target: { value: '13800138000' } })
    fireEvent.change(screen.getByLabelText('密码'), { target: { value: 'password123' } })
    fireEvent.click(screen.getByRole('button', { name: '登录' }))

    await waitFor(() => expect(login).toHaveBeenCalledWith('13800138000', 'password123'))
    await waitFor(() => expect(window.location.hash).toBe('#/today'))
  })

  it('exposes an explicit password recovery tab', () => {
    render(<RouterProvider><Login /></RouterProvider>)
    expect(screen.getByRole('tab', { name: '使用恢复套件重设密码' })).toBeInTheDocument()
  })

  it('shows a registration recovery secret once and blocks dismissal until confirmed', async () => {
    register.mockResolvedValue({
      recovery_kit: {
        recovery_secret: 'askora-registration-recovery-secret',
        credential_version: 1,
        storage_warning: '请立即离线保存；离开后不会再次显示。',
      },
    })
    render(<RouterProvider><Login /></RouterProvider>)

    fireEvent.click(screen.getByRole('tab', { name: '注册' }))
    fireEvent.change(screen.getByLabelText('手机号'), { target: { value: '13800138000' } })
    fireEvent.change(screen.getByLabelText('新密码'), { target: { value: 'a sufficiently long password' } })
    fireEvent.change(screen.getByLabelText('确认新密码'), { target: { value: 'a sufficiently long password' } })
    fireEvent.click(screen.getByRole('button', { name: '注册并生成恢复套件' }))

    expect(await screen.findByLabelText('离线恢复套件')).toHaveTextContent(
      'askora-registration-recovery-secret',
    )
    const finish = screen.getByRole('button', { name: '确认并返回登录' })
    expect(finish).toBeDisabled()
    fireEvent.click(screen.getByRole('checkbox', { name: /已将恢复套件保存在离线安全位置/ }))
    expect(finish).toBeEnabled()
    expect(window.localStorage.getItem('recovery_secret')).toBeNull()
  })

  it('recovers a password without creating a logged-in browser session', async () => {
    recover.mockResolvedValue({
      accepted: true,
      replayed: false,
      recovery_secret: 'askora-rotated-recovery-secret',
      recovery_credential_version: 2,
      requires_login: true,
    })
    render(<RouterProvider><Login /></RouterProvider>)

    fireEvent.click(screen.getByRole('tab', { name: '使用恢复套件重设密码' }))
    fireEvent.change(screen.getByLabelText('手机号'), { target: { value: '13800138000' } })
    fireEvent.change(screen.getByLabelText('离线恢复套件'), {
      target: { value: 'askora-original-recovery-secret' },
    })
    fireEvent.change(screen.getByLabelText('新密码'), { target: { value: 'a sufficiently long new password' } })
    fireEvent.change(screen.getByLabelText('确认新密码'), { target: { value: 'a sufficiently long new password' } })
    fireEvent.click(screen.getByRole('button', { name: '重设密码' }))

    await waitFor(() => expect(recover).toHaveBeenCalledWith(
      '13800138000',
      'askora-original-recovery-secret',
      'a sufficiently long new password',
      expect.stringMatching(/^recover-password-/),
    ))
    expect(await screen.findByLabelText('离线恢复套件')).toHaveTextContent(
      'askora-rotated-recovery-secret',
    )
    expect(window.localStorage.getItem('access_token')).toBeNull()
  })
})
