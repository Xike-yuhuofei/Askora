const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electronAPI', {
  getPlatform: () => ipcRenderer.invoke('app:get-platform'),
  getAppVersion: () => ipcRenderer.invoke('app:get-version'),
  getBackendURL: () => ipcRenderer.invoke('app:get-backend-url'),
  getDataControlStatus: () => ipcRenderer.invoke('data-control:get-status'),
  createVerifiedBackup: (options = {}) =>
    ipcRenderer.invoke('data-control:create-backup', {
      saveExternalCopy: options.saveExternalCopy === true,
    }),
  chooseAndVerifyBackup: () => ipcRenderer.invoke('data-control:choose-and-verify'),
  revealRecoveryKey: () => ipcRenderer.invoke('data-control:reveal-recovery-key'),
  onMaintenanceState: (callback) => {
    const listener = (_event, state) => callback(state)
    ipcRenderer.on('data-control:maintenance-state', listener)
    return () => ipcRenderer.removeListener('data-control:maintenance-state', listener)
  },
})
