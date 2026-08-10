import axios from 'axios'

let cachedBaseURL = null

export const getApiBaseURL = async () => {
  if (cachedBaseURL) return cachedBaseURL

  const envURL = import.meta.env.VITE_API_BASE_URL
  if (!import.meta.env.PROD && envURL) {
    cachedBaseURL = envURL
    return cachedBaseURL
  }

  if (import.meta.env.PROD) {
    cachedBaseURL = '/api/v1'
    return cachedBaseURL
  }

  cachedBaseURL = '/api/v1'
  return cachedBaseURL
}

const api = axios.create({
  baseURL: '/api/v1',
  // Provider execution is bounded at 30s; transport must leave room for validation + commit.
  timeout: 65000,
})

export const getOrCreateDeviceFingerprint = () => {
  let fingerprint = localStorage.getItem('device_fingerprint')
  if (!fingerprint) {
    fingerprint = globalThis.crypto?.randomUUID?.() ||
      `askora-${Date.now()}-${Math.random().toString(36).slice(2)}`
    localStorage.setItem('device_fingerprint', fingerprint)
  }
  return fingerprint
}

// 请求拦截器：仅设置 baseURL（本地单机应用，无认证态）。
api.interceptors.request.use(async (config) => {
  config.baseURL = await getApiBaseURL()
  return config
})

const GLOBAL_NOTICE_CODES = ['SYS-0001']

export function normalizeApiError(error) {
  const payload = error?.response?.data?.error || {}
  return {
    code: payload.code || 'NETWORK_UNAVAILABLE',
    category: payload.category || (error?.response ? 'internal' : 'dependency'),
    message: payload.message || '服务暂时不可用',
    retryable: Boolean(payload.retryable),
    correlation_id: payload.correlation_id || payload.request_id || null,
    details: payload.details || null,
    recovery: payload.recovery || null,
  }
}

// 响应拦截器：处理系统级错误提示。
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // 系统故障使用统一弹窗，并保留 request_id 便于定位。
    const errData = normalizeApiError(error)
    if (errData?.code && GLOBAL_NOTICE_CODES.includes(errData.code)) {
      window.dispatchEvent(
        new CustomEvent('app:api-error', {
          detail: {
            code: errData.code,
            message: errData.message,
            details: errData.details,
            request_id: errData.correlation_id,
          },
        })
      )
    }

    if (errData.code !== 'NETWORK_UNAVAILABLE') {
      window.dispatchEvent(new CustomEvent('app:recovery-refresh'))
    }

    return Promise.reject(error)
  }
)

export default api
