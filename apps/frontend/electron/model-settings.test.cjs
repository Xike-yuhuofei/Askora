'use strict'

const assert = require('node:assert/strict')
const fs = require('node:fs')
const os = require('node:os')
const path = require('node:path')
const vm = require('node:vm')
const { afterEach, describe, test } = require('node:test')

const {
  EncryptedModelVault,
  ModelSettingsController,
  ModelSettingsError,
  applyModelProfileToEnvironment,
  assertRuntime,
  externalSummaryFromEnv,
  isAllowedModelSettingsSender,
  publicSummary,
  validateApplyCommand,
  validateClearCommand,
} = require('./model-settings.cjs')

const temporaryDirectories = []

afterEach(async () => {
  await Promise.all(
    temporaryDirectories.splice(0).map((directory) =>
      fs.promises.rm(directory, { recursive: true, force: true }),
    ),
  )
})

async function makeVault(options = {}) {
  const directory = await fs.promises.mkdtemp(path.join(os.tmpdir(), 'askora-model-settings-'))
  temporaryDirectories.push(directory)
  const filePath = path.join(directory, 'model-route-profile.v1.enc.json')
  let encryptionSequence = 0
  const safeStorage = {
    async isAsyncEncryptionAvailable() {
      if (options.availabilityError) throw new Error('keychain unavailable: raw secret')
      return options.available !== false
    },
    async encryptStringAsync(value) {
      if (options.encryptError) throw new Error('encrypt raw secret')
      encryptionSequence += 1
      return Buffer.from(`cipher-${encryptionSequence}:${value}`, 'utf8')
    },
    async decryptStringAsync(ciphertext) {
      if (options.decryptError) throw new Error('decrypt raw secret')
      const value = ciphertext.toString('utf8').replace(/^cipher-\d+:/, '')
      return { result: value, shouldReEncrypt: Boolean(options.shouldReEncrypt) }
    },
  }
  return {
    directory,
    filePath,
    safeStorage,
    vault: new EncryptedModelVault({
      safeStorage,
      filePath,
      fsPromises: options.fsPromises || fs.promises,
    }),
    encryptionCount: () => encryptionSequence,
  }
}

function activeProfile(overrides = {}) {
  return {
    schema_version: '1.0',
    revision: 1,
    state: 'ACTIVE',
    provider: 'deepseek',
    model: 'deepseek-chat',
    api_key: 'test-secret-that-must-never-leak',
    verified_at: '2026-08-09T01:02:03.000Z',
    ...overrides,
  }
}

function disabledProfile(overrides = {}) {
  return {
    schema_version: '1.0',
    revision: 2,
    state: 'DISABLED',
    provider: null,
    model: null,
    verified_at: null,
    ...overrides,
  }
}

function runtimeFor(profile, overrides = {}) {
  return {
    source: 'DESKTOP_VAULT',
    state: profile.state,
    provider: profile.state === 'ACTIVE' ? profile.provider : null,
    model: profile.state === 'ACTIVE' ? profile.model : null,
    runtime_ready: profile.state === 'ACTIVE',
    runtime_revision: profile.revision,
    ...overrides,
  }
}

function applyCommand(overrides = {}) {
  return {
    schema_version: '1.0',
    provider: 'deepseek',
    model: 'deepseek-chat',
    api_key: 'new-secret-key',
    expected_revision: null,
    ...overrides,
  }
}

describe('EncryptedModelVault', () => {
  test('async safeStorage unavailable fails closed without creating plaintext or ciphertext', async () => {
    const { vault, filePath } = await makeVault({ available: false })

    await assert.rejects(vault.write(activeProfile()), (error) => {
      assert.equal(error.code, 'MODEL_CONFIG_STORAGE_UNAVAILABLE')
      assert.equal(error.category, 'dependency')
      assert.equal(error.retryable, false)
      assert.doesNotMatch(error.message, /test-secret/)
      return true
    })
    await assert.rejects(fs.promises.access(filePath), { code: 'ENOENT' })
  })

  test('async encryption writes only a versioned ciphertext wrapper and decrypts the exact profile', async () => {
    const { vault, filePath } = await makeVault()
    const profile = activeProfile()

    await vault.write(profile)
    const persisted = await fs.promises.readFile(filePath, 'utf8')
    assert.doesNotMatch(persisted, /test-secret-that-must-never-leak/)
    assert.deepEqual(Object.keys(JSON.parse(persisted)).sort(), ['ciphertext', 'wrapper_version'])
    assert.deepEqual(await vault.read(), profile)
  })

  test('encrypt and decrypt failures use the sanitized storage error and never plaintext fallback', async () => {
    const encrypting = await makeVault({ encryptError: true })
    await assert.rejects(encrypting.vault.write(activeProfile()), (error) => {
      assert.equal(error.code, 'MODEL_CONFIG_STORAGE_UNAVAILABLE')
      assert.doesNotMatch(JSON.stringify(error), /raw secret|test-secret/)
      return true
    })

    const decrypting = await makeVault()
    await decrypting.vault.write(activeProfile())
    const failingReader = new EncryptedModelVault({
      safeStorage: { ...decrypting.safeStorage, decryptStringAsync: async () => { throw new Error('raw secret') } },
      filePath: decrypting.filePath,
    })
    await assert.rejects(failingReader.read(), (error) => {
      assert.equal(error.code, 'MODEL_CONFIG_STORAGE_UNAVAILABLE')
      assert.doesNotMatch(JSON.stringify(error), /raw secret|test-secret/)
      return true
    })
  })

  test('decrypt rotation signal re-encrypts after successful parsing and retires old ciphertext atomically', async () => {
    const initial = await makeVault()
    await initial.vault.write(activeProfile())
    const before = await fs.promises.readFile(initial.filePath)
    const rotating = new EncryptedModelVault({
      safeStorage: {
        ...initial.safeStorage,
        async decryptStringAsync(ciphertext) {
          const result = ciphertext.toString('utf8').replace(/^cipher-\d+:/, '')
          return { result, shouldReEncrypt: true }
        },
      },
      filePath: initial.filePath,
    })

    assert.deepEqual(await rotating.read(), activeProfile())
    const after = await fs.promises.readFile(initial.filePath)
    assert.notDeepEqual(after, before)
    assert.equal(initial.encryptionCount(), 2)
    assert.deepEqual((await fs.promises.readdir(initial.directory)).sort(), [path.basename(initial.filePath)])
  })

  test('corrupt wrapper fails closed and never returns or rewrites guessed profile data', async () => {
    const { vault, filePath } = await makeVault()
    await fs.promises.writeFile(filePath, '{"api_key":"plaintext-leak"}', { mode: 0o600 })
    const before = await fs.promises.readFile(filePath)

    await assert.rejects(vault.read(), (error) => {
      assert.equal(error.code, 'MODEL_CONFIG_SCHEMA_UNSUPPORTED')
      assert.doesNotMatch(JSON.stringify(error), /plaintext-leak/)
      return true
    })
    assert.deepEqual(await fs.promises.readFile(filePath), before)
  })

  test('failed atomic rename preserves prior ciphertext and removes the temporary artifact', async () => {
    const initial = await makeVault()
    await initial.vault.write(activeProfile())
    const before = await fs.promises.readFile(initial.filePath)
    const failingFs = Object.create(fs.promises)
    failingFs.rename = async () => { throw new Error('simulated crash before rename') }
    const failingVault = new EncryptedModelVault({
      safeStorage: initial.safeStorage,
      filePath: initial.filePath,
      fsPromises: failingFs,
    })

    await assert.rejects(failingVault.write(activeProfile({ revision: 2 })), {
      code: 'MODEL_CONFIG_STORAGE_UNAVAILABLE',
    })
    assert.deepEqual(await fs.promises.readFile(initial.filePath), before)
    assert.deepEqual((await fs.promises.readdir(initial.directory)).sort(), [path.basename(initial.filePath)])
  })
})

describe('public profile/source contract', () => {
  test('public summary uses the exact secret-free MODEL-CONFIG-010 fields', () => {
    const profile = activeProfile({ ciphertext: 'must-not-leak', control_token: 'must-not-leak' })
    const summary = publicSummary(profile, runtimeFor(profile, {
      reason_codes: ['raw-secret-in-reason', 'MODEL_CONFIGURATION_DISABLED'],
    }))

    assert.deepEqual(Object.keys(summary).sort(), [
      'model',
      'provider',
      'reason_codes',
      'revision',
      'runtime_ready',
      'runtime_revision',
      'schema_version',
      'source',
      'state',
      'verified_at',
    ])
    assert.equal(summary.state, 'ACTIVE')
    assert.deepEqual(summary.reason_codes, ['MODEL_CONFIGURATION_DISABLED'])
    assert.doesNotMatch(JSON.stringify(summary), /api_key|secret|ciphertext|control_token|base_url|internal path/)
  })

  test('desktop ACTIVE and DISABLED revisions both take precedence over external environment', async () => {
    const externalSummary = () => externalSummaryFromEnv({
      LLM_DEFAULT_PROVIDER: 'qwen',
      LLM_QWEN_API_KEY: 'external-secret',
      LLM_QWEN_MODEL: 'qwen-turbo',
    })
    for (const profile of [activeProfile(), disabledProfile()]) {
      const controller = new ModelSettingsController({
        vault: { read: async () => profile },
        probeCandidate: async () => {},
        restartBackend: async () => runtimeFor(profile),
        externalSummary,
      })
      const result = await controller.getSettings()
      assert.equal(result.ok, true)
      assert.equal(result.settings.source, 'DESKTOP_VAULT')
      assert.equal(result.settings.state, profile.state)
      assert.doesNotMatch(JSON.stringify(result), /external-secret/)
    }
  })

  test('external environment is read-only only when no desktop revision exists', async () => {
    const controller = new ModelSettingsController({
      vault: { read: async () => null },
      probeCandidate: async () => {},
      restartBackend: async () => {},
      externalSummary: () => externalSummaryFromEnv({
        LLM_DEFAULT_PROVIDER: 'qwen',
        LLM_QWEN_API_KEY: 'external-secret',
        LLM_QWEN_MODEL: 'qwen-turbo',
      }),
    })

    const result = await controller.getSettings()
    assert.equal(result.settings.state, 'EXTERNAL_READ_ONLY')
    assert.equal(result.settings.source, 'EXTERNAL_ENVIRONMENT')
    assert.equal(result.settings.revision, null)
    assert.doesNotMatch(JSON.stringify(result), /external-secret/)
  })

  test('stored desktop summary is READY only after exact current runtime verification', async () => {
    const profile = activeProfile({ revision: 5 })
    let runtime = runtimeFor(profile)
    const controller = new ModelSettingsController({
      vault: { read: async () => profile },
      probeCandidate: async () => {},
      restartBackend: async () => {},
      getRuntimeSummary: async () => runtime,
      externalSummary: () => externalSummaryFromEnv({}),
    })

    const ready = await controller.getSettings()
    assert.equal(ready.settings.state, 'ACTIVE')
    assert.equal(ready.settings.runtime_ready, true)
    assert.equal(ready.settings.runtime_revision, 5)

    runtime = runtimeFor(profile, { runtime_revision: 4, provider: 'qwen' })
    const degraded = await controller.getSettings()
    assert.equal(degraded.ok, true)
    assert.equal(degraded.settings.state, 'DEGRADED')
    assert.equal(degraded.settings.runtime_ready, false)
    assert.equal(degraded.settings.runtime_revision, 4)
    assert.deepEqual(degraded.settings.reason_codes, ['MODEL_RUNTIME_MISMATCH'])
  })
})

describe('command validation and activation transaction', () => {
  test('apply rejects unknown schema fields and provider/model mismatches before probe', async () => {
    assert.throws(
      () => validateApplyCommand(applyCommand({ unexpected_secret_copy: 'not allowed' })),
      { code: 'MODEL_CONFIG_SCHEMA_UNSUPPORTED' },
    )
    assert.throws(
      () => validateApplyCommand(applyCommand({ provider: 'qwen', model: 'deepseek-chat' })),
      { code: 'MODEL_NOT_AVAILABLE' },
    )
    assert.throws(() => validateApplyCommand(applyCommand({ expected_revision: undefined })), {
      code: 'MODEL_CONFIG_REVISION_CONFLICT',
    })
    assert.throws(() => validateApplyCommand(applyCommand({ expected_revision: -1 })), {
      code: 'MODEL_CONFIG_REVISION_CONFLICT',
    })
  })

  test('clear requires the exact narrow schema and expected revision field', () => {
    assert.throws(() => validateClearCommand({ schema_version: '1.0' }), {
      code: 'MODEL_CONFIG_SCHEMA_UNSUPPORTED',
    })
    assert.throws(
      () => validateClearCommand({ schema_version: '1.0', expected_revision: 1, extra: true }),
      { code: 'MODEL_CONFIG_SCHEMA_UNSUPPORTED' },
    )
  })

  test('probe failure leaves the vault bytes untouched and does not restart backend', async () => {
    const { vault, filePath } = await makeVault()
    await vault.write(activeProfile())
    const before = await fs.promises.readFile(filePath)
    let restartCount = 0
    const controller = new ModelSettingsController({
      vault,
      probeCandidate: async () => {
        throw new ModelSettingsError('MODEL_CREDENTIAL_REJECTED', 'authorization', '凭据被拒绝', false)
      },
      restartBackend: async () => { restartCount += 1 },
      externalSummary: () => externalSummaryFromEnv({}),
    })

    const result = await controller.apply(applyCommand({ expected_revision: 1 }))
    assert.equal(result.ok, false)
    assert.equal(result.error.code, 'MODEL_CREDENTIAL_REJECTED')
    assert.deepEqual(await fs.promises.readFile(filePath), before)
    assert.equal(restartCount, 0)
    assert.doesNotMatch(JSON.stringify(result), /new-secret-key/)
  })

  test('probe success with a different provider or model is rejected before persistence', async () => {
    const { vault, filePath } = await makeVault()
    const controller = new ModelSettingsController({
      vault,
      probeCandidate: async () => ({
        ok: true,
        provider: 'qwen',
        model: 'qwen-turbo',
      }),
      restartBackend: async () => { throw new Error('must not restart') },
      externalSummary: () => externalSummaryFromEnv({}),
    })

    const result = await controller.apply(applyCommand())
    assert.equal(result.ok, false)
    assert.equal(result.error.code, 'MODEL_PROVIDER_UNAVAILABLE')
    await assert.rejects(fs.promises.access(filePath), { code: 'ENOENT' })
  })

  test('storage failure before vault replacement preserves the prior revision without restarting', async () => {
    let restartCount = 0
    const prior = activeProfile({ revision: 3 })
    const controller = new ModelSettingsController({
      vault: {
        read: async () => prior,
        snapshot: async () => Buffer.from('prior'),
        write: async () => { throw new ModelSettingsError(
          'MODEL_CONFIG_STORAGE_UNAVAILABLE',
          'dependency',
          '系统安全存储当前不可用，模型配置未保存',
          false,
        ) },
        restore: async () => { throw new Error('must not restore before replace') },
      },
      probeCandidate: async () => ({ ok: true, provider: 'deepseek', model: 'deepseek-chat' }),
      restartBackend: async () => { restartCount += 1 },
      externalSummary: () => externalSummaryFromEnv({}),
    })

    const result = await controller.apply(applyCommand({ expected_revision: 3 }))
    assert.equal(result.ok, false)
    assert.equal(result.error.code, 'MODEL_CONFIG_STORAGE_UNAVAILABLE')
    assert.equal(restartCount, 0)
  })

  test('provider errors are mapped to stable sanitized public messages without secret echo', async () => {
    const { vault } = await makeVault()
    const controller = new ModelSettingsController({
      vault,
      probeCandidate: async () => {
        throw {
          code: 'MODEL_CREDENTIAL_REJECTED',
          category: 'authorization',
          message: 'provider rejected new-secret-key in Authorization header',
          retryable: false,
        }
      },
      restartBackend: async () => {},
      externalSummary: () => externalSummaryFromEnv({}),
    })

    const result = await controller.apply(applyCommand())
    assert.equal(result.error.code, 'MODEL_CREDENTIAL_REJECTED')
    assert.equal(result.error.category, 'authorization')
    assert.equal(result.error.retryable, false)
    assert.doesNotMatch(JSON.stringify(result), /new-secret-key|Authorization header|provider rejected/)
  })

  test('unknown provider errors fail closed to a stable sanitized dependency error', async () => {
    const { vault } = await makeVault()
    const controller = new ModelSettingsController({
      vault,
      probeCandidate: async () => {
        throw new ModelSettingsError(
          'PROVIDER_RAW_UNKNOWN',
          'internal',
          'new-secret-key leaked by provider',
          false,
        )
      },
      restartBackend: async () => {},
      externalSummary: () => externalSummaryFromEnv({}),
    })

    const result = await controller.apply(applyCommand())
    assert.equal(result.error.code, 'MODEL_PROVIDER_UNAVAILABLE')
    assert.equal(result.error.category, 'dependency')
    assert.equal(result.error.retryable, true)
    assert.doesNotMatch(JSON.stringify(result), /PROVIDER_RAW_UNKNOWN|new-secret-key|leaked by provider/)
  })

  test('stale expected revision conflicts before probe and persistence', async () => {
    const { vault, filePath } = await makeVault()
    await vault.write(activeProfile({ revision: 7 }))
    const before = await fs.promises.readFile(filePath)
    let probeCount = 0
    const controller = new ModelSettingsController({
      vault,
      probeCandidate: async () => { probeCount += 1 },
      restartBackend: async () => {},
      externalSummary: () => externalSummaryFromEnv({}),
    })

    const result = await controller.apply(applyCommand({ expected_revision: 6 }))
    assert.equal(result.error.code, 'MODEL_CONFIG_REVISION_CONFLICT')
    assert.equal(probeCount, 0)
    assert.deepEqual(await fs.promises.readFile(filePath), before)
  })

  test('a second apply or clear is rejected while the first command is in flight', async () => {
    let releaseProbe
    const probeBlocked = new Promise((resolve) => { releaseProbe = resolve })
    const profile = activeProfile()
    const vault = {
      read: async () => null,
      snapshot: async () => null,
      write: async () => {},
      restore: async () => {},
    }
    const controller = new ModelSettingsController({
      vault,
      probeCandidate: async () => probeBlocked,
      restartBackend: async () => runtimeFor(profile),
      externalSummary: () => externalSummaryFromEnv({}),
    })

    const first = controller.apply(applyCommand())
    await new Promise((resolve) => setImmediate(resolve))
    const secondApply = await controller.apply(applyCommand())
    const clear = await controller.clear({ schema_version: '1.0', expected_revision: null })
    assert.equal(secondApply.error.code, 'MODEL_CONFIG_REVISION_CONFLICT')
    assert.equal(clear.error.code, 'MODEL_CONFIG_REVISION_CONFLICT')
    releaseProbe({ ok: true, provider: 'deepseek', model: 'deepseek-chat' })
    assert.equal((await first).ok, true)
  })

  test('an exact repeated successful command returns its committed summary without another probe or restart', async () => {
    let current = null
    let probeCount = 0
    let restartCount = 0
    const controller = new ModelSettingsController({
      vault: {
        read: async () => current,
        snapshot: async () => null,
        write: async (profile) => { current = profile },
        restore: async () => { current = null },
      },
      probeCandidate: async () => {
        probeCount += 1
        return { ok: true, provider: 'deepseek', model: 'deepseek-chat' }
      },
      restartBackend: async (profile) => {
        restartCount += 1
        return runtimeFor(profile)
      },
      externalSummary: () => externalSummaryFromEnv({}),
    })
    const command = applyCommand()

    const first = await controller.apply(command)
    const repeated = await controller.apply({ ...command })
    assert.deepEqual(repeated, first)
    assert.equal(probeCount, 1)
    assert.equal(restartCount, 1)
  })

  test('activation verifies exact runtime revision, provider and model', () => {
    const profile = activeProfile({ revision: 9 })
    assert.doesNotThrow(() => assertRuntime(profile, runtimeFor(profile)))
    for (const mutation of [
      { runtime_revision: 8 },
      { source: 'EXTERNAL_ENVIRONMENT' },
      { provider: 'qwen' },
      { model: 'deepseek-reasoner' },
      { runtime_ready: false },
      { state: 'DEGRADED' },
    ]) {
      assert.throws(() => assertRuntime(profile, runtimeFor(profile, mutation)))
    }
  })

  test('failed activation restores exact prior ciphertext and verifies the prior runtime', async () => {
    const { vault, filePath } = await makeVault()
    const prior = activeProfile({ revision: 4 })
    await vault.write(prior)
    const before = await fs.promises.readFile(filePath)
    const restarted = []
    const controller = new ModelSettingsController({
      vault,
      probeCandidate: async () => ({ ok: true, provider: 'deepseek', model: 'deepseek-chat' }),
      restartBackend: async (profile) => {
        restarted.push(profile)
        if (restarted.length === 1) throw new Error('new backend did not become ready')
        return runtimeFor(prior)
      },
      externalSummary: () => externalSummaryFromEnv({}),
    })

    const result = await controller.apply(applyCommand({ expected_revision: 4 }))
    assert.equal(result.ok, false)
    assert.equal(result.rollback_succeeded, true)
    assert.equal(result.error.code, 'MODEL_CONFIG_APPLY_FAILED')
    assert.deepEqual(await fs.promises.readFile(filePath), before)
    assert.deepEqual(restarted[1], prior)
    assert.equal(result.settings.revision, 4)
  })

  test('rollback runtime mismatch is reported as blocking rollback failure', async () => {
    const prior = activeProfile({ revision: 2 })
    let current = prior
    const vault = {
      read: async () => current,
      snapshot: async () => Buffer.from('exact-prior-ciphertext'),
      write: async (profile) => { current = profile },
      restore: async () => { current = prior },
    }
    let calls = 0
    const controller = new ModelSettingsController({
      vault,
      probeCandidate: async () => ({ ok: true, provider: 'deepseek', model: 'deepseek-chat' }),
      restartBackend: async (profile) => {
        calls += 1
        if (calls === 1) throw new Error('new failed')
        return runtimeFor(profile, { runtime_revision: 999 })
      },
      externalSummary: () => externalSummaryFromEnv({}),
    })

    const result = await controller.apply(applyCommand({ expected_revision: 2 }))
    assert.equal(result.ok, false)
    assert.equal(result.rollback_succeeded, false)
    assert.equal(result.error.code, 'MODEL_CONFIG_ROLLBACK_FAILED')
    assert.equal(result.error.retryable, false)
  })

  test('rollback to no prior vault revision verifies the external runtime exactly', async () => {
    let current = null
    let calls = 0
    const controller = new ModelSettingsController({
      vault: {
        read: async () => current,
        snapshot: async () => null,
        write: async (profile) => { current = profile },
        restore: async () => { current = null },
      },
      probeCandidate: async () => ({ ok: true, provider: 'deepseek', model: 'deepseek-chat' }),
      restartBackend: async () => {
        calls += 1
        if (calls === 1) throw new Error('new failed')
        return {
          source: 'DESKTOP_VAULT',
          state: 'ACTIVE',
          provider: 'qwen',
          model: 'qwen-turbo',
          runtime_ready: true,
          runtime_revision: 99,
        }
      },
      externalSummary: () => externalSummaryFromEnv({}),
    })

    const result = await controller.apply(applyCommand())
    assert.equal(result.rollback_succeeded, false)
    assert.equal(result.error.code, 'MODEL_CONFIG_ROLLBACK_FAILED')
  })

  test('clear writes and activates a new DISABLED tombstone instead of deleting or falling back', async () => {
    const { vault } = await makeVault()
    await vault.write(activeProfile({ revision: 3 }))
    let activated
    const controller = new ModelSettingsController({
      vault,
      probeCandidate: async () => { throw new Error('clear must not probe') },
      restartBackend: async (profile) => {
        activated = profile
        return runtimeFor(profile)
      },
      externalSummary: () => externalSummaryFromEnv({ LLM_QWEN_API_KEY: 'external-secret' }),
    })

    const result = await controller.clear({ schema_version: '1.0', expected_revision: 3 })
    assert.equal(result.ok, true)
    assert.equal(result.settings.state, 'DISABLED')
    assert.equal(result.settings.source, 'DESKTOP_VAULT')
    assert.equal(result.settings.revision, 4)
    assert.deepEqual(await vault.read(), activated)
    assert.equal('api_key' in activated, false)
  })
})

describe('backend launch environment projection', () => {
  const inherited = {
    PATH: '/usr/bin',
    LLM_DEFAULT_PROVIDER: 'qwen',
    LLM_MATH_PROVIDER: 'qwen',
    LLM_QWEN_API_KEY: 'qwen-inherited',
    LLM_DEEPSEEK_API_KEY: 'deepseek-inherited',
    LLM_DOUBAO_API_KEY: 'doubao-inherited',
    LLM_ZHIPU_API_KEY: 'zhipu-inherited',
  }

  test('ACTIVE vault clears every inherited provider key then injects only its exact route', () => {
    const env = applyModelProfileToEnvironment(inherited, activeProfile({ revision: 12 }))
    assert.equal(env.PATH, '/usr/bin')
    assert.equal(env.LLM_QWEN_API_KEY, '')
    assert.equal(env.LLM_DEEPSEEK_API_KEY, 'test-secret-that-must-never-leak')
    assert.equal(env.LLM_DOUBAO_API_KEY, '')
    assert.equal(env.LLM_ZHIPU_API_KEY, '')
    assert.equal(env.LLM_DEFAULT_PROVIDER, 'deepseek')
    assert.equal(env.LLM_MATH_PROVIDER, 'deepseek')
    assert.equal(env.LLM_DEEPSEEK_MODEL, 'deepseek-chat')
    assert.equal(env.MODEL_CONFIG_SOURCE, 'DESKTOP_VAULT')
    assert.equal(env.MODEL_CONFIG_STATE, 'ACTIVE')
    assert.equal(env.MODEL_CONFIG_REVISION, '12')
  })

  test('DISABLED tombstone explicitly clears every inherited provider key', () => {
    const env = applyModelProfileToEnvironment(inherited, disabledProfile({ revision: 13 }))
    for (const provider of ['QWEN', 'DEEPSEEK', 'DOUBAO', 'ZHIPU']) {
      assert.equal(env[`LLM_${provider}_API_KEY`], '')
    }
    assert.equal(env.MODEL_CONFIG_SOURCE, 'DESKTOP_VAULT')
    assert.equal(env.MODEL_CONFIG_STATE, 'DISABLED')
    assert.equal(env.MODEL_CONFIG_REVISION, '13')
  })

  test('absence of vault revision preserves external compatibility without copying it', () => {
    const env = applyModelProfileToEnvironment(inherited, null)
    assert.equal(env.LLM_QWEN_API_KEY, 'qwen-inherited')
    assert.equal(env.MODEL_CONFIG_SOURCE, 'EXTERNAL_ENVIRONMENT')
    assert.equal(env.MODEL_CONFIG_STATE, 'EXTERNAL_READ_ONLY')
    assert.equal('MODEL_CONFIG_REVISION' in env, false)
  })
})

describe('IPC and preload isolation', () => {
  test('sender validation accepts only the exact top-level renderer origin and path', () => {
    const mainFrame = { url: 'http://localhost:5173/' }
    const webContents = { mainFrame }
    const allowed = { sender: webContents, senderFrame: mainFrame }
    assert.equal(
      isAllowedModelSettingsSender(allowed, webContents, {
        isDev: true,
        devURL: 'http://localhost:5173/',
      }),
      true,
    )
    assert.equal(
      isAllowedModelSettingsSender({ ...allowed, senderFrame: { url: mainFrame.url } }, webContents, {
        isDev: true,
        devURL: 'http://localhost:5173/',
      }),
      false,
    )
    assert.equal(
      isAllowedModelSettingsSender(
        { sender: webContents, senderFrame: { url: 'http://localhost:5173/settings' } },
        webContents,
        { isDev: true, devURL: 'http://localhost:5173/' },
      ),
      false,
    )
    assert.equal(
      isAllowedModelSettingsSender(
        { sender: webContents, senderFrame: { url: 'http://127.0.0.1:5173/' } },
        webContents,
        { isDev: true, devURL: 'http://localhost:5173/' },
      ),
      false,
    )
  })

  test('packaged sender validation allows only the configured file URL, not arbitrary file pages', () => {
    const allowedPath = '/Applications/Askora.app/Contents/Resources/app.asar/dist/index.html'
    const mainFrame = { url: `file://${allowedPath}` }
    const webContents = { mainFrame }
    assert.equal(
      isAllowedModelSettingsSender({ sender: webContents, senderFrame: mainFrame }, webContents, {
        isDev: false,
        allowedFilePath: allowedPath,
      }),
      true,
    )
    const otherFrame = { url: 'file:///tmp/untrusted.html' }
    const otherContents = { mainFrame: otherFrame }
    assert.equal(
      isAllowedModelSettingsSender({ sender: otherContents, senderFrame: otherFrame }, otherContents, {
        isDev: false,
        allowedFilePath: allowedPath,
      }),
      false,
    )
  })

  test('preload exposes only narrow functions and invokes only fixed allowlist channels', () => {
    const invocations = []
    let exposed
    const source = fs.readFileSync(path.join(__dirname, 'preload.cjs'), 'utf8')
    vm.runInNewContext(source, {
      require(moduleName) {
        assert.equal(moduleName, 'electron')
        return {
          contextBridge: { exposeInMainWorld: (_name, value) => { exposed = value } },
          ipcRenderer: { invoke: (...args) => { invocations.push(args); return Promise.resolve() } },
        }
      },
    })

    assert.equal(typeof exposed.getModelSettings, 'function')
    assert.equal(typeof exposed.applyModelSettings, 'function')
    assert.equal(typeof exposed.clearModelSettings, 'function')
    assert.equal('ipcRenderer' in exposed, false)
    assert.equal('decryptModelSettings' in exposed, false)
    assert.equal('readFile' in exposed, false)
    assert.equal('getEnvironment' in exposed, false)
    exposed.getModelSettings()
    exposed.applyModelSettings({ schema_version: '1.0' })
    exposed.clearModelSettings({ schema_version: '1.0' })
    assert.deepEqual(invocations.slice(-3), [
      ['model-settings:get'],
      ['model-settings:apply', { schema_version: '1.0' }],
      ['model-settings:clear', { schema_version: '1.0' }],
    ])
  })
})
