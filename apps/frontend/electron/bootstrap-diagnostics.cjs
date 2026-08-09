const ALLOWED_CODES = new Set([
  'BOOTSTRAP_BACKEND_BINARY_MISSING',
  'BOOTSTRAP_BACKEND_SPAWN_FAILED',
  'BOOTSTRAP_BACKEND_EXITED',
  'BOOTSTRAP_BACKEND_START_TIMEOUT',
  'BOOTSTRAP_DATABASE_MIGRATION_REQUIRED',
  'BOOTSTRAP_DATABASE_UNAVAILABLE',
  'BOOTSTRAP_DATABASE_INTEGRITY_FAILED',
])

const PREFIX = 'ASKORA_STARTUP_DIAGNOSTIC '

function isoNow() {
  return new Date().toISOString()
}

function starting(previous = null) {
  const now = isoNow()
  return {
    schema_version: '1.0',
    status: 'starting',
    code: null,
    data_safety: 'unknown',
    retryable: false,
    attempt: (previous?.attempt || 0) + 1,
    started_at: now,
    updated_at: now,
    exit_code: null,
    actions: [],
  }
}

function ready(previous) {
  return {
    ...previous,
    status: 'ready',
    code: null,
    data_safety: 'preserved',
    retryable: false,
    updated_at: isoNow(),
    exit_code: null,
    actions: [],
  }
}

function failed(previous, code, options = {}) {
  const safeCode = ALLOWED_CODES.has(code) ? code : 'BOOTSTRAP_BACKEND_EXITED'
  return {
    ...previous,
    schema_version: '1.0',
    status: 'failed',
    code: safeCode,
    data_safety: options.data_safety === 'preserved' ? 'preserved' : 'unknown',
    retryable: Boolean(options.retryable),
    updated_at: isoNow(),
    exit_code: Number.isInteger(options.exit_code) ? options.exit_code : null,
    actions: options.retryable
      ? ['retry_backend', 'copy_diagnostics']
      : ['copy_diagnostics'],
  }
}

function parseDiagnosticLine(previous, line) {
  if (!line.startsWith(PREFIX)) return null
  try {
    const parsed = JSON.parse(line.slice(PREFIX.length))
    if (parsed.schema_version !== '1.0' || !ALLOWED_CODES.has(parsed.code)) return null
    return failed(previous, parsed.code, {
      retryable: parsed.retryable,
      data_safety: parsed.data_safety,
    })
  } catch {
    return null
  }
}

module.exports = { ALLOWED_CODES, PREFIX, failed, parseDiagnosticLine, ready, starting }
