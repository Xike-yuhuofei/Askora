import { useCallback, useEffect, useRef, useState } from 'react'
import {
  AlertTriangle,
  CircleAlert,
  Download,
  HardDrive,
  KeyRound,
  LockKeyhole,
  LogOut,
  RotateCcw,
  Server,
  Shield,
  Trash2,
  User,
} from 'lucide-react'
import * as usersApi from '../api/users'
import * as dataControlApi from '../api/dataControl'
import { useAuth } from '../hooks/useAuth'
import { useLocation, useNavigate } from '../router'
import './Settings.css'

const MODEL_OPTIONS = {
  qwen: { label: '通义千问', models: ['qwen-turbo'] },
  deepseek: { label: 'DeepSeek', models: ['deepseek-chat'] },
  doubao: { label: '豆包', models: ['doubao-pro-32k'] },
  zhipu: { label: '智谱', models: ['glm-4.7-flash'] },
}

const MODEL_SOURCE_LABELS = {
  DESKTOP_VAULT: 'App 安全存储',
  EXTERNAL_ENVIRONMENT: '外部只读配置',
  NONE: '未配置',
}

function modelStatusLabel(model) {
  if (model.phase === 'loading') return '正在读取'
  if (model.phase === 'validating') return '正在验证'
  if (model.phase === 'applying') return '正在应用'
  if (model.phase === 'unavailable') return '未配置'
  if (model.phase === 'apply_recovered') return '应用失败已恢复'
  if (model.phase === 'rollback_failed') return '恢复失败'
  const summary = model.summary
  if (summary?.state === 'ACTIVE' && summary.runtime_ready) return '已验证'
  if (summary?.state === 'EXTERNAL_READ_ONLY') return '外部只读配置'
  if (summary?.state === 'DISABLED') return '已停用'
  if (summary?.state === 'DEGRADED') return '恢复失败'
  return '未配置'
}

function formatVerifiedAt(value) {
  if (!value) return '尚未验证'
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

function ModelSettingsPanel({ sectionRef }) {
  const { pathname } = useLocation()
  const navigate = useNavigate()
  const [model, setModel] = useState({ phase: 'loading', summary: null, error: null, message: '' })
  const [provider, setProvider] = useState('qwen')
  const [selectedModel, setSelectedModel] = useState(MODEL_OPTIONS.qwen.models[0])
  const [credential, setCredential] = useState('')
  const [clearArmed, setClearArmed] = useState(false)
  const bridgeAvailable = Boolean(window.electronAPI?.getModelSettings)
  const canApply = Boolean(window.electronAPI?.applyModelSettings)
  const canClear = Boolean(window.electronAPI?.clearModelSettings)

  const acceptSummary = useCallback((summary, nextPhase = 'ready') => {
    setModel({ phase: nextPhase, summary, error: null, message: '' })
    if (summary?.provider && MODEL_OPTIONS[summary.provider]) {
      setProvider(summary.provider)
      setSelectedModel(summary.model || MODEL_OPTIONS[summary.provider].models[0])
    }
  }, [])

  const loadModelSettings = useCallback(async () => {
    if (!bridgeAvailable) {
      setModel({ phase: 'unavailable', summary: null, error: null, message: '' })
      return null
    }
    setModel((current) => ({ ...current, phase: 'loading', error: null, message: '' }))
    try {
      const result = await window.electronAPI.getModelSettings()
      if (!result?.ok || !result.settings) {
        setModel({ phase: 'rollback_failed', summary: null, error: result?.error || {
          code: 'MODEL_CONFIG_STORAGE_UNAVAILABLE',
          message: '模型配置状态暂时无法读取。',
        }, message: '' })
        return null
      }
      acceptSummary(result.settings)
      return result.settings
    } catch {
      setModel({ phase: 'rollback_failed', summary: null, error: {
        code: 'MODEL_PROVIDER_UNAVAILABLE',
        message: '模型配置状态暂时无法读取。',
      }, message: '' })
      return null
    }
  }, [acceptSummary, bridgeAvailable])

  useEffect(() => {
    loadModelSettings()
  }, [loadModelSettings])

  useEffect(() => {
    if (pathname !== '/settings/models') return undefined
    const frame = window.requestAnimationFrame(() => sectionRef.current?.focus())
    return () => window.cancelAnimationFrame(frame)
  }, [pathname, sectionRef])

  const changeProvider = (event) => {
    const nextProvider = event.target.value
    setProvider(nextProvider)
    setSelectedModel(MODEL_OPTIONS[nextProvider].models[0])
    setClearArmed(false)
  }

  const applySettings = async (event) => {
    event.preventDefault()
    if (!canApply || ['validating', 'applying'].includes(model.phase)) return
    const candidateKey = credential
    setCredential('')
    setClearArmed(false)
    if (candidateKey.length < 8) {
      setModel((current) => ({
        ...current,
        phase: 'ready',
        error: { code: 'MODEL_CREDENTIAL_REJECTED', message: '请输入有效的模型 Key。' },
        message: '',
      }))
      return
    }
    setModel((current) => ({ ...current, phase: 'validating', error: null, message: '' }))
    try {
      const result = await window.electronAPI.applyModelSettings({
        schema_version: '1.0',
        provider,
        model: selectedModel,
        api_key: candidateKey,
        expected_revision: model.summary?.revision ?? null,
      })
      if (result?.ok && result.settings) {
        setModel({ phase: 'ready', summary: result.settings, error: null, message: '模型配置已验证并应用。' })
        return
      }
      let summary = result?.settings || model.summary
      if (result?.error?.code === 'MODEL_CONFIG_REVISION_CONFLICT') {
        summary = await loadModelSettings() || summary
      }
      setModel({
        phase: result?.rollback_succeeded === true
          ? 'apply_recovered'
          : result?.rollback_succeeded === false || result?.error?.code === 'MODEL_CONFIG_ROLLBACK_FAILED'
            ? 'rollback_failed'
            : 'ready',
        summary,
        error: result?.error || { code: 'MODEL_PROVIDER_UNAVAILABLE', message: '模型连接测试失败。' },
        message: '',
      })
    } catch {
      setModel((current) => ({
        ...current,
        phase: 'ready',
        error: { code: 'MODEL_PROVIDER_UNAVAILABLE', message: '模型连接测试失败。' },
        message: '',
      }))
    }
  }

  const clearSettings = async () => {
    if (!canClear || model.phase === 'applying') return
    setClearArmed(false)
    setCredential('')
    setModel((current) => ({ ...current, phase: 'applying', error: null, message: '' }))
    try {
      const result = await window.electronAPI.clearModelSettings({
        schema_version: '1.0',
        expected_revision: model.summary?.revision ?? null,
      })
      if (result?.ok && result.settings) {
        setModel({ phase: 'ready', summary: result.settings, error: null, message: 'App 模型配置已停用；外部配置未被编辑。' })
        return
      }
      setModel({
        phase: result?.rollback_succeeded === true ? 'apply_recovered' : 'rollback_failed',
        summary: result?.settings || model.summary,
        error: result?.error || { code: 'MODEL_CONFIG_APPLY_FAILED', message: '模型配置未能停用。' },
        message: '',
      })
    } catch {
      setModel((current) => ({
        ...current,
        phase: 'rollback_failed',
        error: { code: 'MODEL_CONFIG_ROLLBACK_FAILED', message: '模型配置恢复失败。' },
        message: '',
      }))
    }
  }

  const busy = ['validating', 'applying'].includes(model.phase)
  const summary = model.summary
  const stateLabel = modelStatusLabel(model)

  return (
    <section
      className="surface settings-section settings-section--wide model-settings"
      ref={sectionRef}
      tabIndex={-1}
      aria-labelledby="model-settings-title"
    >
      <div className="section-heading section-heading--compact">
        <div>
          <p className="eyebrow">SYS08 · 本机安全存储</p>
          <h2 id="model-settings-title">模型与密钥</h2>
          <p>配置 Askora 实际使用的单一 provider/model；已保存的 Key 永不回显。</p>
        </div>
        <KeyRound size={18} />
      </div>

      <div className="model-settings-status" role="status" aria-live="polite">
        <strong>{stateLabel}</strong>
        {model.phase === 'loading' && <span>正在读取脱敏配置…</span>}
        {model.phase === 'unavailable' && (
          <span>仅在 macOS 桌面 App 中提供安全写入；浏览器视图不会接收或保存 Key。</span>
        )}
        {summary && (
          <dl className="model-settings-summary">
            <div><dt>Provider</dt><dd>{MODEL_OPTIONS[summary.provider]?.label || '未配置'}</dd></div>
            <div><dt>Model</dt><dd>{summary.model || '未配置'}</dd></div>
            <div><dt>来源</dt><dd>{MODEL_SOURCE_LABELS[summary.source] || summary.source || '未配置'}</dd></div>
            <div><dt>Revision</dt><dd>{summary.revision ?? '无'}</dd></div>
            <div><dt>最后验证</dt><dd>{formatVerifiedAt(summary.verified_at)}</dd></div>
            <div><dt>运行一致性</dt><dd>{summary.runtime_ready && summary.runtime_revision === summary.revision ? '一致' : '未就绪'}</dd></div>
          </dl>
        )}
      </div>

      {canApply && (
        <form className="model-settings-form" onSubmit={applySettings}>
          <label>
            <span>Provider</span>
            <select value={provider} onChange={changeProvider} disabled={busy}>
              {Object.entries(MODEL_OPTIONS).map(([value, option]) => (
                <option value={value} key={value}>{option.label}</option>
              ))}
            </select>
          </label>
          <label>
            <span>Model</span>
            <select value={selectedModel} onChange={(event) => setSelectedModel(event.target.value)} disabled={busy}>
              {MODEL_OPTIONS[provider].models.map((value) => <option value={value} key={value}>{value}</option>)}
            </select>
          </label>
          <label className="model-settings-key">
            <span>API Key</span>
            <input
              type="password"
              value={credential}
              onChange={(event) => setCredential(event.target.value)}
              autoComplete="new-password"
              spellCheck="false"
              disabled={busy}
              placeholder="提交后立即清空，不会回显"
            />
          </label>
          <div className="model-settings-disclosure">
            <strong>验证边界</strong>
            <p>测试只发送固定合成文本，不发送个人资料，但可能产生极少量 provider 调用费用。</p>
            <p>真实 Book Learning 会发送当前学习意图与一份 learner-visible evidence；兼容 quick flow 最多发送最近 20 条消息。Askora 不读取余额，实际费用以 provider 账户为准。</p>
          </div>
          <div className="model-settings-actions">
            <button type="submit" className="button button--primary" disabled={busy || credential.length < 8}>
              {model.phase === 'validating' ? '正在验证…' : '验证并应用'}
            </button>
            {canClear && summary?.source === 'DESKTOP_VAULT' && summary.state !== 'DISABLED' && !clearArmed && (
              <button type="button" className="button button--secondary" disabled={busy} onClick={() => setClearArmed(true)}>
                停用 App 模型配置
              </button>
            )}
          </div>
          {clearArmed && (
            <div className="model-settings-confirm" role="alert">
              <p>停用会写入 DISABLED revision 并重启本地服务；不会编辑 `.env` 或 provider 账户。</p>
              <div>
                <button type="button" className="button button--danger" onClick={clearSettings}>确认停用</button>
                <button type="button" className="button button--secondary" onClick={() => setClearArmed(false)}>取消</button>
              </div>
            </div>
          )}
        </form>
      )}

      {model.message && <p className="settings-success" role="status">{model.message}</p>}
      {model.error && (
        <div className="inline-error model-settings-error" role="alert">
          <strong>{model.error.message}</strong>
          <span>错误码：{model.error.code}</span>
          <span>{model.phase === 'apply_recovered' ? '旧配置仍可用；本次候选已丢弃。' : model.phase === 'rollback_failed' ? '当前模型不可用，请进入恢复中心处理。' : '候选配置没有写入；当前 owner 状态未被覆盖。'}</span>
          {model.phase === 'rollback_failed' && (
            <button type="button" className="button button--secondary" onClick={() => navigate('/settings/recovery')}>打开恢复中心</button>
          )}
        </div>
      )}
    </section>
  )
}

export default function Settings() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const modelSectionRef = useRef(null)
  const [system, setSystem] = useState({ status: 'loading', data: null, error: '' })
  const [clearing, setClearing] = useState(false)
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
        <section className="surface settings-section settings-section--wide settings-session">
          <div>
            <h2>错误恢复中心</h2>
            <p>查看资料、模型、后台任务和本地数据的可恢复问题，以及每个动作的安全边界。</p>
          </div>
          <button type="button" className="button button--secondary" onClick={() => navigate('/settings/recovery')}>
            <CircleAlert size={16} />
            打开恢复中心
          </button>
        </section>
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
                <dd>{system.data.llm_ready ? '已配置' : '未配置'}</dd>
              </div>
            </dl>
          )}
        </section>

        <ModelSettingsPanel sectionRef={modelSectionRef} />

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
                <option value="ALL_PERSONAL_DATA">全部个人数据与账号</option>
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

        <section className="surface settings-section settings-section--wide settings-session">
          <div>
            <h2>本地会话</h2>
            <p>退出只清除当前设备的令牌和用户缓存，不会删除服务端学习数据。</p>
          </div>
          <button type="button" className="button button--danger" onClick={clearLocalSession} disabled={clearing}>
            <LogOut size={16} />
            {clearing ? '正在退出…' : '退出并清除本地登录信息'}
          </button>
        </section>
      </div>
    </div>
  )
}
