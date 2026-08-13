import { useEffect, useRef, useState } from 'react'
import {
  AlertTriangle,
  CircleAlert,
  Download,
  Eye,
  Settings as SettingsIcon,
  Shield,
  Trash2,
  X,
} from 'lucide-react'
import * as usersApi from '../api/users'
import * as dataControlApi from '../api/dataControl'
import * as onboardingApi from '../api/onboarding'
import Button from '../components/ui/Button'
import { useNavigate } from '../router'
import './Settings.css'

const exportScopeLabels = [
  ['PROFILE', '偏好与本地画像'],
  ['DOCUMENTS', '资料元数据'],
  ['LEARNING_RECORDS', '学习记录'],
  ['MODEL_EXECUTION', '模型执行记录'],
]

const categories = [
  { id: 'general', label: '通用', icon: SettingsIcon },
  { id: 'data', label: '数据管理', icon: Download },
  { id: 'privacy', label: '隐私与安全', icon: Shield },
  { id: 'danger', label: '危险操作', icon: AlertTriangle },
]

export default function Settings({ onClose }) {
  const navigate = useNavigate()
  const dialogRef = useRef(null)
  const closeButtonRef = useRef(null)
  const previouslyFocusedRef = useRef(null)
  const [system, setSystem] = useState({ status: 'loading', data: null, error: '' })
  const [onboardingJourney, setOnboardingJourney] = useState({ status: 'loading', data: null, error: '' })
  const [onboardingReopenState, setOnboardingReopenState] = useState('idle')
  const [activeCategory, setActiveCategory] = useState('general')

  const [exportScopes, setExportScopes] = useState({
    PROFILE: true,
    DOCUMENTS: true,
    LEARNING_RECORDS: true,
    MODEL_EXECUTION: true,
  })
  const [includeDocumentOriginals, setIncludeDocumentOriginals] = useState(false)
  const [exportState, setExportState] = useState({ status: 'idle', message: '' })

  const [erasureScope, setErasureScope] = useState('LEARNING_RECORDS')
  const [erasureTarget, setErasureTarget] = useState('')
  const [erasurePreview, setErasurePreview] = useState(null)
  const [erasureCommandKey, setErasureCommandKey] = useState('')
  const [erasurePhrase, setErasurePhrase] = useState('')
  const [erasureState, setErasureState] = useState({ status: 'idle', message: '', report: null })

  const close = () => {
    if (onClose) onClose()
    else navigate('/today')
  }

  useEffect(() => {
    usersApi.getSystemConfig()
      .then((data) => setSystem({ status: 'ready', data, error: '' }))
      .catch(() => setSystem({ status: 'error', data: null, error: '后端服务不可用，无法读取实时运行状态。' }))
    loadOnboardingJourney()
  }, [])

  useEffect(() => {
    previouslyFocusedRef.current = document.activeElement
    const focusTimer = window.setTimeout(() => closeButtonRef.current?.focus(), 0)
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'

    const handleKeys = (event) => {
      if (event.key === 'Escape') {
        event.preventDefault()
        close()
        return
      }
      if (event.key !== 'Tab') return
      const focusables = Array.from(
        dialogRef.current?.querySelectorAll(
          'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])',
        ) || [],
      )
      if (!focusables.length) return
      const first = focusables[0]
      const last = focusables[focusables.length - 1]
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    }

    document.addEventListener('keydown', handleKeys)
    return () => {
      window.clearTimeout(focusTimer)
      document.removeEventListener('keydown', handleKeys)
      document.body.style.overflow = previousOverflow
      if (previouslyFocusedRef.current instanceof HTMLElement) {
        previouslyFocusedRef.current.focus()
      }
    }
  }, [])

  const loadOnboardingJourney = () => {
    setOnboardingJourney({ status: 'loading', data: null, error: '' })
    onboardingApi.getOnboardingJourney()
      .then((data) => setOnboardingJourney({ status: 'ready', data, error: '' }))
      .catch(() => setOnboardingJourney({ status: 'error', data: null, error: '无法读取首次引导状态。' }))
  }

  const reopenOnboardingFlow = async () => {
    if (onboardingReopenState === 'loading') return
    const current = onboardingJourney
    if (!current.data) return
    setOnboardingReopenState('loading')
    try {
      await onboardingApi.reopenOnboarding({
        expectedVersion: current.data.preference?.preference_version ?? 1,
      })
      setOnboardingReopenState('idle')
      navigate('/welcome')
    } catch {
      setOnboardingReopenState('error')
      setOnboardingJourney((prev) => ({ ...prev, error: '无法重新打开首次引导，请稍后重试。' }))
    }
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

  const confirmErasure = async () => {
    if (!erasurePreview || erasurePhrase !== erasurePreview.confirmation_phrase) return
    setErasureState({ status: 'working', message: '正在删除受影响数据…', report: null })
    try {
      const report = await dataControlApi.confirmErasure({
        previewId: erasurePreview.preview_id,
        confirmationToken: erasurePreview.confirmation_token,
        confirmationPhrase: erasurePhrase,
        idempotencyKey: erasureCommandKey,
      })
      setErasureState({ status: 'success', message: '删除已提交；受影响数据已删除。', report })
      setErasurePreview(null)
      setErasurePhrase('')
    } catch {
      setErasureState({ status: 'error', message: '删除未完成；没有显示成功。', report: null })
    }
  }

  const active = categories.find((item) => item.id === activeCategory) || categories[0]
  const onboardingVisibility = onboardingJourney.data?.preference?.visibility === 'DISMISSED' ? '已暂存' : '进行中'

  return (
    <div className="ds-dialog-backdrop settings-overlay" onClick={close}>
      <div
        ref={dialogRef}
        className="settings-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="settings-dialog-title"
        tabIndex={-1}
        onClick={(event) => event.stopPropagation()}
      >
        <nav className="settings-dialog__nav" aria-label="设置分类">
          {categories.map((cat) => (
            <button
              key={cat.id}
              type="button"
              className={`settings-dialog__nav-item ${activeCategory === cat.id ? 'is-active' : ''}`}
              onClick={() => setActiveCategory(cat.id)}
              aria-current={activeCategory === cat.id ? 'page' : undefined}
            >
              <cat.icon size={16} aria-hidden="true" />
              <span>{cat.label}</span>
            </button>
          ))}
        </nav>

        <div className="settings-dialog__main">
          <header className="settings-dialog__head">
            <h1 id="settings-dialog-title" className="settings-dialog__title">{active.label}</h1>
            <button
              ref={closeButtonRef}
              type="button"
              className="ds-dialog__close"
              aria-label="关闭设置"
              onClick={close}
            >
              <X size={16} />
            </button>
          </header>

          <div className="settings-dialog__body">
            {activeCategory === 'general' && (
              <>
                <SettingGroup title="运行状态">
                  {system.status === 'loading' && (
                    <div className="inline-state" role="status"><div className="spinner" /> 正在读取…</div>
                  )}
                  {system.status === 'error' && <p className="inline-error" role="alert">{system.error}</p>}
                  {system.status === 'ready' && (
                    <>
                      <SettingRow label="运行模式" description="当前应用的本地运行边界。">
                        <span className="settings-row__value">{system.data.mode === 'private' ? '私人使用' : '服务模式'}</span>
                      </SettingRow>
                      <SettingRow label="AI 模型" description="是否已配置可用的本地模型路由。">
                        <span className="settings-row__value">{system.data.llm_ready ? '已配置' : '未配置'}</span>
                      </SettingRow>
                    </>
                  )}
                </SettingGroup>

                <SettingGroup title="引导与恢复">
                  <SettingRow
                    label="首次引导"
                    description="第一次使用时出现的引导流程。"
                  >
                    {onboardingJourney.status === 'loading' && (
                      <div className="inline-state" role="status"><div className="spinner" /> 正在读取…</div>
                    )}
                    {onboardingJourney.status === 'error' && <p className="inline-error" role="alert">{onboardingJourney.error}</p>}
                    {onboardingJourney.status === 'ready' && (
                      <div className="settings-row__actions">
                        <span className="settings-row__value">{onboardingVisibility}</span>
                        <Button
                          variant="secondary"
                          onClick={reopenOnboardingFlow}
                          disabled={onboardingReopenState === 'loading'}
                        >
                          {onboardingReopenState === 'loading' ? '正在打开…' : '重新打开首次引导'}
                        </Button>
                      </div>
                    )}
                  </SettingRow>
                  <SettingRow
                    label="错误恢复中心"
                    description="查看资料、模型、后台任务和本地数据的可恢复问题。"
                  >
                    <Button variant="secondary" onClick={() => navigate('/settings/recovery')}>
                      <CircleAlert size={16} />
                      打开恢复中心
                    </Button>
                  </SettingRow>
                </SettingGroup>
              </>
            )}

            {activeCategory === 'data' && (
              <>
                <SettingGroup title="导出我的数据" intro="生成一次性、短期有效的可读 ZIP；它不是数据库恢复包。">
                  {exportScopeLabels.map(([scope, label]) => (
                    <SettingRow key={scope} label={label}>
                      <label className="settings-check">
                        <input
                          type="checkbox"
                          checked={exportScopes[scope]}
                          onChange={() => toggleExportScope(scope)}
                        />
                        <span className="visually-hidden">{label}</span>
                      </label>
                    </SettingRow>
                  ))}
                  <SettingRow label="包含资料原件" description="仅在导出资料元数据时可选。">
                    <label className="settings-check">
                      <input
                        type="checkbox"
                        checked={includeDocumentOriginals}
                        disabled={!exportScopes.DOCUMENTS}
                        onChange={(event) => setIncludeDocumentOriginals(event.target.checked)}
                      />
                      <span className="visually-hidden">包含资料原件</span>
                    </label>
                  </SettingRow>
                  <SettingRow label="创建导出">
                    <Button
                      variant="secondary"
                      onClick={exportUserData}
                      disabled={exportState.status === 'working' || !Object.values(exportScopes).some(Boolean)}
                    >
                      <Download size={16} />
                      {exportState.status === 'working' ? '正在生成…' : '创建并下载导出'}
                    </Button>
                  </SettingRow>
                  {exportState.message && (
                    <p
                      className={exportState.status === 'error' ? 'inline-error' : 'settings-success'}
                      role={exportState.status === 'error' ? 'alert' : 'status'}
                    >
                      {exportState.message}
                    </p>
                  )}
                </SettingGroup>

                <SettingGroup title="永久删除数据" intro="先读取真实影响，再输入精确短语确认；完成前受影响功能保持关闭。">
                  <SettingRow label="删除范围">
                    <select
                      aria-label="删除范围"
                      className="settings-select"
                      value={erasureScope}
                      onChange={(event) => {
                        setErasureScope(event.target.value)
                        setErasurePreview(null)
                        setErasureState({ status: 'idle', message: '', report: null })
                      }}
                    >
                      <option value="DOCUMENT">单份资料</option>
                      <option value="LEARNING_RECORDS">学习记录</option>
                      <option value="MODEL_EXECUTION">模型执行记录</option>
                    </select>
                  </SettingRow>
                  {erasureScope === 'DOCUMENT' && (
                    <SettingRow label="资料 ID">
                      <input
                        aria-label="资料 ID"
                        className="settings-input"
                        value={erasureTarget}
                        onChange={(event) => setErasureTarget(event.target.value)}
                      />
                    </SettingRow>
                  )}
                  <SettingRow label="预览影响">
                    <Button variant="secondary" onClick={previewErasure} disabled={erasureState.status === 'working'}>
                      预览删除影响
                    </Button>
                  </SettingRow>
                  {erasurePreview && (
                    <div className="settings-erasure-preview">
                      <p><strong>不可恢复操作</strong>：{erasurePreview.backup_impact}</p>
                      <ul>{erasurePreview.impacts.map((impact) => <li key={impact.owner_system}>{impact.owner_system}：{impact.estimated_records} 项</li>)}</ul>
                      <p>请输入：<code>{erasurePreview.confirmation_phrase}</code></p>
                      <label>
                        <span>输入确认短语</span>
                        <input aria-label="输入确认短语" value={erasurePhrase} onChange={(event) => setErasurePhrase(event.target.value)} autoComplete="off" />
                      </label>
                      <Button
                        variant="danger"
                        onClick={confirmErasure}
                        disabled={erasurePhrase !== erasurePreview.confirmation_phrase || erasureState.status === 'working'}
                      >
                        确认永久删除
                      </Button>
                    </div>
                  )}
                  {erasureState.message && (
                    <p className={erasureState.status === 'success' ? 'settings-success' : 'inline-error'} role={erasureState.status === 'success' ? 'status' : 'alert'}>
                      {erasureState.message}
                    </p>
                  )}
                </SettingGroup>
              </>
            )}

            {activeCategory === 'privacy' && (
              <SettingGroup title="隐私与安全事实">
                <SettingRow
                  label="本地优先"
                  description="所有学习数据存储在本地设备，不经过中央服务器。"
                >
                  <Shield size={16} aria-hidden="true" />
                </SettingRow>
                <SettingRow
                  label="不收集个人身份"
                  description="Askora 不要求账号，不收集个人身份信息。"
                >
                  <Eye size={16} aria-hidden="true" />
                </SettingRow>
                <SettingRow
                  label="私人使用边界"
                  description="当前 App 不公开发布；这不代表已经取得备案、合规认证或第三方内容审核。"
                >
                  <AlertTriangle size={16} aria-hidden="true" />
                </SettingRow>
              </SettingGroup>
            )}

            {activeCategory === 'danger' && (
              <SettingGroup title="删除本地学习数据">
                <SettingRow
                  label="永久删除"
                  description="永久删除学习记录、资料和本地知识缓存。建议先导出数据，再执行删除。"
                >
                  <Button variant="danger" onClick={() => setActiveCategory('data')}>
                    <Trash2 size={16} />
                    前往数据管理执行删除
                  </Button>
                </SettingRow>
              </SettingGroup>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function SettingGroup({ title, intro, children }) {
  return (
    <section className="settings-group">
      <h2 className="settings-group__title">{title}</h2>
      {intro ? <p className="settings-group__intro">{intro}</p> : null}
      <div className="settings-group__rows">{children}</div>
    </section>
  )
}

function SettingRow({ label, description, children }) {
  return (
    <div className="settings-row">
      <div className="settings-row__copy">
        <div className="settings-row__label">{label}</div>
        {description ? <p className="settings-row__desc">{description}</p> : null}
      </div>
      <div className="settings-row__control">{children}</div>
    </div>
  )
}
