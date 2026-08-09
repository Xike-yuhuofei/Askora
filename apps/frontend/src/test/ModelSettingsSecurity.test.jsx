import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as usersApi from '../api/users'
import Settings from '../pages/Settings'
import { RouterProvider } from '../router'

vi.mock('../api/users', () => ({ getSystemConfig: vi.fn() }))
vi.mock('../api/dataControl', () => ({
  getDataControlStatus: vi.fn().mockRejectedValue(new Error('desktop bridge unavailable')),
  onMaintenanceState: vi.fn(() => () => {}),
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

    const panel = screen.getByRole('heading', { name: '模型与密钥' }).closest('section')
    expect(await within(panel).findByRole('alert')).toHaveTextContent('模型凭据被 provider 拒绝')
    expect(key).toHaveValue('')
    expect(document.body).not.toHaveTextContent('sk-must-not-persist')
    expect(localSet.mock.calls.some(([, value]) => String(value).includes('sk-must-not-persist'))).toBe(false)
    localSet.mockRestore()
  })

  it('fails closed on an unknown IPC major without rendering unexpected fields', async () => {
    window.electronAPI = {
      getModelSettings: vi.fn().mockResolvedValue({
        ok: true,
        settings: {
          schema_version: '2.0', revision: null, state: 'UNCONFIGURED', provider: null,
          model: null, source: 'NONE', verified_at: null, runtime_ready: false,
          runtime_revision: null, reason_codes: [], api_key: 'must-never-render',
        },
      }),
    }
    const { container } = render(<RouterProvider><Settings /></RouterProvider>)

    expect(await screen.findByText('无法安全读取模型配置')).toBeInTheDocument()
    expect(screen.getByText('请升级 Askora 后重试；当前不会应用或覆盖任何配置。')).toBeInTheDocument()
    expect(container.innerHTML).not.toContain('must-never-render')
  })

  it('clears a submitted credential and blocks duplicate apply while pending', async () => {
    let resolveApply
    const applyModelSettings = vi.fn(() => new Promise((resolve) => { resolveApply = resolve }))
    window.electronAPI = {
      getModelSettings: vi.fn().mockResolvedValue({
        ok: true,
        settings: {
          schema_version: '1.0', revision: null, state: 'UNCONFIGURED', provider: null,
          model: null, source: 'NONE', verified_at: null, runtime_ready: false,
          runtime_revision: null, reason_codes: ['MODEL_CREDENTIAL_MISSING'],
        },
      }),
      applyModelSettings,
    }
    render(<RouterProvider><Settings /></RouterProvider>)

    const key = await screen.findByLabelText('API Key')
    fireEvent.change(key, { target: { value: 'credential-that-must-disappear' } })
    const submit = screen.getByRole('button', { name: '验证并应用' })
    fireEvent.click(submit)
    fireEvent.click(submit)
    expect(applyModelSettings).toHaveBeenCalledTimes(1)
    expect(key).toHaveValue('')
    expect(document.body).not.toHaveTextContent('credential-that-must-disappear')

    resolveApply({
      ok: true,
      settings: {
        schema_version: '1.0', revision: 1, state: 'ACTIVE', provider: 'qwen',
        model: 'qwen-turbo', source: 'DESKTOP_VAULT', verified_at: '2026-08-09T06:00:00Z',
        runtime_ready: true, runtime_revision: 1, reason_codes: [],
      },
    })
    await waitFor(() => expect(screen.getByText('已验证')).toBeInTheDocument())
  })

  it('offers only the fixed recovery command after an unreadable-vault error', async () => {
    const clearModelSettings = vi.fn().mockResolvedValue({
      ok: true,
      settings: {
        schema_version: '1.0', revision: 1, state: 'DISABLED', provider: null,
        model: null, source: 'DESKTOP_VAULT', verified_at: null, runtime_ready: false,
        runtime_revision: 1, reason_codes: ['MODEL_CONFIGURATION_DISABLED'],
      },
    })
    window.electronAPI = {
      getModelSettings: vi.fn().mockResolvedValue({
        ok: false,
        error: { code: 'MODEL_CONFIG_SCHEMA_UNSUPPORTED', category: 'validation', retryable: false },
      }),
      clearModelSettings,
    }
    render(<RouterProvider><Settings /></RouterProvider>)

    expect(await screen.findByText('已保存的配置无法读取')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '重置不可读配置' }))
    expect(screen.getByRole('dialog', { name: '确认重置不可读配置' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '确认重置并停用' }))

    await waitFor(() => expect(clearModelSettings).toHaveBeenCalledWith({
      schema_version: '1.0',
      expected_revision: null,
      recovery_confirmation: 'RESET_UNREADABLE_VAULT',
    }))
  })
})
