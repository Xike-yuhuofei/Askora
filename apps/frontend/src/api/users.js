import api from './client'
import axios from 'axios'
import { getApiBaseURL } from './client'

// 获取用户画像
export const getProfile = () => api.get('/users/profile').then((r) => r.data)

// 获取私人运行模式和 LLM 是否配置；接口不返回任何密钥或连接信息。
export const getSystemConfig = async () => {
  const apiBase = await getApiBaseURL()
  const backendOrigin = apiBase.replace(/\/api\/v1\/?$/, '')
  return axios.get(`${backendOrigin}/health/config`, { timeout: 5000 }).then((r) => r.data)
}

const modelControlUnavailable = () => ({
  ok: false,
  error: {
    code: 'MODEL_CONTROL_NOT_AVAILABLE',
    category: 'security',
    message: '本地模型控制面不可用',
    retryable: false,
  },
})

const getDesktopModelBridge = () => {
  const bridge = typeof window === 'undefined' ? null : window.electronAPI
  if (
    !bridge ||
    typeof bridge.getModelSettings !== 'function' ||
    typeof bridge.applyModelSettings !== 'function' ||
    typeof bridge.clearModelSettings !== 'function'
  ) {
    return null
  }
  return bridge
}

export const getModelSettings = async () => {
  const bridge = getDesktopModelBridge()
  if (!bridge) return modelControlUnavailable()
  try {
    return await bridge.getModelSettings()
  } catch {
    return modelControlUnavailable()
  }
}

export const applyModelSettings = async (command) => {
  const bridge = getDesktopModelBridge()
  if (!bridge) return modelControlUnavailable()
  try {
    return await bridge.applyModelSettings(command)
  } catch {
    return modelControlUnavailable()
  }
}

export const clearModelSettings = async (command) => {
  const bridge = getDesktopModelBridge()
  if (!bridge) return modelControlUnavailable()
  try {
    return await bridge.clearModelSettings(command)
  } catch {
    return modelControlUnavailable()
  }
}
