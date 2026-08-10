import api from './client'

const HEARTBEAT_INTERVAL = 5 * 60 * 1000
const STALE_THRESHOLD = 30 * 60 * 1000

let heartbeatTimer = null
let lastHeartbeatAt = 0
let isRunning = false

function sendHeartbeat() {
  const token = localStorage.getItem('access_token')
  if (!token) {
    stopHeartbeat()
    return
  }
  lastHeartbeatAt = Date.now()
  api.post('/auth/heartbeat').catch(() => {})
}

function cleanupOnUnload() {
  const token = localStorage.getItem('access_token')
  if (!token) return
  try {
    api.post('/auth/logout').catch(() => {})
  } catch {}
}

export function startHeartbeat() {
  if (isRunning) return
  isRunning = true
  lastHeartbeatAt = Date.now()
  sendHeartbeat()
  heartbeatTimer = setInterval(sendHeartbeat, HEARTBEAT_INTERVAL)
  window.addEventListener('beforeunload', cleanupOnUnload)
  document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
      if (Date.now() - lastHeartbeatAt > STALE_THRESHOLD) {
        sendHeartbeat()
      }
    }
  })
}

export function stopHeartbeat() {
  isRunning = false
  if (heartbeatTimer) {
    clearInterval(heartbeatTimer)
    heartbeatTimer = null
  }
  window.removeEventListener('beforeunload', cleanupOnUnload)
}

export function isHeartbeatRunning() {
  return isRunning
}