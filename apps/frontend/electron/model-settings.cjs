'use strict'

const crypto = require('crypto')
const fs = require('fs')
const path = require('path')
const { fileURLToPath } = require('url')

const SCHEMA_VERSION = '1.0'
const WRAPPER_VERSION = '1.0'
const SUPPORTED_MODELS = Object.freeze({
  qwen: Object.freeze(['qwen-turbo']),
  deepseek: Object.freeze(['deepseek-chat']),
  doubao: Object.freeze(['doubao-pro-32k']),
  zhipu: Object.freeze(['glm-4.7-flash']),
})
const PROVIDER_ENV_NAMES = Object.freeze(Object.keys(SUPPORTED_MODELS).map((provider) => provider.toUpperCase()))
const PUBLIC_REASON_CODES = new Set([
  'MODEL_CONFIGURATION_DISABLED',
  'MODEL_CREDENTIAL_MISSING',
  'MODEL_RUNTIME_MISMATCH',
  'MODEL_RUNTIME_UNVERIFIED',
])
const PUBLIC_ERROR_SEMANTICS = Object.freeze({
  MODEL_CONFIG_STORAGE_UNAVAILABLE: Object.freeze({
    category: 'dependency',
    retryable: false,
    message: '系统安全存储当前不可用，模型配置未保存',
  }),
  MODEL_CONFIG_SCHEMA_UNSUPPORTED: Object.freeze({
    category: 'validation',
    retryable: false,
    message: '不支持的模型配置版本或内容',
  }),
  MODEL_CONFIG_REVISION_CONFLICT: Object.freeze({
    category: 'conflict',
    retryable: false,
    message: '模型配置已发生变化，请刷新后重试',
  }),
  MODEL_CREDENTIAL_REJECTED: Object.freeze({
    category: 'authorization',
    retryable: false,
    message: '模型凭据被 provider 拒绝，请更新后重试',
  }),
  MODEL_NOT_AVAILABLE: Object.freeze({
    category: 'dependency',
    retryable: false,
    message: '所选模型不可用，请检查模型权限或选择受支持模型',
  }),
  MODEL_RATE_LIMITED: Object.freeze({
    category: 'transient',
    retryable: true,
    message: 'Provider 暂时限流，请稍后重试',
  }),
  MODEL_PROVIDER_TIMEOUT: Object.freeze({
    category: 'transient',
    retryable: true,
    message: '模型连接测试超时，请稍后重试',
  }),
  MODEL_PROVIDER_UNAVAILABLE: Object.freeze({
    category: 'dependency',
    retryable: true,
    message: '模型服务暂时不可用，请稍后重试',
  }),
  MODEL_CONFIG_APPLY_FAILED: Object.freeze({
    category: 'internal',
    retryable: true,
    message: '新配置未能应用，已恢复之前的配置',
  }),
  MODEL_CONFIG_ROLLBACK_FAILED: Object.freeze({
    category: 'internal',
    retryable: false,
    message: '配置恢复失败，当前模型不可用，请重新配置',
  }),
})

class ModelSettingsError extends Error {
  constructor(code, category, message, retryable = false) {
    super(message)
    this.name = 'ModelSettingsError'
    this.code = code
    this.category = category
    this.retryable = retryable
  }

  toPublic() {
    const semantics = PUBLIC_ERROR_SEMANTICS[this.code]
    if (semantics) return { code: this.code, ...semantics }
    return { code: 'MODEL_PROVIDER_UNAVAILABLE', ...PUBLIC_ERROR_SEMANTICS.MODEL_PROVIDER_UNAVAILABLE }
  }
}

function storageError() {
  return new ModelSettingsError(
    'MODEL_CONFIG_STORAGE_UNAVAILABLE',
    'dependency',
    '系统安全存储当前不可用，模型配置未保存',
    false,
  )
}

function schemaError() {
  return new ModelSettingsError(
    'MODEL_CONFIG_SCHEMA_UNSUPPORTED',
    'validation',
    '不支持的模型配置版本或内容',
    false,
  )
}

function assertPlainObject(value) {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value)
}

function hasExactKeys(value, expectedKeys) {
  if (!assertPlainObject(value)) return false
  const actual = Object.keys(value).sort()
  const expected = [...expectedKeys].sort()
  return actual.length === expected.length && actual.every((key, index) => key === expected[index])
}

function validateExpectedRevision(expectedRevision, currentRevision) {
  const normalized = expectedRevision === undefined ? null : expectedRevision
  if (normalized !== currentRevision) {
    throw new ModelSettingsError(
      'MODEL_CONFIG_REVISION_CONFLICT',
      'conflict',
      '模型配置已发生变化，请刷新后重试',
      false,
    )
  }
}

function validateApplyCommand(command) {
  if (
    !hasExactKeys(command, ['schema_version', 'provider', 'model', 'api_key', 'expected_revision']) ||
    command.schema_version !== SCHEMA_VERSION
  ) {
    throw new ModelSettingsError(
      'MODEL_CONFIG_SCHEMA_UNSUPPORTED',
      'validation',
      '不支持的模型配置版本',
      false,
    )
  }
  const { provider, model, api_key: apiKey, expected_revision: expectedRevision } = command
  if (
    expectedRevision !== null &&
    (!Number.isSafeInteger(expectedRevision) || expectedRevision < 1)
  ) {
    throw new ModelSettingsError(
      'MODEL_CONFIG_REVISION_CONFLICT',
      'conflict',
      '模型配置版本无效，请刷新后重试',
      false,
    )
  }
  if (
    typeof provider !== 'string' ||
    !SUPPORTED_MODELS[provider]?.includes(model) ||
    typeof apiKey !== 'string' ||
    apiKey.length < 8 ||
    apiKey.length > 4096
  ) {
    throw new ModelSettingsError(
      'MODEL_NOT_AVAILABLE',
      'validation',
      '模型配置或 provider/model 组合不受支持',
      false,
    )
  }
  return { provider, model, apiKey, expectedRevision: expectedRevision ?? null }
}

function validateClearCommand(command) {
  if (
    !hasExactKeys(command, ['schema_version', 'expected_revision']) ||
    command.schema_version !== SCHEMA_VERSION
  ) {
    throw new ModelSettingsError(
      'MODEL_CONFIG_SCHEMA_UNSUPPORTED',
      'validation',
      '不支持的模型配置版本',
      false,
    )
  }
  const expectedRevision = command.expected_revision
  if (expectedRevision !== null && (!Number.isSafeInteger(expectedRevision) || expectedRevision < 1)) {
    throw new ModelSettingsError(
      'MODEL_CONFIG_REVISION_CONFLICT',
      'conflict',
      '模型配置版本无效，请刷新后重试',
      false,
    )
  }
  return { expectedRevision: expectedRevision ?? null }
}

function fingerprintApplyCommand(validated) {
  return crypto
    .createHash('sha256')
    .update(
      JSON.stringify([
        'apply',
        SCHEMA_VERSION,
        validated.provider,
        validated.model,
        validated.apiKey,
        validated.expectedRevision,
      ]),
      'utf8',
    )
    .digest('hex')
}

function fingerprintClearCommand(validated) {
  return crypto
    .createHash('sha256')
    .update(JSON.stringify(['clear', SCHEMA_VERSION, validated.expectedRevision]), 'utf8')
    .digest('hex')
}

function validateStoredProfile(profile) {
  if (
    !assertPlainObject(profile) ||
    profile.schema_version !== SCHEMA_VERSION ||
    !Number.isSafeInteger(profile.revision) ||
    profile.revision < 1 ||
    !['ACTIVE', 'DISABLED'].includes(profile.state)
  ) {
    throw new ModelSettingsError(
      'MODEL_CONFIG_SCHEMA_UNSUPPORTED',
      'validation',
      '已保存的模型配置版本不受支持',
      false,
    )
  }
  if (profile.state === 'ACTIVE') {
    if (
      !hasExactKeys(profile, [
        'schema_version',
        'revision',
        'state',
        'provider',
        'model',
        'api_key',
        'verified_at',
      ]) ||
      typeof profile.provider !== 'string' ||
      !SUPPORTED_MODELS[profile.provider]?.includes(profile.model) ||
      typeof profile.api_key !== 'string' ||
      profile.api_key.length < 8
    ) {
      throw new ModelSettingsError(
        'MODEL_CONFIG_SCHEMA_UNSUPPORTED',
        'validation',
        '已保存的模型配置内容无效',
        false,
      )
    }
  } else if (!hasExactKeys(profile, ['schema_version', 'revision', 'state', 'verified_at'])) {
    throw new ModelSettingsError(
      'MODEL_CONFIG_SCHEMA_UNSUPPORTED',
      'validation',
      '停用配置不能包含 credential',
      false,
    )
  }
  return profile
}

function publicSummary(profile, runtime = null) {
  if (!profile) return null
  const active = profile.state === 'ACTIVE'
  return {
    schema_version: SCHEMA_VERSION,
    state: profile.state,
    provider: active ? profile.provider : null,
    model: active ? profile.model : null,
    source: 'DESKTOP_VAULT',
    revision: profile.revision,
    verified_at: profile.verified_at || null,
    runtime_ready: runtime ? Boolean(runtime.runtime_ready) : false,
    runtime_revision: runtime?.runtime_revision ?? null,
    reason_codes: Array.isArray(runtime?.reason_codes)
      ? runtime.reason_codes.filter((code) => PUBLIC_REASON_CODES.has(code))
      : runtime
        ? []
        : ['MODEL_RUNTIME_UNVERIFIED'],
  }
}

function externalSummaryFromEnv(env) {
  const provider = String(env.LLM_DEFAULT_PROVIDER || 'qwen').toLowerCase()
  const model = env[`LLM_${provider.toUpperCase()}_MODEL`] || SUPPORTED_MODELS[provider]?.[0] || null
  const key = env[`LLM_${provider.toUpperCase()}_API_KEY`] || ''
  return {
    schema_version: SCHEMA_VERSION,
    state: key ? 'EXTERNAL_READ_ONLY' : 'UNCONFIGURED',
    provider: key ? provider : null,
    model: key ? model : null,
    source: key ? 'EXTERNAL_ENVIRONMENT' : 'NONE',
    revision: null,
    verified_at: null,
    runtime_ready: Boolean(key),
    runtime_revision: null,
    reason_codes: key ? [] : ['MODEL_CREDENTIAL_MISSING'],
  }
}

function applyModelProfileToEnvironment(baseEnvironment, profile) {
  const env = { ...baseEnvironment }
  if (!profile) {
    env.MODEL_CONFIG_SOURCE = 'EXTERNAL_ENVIRONMENT'
    env.MODEL_CONFIG_STATE = 'EXTERNAL_READ_ONLY'
    delete env.MODEL_CONFIG_REVISION
    delete env.MODEL_CONFIG_VERIFIED_AT
    return env
  }

  for (const provider of PROVIDER_ENV_NAMES) env[`LLM_${provider}_API_KEY`] = ''
  env.MODEL_CONFIG_SOURCE = 'DESKTOP_VAULT'
  env.MODEL_CONFIG_STATE = profile.state
  if (profile.revision === null || profile.revision === undefined) delete env.MODEL_CONFIG_REVISION
  else env.MODEL_CONFIG_REVISION = String(profile.revision)
  env.MODEL_CONFIG_VERIFIED_AT = profile.verified_at || ''
  if (profile.state === 'ACTIVE') {
    const provider = profile.provider.toUpperCase()
    env.LLM_DEFAULT_PROVIDER = profile.provider
    env.LLM_MATH_PROVIDER = profile.provider
    env[`LLM_${provider}_API_KEY`] = profile.api_key
    env[`LLM_${provider}_MODEL`] = profile.model
  }
  return env
}

function isAllowedModelSettingsSender(event, webContents, options) {
  if (!webContents || event?.sender !== webContents) return false
  if (!event.senderFrame || event.senderFrame !== webContents.mainFrame) return false
  try {
    const rendererURL = new URL(event.senderFrame.url)
    if (options?.isDev) {
      if (typeof options.devURL !== 'string') return false
      return rendererURL.href === new URL(options.devURL).href
    }
    if (rendererURL.protocol !== 'file:' || rendererURL.search || rendererURL.hash) return false
    if (typeof options?.allowedFilePath !== 'string') return false
    return path.resolve(fileURLToPath(rendererURL)) === path.resolve(options.allowedFilePath)
  } catch {
    return false
  }
}

class EncryptedModelVault {
  constructor({ safeStorage, filePath, fsPromises = fs.promises }) {
    this.safeStorage = safeStorage
    this.filePath = filePath
    this.fs = fsPromises
  }

  async _assertAvailable() {
    try {
      if (!(await this.safeStorage.isAsyncEncryptionAvailable())) throw storageError()
    } catch (error) {
      if (error instanceof ModelSettingsError) throw error
      throw storageError()
    }
  }

  async read() {
    let raw
    try {
      raw = await this.fs.readFile(this.filePath)
    } catch (error) {
      if (error?.code === 'ENOENT') return null
      throw storageError()
    }
    await this._assertAvailable()
    let wrapper
    try {
      wrapper = JSON.parse(raw.toString('utf8'))
    } catch {
      throw schemaError()
    }
    if (
      !hasExactKeys(wrapper, ['wrapper_version', 'ciphertext']) ||
      wrapper.wrapper_version !== WRAPPER_VERSION ||
      typeof wrapper.ciphertext !== 'string' ||
      wrapper.ciphertext.length === 0 ||
      !/^[A-Za-z0-9+/]+={0,2}$/.test(wrapper.ciphertext)
    ) {
      throw schemaError()
    }
    let decrypted
    try {
      decrypted = await this.safeStorage.decryptStringAsync(Buffer.from(wrapper.ciphertext, 'base64'))
    } catch {
      throw storageError()
    }
    if (
      !assertPlainObject(decrypted) ||
      typeof decrypted.result !== 'string' ||
      typeof decrypted.shouldReEncrypt !== 'boolean'
    ) {
      throw storageError()
    }
    let parsed
    try {
      parsed = JSON.parse(decrypted.result)
    } catch {
      throw schemaError()
    }
    const profile = validateStoredProfile(parsed)
    if (decrypted.shouldReEncrypt) await this.write(profile)
    return profile
  }

  async snapshot() {
    try {
      return await this.fs.readFile(this.filePath)
    } catch (error) {
      if (error?.code === 'ENOENT') return null
      throw storageError()
    }
  }

  async write(profile) {
    validateStoredProfile(profile)
    await this._assertAvailable()
    let encrypted
    try {
      encrypted = await this.safeStorage.encryptStringAsync(JSON.stringify(profile))
    } catch {
      throw storageError()
    }
    if (!Buffer.isBuffer(encrypted) && !(encrypted instanceof Uint8Array)) throw storageError()
    const wrapper = Buffer.from(
      JSON.stringify({
        wrapper_version: WRAPPER_VERSION,
        ciphertext: Buffer.from(encrypted).toString('base64'),
      }),
      'utf8',
    )
    await this._atomicWrite(wrapper)
  }

  async restore(snapshot) {
    if (snapshot === null) {
      try {
        await this.fs.unlink(this.filePath)
      } catch (error) {
        if (error?.code !== 'ENOENT') throw storageError()
      }
      return
    }
    await this._atomicWrite(snapshot)
  }

  async _atomicWrite(contents) {
    const directory = path.dirname(this.filePath)
    const temporary = path.join(
      directory,
      `.${path.basename(this.filePath)}.${crypto.randomBytes(8).toString('hex')}.tmp`,
    )
    let handle
    try {
      await this.fs.mkdir(directory, { recursive: true, mode: 0o700 })
      if (process.platform !== 'win32') await this.fs.chmod(directory, 0o700)
      handle = await this.fs.open(temporary, 'wx', 0o600)
      await handle.writeFile(contents)
      await handle.sync()
      await handle.close()
      handle = null
      await this.fs.rename(temporary, this.filePath)
      if (process.platform !== 'win32') {
        let directoryHandle
        try {
          directoryHandle = await this.fs.open(directory, 'r')
          await directoryHandle.sync()
        } catch {
          // Some platforms/filesystems cannot fsync directories. The ciphertext file itself is synced.
        } finally {
          await directoryHandle?.close().catch(() => {})
        }
      }
    } catch {
      if (handle) await handle.close().catch(() => {})
      await this.fs.unlink(temporary).catch(() => {})
      throw storageError()
    }
  }
}

class ModelSettingsController {
  constructor({ vault, probeCandidate, restartBackend, getRuntimeSummary = null, externalSummary }) {
    this.vault = vault
    this.probeCandidate = probeCandidate
    this.restartBackend = restartBackend
    this.getRuntimeSummary = getRuntimeSummary
    this.externalSummary = externalSummary
    this.operation = null
    this.lastCommittedCommand = null
  }

  async getLaunchProfile() {
    return this.vault.read()
  }

  async getSettings() {
    try {
      const profile = await this.vault.read()
      if (!profile) return { ok: true, settings: this.externalSummary() }
      if (!this.getRuntimeSummary) return { ok: true, settings: publicSummary(profile) }
      let runtime = null
      try {
        runtime = await this.getRuntimeSummary()
        assertRuntime(profile, runtime)
        return { ok: true, settings: publicSummary(profile, runtime) }
      } catch {
        return {
          ok: true,
          settings: {
            ...publicSummary(profile, runtime),
            state: 'DEGRADED',
            runtime_ready: false,
            reason_codes: ['MODEL_RUNTIME_MISMATCH'],
          },
        }
      }
    } catch (error) {
      return { ok: false, error: toPublicError(error) }
    }
  }

  async apply(command) {
    if (this.operation) return this._busyResult()
    let fingerprint
    try {
      fingerprint = fingerprintApplyCommand(validateApplyCommand(command))
    } catch (error) {
      return { ok: false, error: toPublicError(error) }
    }
    if (this.lastCommittedCommand?.fingerprint === fingerprint) {
      return this.lastCommittedCommand.result
    }
    this.operation = this._apply(command)
    try {
      const result = await this.operation
      if (result.ok) this.lastCommittedCommand = { fingerprint, result }
      return result
    } finally {
      this.operation = null
    }
  }

  async clear(command) {
    if (this.operation) return this._busyResult()
    let fingerprint
    try {
      fingerprint = fingerprintClearCommand(validateClearCommand(command))
    } catch (error) {
      return { ok: false, error: toPublicError(error) }
    }
    if (this.lastCommittedCommand?.fingerprint === fingerprint) {
      return this.lastCommittedCommand.result
    }
    this.operation = this._clear(command)
    try {
      const result = await this.operation
      if (result.ok) this.lastCommittedCommand = { fingerprint, result }
      return result
    } finally {
      this.operation = null
    }
  }

  _busyResult() {
    return {
      ok: false,
      error: new ModelSettingsError(
        'MODEL_CONFIG_REVISION_CONFLICT',
        'conflict',
        '已有模型配置操作正在进行',
        false,
      ).toPublic(),
    }
  }

  async _apply(command) {
    let validated
    let prior
    let snapshot
    try {
      validated = validateApplyCommand(command)
      prior = await this.vault.read()
      validateExpectedRevision(validated.expectedRevision, prior?.revision ?? null)
      snapshot = await this.vault.snapshot()
      const probe = await this.probeCandidate({
        schema_version: SCHEMA_VERSION,
        provider: validated.provider,
        model: validated.model,
        api_key: validated.apiKey,
      })
      if (
        !assertPlainObject(probe) ||
        probe.ok !== true ||
        probe.provider !== validated.provider ||
        probe.model !== validated.model
      ) {
        throw new ModelSettingsError(
          'MODEL_PROVIDER_UNAVAILABLE',
          'dependency',
          '模型连接测试结果与候选配置不一致',
          true,
        )
      }
    } catch (error) {
      return { ok: false, error: toPublicError(error) }
    }

    const profile = {
      schema_version: SCHEMA_VERSION,
      revision: (prior?.revision ?? 0) + 1,
      state: 'ACTIVE',
      provider: validated.provider,
      model: validated.model,
      api_key: validated.apiKey,
      verified_at: new Date().toISOString(),
    }
    try {
      await this.vault.write(profile)
    } catch (error) {
      return { ok: false, error: toPublicError(error) }
    }
    try {
      const runtime = await this.restartBackend(profile)
      assertRuntime(profile, runtime)
      return { ok: true, settings: publicSummary(profile, runtime) }
    } catch {
      return this._rollback(snapshot, prior)
    }
  }

  async _clear(command) {
    let prior
    let snapshot
    try {
      const validated = validateClearCommand(command)
      prior = await this.vault.read()
      validateExpectedRevision(validated.expectedRevision, prior?.revision ?? null)
      snapshot = await this.vault.snapshot()
    } catch (error) {
      return { ok: false, error: toPublicError(error) }
    }
    const profile = {
      schema_version: SCHEMA_VERSION,
      revision: (prior?.revision ?? 0) + 1,
      state: 'DISABLED',
      verified_at: new Date().toISOString(),
    }
    try {
      await this.vault.write(profile)
    } catch (error) {
      return { ok: false, error: toPublicError(error) }
    }
    try {
      const runtime = await this.restartBackend(profile)
      assertRuntime(profile, runtime)
      return { ok: true, settings: publicSummary(profile, runtime) }
    } catch {
      return this._rollback(snapshot, prior)
    }
  }

  async _rollback(snapshot, prior) {
    try {
      await this.vault.restore(snapshot)
      const runtime = await this.restartBackend(prior)
      assertRuntime(prior, runtime)
      return {
        ok: false,
        rollback_succeeded: true,
        settings: prior ? publicSummary(prior, runtime) : this.externalSummary(),
        error: new ModelSettingsError(
          'MODEL_CONFIG_APPLY_FAILED',
          'internal',
          '新配置未能应用，已恢复之前的配置',
          true,
        ).toPublic(),
      }
    } catch {
      return {
        ok: false,
        rollback_succeeded: false,
        error: new ModelSettingsError(
          'MODEL_CONFIG_ROLLBACK_FAILED',
          'internal',
          '配置恢复失败，当前模型不可用，请重新配置',
          false,
        ).toPublic(),
      }
    }
  }
}

function assertRuntime(profile, runtime) {
  if (!profile) {
    if (
      !runtime ||
      runtime.runtime_revision !== null ||
      !['EXTERNAL_ENVIRONMENT', 'NONE'].includes(runtime.source)
    ) {
      throw new Error('external runtime mismatch')
    }
    return
  }
  if (!runtime || runtime.runtime_revision !== profile.revision) throw new Error('revision mismatch')
  if (runtime.source !== 'DESKTOP_VAULT') throw new Error('source mismatch')
  if (profile.state === 'DISABLED') {
    if (
      runtime.state !== 'DISABLED' ||
      runtime.runtime_ready ||
      runtime.provider !== null ||
      runtime.model !== null
    ) {
      throw new Error('disabled mismatch')
    }
    return
  }
  if (
    !runtime.runtime_ready ||
    runtime.state !== 'ACTIVE' ||
    runtime.provider !== profile.provider ||
    runtime.model !== profile.model
  ) {
    throw new Error('runtime route mismatch')
  }
}

function toPublicError(error) {
  if (error instanceof ModelSettingsError) return error.toPublic()
  if (assertPlainObject(error) && PUBLIC_ERROR_SEMANTICS[error.code]) {
    return { code: error.code, ...PUBLIC_ERROR_SEMANTICS[error.code] }
  }
  return { code: 'MODEL_PROVIDER_UNAVAILABLE', ...PUBLIC_ERROR_SEMANTICS.MODEL_PROVIDER_UNAVAILABLE }
}

module.exports = {
  EncryptedModelVault,
  ModelSettingsController,
  ModelSettingsError,
  SCHEMA_VERSION,
  SUPPORTED_MODELS,
  applyModelProfileToEnvironment,
  assertRuntime,
  externalSummaryFromEnv,
  isAllowedModelSettingsSender,
  publicSummary,
  validateApplyCommand,
  validateClearCommand,
}
