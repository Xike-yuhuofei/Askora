import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as usersApi from '../api/users'
import * as dataControlApi from '../api/dataControl'
import * as onboardingApi from '../api/onboarding'
import Settings from '../pages/Settings'
import { RouterProvider } from '../router'

vi.mock('../api/users', () => ({ getSystemConfig: vi.fn() }))
vi.mock('../api/dataControl', () => ({
  createUserExport: vi.fn(),
  downloadUserExport: vi.fn(),
  createErasurePreview: vi.fn(),
  confirmErasure: vi.fn(),
}))
vi.mock('../api/onboarding', () => ({
  getOnboardingJourney: vi.fn(),
  reopenOnboarding: vi.fn(),
}))

describe('UI-SCREEN-094 Settings hierarchy and data controls', () => {
  beforeEach(() => {
    window.location.hash = '#/settings'
    usersApi.getSystemConfig.mockReset()
    usersApi.getSystemConfig.mockResolvedValue({
      status: 'ok',
      mode: 'private',
      model_configuration: { provider: 'none', model: 'none', runtime_ready: false },
    })
    dataControlApi.createUserExport.mockReset()
    dataControlApi.downloadUserExport.mockReset()
    dataControlApi.createErasurePreview.mockReset()
    dataControlApi.confirmErasure.mockReset()
    onboardingApi.reopenOnboarding.mockReset()
    onboardingApi.getOnboardingJourney.mockReset()
    onboardingApi.getOnboardingJourney.mockResolvedValue({
      schema_version: '1.0',
      journey_id: 'first-learning-v1',
      generated_at: '2026-08-10T00:00:00Z',
      journey_state: 'ACTIVE',
      should_enter_welcome: true,
      preference: {
        preference_version: 1,
        visibility: 'ACTIVE',
        dismissed_reason: null,
        created_at: '2026-08-10T00:00:00Z',
        updated_at: '2026-08-10T00:00:00Z',
      },
      steps: [],
    })
    onboardingApi.reopenOnboarding.mockResolvedValue({
      schema_version: '1.0',
      journey_id: 'first-learning-v1',
      generated_at: '2026-08-10T00:00:00Z',
      journey_state: 'ACTIVE',
      should_enter_welcome: true,
      preference: {
        preference_version: 2,
        visibility: 'ACTIVE',
        dismissed_reason: null,
        created_at: '2026-08-10T00:00:00Z',
        updated_at: '2026-08-10T00:00:00Z',
      },
      steps: [],
    })
  })

  it('states the runtime boundary without exposing credentials', async () => {
    render(<RouterProvider><Settings /></RouterProvider>)

    expect(screen.getByRole('dialog', { name: '设置' })).toBeInTheDocument()
    expect(await screen.findByText('私人使用')).toBeInTheDocument()
    expect(screen.getAllByText('未配置').length).toBeGreaterThan(0)
    expect(screen.getByRole('button', { name: '打开恢复中心' })).toBeInTheDocument()
    expect(screen.queryByText('账号')).not.toBeInTheDocument()
  })

  it('offers a distinct "重新打开首次引导" action in the 通用 section', async () => {
    render(<RouterProvider><Settings /></RouterProvider>)
    const button = await screen.findByRole('button', { name: /重新打开首次引导/ })
    expect(button).toBeInTheDocument()
  })

  it('calls the onboarding reopen command with the current preference version', async () => {
    render(<RouterProvider><Settings /></RouterProvider>)
    const button = await screen.findByRole('button', { name: /重新打开首次引导/ })
    fireEvent.click(button)
    await waitFor(() => expect(onboardingApi.reopenOnboarding).toHaveBeenCalledTimes(1))
    const call = onboardingApi.reopenOnboarding.mock.calls[0][0]
    expect(call).toHaveProperty('expectedVersion')
    expect(call.expectedVersion).toBeGreaterThanOrEqual(1)
  })

  it('reads model readiness from model_configuration.runtime_ready', async () => {
    usersApi.getSystemConfig.mockResolvedValue({
      status: 'ok',
      mode: 'private',
      model_configuration: { provider: 'qwen', model: 'qwen-coder', runtime_ready: true },
    })
    render(<RouterProvider><Settings /></RouterProvider>)
    expect(await screen.findByText('已配置')).toBeInTheDocument()
  })

  it('disables the AI enhancement toggle with a readable reason when the model is not ready', async () => {
    render(<RouterProvider><Settings /></RouterProvider>)
    const toggle = await screen.findByRole('switch', { name: '用 AI 增强资料解析' })
    expect(toggle).toBeDisabled()
    expect(toggle).not.toBeChecked()
    expect(screen.getByText('用 AI 增强资料解析')).toBeInTheDocument()
    expect(screen.getByText('需先配置可用的本地模型路由，才能开启 AI 增强。')).toBeInTheDocument()
  })

  it('enables the AI enhancement toggle by default and persists the choice when the model is ready', async () => {
    usersApi.getSystemConfig.mockResolvedValue({
      status: 'ok',
      mode: 'private',
      model_configuration: { provider: 'qwen', model: 'qwen-coder', runtime_ready: true },
    })
    render(<RouterProvider><Settings /></RouterProvider>)
    const toggle = await screen.findByRole('switch', { name: '用 AI 增强资料解析' })
    expect(toggle).toBeEnabled()
    expect(toggle).toBeChecked()

    fireEvent.click(toggle)
    expect(toggle).not.toBeChecked()
    expect(await screen.findByText('设置已保存')).toBeInTheDocument()
    await waitFor(() => expect(globalThis.localStorage.getItem('askora:use_ai_parse_enhancement')).toBe('false'))
  })

  it('navigates to data management tab and exposes export scopes', async () => {
    render(<RouterProvider><Settings /></RouterProvider>)

    fireEvent.click(screen.getByRole('button', { name: '数据管理' }))

    expect(await screen.findByRole('heading', { name: '导出我的数据' })).toBeInTheDocument()
    expect(screen.getByRole('checkbox', { name: '偏好与本地画像' })).toBeChecked()
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

    fireEvent.click(screen.getByRole('button', { name: '数据管理' }))
    await screen.findByRole('heading', { name: '导出我的数据' })

    fireEvent.click(screen.getByRole('checkbox', { name: '偏好与本地画像' }))
    fireEvent.click(screen.getByRole('checkbox', { name: '包含资料原件' }))
    fireEvent.click(screen.getByRole('button', { name: '导出全部数据' }))

    expect(await screen.findByText('导出已下载；服务端临时副本已失效。')).toBeInTheDocument()
    expect(dataControlApi.createUserExport).toHaveBeenCalledWith({
      scopes: ['DOCUMENTS', 'LEARNING_RECORDS', 'MODEL_EXECUTION'],
      includeDocumentOriginals: true,
    })
    expect(dataControlApi.downloadUserExport).toHaveBeenCalledWith({
      exportId: 'export-1',
      token: 'download-token-at-least-thirty-two-characters',
    })
  })

  it('previews and explicitly confirms a learning-record erasure', async () => {
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
      status: 'COMPLETED',
      checkpoint: 1,
    })
    render(<RouterProvider><Settings /></RouterProvider>)

    fireEvent.click(screen.getByRole('button', { name: '数据管理' }))
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

    expect(await screen.findByText('删除已提交；受影响数据已删除。')).toBeInTheDocument()
    expect(dataControlApi.confirmErasure).toHaveBeenCalledWith({
      previewId: '11111111-1111-4111-8111-111111111111',
      confirmationToken: 'preview-token-at-least-thirty-two-characters',
      confirmationPhrase: '永久删除 LEARNING_RECORDS',
      idempotencyKey: expect.any(String),
    })
  })

  it('navigates to privacy tab and shows local-first privacy facts', async () => {
    render(<RouterProvider><Settings /></RouterProvider>)

    fireEvent.click(screen.getByRole('button', { name: '隐私与安全' }))

    expect(await screen.findByRole('heading', { name: '隐私与安全事实' })).toBeInTheDocument()
    expect(screen.getByText('本地优先')).toBeInTheDocument()
    expect(screen.getByText('不收集个人身份')).toBeInTheDocument()
  })

  it('navigates to danger tab and shows data reset options', async () => {
    render(<RouterProvider><Settings /></RouterProvider>)

    fireEvent.click(screen.getByRole('button', { name: '危险操作' }))

    expect(await screen.findByRole('heading', { name: '删除本地学习数据' })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: '重置应用' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: '重置应用' })).not.toBeInTheDocument()
  })

  it('closes the settings dialog on Escape and the close control', async () => {
    const onClose = vi.fn()
    render(<RouterProvider><Settings onClose={onClose} /></RouterProvider>)

    expect(screen.getByRole('dialog', { name: '设置' })).toBeInTheDocument()
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(onClose).toHaveBeenCalledTimes(1)

    fireEvent.click(screen.getByRole('button', { name: '关闭设置' }))
    expect(onClose).toHaveBeenCalledTimes(2)
  })
})
