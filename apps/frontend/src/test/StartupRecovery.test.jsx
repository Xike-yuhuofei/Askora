import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { expect, it, vi } from 'vitest'

import StartupRecovery from '../pages/StartupRecovery'

it('explains bootstrap data safety and retries single-flight from the UI', async () => {
  const onRetry = vi.fn().mockResolvedValue({ status: 'ready' })
  render(<StartupRecovery diagnostic={{
    schema_version: '1.0',
    status: 'failed',
    code: 'BOOTSTRAP_DATABASE_MIGRATION_REQUIRED',
    data_safety: 'preserved',
    retryable: true,
    attempt: 2,
    started_at: '2026-08-09T05:00:00Z',
    updated_at: '2026-08-09T05:01:00Z',
    exit_code: 78,
    actions: ['retry_backend', 'copy_diagnostics'],
  }} onRetry={onRetry} />)

  expect(screen.getByText('本地数据库版本需要安全迁移。')).toBeInTheDocument()
  expect(screen.getByText('现有数据已保留。')).toBeInTheDocument()
  expect(screen.queryByText(/\/Users\//)).not.toBeInTheDocument()
  const retry = screen.getByRole('button', { name: '重新启动本地服务' })
  fireEvent.click(retry)
  fireEvent.click(retry)
  await waitFor(() => expect(onRetry).toHaveBeenCalledTimes(1))
})
