import { fireEvent, render, screen, waitFor } from '@testing-library/react'
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
    expect(screen.getByText('未配置，将使用模拟回复')).toBeInTheDocument()
    expect(screen.queryByText(/api[_ -]?key/i)).not.toBeInTheDocument()
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
