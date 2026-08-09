import { useEffect, useState } from 'react'
import {
  AlertTriangle,
  Download,
  HardDrive,
  KeyRound,
  Laptop,
  LockKeyhole,
  LogOut,
  RotateCcw,
  Server,
  Shield,
  Trash2,
  User,
} from 'lucide-react'
import * as authApi from '../api/auth'
import * as usersApi from '../api/users'
import * as dataControlApi from '../api/dataControl'
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
  const [accountRecovery, setAccountRecovery] = useState({ status: 'loading', data: null, error: '' })
  const [accountRecoveryPassword, setAccountRecoveryPassword] = useState('')
  const [accountRecoveryAction, setAccountRecoveryAction] = useState('idle')
  const [issuedRecovery, setIssuedRecovery] = useState(null)
  const [recoveryConfirmed, setRecoveryConfirmed] = useState(false)

  const loadSessions = () => {
    setSessions((current) => ({ ...current, status: 'loading', error: '' }))
    return authApi.listSessions()
      .then((data) => setSessions({ status: 'ready', data: data.sessions || [], error: '' }))
      .catch(() => setSessions({ status: 'error', data: [], error: '无法读取会话，请稍后重试。' }))
  }

  const loadAccountRecoveryStatus = () => {
    setAccountRecovery((current) => ({ ...current, status: 'loading', error: '' }))
    return authApi.getRecoveryStatus()
      .then((data) => setAccountRecovery({ status: 'ready', data, error: '' }))
      .catch(() => setAccountRecovery({ status: 'error', data: null, error: '无法读取恢复套件状态，请稍后重试。' }))
  }
  const [exportScopes, setExportScopes] = useState({
    PROFILE: true,
    DOCUMENTS: true,
    LEARNING_RECORDS: true,
    MODEL_EXECUTION: true,
  })
  const [includeDocumentOriginals, setIncludeDocumentOriginals] = useState(false)
  const [exportState, setExportState] = useState({ status: 'idle', message: '' })
  const [recovery, setRecovery] = useState({ status: 'loading', data: null, message: '' })
  const [recoveryAction, setRecoveryAction] = useState('')
  const [saveExternalCopy, setSaveExternalCopy] = useState(false)
  const [recoveryKey, setRecoveryKey] = useState('')
  const [erasureScope, setErasureScope] = useState('LEARNING_RECORDS')
  const [erasureTarget, setErasureTarget] = useState('')
  const [erasurePreview, setErasurePreview] = useState(null)
  const [erasureCommandKey, setErasureCommandKey] = useState('')
  const [erasurePhrase, setErasurePhrase] = useState('')
  const [erasureState, setErasureState] = useState({ status: 'idle', message: '', report: null })

  const refreshRecovery = () => dataControlApi.getDataControlStatus()
    .then((data) => setRecovery({ status: 'ready', data, message: '' }))
    .catch(() => setRecovery({ status: 'error', data: null, message: '无法读取本机恢复状态。' }))

  useEffect(() => {
    usersApi.getSystemConfig()
      .then((data) => setSystem({ status: 'ready', data, error: '' }))
      .catch(() => setSystem({ status: 'error', data: null, error: '后端服务不可用，无法读取实时运行状态。' }))
    refreshRecovery()
    return dataControlApi.onMaintenanceState?.((state) => {
      if (state?.active) {
        setRecovery((current) => ({ ...current, message: '正在执行离线数据维护…' }))
      } else {
        refreshRecovery()
      }
    })
  }, [])

  useEffect(() => { loadSessions() }, [])
  useEffect(() => { loadAccountRecoveryStatus() }, [])

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

  const issueRecovery = async (event) => {
    event.preventDefault()
    if (accountRecoveryAction === 'loading') return
    setAccountRecoveryAction('loading')
    setAccountRecovery((current) => ({ ...current, error: '' }))
    try {
      const result = await authApi.issueRecoveryKit(
        accountRecoveryPassword,
        createIdempotencyKey('issue-recovery'),
      )
      if (!result.recovery_secret) {
        setAccountRecovery((current) => ({ ...current, error: '本次请求未返回新套件，请重新发起轮换。' }))
        return
      }
      setIssuedRecovery(result)
      setRecoveryConfirmed(false)
      setAccountRecoveryPassword('')
      setAccountRecovery({
        status: 'ready',
        data: {
          configured: true,
          credential_version: result.credential_version,
          created_at: result.created_at,
        },
        error: '',
      })
    } catch (error) {
      const code = error.response?.data?.error?.code
      const messages = {
        AUTH_CURRENT_PASSWORD_INVALID: '当前密码不正确，请重新输入。',
        AUTH_RECOVERY_RATE_LIMITED: '尝试次数过多，请稍后再试。',
      }
      const message = messages[code] || '恢复套件轮换失败，请稍后重试。'
      await loadAccountRecoveryStatus()
      setAccountRecovery((current) => ({
        ...current,
        error: message,
      }))
    } finally {
      setAccountRecoveryAction('idle')
    }
  }

  const dismissIssuedRecovery = () => {
    if (!recoveryConfirmed) return
    setIssuedRecovery(null)
    setRecoveryConfirmed(false)
  }

  const clearLocalSession = async () => {
    if (clearing) return
    setClearing(true)
    await logout()
    navigate('/login')
  }

  const toggleExportScope = (scope) => {
    setExportScopes((current) => ({ ...current, [scope]: !current[scope] }))
    if (scope === 'DOCUMENTS' && exportScopes.DOCUMENTS) {
      setIncludeDocumentOriginals(false)
    }
  }

  const exportUserData = async () => {
    if (exportState.status === 'working') return
    const scopes = Object.entries(exportScopes)
      .filter(([, enabled]) => enabled)
      .map(([scope]) => scope)
    if (scopes.length === 0) {
      setExportState({ status: 'error', message: '至少选择一个导出范围。' })
      return
    }
    setExportState({ status: 'working', message: '正在生成导出…' })
    try {
      const ready = await dataControlApi.createUserExport({
        scopes,
        includeDocumentOriginals,
      })
      await dataControlApi.downloadUserExport({
        exportId: ready.export_id,
        token: ready.download_token,
      })
      setExportState({ status: 'success', message: '导出已下载；服务端临时副本已失效。' })
    } catch {
      setExportState({ status: 'error', message: '导出失败或已过期，请重新创建。' })
    }
  }

  const runRecoveryAction = async (name, action, successMessage) => {
    if (recoveryAction) return
    setRecoveryAction(name)
    setRecovery((current) => ({ ...current, message: '正在执行离线数据维护…' }))
    try {
      await action()
      await refreshRecovery()
      setRecovery((current) => ({ ...current, message: successMessage }))
    } catch {
      setRecovery((current) => ({ ...current, message: '数据维护失败；当前数据未被声明为已恢复。' }))
    } finally {
      setRecoveryAction('')
    }
  }

  const revealKey = async () => {
    try {
      const value = await dataControlApi.revealRecoveryKey()
      if (value) setRecoveryKey(value)
    } catch {
      setRecovery((current) => ({ ...current, message: 'Recovery Key 无法显示。' }))
    }
  }

  const previewErasure = async () => {
    if (erasureState.status === 'working') return
    if (erasureScope === 'DOCUMENT' && !erasureTarget.trim()) {
      setErasureState({ status: 'error', message: '删除单份资料时必须填写资料 ID。', report: null })
      return
    }
    setErasureState({ status: 'working', message: '正在计算实际影响…', report: null })
    try {
      const preview = await dataControlApi.createErasurePreview({
        scope: erasureScope,
        targetRef: erasureScope === 'DOCUMENT' ? erasureTarget.trim() : null,
      })
      setErasurePreview(preview)
      setErasureCommandKey(
        globalThis.crypto?.randomUUID?.()
          || `erase-${Date.now()}-${Math.random().toString(36).slice(2)}`,
      )
      setErasurePhrase('')
      setErasureState({ status: 'preview', message: '', report: null })
    } catch {
      setErasureState({ status: 'error', message: '无法创建删除预览；没有执行删除。', report: null })
    }
  }

  const finishErasureBaseline = async (report, scope) => {
    try {
      const result = await dataControlApi.finalizeErasure({
        workflowId: report.workflow_id,
        checkpoint: report.checkpoint,
        clearLocalSession: scope === 'ALL_PERSONAL_DATA',
      })
      if (result?.post_erasure_point?.status !== 'VERIFIED') throw new Error('baseline not verified')
      setErasureState({
        status: 'success',
        message: '删除完成；删除后恢复基线已验证。',
        report,
      })
      setErasurePreview(null)
      setErasurePhrase('')
      await refreshRecovery()
      if (scope === 'ALL_PERSONAL_DATA') {
        await logout()
        navigate('/login')
      }
    } catch {
      setErasureState({
        status: 'partial',
        message: '数据已删除，但恢复基线尚未完成；学习功能保持关闭，请重试。',
        report,
      })
    }
  }

  const confirmErasure = async () => {
    if (!erasurePreview || erasurePhrase !== erasurePreview.confirmation_phrase) return
    setErasureState({ status: 'working', message: '正在删除并建立反复活检查点…', report: null })
    try {
      const report = await dataControlApi.confirmErasure({
        previewId: erasurePreview.preview_id,
        confirmationToken: erasurePreview.confirmation_token,
        confirmationPhrase: erasurePhrase,
        idempotencyKey: erasureCommandKey,
      })
      if (report.status !== 'AWAITING_RECOVERY_BASELINE') {
        setErasureState({ status: 'error', message: '删除未完成；受影响范围仍被关闭。', report })
        return
      }
      await finishErasureBaseline(report, erasurePreview.scope)
    } catch {
      try {
        const recovered = await dataControlApi.resumePendingErasure()
        if (recovered?.post_erasure_point?.status === 'VERIFIED') {
          setErasurePreview(null)
          setErasureState({
            status: 'success',
            message: '删除完成；删除后恢复基线已验证。',
            report: null,
          })
          await refreshRecovery()
          return
        }
      } catch {}
      setErasureState({ status: 'error', message: '删除未完成；没有显示成功。', report: null })
    }
  }

  const protectionLabel = {
    READY: '已验证保护',
    NOT_PROTECTED: '尚无已验证恢复点',
    PARTIAL: '保护未完成',
    ERROR: '保护异常',
    UNSUPPORTED: '当前模式不支持',
  }[recovery.data?.protection_state] || '正在读取'

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

        <section className="surface settings-section settings-section--wide">
          <div className="section-heading section-heading--compact">
            <div>
              <h2>恢复与备份</h2>
              <p>恢复包经过加密与完整重开校验；可读数据导出不能用于恢复。</p>
            </div>
            <HardDrive size={18} />
          </div>
          {recovery.status === 'loading' && <p className="inline-state" role="status">正在读取保护状态…</p>}
          {recovery.status === 'error' && <p className="inline-error" role="alert">{recovery.message}</p>}
          {recovery.status === 'ready' && (
            <>
              <dl className="settings-list settings-recovery-status">
                <div><dt>保护状态</dt><dd>{protectionLabel}</dd></div>
                <div><dt>最近已验证恢复点</dt><dd>{recovery.data.last_verified ? new Date(recovery.data.last_verified.created_at).toLocaleString('zh-CN') : '无'}</dd></div>
                <div><dt>删除检查点</dt><dd>{recovery.data.erasure_checkpoint}</dd></div>
              </dl>
              <label className="settings-inline-check">
                <input type="checkbox" checked={saveExternalCopy} onChange={(event) => setSaveExternalCopy(event.target.checked)} />
                同时保存一个经验证的外部副本（可防整盘故障）
              </label>
              <div className="settings-actions">
                <button type="button" className="button button--secondary" disabled={Boolean(recoveryAction)} onClick={() => runRecoveryAction('backup', () => dataControlApi.createVerifiedBackup({ saveExternalCopy }), '恢复点已创建并通过完整校验。')}>立即创建恢复点</button>
                <button type="button" className="button button--secondary" disabled={Boolean(recoveryAction)} onClick={() => runRecoveryAction('verify', dataControlApi.chooseAndVerifyBackup, '所选恢复点已通过完整校验。')}>校验恢复点</button>
                <button type="button" className="button button--secondary" disabled={Boolean(recoveryAction)} onClick={() => runRecoveryAction('restore', dataControlApi.chooseAndRestoreBackup, '恢复完成，当前数据已通过启动检查。')}><RotateCcw size={16} />恢复数据</button>
                <button type="button" className="button button--secondary" onClick={revealKey}>显示 Recovery Key</button>
                {recovery.data.protection_state === 'PARTIAL' && (
                  <button type="button" className="button button--danger" disabled={Boolean(recoveryAction)} onClick={() => runRecoveryAction('resume-erasure', dataControlApi.resumePendingErasure, '删除后恢复基线已补齐。')}>完成删除后恢复基线</button>
                )}
              </div>
              {recoveryKey && (
                <div className="settings-recovery-key" role="status">
                  <code>{recoveryKey}</code>
                  <button type="button" onClick={() => setRecoveryKey('')}>隐藏</button>
                </div>
              )}
              {recovery.message && <p className="settings-success" role="status">{recovery.message}</p>}
            </>
          )}
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

        <section className="surface settings-section settings-section--wide settings-erasure">
          <div className="section-heading section-heading--compact">
            <div>
              <h2>永久删除数据</h2>
              <p>先读取真实影响，再输入精确短语确认；完成前受影响功能保持关闭。</p>
            </div>
            <Trash2 size={18} />
          </div>
          <div className="settings-erasure-controls">
            <label>
              <span>删除范围</span>
              <select aria-label="删除范围" value={erasureScope} onChange={(event) => {
                setErasureScope(event.target.value)
                setErasurePreview(null)
                setErasureState({ status: 'idle', message: '', report: null })
              }}>
                <option value="DOCUMENT">单份资料</option>
                <option value="LEARNING_RECORDS">学习记录</option>
                <option value="MODEL_EXECUTION">模型执行记录</option>
              </select>
            </label>
            {erasureScope === 'DOCUMENT' && (
              <label>
                <span>资料 ID</span>
                <input aria-label="资料 ID" value={erasureTarget} onChange={(event) => setErasureTarget(event.target.value)} />
              </label>
            )}
            <button type="button" className="button button--secondary" onClick={previewErasure} disabled={erasureState.status === 'working'}>预览删除影响</button>
          </div>
          {erasurePreview && (
            <div className="settings-erasure-preview">
              <p><strong>不可恢复操作</strong>：{erasurePreview.backup_impact}</p>
              <ul>{erasurePreview.impacts.map((impact) => <li key={impact.owner_system}>{impact.owner_system}：{impact.estimated_records} 项</li>)}</ul>
              <p>请输入：<code>{erasurePreview.confirmation_phrase}</code></p>
              <label>
                <span>输入确认短语</span>
                <input aria-label="输入确认短语" value={erasurePhrase} onChange={(event) => setErasurePhrase(event.target.value)} autoComplete="off" />
              </label>
              <button type="button" className="button button--danger" onClick={confirmErasure} disabled={erasurePhrase !== erasurePreview.confirmation_phrase || erasureState.status === 'working'}>确认永久删除</button>
            </div>
          )}
          {erasureState.status === 'partial' && erasureState.report && (
            <button type="button" className="button button--danger" onClick={() => finishErasureBaseline(erasureState.report, erasureScope)}>重试完成恢复基线</button>
          )}
          {erasureState.message && <p className={erasureState.status === 'success' ? 'settings-success' : 'inline-error'} role={erasureState.status === 'success' ? 'status' : 'alert'}>{erasureState.message}</p>}
          <p className="settings-help">删除全部个人数据与账号需要密码复验和 24 小时可取消等待期。</p>
          <button type="button" className="button button--danger" onClick={() => navigate('/settings/delete-account')}>进入账号删除流程</button>
        </section>

        <section className="surface settings-section settings-section--wide">
          <div className="section-heading section-heading--compact">
            <div>
              <h2>导出我的数据</h2>
              <p>生成一次性、15 分钟有效的可读 ZIP；它不是数据库恢复包。</p>
            </div>
            <Download size={18} />
          </div>
          <div className="settings-export-scopes">
            {[
              ['PROFILE', '账号与画像'],
              ['DOCUMENTS', '资料元数据'],
              ['LEARNING_RECORDS', '学习记录'],
              ['MODEL_EXECUTION', '模型执行记录'],
            ].map(([scope, label]) => (
              <label key={scope}>
                <input
                  type="checkbox"
                  checked={exportScopes[scope]}
                  onChange={() => toggleExportScope(scope)}
                />
                <span>{label}</span>
              </label>
            ))}
            <label>
              <input
                type="checkbox"
                checked={includeDocumentOriginals}
                disabled={!exportScopes.DOCUMENTS}
                onChange={(event) => setIncludeDocumentOriginals(event.target.checked)}
              />
              <span>包含资料原件</span>
            </label>
          </div>
          <button
            type="button"
            className="button button--secondary"
            onClick={exportUserData}
            disabled={exportState.status === 'working' || !Object.values(exportScopes).some(Boolean)}
          >
            <Download size={16} />
            {exportState.status === 'working' ? '正在生成…' : '创建并下载导出'}
          </button>
          {exportState.message && (
            <p
              className={exportState.status === 'error' ? 'inline-error' : 'settings-success'}
              role={exportState.status === 'error' ? 'alert' : 'status'}
            >
              {exportState.message}
            </p>
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

        <section className="surface settings-section settings-section--wide" aria-labelledby="recovery-heading">
          <div className="section-heading section-heading--compact">
            <div>
              <p className="eyebrow">离线恢复</p>
              <h2 id="recovery-heading">恢复套件</h2>
              <p className="settings-help">套件可在忘记密码时离线恢复账号；每次轮换都会立即废止旧套件。</p>
            </div>
            <KeyRound size={18} />
          </div>
          {accountRecovery.status === 'loading' && <div className="inline-state" role="status"><div className="spinner" /> 正在读取恢复状态…</div>}
          {accountRecovery.status === 'ready' && (
            <p className="recovery-status">
              {accountRecovery.data?.configured
                ? `当前套件版本 ${accountRecovery.data.credential_version}`
                : '尚未创建恢复套件'}
            </p>
          )}
          {!issuedRecovery && (
            <form className="settings-form settings-form--recovery" onSubmit={issueRecovery}>
              <label>
                验证当前密码以轮换恢复套件
                <input type="password" autoComplete="current-password" value={accountRecoveryPassword} onChange={(event) => setAccountRecoveryPassword(event.target.value)} required />
              </label>
              <button type="submit" className="button button--secondary" disabled={accountRecoveryAction === 'loading'}>
                {accountRecoveryAction === 'loading' ? '正在轮换…' : accountRecovery.data?.configured ? '轮换恢复套件' : '创建恢复套件'}
              </button>
            </form>
          )}
          {issuedRecovery && (
            <div className="recovery-kit-panel" role="status">
              <strong>新的恢复套件只显示这一次</strong>
              <p>{issuedRecovery.storage_warning}</p>
              <output className="recovery-kit-output" aria-label="新的离线恢复套件">{issuedRecovery.recovery_secret}</output>
              <small>版本 {issuedRecovery.credential_version}</small>
              <label className="recovery-kit-confirm">
                <input type="checkbox" checked={recoveryConfirmed} onChange={(event) => setRecoveryConfirmed(event.target.checked)} />
                我已将新套件保存在离线安全位置
              </label>
              <button type="button" className="button button--primary" disabled={!recoveryConfirmed} onClick={dismissIssuedRecovery}>确认保存并关闭</button>
            </div>
          )}
          {accountRecovery.error && <p className="inline-error" role="alert">{accountRecovery.error}</p>}
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
        <section className="surface settings-section settings-section--wide settings-danger" aria-labelledby="danger-heading">
          <div><p className="eyebrow">危险操作</p><h2 id="danger-heading">删除账号</h2><p>永久删除学习数据、文件、会话和身份信息；先生成可核对的删除清单。</p></div>
          <button type="button" className="button button--danger" onClick={() => navigate('/settings/delete-account')}>查看删除范围</button>
        </section>
      </div>
    </div>
  )
}
