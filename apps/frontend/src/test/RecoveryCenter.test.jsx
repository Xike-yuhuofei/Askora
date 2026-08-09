import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as recoveryApi from '../api/recovery'
import RecoveryCenter from '../pages/RecoveryCenter'
import { RouterProvider } from '../router'

vi.mock('../api/recovery', () => ({
  listRecoveryIssues: vi.fn(),
  executeRecoveryAction: vi.fn(),
}))

const issue = {
  schema_version: '1.0',
  issue_ref: 'document:doc-1:processing',
  issue_version: 8,
  code: 'CONTENT_PROCESSING_FAILED',
  category: 'transient',
  severity: 'blocking',
  status: 'active',
  title: '资料处理没有完成',
  summary: '原文件仍保留，可安全重新提交一次处理任务。',
  data_safety: 'preserved',
  duplicate_risk: 'prevented_by_idempotency',
  source_system: 'SYS01',
  resource_ref: 'document:doc-1',
  correlation_id: 'corr-1',
  attempt_count: 0,
  retry_budget: 3,
  next_eligible_at: null,
  actions: [{
    action_code: 'retry_owner_command',
    label: '重新处理',
    kind: 'command',
    enabled: true,
    endpoint: '/api/v1/recovery/actions',
    method: 'POST',
    route: null,
    requires_idempotency_key: true,
    requires_confirmation: false,
    disabled_reason_code: null,
  }],
  opened_at: '2026-08-09T05:00:00Z',
  updated_at: '2026-08-09T05:01:00Z',
}

const payload = {
  schema_version: '1.0',
  generated_at: '2026-08-09T05:02:00Z',
  issues: [issue],
  active_count: 1,
  correlation_id: 'query-1',
}

describe('P107 recovery center', () => {
  beforeEach(() => {
    window.location.hash = '#/settings/recovery'
    recoveryApi.listRecoveryIssues.mockReset()
    recoveryApi.executeRecoveryAction.mockReset()
    recoveryApi.listRecoveryIssues.mockResolvedValue(payload)
  })

  it('shows what happened, safety, action and duplicate semantics', async () => {
    render(<RouterProvider><RecoveryCenter /></RouterProvider>)

    expect(await screen.findByRole('heading', { name: '资料处理没有完成' })).toBeInTheDocument()
    expect(screen.getByText('发生了什么')).toBeInTheDocument()
    expect(screen.getByText('数据是否安全')).toBeInTheDocument()
    expect(screen.getByText('现在能做什么')).toBeInTheDocument()
    expect(screen.getByText('重试说明')).toBeInTheDocument()
    expect(screen.getByText('数据已保留')).toBeInTheDocument()
    expect(screen.getByText(/不会创建第二份任务/)).toBeInTheDocument()
    expect(screen.getByText('已尝试 0 次；安全预算上限 3 次。')).toBeInTheDocument()
    expect(screen.queryByText(/\/Users\//)).not.toBeInTheDocument()
  })

  it('explains a server-disabled policy action without executing it', async () => {
    recoveryApi.listRecoveryIssues.mockResolvedValue({
      ...payload,
      issues: [{
        ...issue,
        issue_ref: 'document:doc-1:quarantine',
        code: 'CONTENT_QUARANTINED',
        title: '资料仍在安全隔离中',
        actions: [{
          ...issue.actions[0],
          action_code: 'reinspect_document',
          label: '暂无更新的安全策略',
          enabled: false,
          disabled_reason_code: 'CONTENT_REINSPECTION_POLICY_UNCHANGED',
        }],
      }],
    })
    render(<RouterProvider><RecoveryCenter /></RouterProvider>)

    const action = await screen.findByRole('button', { name: '暂无更新的安全策略' })
    expect(action).toBeDisabled()
    expect(screen.getByText(/CONTENT_REINSPECTION_POLICY_UNCHANGED/)).toBeInTheDocument()
    fireEvent.click(action)
    expect(recoveryApi.executeRecoveryAction).not.toHaveBeenCalled()
  })

  it('submits the exact server-allowed action and re-queries owner state', async () => {
    recoveryApi.executeRecoveryAction.mockResolvedValue({
      status: 'accepted',
      message: '已创建安全的资料处理任务',
    })
    render(<RouterProvider><RecoveryCenter /></RouterProvider>)

    fireEvent.click(await screen.findByRole('button', { name: '重新处理' }))
    await waitFor(() => expect(recoveryApi.executeRecoveryAction).toHaveBeenCalledTimes(1))
    expect(recoveryApi.executeRecoveryAction.mock.calls[0][0]).toMatchObject({
      schema_version: '1.0',
      issue_ref: issue.issue_ref,
      expected_issue_version: issue.issue_version,
      action_code: 'retry_owner_command',
    })
    await waitFor(() => expect(recoveryApi.listRecoveryIssues.mock.calls.length).toBeGreaterThan(1))
    expect(await screen.findByText('已创建安全的资料处理任务')).toBeInTheDocument()
  })

  it('uses an honest empty state', async () => {
    recoveryApi.listRecoveryIssues.mockResolvedValue({ ...payload, issues: [], active_count: 0 })
    render(<RouterProvider><RecoveryCenter /></RouterProvider>)
    expect(await screen.findByText('目前没有待处理问题')).toBeInTheDocument()
    expect(screen.getByText(/不代表绝对安全/)).toBeInTheDocument()
  })

  it('navigates an OCR issue to the exact SYS01 review run', async () => {
    recoveryApi.listRecoveryIssues.mockResolvedValue({
      ...payload,
      issues: [{
        ...issue,
        issue_ref: 'ocr:run-1:review',
        code: 'CONTENT_OCR_REVIEW_REQUIRED',
        category: 'conflict',
        title: '扫描文字等待人工复核',
        data_safety: 'preserved_but_unavailable',
        duplicate_risk: 'not_applicable',
        actions: [{
          action_code: 'open_ocr_review',
          label: '打开 OCR 复核',
          kind: 'navigate',
          enabled: true,
          route: '/library?document=document-1&ocrRun=run-1',
        }],
      }],
    })
    render(<RouterProvider><RecoveryCenter /></RouterProvider>)

    fireEvent.click(await screen.findByRole('button', { name: '打开 OCR 复核' }))

    await waitFor(() => expect(window.location.hash).toBe(
      '#/library?document=document-1&ocrRun=run-1',
    ))
    expect(recoveryApi.executeRecoveryAction).not.toHaveBeenCalled()
  })
})
