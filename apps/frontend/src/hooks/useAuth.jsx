import { createContext, useContext, useState, useEffect } from 'react'
import * as authApi from '../api/auth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    const initialize = async () => {
      const token = localStorage.getItem('access_token')
      const savedUser = localStorage.getItem('user')
      const demoMode = localStorage.getItem('demo_mode') === 'true'
      if (!token || !savedUser) {
        if (!cancelled) setLoading(false)
        return
      }

      try {
        if (demoMode && token === 'demo-access-token') {
          if (!cancelled) setUser(JSON.parse(savedUser))
        } else {
          const currentUser = await authApi.getMe()
          if (!cancelled) {
            setUser(currentUser)
            localStorage.setItem('user', JSON.stringify(currentUser))
          }
        }
      } catch {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
        localStorage.removeItem('demo_mode')
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
    localStorage.removeItem('demo_mode')
    setUser(data.user)
    return data
  }

  const loginDemo = () => {
    const demoUser = {
      id: 'demo-user-001',
      role: 'user',
      status: 'active',
      is_verified: false,
      nickname: 'Askora 演示用户',
    }
    localStorage.setItem('access_token', 'demo-access-token')
    localStorage.setItem('refresh_token', 'demo-refresh-token')
    localStorage.setItem('user', JSON.stringify(demoUser))
    localStorage.setItem('demo_mode', 'true')
    setUser(demoUser)
    return { user: demoUser, demo_mode: true }
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
      if (localStorage.getItem('demo_mode') !== 'true') await authApi.logout()
    } catch {}
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    localStorage.removeItem('demo_mode')
    setUser(null)
  }

  const fetchMe = async () => {
    if (localStorage.getItem('demo_mode') === 'true') return user
    try {
      const data = await authApi.getMe()
      setUser(data)
      localStorage.setItem('user', JSON.stringify(data))
      return data
    } catch {
      return null
    }
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, loginDemo, register, logout, fetchMe }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
