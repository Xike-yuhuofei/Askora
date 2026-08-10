import api from './client'
import { getOrCreateDeviceFingerprint } from './client'

// 手机号登录
export const loginWithPhone = (phone, password) =>
  api.post('/auth/login/phone', {
    phone,
    password,
    device_fingerprint: getOrCreateDeviceFingerprint(),
  }, { skipAuth: true }).then((r) => r.data)

// 注册
export const registerWithPhone = (phone, password, nickname) =>
  api.post('/auth/register', { phone, password, nickname }, { skipAuth: true }).then((r) => r.data)

// 登出
export const logout = () => api.post('/auth/logout').then((r) => r.data)

// 获取当前用户
export const getMe = () => api.get('/auth/me').then((r) => r.data)

export const changePassword = (command) =>
  api.post('/auth/password/change', command).then((r) => r.data)

export const listSessions = () => api.get('/auth/sessions').then((r) => r.data)

export const revokeSession = (sessionId, idempotencyKey) =>
  api.post(`/auth/sessions/${encodeURIComponent(sessionId)}/revoke`, {
    schema_version: '1.0',
    idempotency_key: idempotencyKey,
  }).then((r) => r.data)

export const revokeOtherSessions = (idempotencyKey) =>
  api.post('/auth/sessions/revoke-others', {
    schema_version: '1.0',
    idempotency_key: idempotencyKey,
  }).then((r) => r.data)

export const getRecoveryStatus = () =>
  api.get('/auth/recovery/status').then((r) => r.data)

export const issueRecoveryKit = (currentPassword, idempotencyKey) =>
  api.post('/auth/recovery/issue', {
    schema_version: '1.0',
    current_password: currentPassword,
    idempotency_key: idempotencyKey,
  }).then((r) => r.data)

export const recoverPassword = (phone, recoverySecret, newPassword, idempotencyKey) =>
  api.post('/auth/recovery/password', {
    schema_version: '1.0',
    phone,
    recovery_secret: recoverySecret,
    new_password: newPassword,
    client_instance: getOrCreateDeviceFingerprint(),
    idempotency_key: idempotencyKey,
  }, { skipAuth: true, _skipRefresh: true }).then((r) => r.data)

// 刷新 token
export const refreshToken = (refresh_token) =>
  api.post('/auth/refresh', {
    refresh_token,
    device_fingerprint: getOrCreateDeviceFingerprint(),
  }, { skipAuth: true, _skipRefresh: true }).then((r) => r.data)

// 心跳 - 保持会话活跃
export const heartbeat = () =>
  api.post('/auth/heartbeat').then((r) => r.data)

// 开发自动登录（仅开发/本地调试环境启用，后端关闭时返回 404）
export const devAutoLogin = () =>
  api.post('/auth/dev/auto-login', {
    device_fingerprint: getOrCreateDeviceFingerprint(),
  }, { skipAuth: true }).then((r) => r.data)
