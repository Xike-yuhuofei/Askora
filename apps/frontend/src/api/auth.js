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

// 刷新 token
export const refreshToken = (refresh_token) =>
  api.post('/auth/refresh', {
    refresh_token,
    device_fingerprint: getOrCreateDeviceFingerprint(),
  }, { skipAuth: true, _skipRefresh: true }).then((r) => r.data)
