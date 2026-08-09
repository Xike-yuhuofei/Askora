const assert = require('node:assert/strict')
const { describe, test } = require('node:test')

const { createActiveMigrationGuard } = require('./data-control-migration.cjs')

function deferred() {
  let resolve
  const promise = new Promise((done) => { resolve = done })
  return { promise, resolve }
}

describe('DATA-050 desktop active migration guard', () => {
  test('current schema is a no-op and does not restart or finalize', async () => {
    const calls = []
    const guard = createActiveMigrationGuard({
      runCommand: async (command) => {
        calls.push(command)
        return { schema_version: '1.0', required: false, schema_before: 'head', schema_after: 'head' }
      },
      startBackend: async () => { throw new Error('must not start inside no-op guard') },
      stopBackend: async () => {},
      reportFailure: () => { throw new Error('must not fail') },
    })

    assert.deepEqual(await guard.run({ state: 'DISABLED' }), {
      ok: true,
      migrated: false,
      backend_started: false,
    })
    assert.deepEqual(calls, ['recover-interrupted-restore', 'migrate-active'])
  })

  test('an interrupted activation is recovered before the active revision is planned', async () => {
    const calls = []
    const guard = createActiveMigrationGuard({
      runCommand: async (command) => {
        calls.push(command)
        if (command === 'recover-interrupted-restore') {
          return { action: 'ROLLED_BACK_INTERRUPTED_RESTORE' }
        }
        return { required: false, schema_before: 'head', schema_after: 'head' }
      },
      startBackend: async () => { throw new Error('must not start inside no-op guard') },
      stopBackend: async () => {},
      reportFailure: () => { throw new Error('must not fail') },
    })

    assert.equal((await guard.run(null)).ok, true)
    assert.deepEqual(calls, ['recover-interrupted-restore', 'migrate-active'])
  })

  test('a fresh install does not invoke maintenance before backend bootstrap diagnostics', async () => {
    const calls = []
    const guard = createActiveMigrationGuard({
      runCommand: async (command) => {
        calls.push(command)
        return { action: null }
      },
      hasActiveDatabase: () => false,
      startBackend: async () => { throw new Error('guard must leave first launch to the caller') },
      stopBackend: async () => {},
      reportFailure: () => { throw new Error('must not fail') },
    })

    assert.deepEqual(await guard.run(null), {
      ok: true,
      migrated: false,
      backend_started: false,
    })
    assert.deepEqual(calls, [])
  })

  test('an activation journal is recovered even while the active database is temporarily absent', async () => {
    const calls = []
    let activeDatabaseExists = false
    const guard = createActiveMigrationGuard({
      runCommand: async (command) => {
        calls.push(command)
        if (command === 'recover-interrupted-restore') {
          activeDatabaseExists = true
          return { action: 'ROLLED_BACK_INTERRUPTED_RESTORE' }
        }
        return { required: false, schema_before: 'old', schema_after: 'head' }
      },
      hasActiveDatabase: () => activeDatabaseExists,
      hasInterruptedActivation: () => true,
      startBackend: async () => { throw new Error('must not start inside no-op guard') },
      stopBackend: async () => {},
      reportFailure: () => { throw new Error('must not fail') },
    })

    assert.equal((await guard.run(null)).ok, true)
    assert.deepEqual(calls, ['recover-interrupted-restore', 'migrate-active'])
  })

  test('verified staging migration starts exact profile then finalizes readiness', async () => {
    const calls = []
    const profile = { state: 'ACTIVE', revision: 4 }
    const guard = createActiveMigrationGuard({
      runCommand: async (command, args = []) => {
        calls.push([command, ...args])
        if (command === 'migrate-active') {
          return {
            schema_version: '1.0',
            required: true,
            schema_before: 'old',
            schema_after: 'head',
            recovery_report: { transaction_id: '11111111-1111-4111-8111-111111111111' },
          }
        }
        return { status: 'COMPLETED' }
      },
      startBackend: async (candidate) => {
        calls.push(['start-backend', candidate])
        return 'http://127.0.0.1:8765'
      },
      stopBackend: async () => { calls.push(['stop-backend']) },
      reportFailure: () => { throw new Error('must not fail') },
    })

    assert.deepEqual(await guard.run(profile), {
      ok: true,
      migrated: true,
      backend_started: true,
    })
    assert.deepEqual(calls, [
      ['recover-interrupted-restore'],
      ['migrate-active'],
      ['start-backend', profile],
      ['finalize-restore', '--transaction-id', '11111111-1111-4111-8111-111111111111'],
    ])
  })

  test('concurrent callers share one migration transaction', async () => {
    const pending = deferred()
    let migrationCalls = 0
    const guard = createActiveMigrationGuard({
      runCommand: async (command) => {
        if (command === 'migrate-active') {
          migrationCalls += 1
          return pending.promise
        }
        return { status: 'COMPLETED' }
      },
      startBackend: async () => 'http://127.0.0.1:8765',
      stopBackend: async () => {},
      reportFailure: () => {},
    })

    const first = guard.run(null)
    const second = guard.run(null)
    pending.resolve({ required: false, schema_before: 'head', schema_after: 'head' })

    assert.equal(first, second)
    await first
    assert.equal(migrationCalls, 1)
  })

  test('readiness failure rolls back before reporting preserved data', async () => {
    const calls = []
    let failure
    const guard = createActiveMigrationGuard({
      runCommand: async (command, args = []) => {
        calls.push([command, ...args])
        if (command === 'migrate-active') {
          return {
            required: true,
            recovery_report: { transaction_id: '22222222-2222-4222-8222-222222222222' },
          }
        }
        return { status: 'FAILED_ROLLED_BACK' }
      },
      startBackend: async () => null,
      stopBackend: async () => { calls.push(['stop-backend']) },
      reportFailure: (code, options) => { failure = { code, options } },
    })

    assert.deepEqual(await guard.run(null), {
      ok: false,
      migrated: false,
      backend_started: false,
    })
    assert.deepEqual(calls, [
      ['recover-interrupted-restore'],
      ['migrate-active'],
      ['stop-backend'],
      ['rollback-restore', '--transaction-id', '22222222-2222-4222-8222-222222222222'],
    ])
    assert.deepEqual(failure, {
      code: 'BOOTSTRAP_DATABASE_MIGRATION_REQUIRED',
      options: { retryable: true, data_safety: 'preserved' },
    })
  })

  test('rollback failure never claims that active data is preserved', async () => {
    let failure
    const guard = createActiveMigrationGuard({
      runCommand: async (command) => {
        if (command === 'migrate-active') {
          return {
            required: true,
            recovery_report: { transaction_id: '33333333-3333-4333-8333-333333333333' },
          }
        }
        throw new Error('rollback failed')
      },
      startBackend: async () => null,
      stopBackend: async () => {},
      reportFailure: (code, options) => { failure = { code, options } },
    })

    await guard.run(null)
    assert.deepEqual(failure, {
      code: 'BOOTSTRAP_DATABASE_MIGRATION_REQUIRED',
      options: { retryable: true, data_safety: 'unknown' },
    })
  })

  test('corrupt active database is reported as a non-retryable integrity failure', async () => {
    let failure
    const guard = createActiveMigrationGuard({
      runCommand: async () => {
        const error = new Error('sanitized maintenance failure')
        error.code = 'DATA_BACKUP_INTEGRITY_FAILED'
        throw error
      },
      startBackend: async () => null,
      stopBackend: async () => {},
      reportFailure: (code, options) => { failure = { code, options } },
    })

    await guard.run(null)
    assert.deepEqual(failure, {
      code: 'BOOTSTRAP_DATABASE_INTEGRITY_FAILED',
      options: { retryable: false, data_safety: 'unknown' },
    })
  })
})
