import { useEffect, useState } from 'react'
import {
  AlertTriangle,
  CircleAlert,
  Download,
  Eye,
  RefreshCw,
  Server,
  Shield,
  Trash2,
} from 'lucide-react'
import * as usersApi from '../api/users'
import * as dataControlApi from '../api/dataControl'
import * as onboardingApi from '../api/onboarding'
import { useNavigate } from '../router'
import './Settings.css'

const exportScopeLabels = [
  ['PROFILE', '偏好与本地画像'],
  ['DOCUMENTS', '资料元数据'],
  ['LEARNING_RECORDS', '学习记录'],
  ['MODEL_EXECUTION', '模型执行记录'],
]

export default function Settings() {
  const navigate = useNavigate()
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

  useEffect(() => {
    usersApi.getSystemConfig()
      .then((data) => setSystem({ status: 'ready', data, error: '' }))
      .catch(() => setSystem({ status: 'error', data: null, error: '后端服务不可用，无法读取实时运行状态。' }))
    loadOnboardingJourney()
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

  const categories = [
    { id: 'general', label: '通用' },
    { id: 'data', label: '数据管理' },
    { id: 'privacy', label: '隐私与安全' },
    { id: 'danger', label: '危险操作' },
  ]

  return (
    <div className="settings-page page-stack">
      <header className="page-header">
        <p className="eyebrow">本地应用</p>
        <h1>设置</h1>
        <p>管理应用行为、数据与安全边界。</p>
      </header>

      <nav className="settings-categories" aria-label="设置分类">
        {categories.map((cat) => (
          <button
            key={cat.id}
            type="button"
            className={`settings-category ${activeCategory === cat.id ? 'is-active' : ''}`}
            onClick={() => setActiveCategory(cat.id)}
            aria-current={activeCategory === cat.id ? 'page' : undefined}
          >
            {cat.label}
          </button>
        ))}
      </nav>

      {activeCategory === 'general' && (
        <div className="settings-grid">
          <section className="surface settings-section settings-section--wide">
            <div className="section-heading section-heading--compact">
              <div>
                <h2>错误恢复中心</h2>
                <p>查看资料、模型、后台任务和本地数据的可恢复问题，以及每个动作的安全边界。</p>
              </div>
              <CircleAlert size={18} />
            </div>
            <button type="button" className="button button--secondary" onClick={() => navigate('/settings/recovery')}>
              打开恢复中心
            </button>
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

          <section className="surface settings-section">
            <div className="section-heading section-heading--compact">
              <div>
                <p className="eyebrow">App 工具</p>
                <h2>首次引导</h2>
                <p>第一次使用时出现的引导流程。</p>
              </div>
              <Eye size={18} />
            </div>
            {onboardingJourney.status === 'loading' && <div className="inline-state" role="status"><div className="spinner" /> 正在读取…</div>}
            {onboardingJourney.status === 'error' && <p className="inline-error" role="alert">{onboardingJourney.error}</p>}
            {onboardingJourney.status === 'ready' && (
              <>
                <p className="settings-help">
                  当前引导：{onboardingJourney.data?.preference?.visibility === 'DISMISSED' ? '已暂存' : '进行中'}。
                </p>
                <button
                  type="button"
                  className="button button--secondary"
                  onClick={reopenOnboardingFlow}
                  disabled={onboardingReopenState === 'loading'}
                >
                  {onboardingReopenState === 'loading' ? '正在打开…' : '重新打开首次引导'}
                </button>
              </>
            )}
          </section>
        </div>
      )}

      {activeCategory === 'data' && (
        <div className="settings-grid">
          <section className="surface settings-section settings-section--wide">
            <div className="section-heading section-heading--compact">
              <div>
                <h2>导出我的数据</h2>
                <p>生成一次性、短期有效的可读 ZIP；它不是数据库恢复包。</p>
              </div>
              <Download size={18} />
            </div>
            <div className="settings-export-scopes">
              {exportScopeLabels.map(([scope, label]) => (
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
            {erasureState.message && <p className={erasureState.status === 'success' ? 'settings-success' : 'inline-error'} role={erasureState.status === 'success' ? 'status' : 'alert'}>{erasureState.message}</p>}
          </section>
        </div>
      )}

      {activeCategory === 'privacy' && (
        <div className="settings-grid">
          <section className="surface settings-section settings-section--wide">
            <div className="section-heading section-heading--compact">
              <div><h2>隐私与安全事实</h2></div>
              <Shield size={18} />
            </div>
            <div className="fact-list">
              <div><Shield size={18} /><span><strong>本地优先</strong><small>所有学习数据存储在本地设备，不经过中央服务器。</small></span></div>
              <div><Eye size={18} /><span><strong>不收集个人身份</strong><small>Askora 不要求账号，不收集个人身份信息。</small></span></div>
              <div><AlertTriangle size={18} /><span><strong>私人使用边界</strong><small>当前 App 不公开发布；这不代表已经取得备案、合规认证或第三方内容审核。</small></span></div>
            </div>
          </section>
        </div>
      )}

      {activeCategory === 'danger' && (
        <div className="settings-grid">
          <section className="surface settings-section settings-section--wide settings-danger">
            <div className="section-heading section-heading--compact">
              <div>
                <p className="eyebrow">危险操作</p>
                <h2>删除本地学习数据</h2>
                <p>永久删除学习记录、资料和本地知识缓存；操作不可撤销。</p>
              </div>
              <Trash2 size={18} />
            </div>
            <p className="settings-help">建议先导出数据，再执行删除。删除后学习进度将无法恢复。</p>
            <button
              type="button"
              className="button button--danger"
              onClick={() => setActiveCategory('data')}
            >
              前往数据管理执行删除
            </button>
          </section>

          <section className="surface settings-section settings-section--wide">
            <div className="section-heading section-heading--compact">
              <div>
                <p className="eyebrow">危险操作</p>
                <h2>重置应用</h2>
                <p>清除所有本地数据，恢复到首次启动状态。</p>
              </div>
              <RefreshCw size={18} />
            </div>
            <p className="settings-help">此操作将删除所有资料、学习记录和配置。请谨慎操作。</p>
            <button
              type="button"
              className="button button--danger"
              disabled
              title="重置功能将在后续版本中开放"
            >
              重置应用
            </button>
          </section>
        </div>
      )}
    </div>
  )
}
