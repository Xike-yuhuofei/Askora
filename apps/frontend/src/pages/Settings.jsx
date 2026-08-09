import { useEffect, useState } from 'react'
import { AlertTriangle, KeyRound, Laptop, LockKeyhole, LogOut, Server, Shield, User } from 'lucide-react'
import * as authApi from '../api/auth'
import * as usersApi from '../api/users'
import { useAuth } from '../hooks/useAuth'
import { useNavigate } from '../router'
import './Settings.css'

export default function Settings() {
  const { user, logout, replaceSessionTokens } = useAuth()
  const navigate = useNavigate()
  const [system, setSystem] = useState({ status: 'loading', data: null, error: '' })
  const [clearing, setClearing] = useState(false)
  const [sessions, setSessions] = useState({ status: 'loading', data: [], error: '' })
  const [passwordForm, setPasswordForm] = useState({ current: '', next: '', confirm: '' })
  const [passwordState, setPasswordState] = useState({ status: 'idle', message: '' })
  const [sessionAction, setSessionAction] = useState('')

  const loadSessions = () => {
    setSessions((current) => ({ ...current, status: 'loading', error: '' }))
    return authApi.listSessions()
      .then((data) => setSessions({ status: 'ready', data: data.sessions || [], error: '' }))
      .catch(() => setSessions({ status: 'error', data: [], error: '无法读取会话，请稍后重试。' }))
  }

  useEffect(() => {
    usersApi.getSystemConfig()
      .then((data) => setSystem({ status: 'ready', data, error: '' }))
      .catch(() => setSystem({ status: 'error', data: null, error: '后端服务不可用，无法读取实时运行状态。' }))
  }, [])

  useEffect(() => { loadSessions() }, [])

  const createIdempotencyKey = (prefix) => `${prefix}-${crypto.randomUUID()}`

  const submitPassword = async (event) => {
    event.preventDefault()
    if (passwordState.status === 'loading') return
    if (passwordForm.next !== passwordForm.confirm) {
      setPasswordState({ status: 'error', message: '两次输入的新密码不一致。' })
      return
    }
    const currentSession = sessions.data.find((session) => session.current)
    if (!currentSession) {
      setPasswordState({ status: 'error', message: '当前会话状态不可用，请刷新会话列表后重试。' })
      return
    }
    setPasswordState({ status: 'loading', message: '正在安全修改密码…' })
    try {
      const result = await authApi.changePassword({
        schema_version: '1.0',
        current_password: passwordForm.current,
        new_password: passwordForm.next,
        idempotency_key: createIdempotencyKey('change-password'),
        current_session_version: currentSession.version,
      })
      if (result.tokens) replaceSessionTokens(result.tokens)
      setPasswordForm({ current: '', next: '', confirm: '' })
      setPasswordState({
        status: 'success',
        message: `密码已修改；已撤销 ${result.revoked_other_sessions} 个其他会话，当前会话已轮换。`,
      })
      await loadSessions()
    } catch (error) {
      const code = error.response?.data?.error?.code
      const messages = {
        AUTH_CURRENT_PASSWORD_INVALID: '当前密码不正确，请重新输入。',
        AUTH_PASSWORD_POLICY_REJECTED: '新密码需为 15～128 个字符，且不能与当前密码相同。',
        CONCURRENT_VERSION_CONFLICT: '会话已变化，请刷新后重试。',
      }
      setPasswordState({ status: 'error', message: messages[code] || '密码修改失败，请稍后重试。' })
      await loadSessions()
    }
  }

  const revokeOne = async (sessionId) => {
    if (sessionAction) return
    setSessionAction(sessionId)
    try {
      await authApi.revokeSession(sessionId, createIdempotencyKey('revoke-session'))
      await loadSessions()
    } catch {
      setSessions((current) => ({ ...current, error: '撤销失败，会话状态已重新读取。' }))
      await loadSessions()
    } finally {
      setSessionAction('')
    }
  }

  const revokeOthers = async () => {
    if (sessionAction) return
    setSessionAction('others')
    try {
      await authApi.revokeOtherSessions(createIdempotencyKey('revoke-others'))
      await loadSessions()
    } catch {
      setSessions((current) => ({ ...current, error: '撤销其他会话失败，请稍后重试。' }))
    } finally {
      setSessionAction('')
    }
  }

  const clearLocalSession = async () => {
    if (clearing) return
    setClearing(true)
    await logout()
    navigate('/login')
  }

  return (
    <div className="settings-page page-stack">
      <header className="page-header">
        <p className="eyebrow">本地应用</p>
        <h1>设置</h1>
        <p>查看账号、运行模式和本地会话边界。</p>
      </header>

      <div className="settings-grid">
        <section className="surface settings-section">
          <div className="section-heading section-heading--compact">
            <div><h2>账号信息</h2></div>
            <User size={18} />
          </div>
          <dl className="settings-list">
            <div><dt>昵称</dt><dd>{user?.nickname || '未设置'}</dd></div>
            <div><dt>账号类型</dt><dd>个人用户</dd></div>
            <div><dt>账号状态</dt><dd>{user?.status === 'active' ? '正常' : (user?.status || '未知')}</dd></div>
            <div><dt>手机号</dt><dd>当前接口不返回明文</dd></div>
          </dl>
        </section>

        <section className="surface settings-section">
          <div className="section-heading section-heading--compact">
            <div><h2>运行状态</h2></div>
            <Server size={18} />
          </div>
          {system.status === 'loading' && <div className="inline-state" role="status"><div className="spinner" /> 正在读取…</div>}
          {system.status === 'error' && <p className="inline-error" role="alert">{system.error}</p>}
          {system.status === 'ready' && (
            <dl className="settings-list">
              <div><dt>运行模式</dt><dd>{system.data.mode === 'private' ? '私人使用' : '服务模式'}</dd></div>
              <div>
                <dt>AI 模型</dt>
                <dd>{system.data.llm_ready ? '已配置' : '未配置，将使用模拟回复'}</dd>
              </div>
            </dl>
          )}
        </section>

        <section className="surface settings-section settings-section--wide">
          <div className="section-heading section-heading--compact">
            <div><h2>隐私与安全事实</h2></div>
            <Shield size={18} />
          </div>
          <div className="fact-list">
            <div><LockKeyhole size={18} /><span><strong>账号字段保护</strong><small>手机号加密存储，并使用不可逆盲索引完成登录查找。</small></span></div>
            <div><KeyRound size={18} /><span><strong>会话保护</strong><small>访问令牌短期有效，刷新令牌每次使用后轮换。</small></span></div>
            <div><AlertTriangle size={18} /><span><strong>私人使用边界</strong><small>当前 App 不公开发布；这不代表已经取得备案、合规认证或第三方内容审核。</small></span></div>
          </div>
        </section>

        <section className="surface settings-section settings-section--wide" aria-labelledby="password-heading">
          <div className="section-heading section-heading--compact">
            <div>
              <p className="eyebrow">账号安全</p>
              <h2 id="password-heading">修改密码</h2>
            </div>
            <KeyRound size={18} />
          </div>
          <form className="settings-form" onSubmit={submitPassword}>
            <label>当前密码<input type="password" autoComplete="current-password" value={passwordForm.current} onChange={(event) => setPasswordForm({ ...passwordForm, current: event.target.value })} required /></label>
            <label>新密码<input type="password" autoComplete="new-password" minLength={15} maxLength={128} value={passwordForm.next} onChange={(event) => setPasswordForm({ ...passwordForm, next: event.target.value })} required aria-describedby="password-help" /></label>
            <label>确认新密码<input type="password" autoComplete="new-password" minLength={15} maxLength={128} value={passwordForm.confirm} onChange={(event) => setPasswordForm({ ...passwordForm, confirm: event.target.value })} required /></label>
            <p id="password-help" className="settings-help">15～128 个字符；允许空格和 Unicode，不要求机械组合字符。</p>
            <button type="submit" className="button button--primary" disabled={passwordState.status === 'loading'}>{passwordState.status === 'loading' ? '正在修改…' : '修改密码并轮换会话'}</button>
          </form>
          {passwordState.message && <p className={passwordState.status === 'error' ? 'inline-error' : 'inline-success'} role={passwordState.status === 'error' ? 'alert' : 'status'}>{passwordState.message}</p>}
        </section>

        <section className="surface settings-section settings-section--wide" aria-labelledby="sessions-heading">
          <div className="section-heading section-heading--compact">
            <div>
              <p className="eyebrow">设备与会话</p>
              <h2 id="sessions-heading">Askora App 实例</h2>
              <p className="settings-help">名称只用于识别登录实例，不代表可信硬件身份。</p>
            </div>
            <Laptop size={18} />
          </div>
          {sessions.status === 'loading' && <div className="inline-state" role="status"><div className="spinner" /> 正在读取会话…</div>}
          {sessions.status === 'error' && <p className="inline-error" role="alert">{sessions.error}</p>}
          {sessions.status === 'ready' && (
            <div className="session-list">
              {sessions.data.map((session) => (
                <article className="session-item" key={session.session_id}>
                  <div>
                    <strong>{session.client_label}{session.current ? '（当前）' : ''}</strong>
                    <small>最近活动：{new Date(session.last_seen_at).toLocaleString('zh-CN')}</small>
                    {session.revoked && <span className="status-chip">已撤销</span>}
                  </div>
                  {!session.current && !session.revoked && <button type="button" className="button button--secondary" onClick={() => revokeOne(session.session_id)} disabled={Boolean(sessionAction)}>{sessionAction === session.session_id ? '正在撤销…' : '撤销'}</button>}
                </article>
              ))}
              <button type="button" className="button button--secondary" onClick={revokeOthers} disabled={Boolean(sessionAction)}>{sessionAction === 'others' ? '正在撤销…' : '撤销其他所有会话'}</button>
            </div>
          )}
        </section>

        <section className="surface settings-section settings-section--wide settings-session">
          <div>
            <h2>退出当前会话</h2>
            <p>退出会撤销服务端当前会话并清除本地令牌，不会删除学习数据。</p>
          </div>
          <button type="button" className="button button--danger" onClick={clearLocalSession} disabled={clearing}>
            <LogOut size={16} />
            {clearing ? '正在退出…' : '退出当前会话'}
          </button>
        </section>
      </div>
    </div>
  )
}
