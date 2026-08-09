import { useState } from 'react'
import { BookOpen, KeyRound, ShieldCheck, User, UserPlus } from 'lucide-react'
import { useAuth } from '../hooks/useAuth'
import { useNavigate } from '../router'
import './Login.css'

export default function Login() {
  const [mode, setMode] = useState('login')
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [nickname, setNickname] = useState('')
  const [recoverySecret, setRecoverySecret] = useState('')
  const [issuedKit, setIssuedKit] = useState(null)
  const [kitConfirmed, setKitConfirmed] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const { login, register, recover } = useAuth()
  const navigate = useNavigate()

  const idempotencyKey = (prefix) => `${prefix}-${crypto.randomUUID()}`

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    const normalizedPhone = phone.trim()
    if (!/^1[3-9]\d{9}$/.test(normalizedPhone)) {
      setError('请输入有效的中国大陆手机号')
      return
    }
    if (!password) {
      setError('请输入密码')
      return
    }
    if (mode !== 'login' && (password.length < 15 || password.length > 128)) {
      setError('新密码需为 15～128 个字符')
      return
    }
    if (mode !== 'login' && password !== confirmPassword) {
      setError('两次输入的密码不一致')
      return
    }
    if (mode === 'recover' && recoverySecret.length < 20) {
      setError('请输入完整的离线恢复套件')
      return
    }

    setLoading(true)
    try {
      if (mode === 'login') {
        await login(normalizedPhone, password)
        navigate('/today')
      } else if (mode === 'register') {
        const data = await register(normalizedPhone, password, nickname.trim())
        setIssuedKit(data.recovery_kit)
        setMode('kit')
      } else {
        const data = await recover(
          normalizedPhone,
          recoverySecret,
          password,
          idempotencyKey('recover-password'),
        )
        setIssuedKit({
          recovery_secret: data.recovery_secret,
          credential_version: data.recovery_credential_version,
          storage_warning: '恢复成功。请保存新的套件；旧套件已经失效。',
        })
        setMode('kit')
      }
    } catch (err) {
      setError(
        err.response?.data?.error?.message ||
        err.response?.data?.detail?.message ||
        err.message ||
        (mode === 'login' ? '登录失败，请检查手机号、密码或后端服务' : '操作失败，请重试')
      )
    } finally {
      setLoading(false)
    }
  }

  const switchMode = (nextMode) => {
    setMode(nextMode)
    setError('')
    setPassword('')
    setConfirmPassword('')
    setRecoverySecret('')
  }

  const finishKit = () => {
    if (!kitConfirmed) return
    setIssuedKit(null)
    setKitConfirmed(false)
    setMode('login')
    setPassword('')
    setConfirmPassword('')
    setRecoverySecret('')
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-logo">
          <div className="logo-circle"><BookOpen size={32} /></div>
          <h1>Askora</h1>
          <p>AI 个性化学习伙伴 · 让思考成为一种习惯</p>
        </div>

        {mode === 'kit' ? (
          <section className="recovery-result" aria-labelledby="recovery-kit-heading">
            <KeyRound size={24} />
            <h2 id="recovery-kit-heading">保存离线恢复套件</h2>
            <p>{issuedKit?.storage_warning || '请立即离线保存；离开后不会再次显示。'}</p>
            <output className="recovery-code" aria-label="离线恢复套件">{issuedKit?.recovery_secret}</output>
            <p className="recovery-version">版本 {issuedKit?.credential_version}</p>
            <label className="recovery-confirm">
              <input type="checkbox" checked={kitConfirmed} onChange={(event) => setKitConfirmed(event.target.checked)} />
              我已将恢复套件保存在离线安全位置
            </label>
            <button type="button" className="btn btn-primary login-btn" disabled={!kitConfirmed} onClick={finishKit}>确认并返回登录</button>
          </section>
        ) : (
          <>
            <div className="login-tabs" role="tablist" aria-label="账号操作">
              <button type="button" role="tab" aria-selected={mode === 'login'} className={mode === 'login' ? 'tab active' : 'tab'} onClick={() => switchMode('login')}><User size={16} />登录</button>
              <button type="button" role="tab" aria-selected={mode === 'register'} className={mode === 'register' ? 'tab active' : 'tab'} onClick={() => switchMode('register')}><UserPlus size={16} />注册</button>
              <button type="button" role="tab" aria-label="使用恢复套件重设密码" aria-selected={mode === 'recover'} className={mode === 'recover' ? 'tab active' : 'tab'} onClick={() => switchMode('recover')}><KeyRound size={16} />恢复</button>
            </div>

            <form onSubmit={handleSubmit} noValidate>
              <div className="form-group">
                <label className="label" htmlFor="phone">手机号</label>
                <input id="phone" className="input" type="tel" inputMode="numeric" placeholder="请输入手机号" value={phone} onChange={(event) => setPhone(event.target.value)} autoComplete="tel" pattern="1[3-9][0-9]{9}" maxLength={11} required />
              </div>

              {mode === 'register' && <div className="form-group"><label className="label" htmlFor="nickname">昵称</label><input id="nickname" className="input" type="text" placeholder="请输入昵称（选填）" value={nickname} onChange={(event) => setNickname(event.target.value)} maxLength={64} /></div>}

              {mode === 'recover' && <div className="form-group"><label className="label" htmlFor="recovery-secret">离线恢复套件</label><input id="recovery-secret" className="input recovery-secret-input" type="text" autoCapitalize="none" autoCorrect="off" value={recoverySecret} onChange={(event) => setRecoverySecret(event.target.value.trim())} required /></div>}

              <div className="form-group">
                <label className="label" htmlFor="password">{mode === 'login' ? '密码' : '新密码'}</label>
                <input id="password" className="input" type="password" placeholder={mode === 'login' ? '请输入密码' : '15～128 个字符'} value={password} onChange={(event) => setPassword(event.target.value)} autoComplete={mode === 'login' ? 'current-password' : 'new-password'} minLength={mode === 'login' ? 1 : 15} maxLength={128} required />
              </div>

              {mode !== 'login' && <div className="form-group"><label className="label" htmlFor="confirm-password">确认新密码</label><input id="confirm-password" className="input" type="password" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} autoComplete="new-password" minLength={15} maxLength={128} required /></div>}

              {mode !== 'login' && <p className="password-policy">允许空格和 Unicode；不要求机械组合字符。</p>}
              {error && <div className="error-msg" role="alert">{error}</div>}
              <button type="submit" className="btn btn-primary login-btn" disabled={loading}>{loading ? <div className="spinner spinner-sm" /> : (mode === 'login' ? '登录' : mode === 'register' ? '注册并生成恢复套件' : '重设密码')}</button>
            </form>
          </>
        )}

        <div className="compliance-notice"><ShieldCheck size={14} /><span>私人使用模式 · 不作为公开服务发布</span></div>
      </div>
    </div>
  )
}
