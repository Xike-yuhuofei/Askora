import { createRequire } from 'node:module'
import { describe, expect, it } from 'vitest'

const require = createRequire(import.meta.url)
const diagnostics = require('../../electron/bootstrap-diagnostics.cjs')

describe('P107 bootstrap diagnostic parser', () => {
  it('accepts only strict prefixed allowlisted diagnostics', () => {
    const state = diagnostics.starting({ attempt: 0 })
    const parsed = diagnostics.parseDiagnosticLine(
      state,
      `${diagnostics.PREFIX}{"schema_version":"1.0","code":"BOOTSTRAP_DATABASE_MIGRATION_REQUIRED","retryable":true,"data_safety":"preserved"}`,
    )
    expect(parsed).toMatchObject({
      status: 'failed',
      code: 'BOOTSTRAP_DATABASE_MIGRATION_REQUIRED',
      retryable: true,
      data_safety: 'preserved',
      actions: ['retry_backend', 'copy_diagnostics'],
    })
    expect(diagnostics.parseDiagnosticLine(state, 'database failed at /Users/private/db')).toBeNull()
    expect(diagnostics.parseDiagnosticLine(
      state,
      `${diagnostics.PREFIX}{"schema_version":"1.0","code":"UNSAFE_UNKNOWN","path":"/Users/private/db"}`,
    )).toBeNull()
  })

  it('sanitizes unknown process failures and never carries raw detail', () => {
    const state = diagnostics.failed(diagnostics.starting({ attempt: 1 }), 'RAW_ERROR', {
      retryable: true,
      path: '/Users/private/db',
      secret: 'do-not-copy',
      exit_code: 2,
    })
    expect(state.code).toBe('BOOTSTRAP_BACKEND_EXITED')
    expect(state.exit_code).toBe(2)
    expect(JSON.stringify(state)).not.toMatch(/Users|do-not-copy|secret|path/)
  })
})
