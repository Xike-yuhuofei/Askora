import { render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const authApi = vi.hoisted(() => ({
  devAutoLogin: vi.fn(),
  getMe: vi.fn(),
  loginWithPhone: vi.fn(),
  logout: vi.fn(),
  registerWithPhone: vi.fn(),
  changePassword: vi.fn(),
  listSessions: vi.fn(),
  revokeOtherSessions: vi.fn(),
  revokeSession: vi.fn(),
}))

vi.mock('../api/auth', () => authApi)
vi.mock('../api/client', () => ({ getOrCreateDeviceFingerprint: vi.fn() }))

async function renderAuthProbe(autoLoginValue) {
  vi.stubEnv('VITE_ENABLE_DEV_AUTO_LOGIN', autoLoginValue)
  vi.resetModules()
  const { AuthProvider, useAuth } = await import('../hooks/useAuth')

  function Probe() {
    const { loading, user } = useAuth()
    return <div>{loading ? 'loading' : (user?.nickname || 'anonymous')}</div>
  }

  render(<AuthProvider><Probe /></AuthProvider>)
}

describe('UI-SCREEN-AC-008 explicit dev auto-login boundary', () => {
  beforeEach(() => {
    localStorage.clear()
    authApi.devAutoLogin.mockReset()
    authApi.getMe.mockReset()
  })

  afterEach(() => {
    vi.unstubAllEnvs()
  })

  it('does not call the development endpoint unless the flag is exactly true', async () => {
    await renderAuthProbe('false')

    expect(await screen.findByText('anonymous')).toBeInTheDocument()
    expect(authApi.devAutoLogin).not.toHaveBeenCalled()
  })

  it('uses the explicit development endpoint when the flag is true', async () => {
    authApi.devAutoLogin.mockResolvedValue({
      access_token: 'development-token',
      refresh_token: 'development-refresh',
      user: { id: 'dev-user', nickname: '开发用户' },
    })
    await renderAuthProbe('true')

    expect(await screen.findByText('开发用户')).toBeInTheDocument()
    await waitFor(() => expect(authApi.devAutoLogin).toHaveBeenCalledTimes(1))
    expect(localStorage.getItem('access_token')).toBe('development-token')
  })
})
