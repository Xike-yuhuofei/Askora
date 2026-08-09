import { useEffect, useState } from 'react'
import {
  AlertTriangle,
  CircleAlert,
  Download,
  KeyRound,
  LockKeyhole,
  LogOut,
  Server,
  Shield,
  User,
} from 'lucide-react'
import * as usersApi from '../api/users'
import * as dataControlApi from '../api/dataControl'
import { useAuth } from '../hooks/useAuth'
import { useNavigate } from '../router'
import './Settings.css'

export default function Settings() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
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

  useEffect(() => {
    usersApi.getSystemConfig()
      .then((data) => setSystem({ status: 'ready', data, error: '' }))
      .catch(() => setSystem({ status: 'error', data: null, error: '后端服务不可用，无法读取实时运行状态。' }))
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
