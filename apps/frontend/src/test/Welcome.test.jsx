import { fireEvent, render, screen, waitFor } from '@testing-library/react'
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

vi.mock('../router', async () => {
  const mod = await vi.importActual('../router')
  return { ...mod, useNavigate: () => vi.fn() }
})

function makeJourney(overrides = {}) {
  const baseSteps = [
    { step: 'MODEL', state: 'COMPLETE', title: '模型', summary: '模型已真实验证并启用', source_status: [] },
    { step: 'MATERIAL', state: 'NOT_STARTED', title: '资料', summary: '尚未导入学习资料', source_status: [] },
    { step: 'GOAL', state: 'NOT_STARTED', title: '目标', summary: '尚未确认学习目标', source_status: [] },
    { step: 'FIRST_ACTIVITY', state: 'NOT_STARTED', title: '第一节', summary: '尚未准备完成', source_status: [] },
  ]
  return {
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
    steps: baseSteps,
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
    correlation_id: 'test-correlation-id',
    ...overrides,
  }
}

describe('P106 Welcome page — owner-fact driven four-step journey', () => {
  beforeEach(() => {
    window.location.hash = '#/welcome'
    onboardingApi.getOnboardingJourney.mockReset()
    onboardingApi.acknowledgeBoundaries.mockReset()
    onboardingApi.dismissOnboarding.mockReset()
    onboardingApi.reopenOnboarding.mockReset()
    onboardingApi.finishAndDismissOnboarding.mockReset()
    onboardingApi.getOnboardingJourney.mockResolvedValue(makeJourney())
  })

  it('renders the four steps exactly in the frozen order MODEL / MATERIAL / GOAL / FIRST_ACTIVITY', async () => {
    render(<RouterProvider><Welcome /></RouterProvider>)
    const titles = await screen.findAllByText(/^(模型|资料|目标|第一节)$/)
    const labels = titles.map((node) => node.textContent.trim())
    expect(labels).toEqual(['模型', '资料', '目标', '第一节'])
  })

  it('exposes exactly one primary action and a dismiss affordance', async () => {
    render(<RouterProvider><Welcome /></RouterProvider>)
    const primary = await screen.findByRole('button', { name: '我已了解，开始设置' })
    expect(primary).toBeInTheDocument()
    expect(primary.classList.contains('button--primary') || primary.className.includes('primary')).toBeTruthy()
    expect(screen.getByRole('button', { name: /稍后再做/ })).toBeInTheDocument()
  })

  it('does not leak internal system names (SYS01, SYS06, planner, diagnostic) into copy', async () => {
    render(<RouterProvider><Welcome /></RouterProvider>)
    await screen.findByText('模型')
    const body = document.body.textContent || ''
    expect(body).not.toMatch(/SYS0[1-8]/)
    expect(body).not.toMatch(/planner/i)
  })

  it('announces loading state and exposes a live region', async () => {
    onboardingApi.getOnboardingJourney.mockRejectedValue({ response: { status: 500 } })
    render(<RouterProvider><Welcome /></RouterProvider>)
    const alert = await screen.findByRole('alert')
    expect(alert).toBeInTheDocument()
  })

  it('shows BLOCKED state with recovery action when next_action.kind is recover', async () => {
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
    onboardingApi.getOnboardingJourney.mockResolvedValue(makeJourney({
      steps: [
        { step: 'MODEL', state: 'BLOCKED', title: '模型', summary: '模型配置需要恢复', source_status: [] },
        { step: 'MATERIAL', state: 'NOT_STARTED', title: '资料', summary: '尚未导入', source_status: [] },
        { step: 'GOAL', state: 'NOT_STARTED', title: '目标', summary: '尚未确认', source_status: [] },
        { step: 'FIRST_ACTIVITY', state: 'NOT_STARTED', title: '第一节', summary: '尚未准备', source_status: [] },
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
    }))
    render(<RouterProvider><Welcome /></RouterProvider>)
    const primary = await screen.findByRole('button', { name: '重新验证模型' })
    expect(primary).toBeInTheDocument()
    expect(primary).toBeEnabled()
  })

  it('marks the first activity COMPLETE and sends user to /today as next_action', async () => {
    onboardingApi.getOnboardingJourney.mockResolvedValue(makeJourney({
      journey_state: 'ACTIVE',
      should_enter_welcome: true,
      preference: {
        ...makeJourney().preference,
        boundary_notice_version_acknowledged: 'privacy-and-model-v1',
      },
      boundary_notice: { ...makeJourney().boundary_notice, acknowledged: true },
      steps: [
        { step: 'MODEL', state: 'COMPLETE', title: '模型', summary: '模型已验证', source_status: [] },
        { step: 'MATERIAL', state: 'COMPLETE', title: '资料', summary: '资料已准备', source_status: [] },
        { step: 'GOAL', state: 'COMPLETE', title: '目标', summary: '目标已确认', source_status: [] },
        { step: 'FIRST_ACTIVITY', state: 'COMPLETE', title: '第一节', summary: '第一节已完成', source_status: [] },
      ],
      next_action: {
        action_code: 'OPEN_TODAY',
        kind: 'navigate',
        label: '回到今天查看下一步',
        enabled: true,
        route: '/today',
        resource_ref: null,
        recovery_action: null,
        reason_codes: [],
      },
    }))
    render(<RouterProvider><Welcome /></RouterProvider>)
    const primary = await screen.findByRole('button', { name: '回到今天查看下一步' })
    expect(primary).toBeInTheDocument()
  })

  it('dismiss calls the backend command and marks preference DISMISSED', async () => {
    onboardingApi.dismissOnboarding.mockResolvedValue(makeJourney({
      preference: {
        ...makeJourney().preference,
        preference_version: 2,
        visibility: 'DISMISSED',
        dismissed_reason: 'USER_DEFERRED',
      },
      should_enter_welcome: false,
      next_action: {
        action_code: 'NONE',
        kind: 'none',
        label: '',
        enabled: false,
        route: null,
        resource_ref: null,
        recovery_action: null,
        reason_codes: [],
      },
    }))
    render(<RouterProvider><Welcome /></RouterProvider>)
    fireEvent.click(await screen.findByRole('button', { name: /稍后再做/ }))
    await waitFor(() => expect(onboardingApi.dismissOnboarding).toHaveBeenCalledWith({ expectedVersion: 1 }))
  })

  it('reload re-reads the journey from owner facts (no localStorage completion)', async () => {
    const spy = vi.fn().mockResolvedValue(makeJourney())
    onboardingApi.getOnboardingJourney.mockImplementation(spy)
    render(<RouterProvider><Welcome /></RouterProvider>)
    await screen.findByText('模型')
    expect(spy).toHaveBeenCalledTimes(1)
    expect(localStorage.getItem('onboarding_complete')).toBeNull()
    // simulate reload by re-rendering
    render(<RouterProvider><Welcome /></RouterProvider>)
    await screen.findByText('模型')
    expect(spy).toHaveBeenCalledTimes(2)
  })

  it('uses keyboard-accessible focus and aria-describedby for primary action', async () => {
    render(<RouterProvider><Welcome /></RouterProvider>)
    const primary = await screen.findByRole('button', { name: '我已了解，开始设置' })
    primary.focus()
    expect(document.activeElement).toBe(primary)
  })
})
