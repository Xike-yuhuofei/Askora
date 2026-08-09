import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as usersApi from '../api/users'
import * as dataControlApi from '../api/dataControl'
import Settings from '../pages/Settings'
import { RouterProvider } from '../router'

const logout = vi.fn()

vi.mock('../api/users', () => ({ getSystemConfig: vi.fn() }))
vi.mock('../api/dataControl', () => ({
  createUserExport: vi.fn(),
  downloadUserExport: vi.fn(),
}))
vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({ user: { nickname: '测试用户', status: 'active' }, logout }),
}))

describe('UI-SCREEN-090 / UI01-VSLICE-AC-008 settings', () => {
  beforeEach(() => {
    window.location.hash = '#/settings'
    logout.mockReset()
    usersApi.getSystemConfig.mockReset()
    usersApi.getSystemConfig.mockResolvedValue({ mode: 'private', llm_ready: false })
    dataControlApi.createUserExport.mockReset()
    dataControlApi.downloadUserExport.mockReset()
    delete window.electronAPI
  })

  it('states the private runtime boundary without exposing credentials', async () => {
    render(<RouterProvider><Settings /></RouterProvider>)

    expect(await screen.findByText('私人使用')).toBeInTheDocument()
    expect(screen.getAllByText('未配置').length).toBeGreaterThan(0)
    expect(screen.getByText(/仅在 macOS 桌面 App 中提供安全写入/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '打开恢复中心' })).toBeInTheDocument()
  })

  it('shows the exact secret-free desktop model revision', async () => {
    window.electronAPI = {
      getModelSettings: vi.fn().mockResolvedValue({
        ok: true,
        settings: {
          schema_version: '1.0',
          revision: 4,
          state: 'ACTIVE',
          provider: 'deepseek',
          model: 'deepseek-chat',
          source: 'DESKTOP_VAULT',
          verified_at: '2026-08-09T06:00:00Z',
          runtime_ready: true,
          runtime_revision: 4,
          reason_codes: [],
        },
      }),
    }

    render(<RouterProvider><Settings /></RouterProvider>)

    expect(await screen.findByText('已验证')).toBeInTheDocument()
    expect(screen.getByText('DeepSeek')).toBeInTheDocument()
    expect(screen.getByText('deepseek-chat')).toBeInTheDocument()
    expect(screen.getByText('App 安全存储')).toBeInTheDocument()
    expect(screen.getByText('4')).toBeInTheDocument()
    expect(document.body).not.toHaveTextContent('sk-secret-value')
  })

  it('validates and applies through the narrow bridge, then clears the credential field', async () => {
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

    const keyField = await screen.findByLabelText('API Key')
    fireEvent.change(screen.getByLabelText('Provider'), { target: { value: 'deepseek' } })
    fireEvent.change(keyField, { target: { value: 'sk-secret-value' } })
    fireEvent.click(screen.getByRole('button', { name: '验证并应用' }))

    expect(applyModelSettings).toHaveBeenCalledWith({
      schema_version: '1.0',
      provider: 'deepseek',
      model: 'deepseek-chat',
      api_key: 'sk-secret-value',
      expected_revision: null,
    })
    expect(keyField).toHaveValue('')
    expect(screen.getByRole('button', { name: '正在验证…' })).toBeDisabled()

    resolveApply({
      ok: true,
      settings: {
        schema_version: '1.0', revision: 1, state: 'ACTIVE', provider: 'deepseek',
        model: 'deepseek-chat', source: 'DESKTOP_VAULT', verified_at: '2026-08-09T06:00:00Z',
        runtime_ready: true, runtime_revision: 1, reason_codes: [],
      },
    })
    expect(await screen.findByText('模型配置已验证并应用。')).toBeInTheDocument()
    expect(screen.getByText('已验证')).toBeInTheDocument()
  })

  it('requires a second explicit action before writing a DISABLED tombstone', async () => {
    const clearModelSettings = vi.fn().mockResolvedValue({
      ok: true,
      settings: {
        schema_version: '1.0', revision: 6, state: 'DISABLED', provider: null,
        model: null, source: 'DESKTOP_VAULT', verified_at: '2026-08-09T06:00:00Z',
        runtime_ready: false, runtime_revision: 6, reason_codes: ['MODEL_CONFIGURATION_DISABLED'],
      },
    })
    window.electronAPI = {
      getModelSettings: vi.fn().mockResolvedValue({
        ok: true,
        settings: {
          schema_version: '1.0', revision: 5, state: 'ACTIVE', provider: 'zhipu',
          model: 'glm-4.7-flash', source: 'DESKTOP_VAULT', verified_at: '2026-08-09T05:00:00Z',
          runtime_ready: true, runtime_revision: 5, reason_codes: [],
        },
      }),
      applyModelSettings: vi.fn(),
      clearModelSettings,
    }
    render(<RouterProvider><Settings /></RouterProvider>)

    fireEvent.click(await screen.findByRole('button', { name: '停用 App 模型配置' }))
    expect(clearModelSettings).not.toHaveBeenCalled()
    fireEvent.click(screen.getByRole('button', { name: '确认停用' }))
    await waitFor(() => expect(clearModelSettings).toHaveBeenCalledWith({
      schema_version: '1.0',
      expected_revision: 5,
    }))
    expect(await screen.findByText('已停用')).toBeInTheDocument()
  })

  it('reloads the owner revision after a concurrent update conflict', async () => {
    const getModelSettings = vi.fn()
      .mockResolvedValueOnce({
        ok: true,
        settings: {
          schema_version: '1.0', revision: 2, state: 'ACTIVE', provider: 'qwen',
          model: 'qwen-turbo', source: 'DESKTOP_VAULT', verified_at: '2026-08-09T05:00:00Z',
          runtime_ready: true, runtime_revision: 2, reason_codes: [],
        },
      })
      .mockResolvedValueOnce({
        ok: true,
        settings: {
          schema_version: '1.0', revision: 3, state: 'ACTIVE', provider: 'deepseek',
          model: 'deepseek-chat', source: 'DESKTOP_VAULT', verified_at: '2026-08-09T06:00:00Z',
          runtime_ready: true, runtime_revision: 3, reason_codes: [],
        },
      })
    window.electronAPI = {
      getModelSettings,
      applyModelSettings: vi.fn().mockResolvedValue({
        ok: false,
        error: {
          code: 'MODEL_CONFIG_REVISION_CONFLICT',
          message: '配置已在其他操作中更新，请重新确认。',
        },
      }),
    }
    render(<RouterProvider><Settings /></RouterProvider>)

    const key = await screen.findByLabelText('API Key')
    fireEvent.change(key, { target: { value: 'sk-conflict-value' } })
    fireEvent.click(screen.getByRole('button', { name: '验证并应用' }))

    expect(await screen.findByText('配置已在其他操作中更新，请重新确认。')).toBeInTheDocument()
    expect(getModelSettings).toHaveBeenCalledTimes(2)
    const panel = screen.getByRole('heading', { name: '模型与密钥' }).closest('section')
    expect(within(panel).getByText('DeepSeek', { selector: 'dd' })).toBeInTheDocument()
    expect(within(panel).getByText('3', { selector: 'dd' })).toBeInTheDocument()
    expect(key).toHaveValue('')
  })

  it('keeps the prior revision available when apply rollback succeeds', async () => {
    window.electronAPI = {
      getModelSettings: vi.fn().mockResolvedValue({
        ok: true,
        settings: {
          schema_version: '1.0', revision: 7, state: 'ACTIVE', provider: 'qwen',
          model: 'qwen-turbo', source: 'DESKTOP_VAULT', verified_at: '2026-08-09T05:00:00Z',
          runtime_ready: true, runtime_revision: 7, reason_codes: [],
        },
      }),
      applyModelSettings: vi.fn().mockResolvedValue({
        ok: false,
        rollback_succeeded: true,
        settings: {
          schema_version: '1.0', revision: 7, state: 'ACTIVE', provider: 'qwen',
          model: 'qwen-turbo', source: 'DESKTOP_VAULT', verified_at: '2026-08-09T05:00:00Z',
          runtime_ready: true, runtime_revision: 7, reason_codes: [],
        },
        error: { code: 'MODEL_PROVIDER_UNAVAILABLE', message: '模型连接测试失败。' },
      }),
    }
    render(<RouterProvider><Settings /></RouterProvider>)

    const key = await screen.findByLabelText('API Key')
    fireEvent.change(key, { target: { value: 'sk-unavailable-value' } })
    fireEvent.click(screen.getByRole('button', { name: '验证并应用' }))

    expect(await screen.findByText('应用失败已恢复')).toBeInTheDocument()
    expect(screen.getByText('旧配置仍可用；本次候选已丢弃。')).toBeInTheDocument()
    const panel = screen.getByRole('heading', { name: '模型与密钥' }).closest('section')
    expect(within(panel).queryByRole('button', { name: '打开恢复中心' })).not.toBeInTheDocument()
  })

  it('routes unrecoverable apply failure to the recovery center', async () => {
    window.electronAPI = {
      getModelSettings: vi.fn().mockResolvedValue({
        ok: true,
        settings: {
          schema_version: '1.0', revision: 8, state: 'ACTIVE', provider: 'qwen',
          model: 'qwen-turbo', source: 'DESKTOP_VAULT', verified_at: '2026-08-09T05:00:00Z',
          runtime_ready: true, runtime_revision: 8, reason_codes: [],
        },
      }),
      applyModelSettings: vi.fn().mockResolvedValue({
        ok: false,
        rollback_succeeded: false,
        error: { code: 'MODEL_CONFIG_ROLLBACK_FAILED', message: '旧配置恢复失败。' },
      }),
    }
    render(<RouterProvider><Settings /></RouterProvider>)

    const key = await screen.findByLabelText('API Key')
    fireEvent.change(key, { target: { value: 'sk-rollback-value' } })
    fireEvent.click(screen.getByRole('button', { name: '验证并应用' }))

    expect(await screen.findByText('恢复失败')).toBeInTheDocument()
    const panel = screen.getByRole('heading', { name: '模型与密钥' }).closest('section')
    fireEvent.click(within(panel).getByRole('button', { name: '打开恢复中心' }))
    expect(window.location.hash).toBe('#/settings/recovery')
  })

  it('shows external configuration as read-only and never offers App disable', async () => {
    window.electronAPI = {
      getModelSettings: vi.fn().mockResolvedValue({
        ok: true,
        settings: {
          schema_version: '1.0', revision: null, state: 'EXTERNAL_READ_ONLY', provider: 'zhipu',
          model: 'glm-4.7-flash', source: 'EXTERNAL_ENVIRONMENT', verified_at: null,
          runtime_ready: true, runtime_revision: null, reason_codes: [],
        },
      }),
      applyModelSettings: vi.fn(),
      clearModelSettings: vi.fn(),
    }
    render(<RouterProvider><Settings /></RouterProvider>)

    expect((await screen.findAllByText('外部只读配置')).length).toBe(2)
    expect(screen.getByText('外部只读配置', { selector: 'dd' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: '停用 App 模型配置' })).not.toBeInTheDocument()
  })

  it('describes logout as local-session clearing and returns to login', async () => {
    logout.mockResolvedValue(undefined)
    render(<RouterProvider><Settings /></RouterProvider>)

    expect(screen.getByText(/不会删除服务端学习数据/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /退出并清除本地登录信息/ }))
    await waitFor(() => expect(logout).toHaveBeenCalledTimes(1))
    await waitFor(() => expect(window.location.hash).toBe('#/login'))
  })

  it('offers explicit export scopes and keeps document originals opt-in', async () => {
    render(<RouterProvider><Settings /></RouterProvider>)

    expect(await screen.findByRole('heading', { name: '导出我的数据' })).toBeInTheDocument()
    expect(screen.getByRole('checkbox', { name: '账号与画像' })).toBeChecked()
    expect(screen.getByRole('checkbox', { name: '资料元数据' })).toBeChecked()
    expect(screen.getByRole('checkbox', { name: '学习记录' })).toBeChecked()
    expect(screen.getByRole('checkbox', { name: '模型执行记录' })).toBeChecked()
    expect(screen.getByRole('checkbox', { name: '包含资料原件' })).not.toBeChecked()
  })

  it('creates the selected export and reports download completion', async () => {
    dataControlApi.createUserExport.mockResolvedValue({
      schema_version: '1.0',
      export_id: 'export-1',
      created_at: '2026-08-09T00:00:00Z',
      expires_at: '2026-08-09T00:15:00Z',
      download_token: 'download-token-at-least-thirty-two-characters',
      file_count: 4,
      size_bytes: 1024,
    })
    dataControlApi.downloadUserExport.mockResolvedValue(undefined)
    render(<RouterProvider><Settings /></RouterProvider>)

    fireEvent.click(screen.getByRole('checkbox', { name: '模型执行记录' }))
    fireEvent.click(screen.getByRole('checkbox', { name: '包含资料原件' }))
    fireEvent.click(screen.getByRole('button', { name: '创建并下载导出' }))

    expect(await screen.findByText('导出已下载；服务端临时副本已失效。')).toBeInTheDocument()
    expect(dataControlApi.createUserExport).toHaveBeenCalledWith({
      scopes: ['PROFILE', 'DOCUMENTS', 'LEARNING_RECORDS'],
      includeDocumentOriginals: true,
    })
    expect(dataControlApi.downloadUserExport).toHaveBeenCalledWith({
      exportId: 'export-1',
      token: 'download-token-at-least-thirty-two-characters',
    })
  })
})
