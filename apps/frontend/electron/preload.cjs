const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electronAPI', {
  getPlatform: () => ipcRenderer.invoke('app:get-platform'),
  getAppVersion: () => ipcRenderer.invoke('app:get-version'),
  getBackendURL: () => ipcRenderer.invoke('app:get-backend-url'),
  getBackendStartupState: () => ipcRenderer.invoke('app:get-backend-startup-state'),
  retryBackendStartup: () => ipcRenderer.invoke('app:retry-backend-startup'),
  onBackendStartupState: (callback) => {
    const handler = (_event, state) => callback(state)
    ipcRenderer.on('app:backend-startup-state', handler)
    return () => ipcRenderer.removeListener('app:backend-startup-state', handler)
  },
  getDataControlStatus: () => ipcRenderer.invoke('data-control:get-status'),
  createVerifiedBackup: (options = {}) =>
    ipcRenderer.invoke('data-control:create-backup', {
      saveExternalCopy: options.saveExternalCopy === true,
    }),
  chooseAndVerifyBackup: () => ipcRenderer.invoke('data-control:choose-and-verify'),
  chooseAndRestoreBackup: () => ipcRenderer.invoke('data-control:choose-and-restore'),
  finalizeErasure: (options) => ipcRenderer.invoke('data-control:finalize-erasure', {
    workflowId: options?.workflowId,
    checkpoint: options?.checkpoint,
    clearLocalSession: options?.clearLocalSession === true,
  }),
  resumePendingErasure: () => ipcRenderer.invoke('data-control:resume-pending-erasure'),
  revealRecoveryKey: () => ipcRenderer.invoke('data-control:reveal-recovery-key'),
  onMaintenanceState: (callback) => {
    const listener = (_event, state) => callback(state)
    ipcRenderer.on('data-control:maintenance-state', listener)
    return () => ipcRenderer.removeListener('data-control:maintenance-state', listener)
  },
  onRestored: (callback) => {
    const listener = (_event, state) => callback(state)
    ipcRenderer.on('data-control:restored', listener)
    return () => ipcRenderer.removeListener('data-control:restored', listener)
  },
  getModelSettings: () => ipcRenderer.invoke('model-settings:get'),
  applyModelSettings: (command) => ipcRenderer.invoke('model-settings:apply', command),
  clearModelSettings: (command) => ipcRenderer.invoke('model-settings:clear', command),
})
