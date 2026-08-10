import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as usersApi from '../api/users'
import * as authApi from '../api/auth'
import * as dataControlApi from '../api/dataControl'
import * as onboardingApi from '../api/onboarding'
import Settings from '../pages/Settings'
import { RouterProvider } from '../router'

const logout = vi.fn()
const replaceSessionTokens = vi.fn()

vi.mock('../api/users', () => ({ getSystemConfig: vi.fn() }))
vi.mock('../api/auth', () => ({
  changePassword: vi.fn(),
  getRecoveryStatus: vi.fn(),
  issueRecoveryKit: vi.fn(),
  listSessions: vi.fn(),
  revokeOtherSessions: vi.fn(),
  revokeSession: vi.fn(),
}))
vi.mock('../api/dataControl', () => ({
  createUserExport: vi.fn(),
  downloadUserExport: vi.fn(),
  createErasurePreview: vi.fn(),
  confirmErasure: vi.fn(),
}))
vi.mock('../api/onboarding', () => ({
  getOnboardingJourney: vi.fn(),
  acknowledgeBoundaries: vi.fn(),
  dismissOnboarding: vi.fn(),
  reopenOnboarding: vi.fn(),
  finishAndDismissOnboarding: vi.fn(),
}))
vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({ user: { nickname: '测试用户', status: 'active' }, logout, replaceSessionTokens }),
}))

describe('UI-SCREEN-094 / IDP-AC-001 settings identity controls', () => {
  beforeEach(() => {
    window.location.hash = '#/settings'
    logout.mockReset()
    replaceSessionTokens.mockReset()
    usersApi.getSystemConfig.mockReset()
    usersApi.getSystemConfig.mockResolvedValue({ mode: 'private', llm_ready: false })
    authApi.listSessions.mockReset()
    authApi.getRecoveryStatus.mockReset()
    authApi.issueRecoveryKit.mockReset()
    authApi.changePassword.mockReset()
    authApi.revokeOtherSessions.mockReset()
    authApi.revokeSession.mockReset()
    authApi.listSessions.mockResolvedValue({
      sessions: [
        {
          session_id: 'session-current',
          version: 1,
          client_label: 'Askora App 实例 · current',
          current: true,
          revoked: false,
          last_seen_at: '2026-08-09T01:00:00Z',
        },
        {
          session_id: 'session-other',
          version: 1,
          client_label: 'Askora App 实例 · other',
          current: false,
          revoked: false,
          last_seen_at: '2026-08-08T01:00:00Z',
        },
      ],
    })
    authApi.getRecoveryStatus.mockResolvedValue({
      configured: true,
      credential_version: 1,
      created_at: '2026-08-09T01:00:00Z',
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
      boundary_notice: {
        notice_version: 'privacy-and-model-v1',
        acknowledged: false,
        data_control_route: '/settings/data',
        model_settings_route: '/settings#model',
      },
      steps: [],
      next_action: { action_code: 'ACKNOWLEDGE_BOUNDARIES', kind: 'command', label: '我已了解，开始设置', enabled: true, route: null, resource_ref: null, recovery_action: null, reason_codes: [] },
      correlation_id: 'corr-1',
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
      boundary_notice: {
        notice_version: 'privacy-and-model-v1',
        acknowledged: false,
        data_control_route: '/settings/data',
        model_settings_route: '/settings#model',
      },
      steps: [],
      next_action: { action_code: 'ACKNOWLEDGE_BOUNDARIES', kind: 'command', label: '我已了解，开始设置', enabled: true, route: null, resource_ref: null, recovery_action: null, reason_codes: [] },
      correlation_id: 'corr-1',
    })
  })

  it('states the runtime boundary without exposing credentials', async () => {
    render(<RouterProvider><Settings /></RouterProvider>)

    expect(await screen.findByText('私人使用')).toBeInTheDocument()
    expect(screen.getAllByText('未配置').length).toBeGreaterThan(0)
    expect(screen.getByRole('button', { name: '打开恢复中心' })).toBeInTheDocument()
  })

  it('describes logout as server-side session revocation and returns to login', async () => {
    logout.mockResolvedValue(undefined)
    render(<RouterProvider><Settings /></RouterProvider>)

    expect(await screen.findByText(/不会删除学习数据/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /退出当前会话/ }))
    await waitFor(() => expect(logout).toHaveBeenCalledTimes(1))
    await waitFor(() => expect(window.location.hash).toBe('#/login'))
  })

  it('changes password, rotates tokens and reports revoked sessions', async () => {
    authApi.changePassword.mockResolvedValue({
      changed: true,
      revoked_other_sessions: 1,
      tokens: { access_token: 'new-access', refresh_token: 'new-refresh' },
    })
    render(<RouterProvider><Settings /></RouterProvider>)

    await screen.findByText('Askora App 实例 · current（当前）')
    fireEvent.change(screen.getByLabelText('当前密码'), { target: { value: 'correct horse battery staple' } })
    fireEvent.change(screen.getByLabelText('新密码'), { target: { value: '新的 Askora 密码 足够长 2026' } })
    fireEvent.change(screen.getByLabelText('确认新密码'), { target: { value: '新的 Askora 密码 足够长 2026' } })
    fireEvent.click(screen.getByRole('button', { name: '修改密码并轮换会话' }))

    await waitFor(() => expect(authApi.changePassword).toHaveBeenCalledTimes(1))
    expect(replaceSessionTokens).toHaveBeenCalledWith({ access_token: 'new-access', refresh_token: 'new-refresh' })
    expect(await screen.findByText(/已撤销 1 个其他会话/)).toBeInTheDocument()
  })

  it('labels instances as untrusted display data and can revoke another session', async () => {
    authApi.revokeSession.mockResolvedValue({ success: true, revoked_sessions: 1 })
    render(<RouterProvider><Settings /></RouterProvider>)

    expect(await screen.findByText(/不代表可信硬件身份/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '撤销' }))
    await waitFor(() => expect(authApi.revokeSession).toHaveBeenCalledWith(
      'session-other', expect.stringMatching(/^revoke-session-/),
    ))
  })

  it('rotates the offline recovery kit and requires explicit storage confirmation', async () => {
    authApi.issueRecoveryKit.mockResolvedValue({
      issued: true,
      replayed: false,
      recovery_secret: 'askora-recovery-new-secret-value',
      credential_version: 2,
      created_at: '2026-08-09T02:00:00Z',
      storage_warning: '请立即离线保存；此恢复套件不会再次显示',
    })
    render(<RouterProvider><Settings /></RouterProvider>)

    expect(await screen.findByText('当前套件版本 1')).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('验证当前密码以轮换恢复套件'), {
      target: { value: 'correct horse battery staple' },
    })
    fireEvent.click(screen.getByRole('button', { name: '轮换恢复套件' }))

    expect(await screen.findByLabelText('新的离线恢复套件')).toHaveTextContent(
      'askora-recovery-new-secret-value',
    )
    const dismiss = screen.getByRole('button', { name: '确认保存并关闭' })
    expect(dismiss).toBeDisabled()
    fireEvent.click(screen.getByRole('checkbox', { name: /已将新套件保存在离线安全位置/ }))
    expect(dismiss).toBeEnabled()
    fireEvent.click(dismiss)
    expect(screen.queryByText('askora-recovery-new-secret-value')).not.toBeInTheDocument()
    expect(window.localStorage.getItem('recovery_secret')).toBeNull()
  })

  it('keeps a recovery rotation error visible after refreshing status', async () => {
    authApi.issueRecoveryKit.mockRejectedValue({
      response: { data: { error: { code: 'AUTH_CURRENT_PASSWORD_INVALID' } } },
    })
    render(<RouterProvider><Settings /></RouterProvider>)

    await screen.findByText('当前套件版本 1')
    fireEvent.change(screen.getByLabelText('验证当前密码以轮换恢复套件'), {
      target: { value: 'wrong current password' },
    })
    fireEvent.click(screen.getByRole('button', { name: '轮换恢复套件' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('当前密码不正确，请重新输入。')
  })

  it('exposes account deletion as a distinct danger operation', async () => {
    render(<RouterProvider><Settings /></RouterProvider>)
    await screen.findByText('私人使用')
    fireEvent.click(screen.getByRole('button', { name: '查看删除范围' }))
    await waitFor(() => expect(window.location.hash).toBe('#/settings/delete-account'))
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

  it('previews non-account erasure scopes and routes account deletion separately', async () => {
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

    expect(dataControlApi.createErasurePreview).toHaveBeenCalledTimes(3)
    expect(screen.queryByRole('option', { name: '全部个人数据与账号' })).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '进入账号删除流程' }))
    expect(window.location.hash).toBe('#/settings/delete-account')
  })

  it('offers a distinct "重新打开首次引导" action inside the App Utility section', async () => {
    render(<RouterProvider><Settings /></RouterProvider>)
    const button = await screen.findByRole('button', { name: /重新打开首次引导/ })
    expect(button).toBeInTheDocument()
    expect(button).toHaveAttribute('aria-label')
  })

  it('calls the owner-fact reopen command with the current preference version', async () => {
    render(<RouterProvider><Settings /></RouterProvider>)
    const button = await screen.findByRole('button', { name: /重新打开首次引导/ })
    fireEvent.click(button)
    await waitFor(() => expect(onboardingApi.reopenOnboarding).toHaveBeenCalledTimes(1))
    const call = onboardingApi.reopenOnboarding.mock.calls[0][0]
    expect(call).toHaveProperty('expectedVersion')
    expect(call.expectedVersion).toBeGreaterThanOrEqual(1)
  })
})