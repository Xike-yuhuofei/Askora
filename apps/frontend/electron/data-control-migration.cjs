const TRANSACTION_ID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

function createActiveMigrationGuard({
  runCommand,
  startBackend,
  stopBackend,
  reportFailure,
  hasActiveDatabase = () => true,
  hasInterruptedActivation = () => false,
}) {
  let inFlight = null

  async function fail(code, dataSafety, retryable = true) {
    reportFailure(code, {
      retryable,
      data_safety: dataSafety,
    })
    return { ok: false, migrated: false, backend_started: false }
  }

  function failMaintenance(error) {
    if (error?.code === 'DATA_BACKUP_INTEGRITY_FAILED') {
      return fail('BOOTSTRAP_DATABASE_INTEGRITY_FAILED', 'unknown', false)
    }
    if (error?.code === 'DATA_MAINTENANCE_BUSY') {
      return fail('BOOTSTRAP_DATABASE_UNAVAILABLE', 'unknown')
    }
    return fail('BOOTSTRAP_DATABASE_MIGRATION_REQUIRED', 'unknown')
  }

  async function execute(profile) {
    if (!hasActiveDatabase() && !hasInterruptedActivation()) {
      return { ok: true, migrated: false, backend_started: false }
    }
    try {
      await runCommand('recover-interrupted-restore')
    } catch (error) {
      return failMaintenance(error)
    }
    if (!hasActiveDatabase()) {
      return { ok: true, migrated: false, backend_started: false }
    }

    let migration
    try {
      migration = await runCommand('migrate-active')
    } catch (error) {
      return failMaintenance(error)
    }
    if (migration?.required !== true) {
      return { ok: true, migrated: false, backend_started: false }
    }

    const transactionId = migration?.recovery_report?.transaction_id
    if (typeof transactionId !== 'string' || !TRANSACTION_ID.test(transactionId)) {
      return fail('BOOTSTRAP_DATABASE_MIGRATION_REQUIRED', 'unknown')
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
      return fail(
        'BOOTSTRAP_DATABASE_MIGRATION_REQUIRED',
        rollbackSucceeded ? 'preserved' : 'unknown',
      )
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
