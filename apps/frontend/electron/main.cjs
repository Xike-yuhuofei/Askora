const { app, BrowserWindow, Menu, shell, ipcMain, safeStorage, dialog } = require('electron')
const crypto = require('crypto')
const fs = require('fs')
const http = require('http')
const path = require('path')
const { spawn } = require('child_process')
const { createAppMenu } = require('./app-menu.cjs')
const bootstrapDiagnostics = require('./bootstrap-diagnostics.cjs')
const {
  EncryptedModelVault,
  ModelSettingsController,
  ModelSettingsError,
  applyModelProfileToEnvironment,
  externalSummaryFromEnv,
  isAllowedModelSettingsSender,
} = require('./model-settings.cjs')

const isDev = !app.isPackaged
if (process.platform !== 'win32') process.umask(0o077)
const userDataPath = process.env.ASKORA_USER_DATA_DIR
  ? path.resolve(process.env.ASKORA_USER_DATA_DIR)
  : path.join(app.getPath('appData'), 'askora')
fs.mkdirSync(userDataPath, { recursive: true })
if (process.platform !== 'win32') fs.chmodSync(userDataPath, 0o700)
app.setPath('userData', userDataPath)
app.setPath('sessionData', path.join(userDataPath, 'Session'))

const BACKEND_PORT = 8765
// PyInstaller one-file 首次解压在较慢磁盘上可能超过 20 秒。
const BACKEND_STARTUP_TIMEOUT = 60000
const MAINTENANCE_TIMEOUT = 15 * 60 * 1000
const MAX_MAINTENANCE_OUTPUT_BYTES = 2 * 1024 * 1024

let mainWindow
let backendProcess = null
let readyBackendURL = null
let backendStartPromise = null
let backendDiagnosticBuffer = ''
let backendStartupState = bootstrapDiagnostics.starting({ attempt: -1 })
let desktopControlToken = null
let modelSettingsController = null
let activeLaunchProfile = null
let windowCreationPromise = null

function getBackendBinaryPath() {
  if (isDev) {
    const backendDir = path.join(__dirname, '..', '..', 'backend')
    const pythonPath = path.join(backendDir, '.venv', 'bin', 'python')
    if (!fs.existsSync(pythonPath)) return null
    return { command: pythonPath, args: ['-m', 'app.main'], cwd: backendDir }
  }

  const backendBin = path.join(process.resourcesPath || '', 'backend', 'askora-backend')
  if (!fs.existsSync(backendBin)) return null
  return { command: backendBin, args: [], cwd: path.dirname(backendBin) }
}

function loadOrCreateLocalSecrets() {
  const secretsPath = path.join(userDataPath, 'local-secrets.json')
  try {
    const parsed = JSON.parse(fs.readFileSync(secretsPath, 'utf8'))
    if (parsed.jwtSecret?.length >= 32 && parsed.kekSecret?.length >= 32) {
      fs.chmodSync(secretsPath, 0o600)
      return parsed
    }
  } catch {}

  const secrets = {
    jwtSecret: crypto.randomBytes(48).toString('base64url'),
    kekSecret: crypto.randomBytes(48).toString('base64url'),
  }
  fs.writeFileSync(secretsPath, JSON.stringify(secrets), { mode: 0o600 })
  return secrets
}

function loadOrCreateRecoveryKey() {
  if (process.platform !== 'darwin' || !safeStorage.isEncryptionAvailable()) {
    const error = new Error('当前设备无法使用系统安全存储')
    error.code = 'DATA_MODE_UNSUPPORTED'
    throw error
  }
  const keyPath = path.join(userDataPath, 'recovery-key.bin')
  try {
    const encrypted = fs.readFileSync(keyPath)
    const recovered = safeStorage.decryptString(encrypted)
    if (/^[A-Za-z0-9_-]{43}$/.test(recovered)) {
      fs.chmodSync(keyPath, 0o600)
      return recovered
    }
  } catch {}

  const recoveryKey = crypto.randomBytes(32).toString('base64url')
  const encrypted = safeStorage.encryptString(recoveryKey)
  const temporaryPath = `${keyPath}.${process.pid}.tmp`
  fs.writeFileSync(temporaryPath, encrypted, { mode: 0o600, flag: 'wx' })
  fs.renameSync(temporaryPath, keyPath)
  fs.chmodSync(keyPath, 0o600)
  return recoveryKey
}

function waitForBackend(url, timeoutMs) {
  const deadline = Date.now() + timeoutMs
  return new Promise((resolve) => {
    const check = () => {
      if (!backendProcess || backendProcess.exitCode !== null || Date.now() >= deadline) {
        resolve(false)
        return
      }

      const request = http.get(`${url}/ready`, (response) => {
        response.resume()
        if (response.statusCode === 200) {
          resolve(true)
        } else {
          setTimeout(check, 250)
        }
      })
      request.setTimeout(1000, () => request.destroy())
      request.on('error', () => setTimeout(check, 250))
    }
    check()
  })
}

function setBackendFailure(code, options = {}) {
  publishBackendStartupState(bootstrapDiagnostics.failed(backendStartupState, code, options))
}

function publishBackendStartupState(nextState) {
  backendStartupState = nextState
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send('app:backend-startup-state', { ...backendStartupState })
  }
}

function consumeBackendDiagnostics(data) {
  backendDiagnosticBuffer += data.toString()
  const lines = backendDiagnosticBuffer.split(/\r?\n/)
  backendDiagnosticBuffer = lines.pop() || ''
  for (const line of lines) {
    const diagnostic = bootstrapDiagnostics.parseDiagnosticLine(backendStartupState, line.trim())
    if (diagnostic) publishBackendStartupState(diagnostic)
  }
}

function buildBackendEnvironment(profile, localSecrets, databasePath, controlToken) {
  const baseEnvironment = {
    ...process.env,
    APP_ENV: 'local',
    PRIVATE_APP: 'true',
    APP_NAME: 'askora-local',
    APP_VERSION: '0.1.0',
    HOST: '127.0.0.1',
    PORT: String(BACKEND_PORT),
    DATABASE_URL: `sqlite+aiosqlite:///${databasePath}`,
    LOCAL_STORAGE_BASE_PATH: path.join(userDataPath, 'documents'),
    REDIS_URL: 'redis://127.0.0.1:6379/0',
    JWT_SECRET_KEY: localSecrets.jwtSecret,
    KEK_MASTER_KEY: localSecrets.kekSecret,
    ENABLE_ORCHESTRATOR_DEBUG_API: 'false',
    WORKER_ENABLED: 'false',
    DESKTOP_CONTROL_TOKEN: controlToken,
  }
  return applyModelProfileToEnvironment(baseEnvironment, profile)
}

async function startLocalBackendAttempt(profile = activeLaunchProfile) {
  publishBackendStartupState(bootstrapDiagnostics.starting(backendStartupState))
  backendDiagnosticBuffer = ''
  const backendInfo = getBackendBinaryPath()
  if (!backendInfo) {
    console.error('[Askora] Local backend executable was not found')
    setBackendFailure('BOOTSTRAP_BACKEND_BINARY_MISSING', { retryable: false })
    return null
  }

  const localSecrets = loadOrCreateLocalSecrets()
  const databasePath = path.join(userDataPath, 'askora.db')
  const backendURL = `http://127.0.0.1:${BACKEND_PORT}`
  desktopControlToken = crypto.randomBytes(48).toString('base64url')
  const env = buildBackendEnvironment(profile, localSecrets, databasePath, desktopControlToken)
  const spawnedProcess = spawn(backendInfo.command, backendInfo.args, {
    env,
    stdio: ['ignore', 'pipe', 'pipe'],
    windowsHide: true,
    cwd: backendInfo.cwd,
  })
  backendProcess = spawnedProcess

  // Backend output may contain paths or provider detail. The desktop boundary only
  // consumes the fixed-prefix sanitized diagnostic channel and never mirrors raw text.
  spawnedProcess.stdout?.on('data', () => {})
  spawnedProcess.stderr?.on('data', (data) => {
    consumeBackendDiagnostics(data)
  })
  spawnedProcess.on('error', () => {
    console.error('[Askora] Failed to start local backend')
    setBackendFailure('BOOTSTRAP_BACKEND_SPAWN_FAILED', { retryable: true })
  })
  spawnedProcess.on('exit', (code) => {
    console.log(`[Askora] Local backend exited with code ${code}`)
    if (backendProcess !== spawnedProcess) return
    if (backendStartupState.status === 'starting' || backendStartupState.status === 'ready') {
      setBackendFailure('BOOTSTRAP_BACKEND_EXITED', { retryable: true, exit_code: code })
    }
    backendProcess = null
    readyBackendURL = null
    desktopControlToken = null
  })

  const ready = await waitForBackend(backendURL, BACKEND_STARTUP_TIMEOUT)
  if (!ready) {
    console.error('[Askora] Local backend did not become ready before the timeout')
    if (backendStartupState.status === 'starting') {
      setBackendFailure('BOOTSTRAP_BACKEND_START_TIMEOUT', { retryable: true })
    }
    await stopLocalBackend()
    return null
  }

  readyBackendURL = backendURL
  activeLaunchProfile = profile
  publishBackendStartupState(bootstrapDiagnostics.ready(backendStartupState))
  console.log('[Askora] Local backend is ready')
  return backendURL
}

function startLocalBackend(profile = activeLaunchProfile) {
  if (backendStartPromise) return backendStartPromise
  backendStartPromise = startLocalBackendAttempt(profile).finally(() => {
    backendStartPromise = null
  })
  return backendStartPromise
}

async function retryLocalBackend() {
  if (backendStartPromise) return backendStartPromise
  const previousProcess = backendProcess
  stopLocalBackend()
  if (previousProcess && previousProcess.exitCode === null) {
    await new Promise((resolve) => {
      const timer = setTimeout(resolve, 3200)
      previousProcess.once('exit', () => {
        clearTimeout(timer)
        resolve()
      })
    })
  }
  return startLocalBackend()
}

function stopLocalBackend() {
  const processToStop = backendProcess
  readyBackendURL = null
  desktopControlToken = null
  if (!processToStop || processToStop.exitCode !== null) return Promise.resolve()

  return new Promise((resolve) => {
    let settled = false
    const finish = () => {
      if (settled) return
      settled = true
      resolve()
    }
    processToStop.once('exit', finish)
    try {
      processToStop.kill('SIGTERM')
    } catch {
      finish()
      return
    }
    setTimeout(() => {
      if (processToStop.exitCode === null) {
        try {
          processToStop.kill('SIGKILL')
        } catch {}
      }
      setTimeout(finish, 500)
    }, 3000)
  })
}

function requestBackendJSON({ method = 'GET', pathname, body = null, token = null, timeoutMs = 15000 }) {
  return new Promise((resolve, reject) => {
    const encoded = body === null ? null : Buffer.from(JSON.stringify(body), 'utf8')
    const request = http.request(
      {
        hostname: '127.0.0.1',
        port: BACKEND_PORT,
        path: pathname,
        method,
        headers: {
          ...(encoded ? { 'content-type': 'application/json', 'content-length': encoded.length } : {}),
          ...(token ? { 'x-askora-desktop-control': token } : {}),
        },
      },
      (response) => {
        const chunks = []
        response.on('data', (chunk) => chunks.push(chunk))
        response.on('end', () => {
          try {
            const payload = JSON.parse(Buffer.concat(chunks).toString('utf8'))
            resolve({ statusCode: response.statusCode || 500, payload })
          } catch {
            reject(new Error('invalid backend response'))
          }
        })
      },
    )
    request.setTimeout(timeoutMs, () => request.destroy(new Error('backend request timeout')))
    request.on('error', reject)
    if (encoded) request.write(encoded)
    request.end()
  })
}

async function probeModelCandidate(candidate) {
  if (!readyBackendURL || !desktopControlToken) {
    throw new ModelSettingsError(
      'MODEL_PROVIDER_UNAVAILABLE',
      'dependency',
      '本地模型服务尚未就绪',
      true,
    )
  }
  const result = await requestBackendJSON({
    method: 'POST',
    pathname: '/_desktop/model-configuration/probe',
    body: candidate,
    token: desktopControlToken,
  })
  if (result.statusCode !== 200 || !result.payload?.ok) {
    const error = result.payload?.error || {}
    throw new ModelSettingsError(
      typeof error.code === 'string' ? error.code : 'MODEL_PROVIDER_UNAVAILABLE',
      typeof error.category === 'string' ? error.category : 'dependency',
      typeof error.message === 'string' ? error.message : '模型连接测试失败',
      Boolean(error.retryable),
    )
  }
  return result.payload
}

async function getBackendRuntimeSummary() {
  if (!readyBackendURL) throw new Error('runtime configuration unavailable')
  const result = await requestBackendJSON({ pathname: '/health/config', timeoutMs: 5000 })
  if (result.statusCode !== 200 || !result.payload?.model_configuration) {
    throw new Error('runtime configuration unavailable')
  }
  return result.payload.model_configuration
}

async function restartBackendWithProfile(profile) {
  await stopLocalBackend()
  const url = await startLocalBackend(profile)
  if (!url) throw new Error('backend restart failed')
  return getBackendRuntimeSummary()
}

function isAllowedRenderer(event) {
  if (!mainWindow) return false
  return isAllowedModelSettingsSender(event, mainWindow.webContents, {
    isDev,
    devURL: 'http://localhost:5173/',
    allowedFilePath: path.join(__dirname, '..', 'dist', 'index.html'),
  })
}

function registerModelSettingsIPC() {
  const denied = () => ({
    ok: false,
    error: {
      code: 'MODEL_CONFIG_IPC_DENIED',
      category: 'security',
      message: '模型配置请求未获授权',
      retryable: false,
    },
  })
  for (const channel of ['model-settings:get', 'model-settings:apply', 'model-settings:clear']) {
    ipcMain.removeHandler(channel)
  }
  ipcMain.handle('model-settings:get', (event) =>
    isAllowedRenderer(event) ? modelSettingsController.getSettings() : denied(),
  )
  ipcMain.handle('model-settings:apply', (event, command) =>
    isAllowedRenderer(event) ? modelSettingsController.apply(command) : denied(),
  )
  ipcMain.handle('model-settings:clear', (event, command) =>
    isAllowedRenderer(event) ? modelSettingsController.clear(command) : denied(),
  )
}

function stopLocalBackendForMaintenance() {
  const processToStop = backendProcess
  readyBackendURL = null
  if (!processToStop || processToStop.exitCode !== null) return Promise.resolve()

  return new Promise((resolve) => {
    let settled = false
    const finish = () => {
      if (settled) return
      settled = true
      resolve()
    }
    processToStop.once('exit', finish)
    try {
      processToStop.kill('SIGTERM')
    } catch {
      finish()
      return
    }
    setTimeout(() => {
      if (processToStop.exitCode === null) processToStop.kill('SIGKILL')
    }, 3000)
    setTimeout(finish, 5000)
  })
}

function runDataControlCommand(command, commandArgs = []) {
  const allowedCommands = new Set([
    'status',
    'backup',
    'verify',
    'restore',
    'finalize-restore',
    'rollback-restore',
    'recover-interrupted-restore',
    'finalize-erasure',
    'recover-interrupted-erasure',
  ])
  if (!allowedCommands.has(command)) {
    return Promise.reject(new Error('Unsupported data-control command'))
  }
  const backendInfo = getBackendBinaryPath()
  if (!backendInfo) return Promise.reject(new Error('Local backend executable was not found'))
  const recoveryKey = loadOrCreateRecoveryKey()
  const maintenanceEnvironment = applyModelProfileToEnvironment(process.env, {
    state: 'DISABLED',
    revision: null,
    verified_at: null,
  })
  const args = [
    ...backendInfo.args,
    'data-control',
    '--user-data-dir',
    userDataPath,
    '--app-version',
    app.getVersion(),
    command,
    ...commandArgs,
  ]

  return new Promise((resolve, reject) => {
    const maintenanceProcess = spawn(backendInfo.command, args, {
      cwd: backendInfo.cwd,
      // Data-control owns recovery data only. Provider credentials stay inside
      // the P1-02 runtime boundary and are explicitly cleared for this child.
      env: { ...maintenanceEnvironment, ASKORA_RECOVERY_KEY: recoveryKey },
      stdio: ['ignore', 'pipe', 'pipe'],
      windowsHide: true,
    })
    let stdout = ''
    let stderr = ''
    let outputExceeded = false
    const appendOutput = (current, data) => {
      const updated = current + data.toString('utf8')
      if (Buffer.byteLength(updated, 'utf8') > MAX_MAINTENANCE_OUTPUT_BYTES) {
        outputExceeded = true
        maintenanceProcess.kill('SIGKILL')
      }
      return updated
    }
    maintenanceProcess.stdout?.on('data', (data) => {
      stdout = appendOutput(stdout, data)
    })
    maintenanceProcess.stderr?.on('data', (data) => {
      stderr = appendOutput(stderr, data)
    })
    maintenanceProcess.once('error', reject)
    const timeout = setTimeout(() => maintenanceProcess.kill('SIGKILL'), MAINTENANCE_TIMEOUT)
    maintenanceProcess.once('exit', (code) => {
      clearTimeout(timeout)
      if (outputExceeded) {
        reject(new Error('Data-control output exceeded its safety limit'))
        return
      }
      const payloadLine = stdout
        .split(/\r?\n/)
        .reverse()
        .find((line) => line.trim().startsWith('{'))
      let payload
      try {
        payload = JSON.parse(payloadLine || '')
      } catch {
        console.error('[Askora] Data-control command did not return valid JSON')
        reject(new Error('Data-control command failed'))
        return
      }
      if (code !== 0 || !payload.ok) {
        const error = new Error(payload.error?.message || 'Data-control command failed')
        error.code = payload.error?.code || 'DATA_BACKUP_INTEGRITY_FAILED'
        reject(error)
        return
      }
      resolve(payload.result)
    })
  })
}

async function runOfflineDataControl(command, commandArgs = []) {
  mainWindow?.webContents.send('data-control:maintenance-state', { active: true })
  await stopLocalBackendForMaintenance()
  try {
    return await runDataControlCommand(command, commandArgs)
  } finally {
    await startLocalBackend()
    mainWindow?.webContents.send('data-control:maintenance-state', { active: false })
  }
}

async function createVerifiedBackup(reason, saveExternalCopy) {
  const point = await runOfflineDataControl('backup', ['--reason', reason])
  if (!saveExternalCopy) return { point, externalCopy: null }

  const choice = await dialog.showSaveDialog(mainWindow, {
    title: '保存 Askora 恢复点副本',
    defaultPath: `Askora-${new Date().toISOString().slice(0, 10)}.askora-recovery`,
    filters: [{ name: 'Askora Recovery', extensions: ['askora-recovery'] }],
  })
  if (choice.canceled || !choice.filePath) return { point, externalCopy: { saved: false } }
  const sourcePath = path.join(userDataPath, 'recovery', point.relative_path)
  const temporaryPath = `${choice.filePath}.${process.pid}.partial`
  fs.copyFileSync(sourcePath, temporaryPath)
  try {
    await runDataControlCommand('verify', ['--path', temporaryPath])
    fs.renameSync(temporaryPath, choice.filePath)
    return { point, externalCopy: { saved: true, verified: true } }
  } finally {
    try {
      fs.unlinkSync(temporaryPath)
    } catch {}
  }
}

async function runScheduledBackupIfDue() {
  try {
    await runDataControlCommand('recover-interrupted-erasure')
    await runDataControlCommand('recover-interrupted-restore')
    if (!fs.existsSync(path.join(userDataPath, 'askora.db'))) return
    const status = await runDataControlCommand('status')
    const due = !status.last_verified || !status.automatic_backup.next_due_at ||
      Date.parse(status.automatic_backup.next_due_at) <= Date.now()
    if (due) await runDataControlCommand('backup', ['--reason', 'SCHEDULED'])
  } catch (error) {
    console.error('[Askora] Scheduled recovery point failed:', error.code || 'DATA_CONTROL_FAILED')
  }
}

function pendingErasureRequest() {
  const markerPath = path.join(userDataPath, 'recovery', 'erasure-pending.json')
  if (!fs.existsSync(markerPath)) return null
  let payload
  try {
    payload = JSON.parse(fs.readFileSync(markerPath, 'utf8'))
  } catch {
    throw new Error('Pending erasure marker is invalid')
  }
  const workflowId = typeof payload.workflow_id === 'string' ? payload.workflow_id : ''
  const checkpoint = Number(payload.checkpoint)
  if (
    payload.schema_version !== '1.0' ||
    !/^[0-9a-f-]{36}$/i.test(workflowId) ||
    !Number.isSafeInteger(checkpoint) ||
    checkpoint < 1
  ) {
    throw new Error('Pending erasure marker is invalid')
  }
  return { workflowId, checkpoint }
}

async function finalizePendingErasure() {
  const pending = pendingErasureRequest()
  if (!pending) return null
  return runDataControlCommand('finalize-erasure', [
    '--workflow-id', pending.workflowId,
    '--checkpoint', String(pending.checkpoint),
  ])
}

async function chooseAndRestoreBackup() {
  const choice = await dialog.showOpenDialog(mainWindow, {
    title: '选择要恢复的 Askora 恢复点',
    properties: ['openFile'],
    filters: [{ name: 'Askora Recovery', extensions: ['askora-recovery'] }],
  })
  if (choice.canceled || choice.filePaths.length !== 1) return null

  mainWindow?.webContents.send('data-control:maintenance-state', { active: true })
  await stopLocalBackendForMaintenance()
  let awaitingReport = null
  try {
    awaitingReport = await runDataControlCommand('restore', ['--path', choice.filePaths[0]])
    const backendURL = await startLocalBackend()
    if (!backendURL) throw new Error('Restored backend readiness failed')
    const completed = await runDataControlCommand('finalize-restore', [
      '--transaction-id',
      awaitingReport.transaction_id,
    ])
    await mainWindow?.webContents.session.clearStorageData({
      storages: ['cookies', 'localstorage', 'cachestorage'],
    })
    mainWindow?.webContents.send('data-control:restored', {
      reportId: completed.report_id,
    })
    mainWindow?.webContents.reload()
    return completed
  } catch (error) {
    if (awaitingReport?.transaction_id) {
      await stopLocalBackendForMaintenance()
      try {
        await runDataControlCommand('rollback-restore', [
          '--transaction-id',
          awaitingReport.transaction_id,
        ])
      } finally {
        await startLocalBackend()
      }
    } else if (!backendProcess) {
      await startLocalBackend()
    }
    throw error
  } finally {
    mainWindow?.webContents.send('data-control:maintenance-state', { active: false })
  }
}

async function finalizeErasure(options) {
  const workflowId = typeof options?.workflowId === 'string' ? options.workflowId : ''
  const checkpoint = Number(options?.checkpoint)
  if (!/^[0-9a-f-]{36}$/i.test(workflowId) || !Number.isSafeInteger(checkpoint) || checkpoint < 1) {
    throw new Error('Invalid erasure maintenance request')
  }
  const result = await runOfflineDataControl('finalize-erasure', [
    '--workflow-id', workflowId,
    '--checkpoint', String(checkpoint),
  ])
  if (options?.clearLocalSession === true) {
    await mainWindow?.webContents.session.clearStorageData({
      storages: ['cookies', 'localstorage', 'cachestorage'],
    })
  }
  return result
}

async function resumePendingErasure() {
  mainWindow?.webContents.send('data-control:maintenance-state', { active: true })
  await stopLocalBackendForMaintenance()
  try {
    return await finalizePendingErasure()
  } finally {
    await startLocalBackend()
    mainWindow?.webContents.send('data-control:maintenance-state', { active: false })
  }
}

async function createWindow() {
  if (!modelSettingsController) {
    const vault = new EncryptedModelVault({
      safeStorage,
      filePath: path.join(userDataPath, 'model-route-profile.v1.enc.json'),
    })
    modelSettingsController = new ModelSettingsController({
      vault,
      probeCandidate: probeModelCandidate,
      restartBackend: restartBackendWithProfile,
      getRuntimeSummary: getBackendRuntimeSummary,
      externalSummary: () => externalSummaryFromEnv(process.env),
    })
  }
  let launchProfile
  try {
    launchProfile = await modelSettingsController.getLaunchProfile()
  } catch {
    // An unreadable existing vault must not silently reactivate inherited environment keys.
    launchProfile = { state: 'DISABLED', revision: null, verified_at: null }
  }
  await runScheduledBackupIfDue()
  await startLocalBackend(launchProfile)

  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 360,
    minHeight: 600,
    title: 'Askora',
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      preload: path.join(__dirname, 'preload.cjs'),
      webSecurity: true,
    },
  })

  registerModelSettingsIPC()

  Menu.setApplicationMenu(createAppMenu(mainWindow))
  if (isDev) {
    await mainWindow.loadURL('http://localhost:5173')
  } else {
    await mainWindow.loadFile(path.join(__dirname, '..', 'dist', 'index.html'))
  }

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    try {
      const parsed = new URL(url)
      if (parsed.protocol === 'https:') shell.openExternal(url)
    } catch {}
    return { action: 'deny' }
  })
  mainWindow.webContents.on('will-navigate', (event, url) => {
    const currentURL = mainWindow.webContents.getURL()
    if (url !== currentURL) event.preventDefault()
  })
  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

function ensureWindow() {
  if (mainWindow) return Promise.resolve()
  if (!windowCreationPromise) {
    windowCreationPromise = createWindow().finally(() => {
      windowCreationPromise = null
    })
  }
  return windowCreationPromise
}

ipcMain.handle('app:get-version', () => app.getVersion())
ipcMain.handle('app:get-platform', () => process.platform)
ipcMain.handle('app:get-backend-url', () => readyBackendURL)
ipcMain.handle('app:get-backend-startup-state', () => ({ ...backendStartupState }))
ipcMain.handle('app:retry-backend-startup', async () => {
  await retryLocalBackend()
  return { ...backendStartupState }
})
ipcMain.handle('data-control:get-status', () => runDataControlCommand('status'))
ipcMain.handle('data-control:create-backup', (_event, options) => {
  const saveExternalCopy = options?.saveExternalCopy === true
  return createVerifiedBackup('MANUAL', saveExternalCopy)
})
ipcMain.handle('data-control:choose-and-verify', async () => {
  const choice = await dialog.showOpenDialog(mainWindow, {
    title: '选择 Askora 恢复点',
    properties: ['openFile'],
    filters: [{ name: 'Askora Recovery', extensions: ['askora-recovery'] }],
  })
  if (choice.canceled || choice.filePaths.length !== 1) return null
  return runDataControlCommand('verify', ['--path', choice.filePaths[0]])
})
ipcMain.handle('data-control:choose-and-restore', () => chooseAndRestoreBackup())
ipcMain.handle('data-control:finalize-erasure', (_event, options) => finalizeErasure(options))
ipcMain.handle('data-control:resume-pending-erasure', () => resumePendingErasure())
ipcMain.handle('data-control:reveal-recovery-key', async () => {
  const confirmation = await dialog.showMessageBox(mainWindow, {
    type: 'warning',
    title: '显示 Recovery Key',
    message: 'Recovery Key 可用于解密完整恢复点。只在私密环境中显示并离线保存。',
    buttons: ['取消', '继续显示'],
    defaultId: 0,
    cancelId: 0,
  })
  if (confirmation.response !== 1) return null
  return loadOrCreateRecoveryKey()
})

app.whenReady().then(ensureWindow).catch((error) => {
  console.error('[Askora] Window startup failed:', error.code || error.message)
})

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    ensureWindow().catch((error) => {
      console.error('[Askora] Window activation failed:', error.code || error.message)
    })
  }
})

app.on('window-all-closed', () => {
  void stopLocalBackend()
  if (process.platform !== 'darwin') app.quit()
})

app.on('before-quit', () => {
  void stopLocalBackend()
})
