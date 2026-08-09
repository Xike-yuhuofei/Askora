const TRANSACTION_ID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

function createActiveMigrationGuard({
  runCommand,
  startBackend,
  stopBackend,
  reportFailure,
  hasActiveDatabase = () => true,
}) {
  let inFlight = null

  async function fail(dataSafety) {
    reportFailure('BOOTSTRAP_DATABASE_MIGRATION_REQUIRED', {
      retryable: true,
      data_safety: dataSafety,
    })
    return { ok: false, migrated: false, backend_started: false }
  }

  async function execute(profile) {
    try {
      await runCommand('recover-interrupted-restore')
    } catch {
      return fail('unknown')
    }
    if (!hasActiveDatabase()) {
      return { ok: true, migrated: false, backend_started: false }
    }

    let migration
    try {
      migration = await runCommand('migrate-active')
    } catch {
      return fail('unknown')
    }
    if (migration?.required !== true) {
      return { ok: true, migrated: false, backend_started: false }
    }

    const transactionId = migration?.recovery_report?.transaction_id
    if (typeof transactionId !== 'string' || !TRANSACTION_ID.test(transactionId)) {
      return fail('unknown')
    }

    try {
      const backendURL = await startBackend(profile)
      if (!backendURL) throw new Error('backend readiness failed')
      await runCommand('finalize-restore', ['--transaction-id', transactionId])
      return { ok: true, migrated: true, backend_started: true }
    } catch {
      try {
        await stopBackend()
      } catch {}
      let rollbackSucceeded = false
      try {
        const rolledBack = await runCommand('rollback-restore', [
          '--transaction-id', transactionId,
        ])
        rollbackSucceeded = rolledBack?.status === 'FAILED_ROLLED_BACK'
      } catch {}
      return fail(rollbackSucceeded ? 'preserved' : 'unknown')
    }
  }

  function run(profile) {
    if (inFlight) return inFlight
    inFlight = execute(profile).finally(() => {
      inFlight = null
    })
    return inFlight
  }

  return { run }
}

module.exports = { createActiveMigrationGuard }
