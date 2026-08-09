import { createContext, useContext, useState, useEffect } from 'react'
import * as authApi from '../api/auth'
import { getOrCreateDeviceFingerprint } from '../api/client'

const AuthContext = createContext(null)

// 开发模式免登录直接进入系统（仅在 VITE_ENABLE_DEV_AUTO_LOGIN=true 时启用）
const DEV_AUTO_LOGIN_ENABLED = import.meta.env.VITE_ENABLE_DEV_AUTO_LOGIN === 'true'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  const clearTokens = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  }

  const applyDevSession = async () => {
    const data = await authApi.devAutoLogin()
    localStorage.setItem('access_token', data.access_token)
    if (data.refresh_token) localStorage.setItem('refresh_token', data.refresh_token)
    localStorage.setItem('user', JSON.stringify(data.user))
    setUser(data.user)
  }

  useEffect(() => {
    let cancelled = false
    const initialize = async () => {
      const token = localStorage.getItem('access_token')
      const savedUser = localStorage.getItem('user')
      if (!token || !savedUser) {
        if (!cancelled) {
          if (DEV_AUTO_LOGIN_ENABLED) {
            try {
              await applyDevSession()
            } catch {
              // 自动登录失败时静默回退，交由路由进入登录页
            }
          }
          if (!cancelled) setLoading(false)
        }
        return
      }

      try {
        const currentUser = await authApi.getMe()
        if (!cancelled) {
          setUser(currentUser)
          localStorage.setItem('user', JSON.stringify(currentUser))
        }
      } catch {
        clearTokens()
        if (!cancelled) {
          if (DEV_AUTO_LOGIN_ENABLED) {
            try {
              await applyDevSession()
            } catch {
              if (!cancelled) setLoading(false)
            }
          } else {
            setLoading(false)
          }
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    initialize()
    return () => { cancelled = true }
  }, [])

  const login = async (phone, password) => {
    const data = await authApi.loginWithPhone(phone, password)
    localStorage.setItem('access_token', data.access_token)
    if (data.refresh_token) localStorage.setItem('refresh_token', data.refresh_token)
    localStorage.setItem('user', JSON.stringify(data.user))
    setUser(data.user)
    return data
  }

  const register = async (phone, password, nickname) => {
    try {
      const data = await authApi.registerWithPhone(phone, password, nickname)
      return data
    } catch (err) {
      if (err.response?.status === 409) {
        throw new Error('该手机号已注册，请直接登录')
      }
      if (err.response?.status === 422) {
        throw new Error('注册信息格式错误，请检查手机号和密码')
      }
      throw new Error('注册失败，请检查网络或稍后重试')
    }
  }

  const logout = async () => {
    try {
      await authApi.logout()
    } catch {}
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    setUser(null)
  }

  const fetchMe = async () => {
    try {
      const data = await authApi.getMe()
      setUser(data)
      localStorage.setItem('user', JSON.stringify(data))
      return data
    } catch {
      return null
    }
  }

  const replaceSessionTokens = (tokens) => {
    if (!tokens?.access_token || !tokens?.refresh_token) {
      throw new Error('新的会话令牌缺失，请重新登录')
    }
    localStorage.setItem('access_token', tokens.access_token)
    localStorage.setItem('refresh_token', tokens.refresh_token)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, fetchMe, replaceSessionTokens }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
