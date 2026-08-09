import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as usersApi from '../api/users'
import * as dataControlApi from '../api/dataControl'
import Settings from '../pages/Settings'
import { RouterProvider } from '../router'

const logout = vi.fn()

vi.mock('../api/users', () => ({ getSystemConfig: vi.fn() }))
vi.mock('../api/dataControl', () => ({
  getDataControlStatus: vi.fn(),
  createVerifiedBackup: vi.fn(),
  chooseAndVerifyBackup: vi.fn(),
  chooseAndRestoreBackup: vi.fn(),
  revealRecoveryKey: vi.fn(),
  createUserExport: vi.fn(),
  downloadUserExport: vi.fn(),
  createErasurePreview: vi.fn(),
  confirmErasure: vi.fn(),
  finalizeErasure: vi.fn(),
  resumePendingErasure: vi.fn(),
  onMaintenanceState: vi.fn(() => () => {}),
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
    dataControlApi.getDataControlStatus.mockReset()
    dataControlApi.getDataControlStatus.mockResolvedValue({
      schema_version: '1.0',
      protection_state: 'READY',
      supported_mode: 'PRIVATE_DESKTOP_SQLITE',
      last_verified: {
        backup_id: 'backup-1',
        status: 'VERIFIED',
        created_at: '2026-08-09T00:00:00Z',
      },
      automatic_backup: { enabled: true, next_due_at: '2026-08-10T00:00:00Z' },
      erasure_checkpoint: 0,
      reason_codes: [],
    })
    dataControlApi.createVerifiedBackup.mockReset()
    dataControlApi.chooseAndVerifyBackup.mockReset()
    dataControlApi.chooseAndRestoreBackup.mockReset()
    dataControlApi.revealRecoveryKey.mockReset()
    dataControlApi.createErasurePreview.mockReset()
    dataControlApi.confirmErasure.mockReset()
    dataControlApi.finalizeErasure.mockReset()
    dataControlApi.resumePendingErasure.mockReset()
    dataControlApi.onMaintenanceState.mockClear()
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

  it('shows verified recovery status and creates a fresh recovery point', async () => {
    dataControlApi.createVerifiedBackup.mockResolvedValue({
      point: { backup_id: 'backup-2', status: 'VERIFIED' },
      externalCopy: null,
    })
    render(<RouterProvider><Settings /></RouterProvider>)

    expect(await screen.findByRole('heading', { name: '恢复与备份' })).toBeInTheDocument()
    expect(await screen.findByText('已验证保护')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '立即创建恢复点' }))

    expect(await screen.findByText('恢复点已创建并通过完整校验。')).toBeInTheDocument()
    expect(dataControlApi.createVerifiedBackup).toHaveBeenCalledWith({
      saveExternalCopy: false,
    })
  })

  it('previews, explicitly confirms, and finalizes a learning-record erasure', async () => {
    dataControlApi.createErasurePreview.mockResolvedValue({
      preview_id: '11111111-1111-4111-8111-111111111111',
      scope: 'LEARNING_RECORDS',
      target_ref: null,
      confirmation_phrase: '永久删除 LEARNING_RECORDS',
      confirmation_token: 'preview-token-at-least-thirty-two-characters',
      impacts: [{ owner_system: 'SYS03', estimated_records: 4, actions: ['ERASE'] }],
      backup_impact: '旧恢复点将失效并清理。',
      irreversible: true,
      expires_at: '2026-08-09T00:10:00Z',
    })
    dataControlApi.confirmErasure.mockResolvedValue({
      workflow_id: '22222222-2222-4222-8222-222222222222',
      scope: 'LEARNING_RECORDS',
      status: 'AWAITING_RECOVERY_BASELINE',
      checkpoint: 1,
    })
    dataControlApi.finalizeErasure.mockResolvedValue({
      checkpoint: 1,
      post_erasure_point: { status: 'VERIFIED' },
    })
    render(<RouterProvider><Settings /></RouterProvider>)

    expect(await screen.findByRole('heading', { name: '永久删除数据' })).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('删除范围'), {
      target: { value: 'LEARNING_RECORDS' },
    })
    fireEvent.click(screen.getByRole('button', { name: '预览删除影响' }))
    expect(await screen.findByText('SYS03：4 项')).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('输入确认短语'), {
      target: { value: '永久删除 LEARNING_RECORDS' },
    })
    fireEvent.click(screen.getByRole('button', { name: '确认永久删除' }))

    expect(await screen.findByText('删除完成；删除后恢复基线已验证。')).toBeInTheDocument()
    expect(dataControlApi.finalizeErasure).toHaveBeenCalledWith({
      workflowId: '22222222-2222-4222-8222-222222222222',
      checkpoint: 1,
      clearLocalSession: false,
    })
  })

  it('previews every supported erasure scope through the settings UI', async () => {
    dataControlApi.createErasurePreview.mockImplementation(({ scope, targetRef }) => Promise.resolve({
      preview_id: `${scope}-preview`,
      scope,
      target_ref: targetRef,
      confirmation_phrase: `永久删除 ${scope}`,
      confirmation_token: `${scope}-preview-token-at-least-thirty-two-characters`,
      impacts: [{ owner_system: 'DATA_CONTROL', estimated_records: 1, actions: ['ERASE'] }],
      backup_impact: '旧恢复点将失效并清理。',
      irreversible: true,
      expires_at: '2026-08-09T00:10:00Z',
    }))
    render(<RouterProvider><Settings /></RouterProvider>)

    const scopeSelect = await screen.findByLabelText('删除范围')
    const previewButton = screen.getByRole('button', { name: '预览删除影响' })
    const cases = [
      ['DOCUMENT', 'document-current'],
      ['LEARNING_RECORDS', null],
      ['MODEL_EXECUTION', null],
      ['ALL_PERSONAL_DATA', null],
    ]

    for (const [scope, targetRef] of cases) {
      fireEvent.change(scopeSelect, { target: { value: scope } })
      if (scope === 'DOCUMENT') {
        fireEvent.change(screen.getByLabelText('资料 ID'), {
          target: { value: targetRef },
        })
      }
      fireEvent.click(previewButton)
      await waitFor(() => expect(dataControlApi.createErasurePreview).toHaveBeenCalledWith({
        scope,
        targetRef,
      }))
    }

    expect(dataControlApi.createErasurePreview).toHaveBeenCalledTimes(4)
  })

  it('serializes async packaged-window startup before maintenance completes', () => {
    const mainSource = readFileSync(
      path.join(process.cwd(), 'electron', 'main.cjs'),
      'utf8',
    )

    expect(mainSource).toContain('let windowCreationPromise = null')
    expect(mainSource).toContain('function ensureWindow()')
    expect(mainSource).toContain('app.whenReady().then(ensureWindow)')
  })
})
