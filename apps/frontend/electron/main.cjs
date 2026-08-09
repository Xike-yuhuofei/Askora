const { app, BrowserWindow, Menu, shell, ipcMain, safeStorage, dialog } = require('electron')
const crypto = require('crypto')
const fs = require('fs')
const http = require('http')
const path = require('path')
const { spawn } = require('child_process')
const { createAppMenu } = require('./app-menu.cjs')
const bootstrapDiagnostics = require('./bootstrap-diagnostics.cjs')

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

async function startLocalBackendAttempt() {
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
  const env = {
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
  }

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
  })

  const ready = await waitForBackend(backendURL, BACKEND_STARTUP_TIMEOUT)
  if (!ready) {
    console.error('[Askora] Local backend did not become ready before the timeout')
    if (backendStartupState.status === 'starting') {
      setBackendFailure('BOOTSTRAP_BACKEND_START_TIMEOUT', { retryable: true })
    }
    stopLocalBackend()
    return null
  }

  readyBackendURL = backendURL
  publishBackendStartupState(bootstrapDiagnostics.ready(backendStartupState))
  console.log('[Askora] Local backend is ready')
  return backendURL
}

function startLocalBackend() {
  if (backendStartPromise) return backendStartPromise
  backendStartPromise = startLocalBackendAttempt().finally(() => {
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
  if (!processToStop || processToStop.exitCode !== null) return

  try {
    processToStop.kill('SIGTERM')
    setTimeout(() => {
      if (processToStop.exitCode === null) processToStop.kill('SIGKILL')
    }, 3000)
  } catch {}
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
  const allowedCommands = new Set(['status', 'backup', 'verify'])
  if (!allowedCommands.has(command)) {
    return Promise.reject(new Error('Unsupported data-control command'))
  }
  const backendInfo = getBackendBinaryPath()
  if (!backendInfo) return Promise.reject(new Error('Local backend executable was not found'))
  const recoveryKey = loadOrCreateRecoveryKey()
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
      env: { ...process.env, ASKORA_RECOVERY_KEY: recoveryKey },
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
  if (!fs.existsSync(path.join(userDataPath, 'askora.db'))) return
  try {
    const status = await runDataControlCommand('status')
    const due = !status.last_verified || !status.automatic_backup.next_due_at ||
      Date.parse(status.automatic_backup.next_due_at) <= Date.now()
    if (due) await runDataControlCommand('backup', ['--reason', 'SCHEDULED'])
  } catch (error) {
    console.error('[Askora] Scheduled recovery point failed:', error.code || 'DATA_CONTROL_FAILED')
  }
}

async function createWindow() {
  await runScheduledBackupIfDue()
  await startLocalBackend()

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

app.whenReady().then(createWindow)

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow()
})

app.on('window-all-closed', () => {
  stopLocalBackend()
  if (process.platform !== 'darwin') app.quit()
})

app.on('before-quit', stopLocalBackend)
