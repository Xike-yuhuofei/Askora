import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as usersApi from '../api/users'
import Settings from '../pages/Settings'
import { RouterProvider } from '../router'

vi.mock('../api/users', () => ({ getSystemConfig: vi.fn() }))
vi.mock('../api/dataControl', () => ({
  createUserExport: vi.fn(),
  downloadUserExport: vi.fn(),
}))
vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({ user: { nickname: '测试用户', status: 'active' }, logout: vi.fn() }),
}))

describe('MODEL-CONFIG-033 renderer credential boundary', () => {
  beforeEach(() => {
    window.location.hash = '#/settings/models'
    usersApi.getSystemConfig.mockResolvedValue({ mode: 'private', llm_ready: false })
  })

  it('never persists or retains a rejected credential after submit', async () => {
    const localSet = vi.spyOn(Storage.prototype, 'setItem')
    window.electronAPI = {
      getModelSettings: vi.fn().mockResolvedValue({
        ok: true,
        settings: {
          schema_version: '1.0', revision: null, state: 'UNCONFIGURED', provider: null,
          model: null, source: 'NONE', verified_at: null, runtime_ready: false,
          runtime_revision: null, reason_codes: ['MODEL_CREDENTIAL_MISSING'],
        },
      }),
      applyModelSettings: vi.fn().mockResolvedValue({
        ok: false,
        error: {
          code: 'MODEL_CREDENTIAL_REJECTED',
          category: 'authorization',
          message: '模型凭据被 provider 拒绝，请更新后重试',
          retryable: false,
        },
      }),
    }
    render(<RouterProvider><Settings /></RouterProvider>)

    const key = await screen.findByLabelText('API Key')
    fireEvent.change(key, { target: { value: 'sk-must-not-persist' } })
    fireEvent.click(screen.getByRole('button', { name: '验证并应用' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('模型凭据被 provider 拒绝')
    expect(key).toHaveValue('')
    expect(document.body).not.toHaveTextContent('sk-must-not-persist')
    expect(localSet.mock.calls.some(([, value]) => String(value).includes('sk-must-not-persist'))).toBe(false)
    localSet.mockRestore()
  })
})
