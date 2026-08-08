import { useState } from 'react'
import { useNavigate } from '../router'
import { BookOpen, UserPlus, ShieldCheck } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import './Login.css'

export default function Login() {
  const [mode, setMode] = useState('login')
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [nickname, setNickname] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const { login, register } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    const normalizedPhone = phone.trim()
    if (!/^1[3-9]\d{9}$/.test(normalizedPhone)) {
      setError('请输入有效的中国大陆手机号')
      return
    }
    if (password.length < 8) {
      setError('密码至少需要 8 位')
      return
    }
    if (new TextEncoder().encode(password).length > 72) {
      setError('密码的 UTF-8 编码不能超过 72 字节')
      return
    }

    setLoading(true)

    try {
      if (mode === 'login') {
        await login(normalizedPhone, password)
        navigate('/')
      } else {
        if (password !== confirmPassword) {
          setError('两次输入的密码不一致')
          setLoading(false)
          return
        }
        await register(normalizedPhone, password, nickname.trim())
        setSuccess('注册成功！请使用手机号登录')
        setMode('login')
        setPassword('')
        setConfirmPassword('')
      }
    } catch (err) {
      setError(
        err.response?.data?.error?.message ||
        err.response?.data?.detail?.message ||
        err.message ||
        (mode === 'login' ? '登录失败，请检查手机号、密码或后端服务' : '注册失败，请重试')
      )
    } finally {
      setLoading(false)
    }
  }

  const switchMode = (newMode) => {
    setMode(newMode)
    setError('')
    setSuccess('')
    setPassword('')
    setConfirmPassword('')
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-logo">
          <div className="logo-circle">
            <BookOpen size={32} />
          </div>
          <h1>Askora</h1>
          <p>AI 个性化学习伙伴 · 让思考成为一种习惯</p>
        </div>

        <div className="login-tabs">
          <button
            className={mode === 'login' ? 'tab active' : 'tab'}
            onClick={() => switchMode('login')}
          >
            <User size={16} />
            登录
          </button>
          <button
            className={mode === 'register' ? 'tab active' : 'tab'}
            onClick={() => switchMode('register')}
          >
            <UserPlus size={16} />
            注册
          </button>
        </div>

        <form onSubmit={handleSubmit} noValidate>
          <div className="form-group">
            <label className="label" htmlFor="phone">手机号</label>
            <input
              id="phone"
              className="input"
              type="tel"
              inputMode="numeric"
              placeholder="请输入手机号"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              autoComplete="tel"
              pattern="1[3-9][0-9]{9}"
              maxLength={11}
              required
            />
          </div>

          {mode === 'register' && (
            <div className="form-group">
              <label className="label" htmlFor="nickname">昵称</label>
              <input
                id="nickname"
                className="input"
                type="text"
                placeholder="请输入昵称（选填）"
                value={nickname}
                onChange={(e) => setNickname(e.target.value)}
                maxLength={64}
              />
            </div>
          )}

          <div className="form-group">
            <label className="label" htmlFor="password">密码</label>
            <input
              id="password"
              className="input"
              type="password"
              placeholder="请输入密码"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
              minLength={8}
              required
            />
          </div>

          {mode === 'register' && (
            <div className="form-group">
              <label className="label" htmlFor="confirm-password">确认密码</label>
              <input
                id="confirm-password"
                className="input"
                type="password"
                placeholder="请再次输入密码"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                autoComplete="new-password"
                minLength={8}
                required
              />
            </div>
          )}

          {error && <div className="error-msg" role="alert">{error}</div>}
          {success && <div className="success-msg" role="status">{success}</div>}

          <button type="submit" className="btn btn-primary login-btn" disabled={loading}>
            {loading ? <div className="spinner spinner-sm" /> : (mode === 'login' ? '登录' : '注册')}
          </button>

        </form>

        <div className="compliance-notice">
          <ShieldCheck size={14} />
          <span>私人使用模式 · 不作为公开服务发布</span>
        </div>
      </div>
    </div>
  )
}
