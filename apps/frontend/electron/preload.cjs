const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('electronAPI', {
  getPlatform: () => ipcRenderer.invoke('app:get-platform'),
  getAppVersion: () => ipcRenderer.invoke('app:get-version'),
  getBackendURL: () => ipcRenderer.invoke('app:get-backend-url'),
})
