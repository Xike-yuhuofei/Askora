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
})
