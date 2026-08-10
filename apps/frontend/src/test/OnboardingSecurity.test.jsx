import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as onboardingApi from '../api/onboarding'
import Welcome from '../pages/Welcome'
import { RouterProvider } from '../router'

vi.mock('../api/onboarding', () => ({
  getOnboardingJourney: vi.fn(),
  acknowledgeBoundaries: vi.fn(),
  dismissOnboarding: vi.fn(),
  reopenOnboarding: vi.fn(),
  finishAndDismissOnboarding: vi.fn(),
}))

const secureJourney = {
  schema_version: '1.0',
  journey_id: 'first-learning-v1',
  generated_at: '2026-08-10T00:00:00Z',
  journey_state: 'ACTIVE',
  should_enter_welcome: true,
  preference: {
    schema_version: '1.0',
    journey_id: 'first-learning-v1',
    preference_version: 1,
    visibility: 'ACTIVE',
    boundary_notice_version_acknowledged: null,
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
  steps: [
    { step: 'MODEL', state: 'COMPLETE', title: '模型', summary: '模型已验证', source_status: [] },
    { step: 'MATERIAL', state: 'NOT_STARTED', title: '资料', summary: '尚未导入', source_status: [] },
    { step: 'GOAL', state: 'NOT_STARTED', title: '目标', summary: '尚未确认', source_status: [] },
    { step: 'FIRST_ACTIVITY', state: 'NOT_STARTED', title: '第一节', summary: '尚未准备', source_status: [] },
  ],
  next_action: {
    action_code: 'ACKNOWLEDGE_BOUNDARIES',
    kind: 'command',
    label: '我已了解，开始设置',
    enabled: true,
    route: null,
    resource_ref: null,
    recovery_action: null,
    reason_codes: [],
  },
  correlation_id: 'corr-1',
}

describe('P106 onboarding security boundaries', () => {
  beforeEach(() => {
    window.location.hash = '#/welcome'
    onboardingApi.getOnboardingJourney.mockReset()
    onboardingApi.getOnboardingJourney.mockResolvedValue(secureJourney)
  })

  it('does not render access tokens, refresh tokens or API keys anywhere in the DOM', async () => {
    render(<RouterProvider><Welcome /></RouterProvider>)
    await screen.findByText('模型')
    const body = document.body.textContent || ''
    expect(body).not.toMatch(/Bearer\s+[A-Za-z0-9._-]+/)
    expect(body).not.toMatch(/access_token/)
    expect(body).not.toMatch(/refresh_token/)
    expect(body).not.toMatch(/sk-[A-Za-z0-9]+/)
  })

  it('does not expose raw source paths (e.g., /Users/, managed/ paths) or stack traces', async () => {
    render(<RouterProvider><Welcome /></RouterProvider>)
    await screen.findByText('模型')
    const body = document.body.textContent || ''
    expect(body).not.toMatch(/\/Users\//)
    expect(body).not.toMatch(/managed\//)
    expect(body).not.toMatch(/Traceback/)
    expect(body).not.toMatch(/\bFile ".*\.py"/)
  })

  it('does not leak owner ref ids or raw entity keys into the DOM copy', async () => {
    onboardingApi.getOnboardingJourney.mockResolvedValue({
      ...secureJourney,
      next_action: {
        ...secureJourney.next_action,
        recovery_action: {
          action_code: 'retry_model_verification',
          label: '重新验证模型',
          kind: 'command',
          enabled: true,
          disabled_reason_code: null,
          endpoint: '/api/v1/model/retry',
          method: 'POST',
          route: null,
          requires_idempotency_key: true,
          requires_confirmation: false,
        },
      },
    })
    render(<RouterProvider><Welcome /></RouterProvider>)
    const body = document.body.textContent || ''
    expect(body).not.toMatch(/source_ref/)
    expect(body).not.toMatch(/entity_type/)
  })

  it('does not write completion flags into localStorage', async () => {
    render(<RouterProvider><Welcome /></RouterProvider>)
    await screen.findByText('模型')
    const keys = []
    for (let i = 0; i < localStorage.length; i += 1) keys.push(localStorage.key(i))
    const onboardingKeys = keys.filter((key) => key?.startsWith('onboarding'))
    expect(onboardingKeys).toEqual([])
  })

  it('forbids UI-provided RecoveryAction code — only renders server-supplied action_code', async () => {
    const recoveryAction = {
      action_code: 'retry_model_verification',
      label: '重新验证模型',
      kind: 'command',
      enabled: true,
      disabled_reason_code: null,
      endpoint: '/api/v1/model/retry',
      method: 'POST',
      route: null,
      requires_idempotency_key: true,
      requires_confirmation: false,
    }
    onboardingApi.getOnboardingJourney.mockResolvedValue({
      ...secureJourney,
      steps: [
        { step: 'MODEL', state: 'BLOCKED', title: '模型', summary: '模型需要恢复', source_status: [] },
        ...secureJourney.steps.slice(1),
      ],
      next_action: {
        action_code: 'RECOVER',
        kind: 'recover',
        label: '重新验证模型',
        enabled: true,
        route: null,
        resource_ref: null,
        recovery_action: recoveryAction,
        reason_codes: ['MODEL_PROVIDER_KEY_INVALID'],
      },
    })
    render(<RouterProvider><Welcome /></RouterProvider>)
    const primary = await screen.findByRole('button', { name: '重新验证模型' })
    expect(primary).toBeInTheDocument()
    expect(onboardingApi.acknowledgeBoundaries).not.toHaveBeenCalled()
  })
})
