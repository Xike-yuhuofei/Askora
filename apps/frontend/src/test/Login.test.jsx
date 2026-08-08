import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import Login from '../pages/Login'
import { RouterProvider } from '../router'

const login = vi.fn()
const register = vi.fn()

vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({ login, register }),
}))

describe('UI-SCREEN-092 / UI01-VSLICE-AC-007 login', () => {
  beforeEach(() => {
    login.mockReset()
    register.mockReset()
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
})
