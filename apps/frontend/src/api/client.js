import axios from 'axios'

let cachedBaseURL = null
let refreshPromise = null

export const getApiBaseURL = async () => {
  if (cachedBaseURL) return cachedBaseURL

  if (window.electronAPI?.getBackendURL) {
    try {
      const localURL = await window.electronAPI.getBackendURL()
      if (localURL) {
        cachedBaseURL = `${localURL}/api/v1`
        return cachedBaseURL
      }
    } catch {}
  }

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

// 请求拦截器：附加 token 与设备指纹（skipAuth 请求跳过）
api.interceptors.request.use(async (config) => {
  config.baseURL = await getApiBaseURL()
  if (config.skipAuth) return config
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  // Token 可绑定当前私人设备，所有真实认证请求都携带同一指纹。
  const deviceFingerprint = getOrCreateDeviceFingerprint()
  if (deviceFingerprint) {
    config.headers['X-Device-Fingerprint'] = deviceFingerprint
  }
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

// 响应拦截器：处理 401 与系统级错误提示。
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    if (
      error.response?.status === 401 &&
      !originalRequest?._retry &&
      !originalRequest?._skipRefresh
    ) {
      originalRequest._retry = true
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          if (!refreshPromise) {
            refreshPromise = api.post(
              '/auth/refresh',
              {
                refresh_token: refreshToken,
                device_fingerprint: getOrCreateDeviceFingerprint(),
              },
              { skipAuth: true, _skipRefresh: true }
            ).finally(() => {
              refreshPromise = null
            })
          }
          const res = await refreshPromise
          const { access_token, refresh_token } = res.data
          localStorage.setItem('access_token', access_token)
          if (refresh_token) localStorage.setItem('refresh_token', refresh_token)
          originalRequest.headers.Authorization = `Bearer ${access_token}`
          return api(originalRequest)
        } catch {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          localStorage.removeItem('user')
          window.location.hash = '/login'
        }
      }
    }

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
