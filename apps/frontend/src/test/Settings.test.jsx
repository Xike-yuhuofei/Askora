import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as usersApi from '../api/users'
import Settings from '../pages/Settings'
import { RouterProvider } from '../router'

const logout = vi.fn()

vi.mock('../api/users', () => ({ getSystemConfig: vi.fn() }))
vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({ user: { nickname: '测试用户', status: 'active' }, logout }),
}))

describe('UI-SCREEN-090 / UI01-VSLICE-AC-008 settings', () => {
  beforeEach(() => {
    window.location.hash = '#/settings'
    logout.mockReset()
    usersApi.getSystemConfig.mockReset()
    usersApi.getSystemConfig.mockResolvedValue({ mode: 'private', llm_ready: false })
  })

  it('states the private runtime boundary without exposing credentials', async () => {
    render(<RouterProvider><Settings /></RouterProvider>)

    expect(await screen.findByText('私人使用')).toBeInTheDocument()
    expect(screen.getByText('未配置，将使用模拟回复')).toBeInTheDocument()
    expect(screen.queryByText(/api[_ -]?key/i)).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: '打开恢复中心' })).toBeInTheDocument()
  })

  it('describes logout as local-session clearing and returns to login', async () => {
    logout.mockResolvedValue(undefined)
    render(<RouterProvider><Settings /></RouterProvider>)

    expect(screen.getByText(/不会删除服务端学习数据/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /退出并清除本地登录信息/ }))
    await waitFor(() => expect(logout).toHaveBeenCalledTimes(1))
    await waitFor(() => expect(window.location.hash).toBe('#/login'))
  })
})
