import { useEffect, useState } from 'react'
import { useNavigate } from '../router'
import { AlertTriangle, KeyRound, LockKeyhole, LogOut, Server, Shield, User } from 'lucide-react'
import Sidebar from '../components/Sidebar'
import { useAuth } from '../hooks/useAuth'
import * as usersApi from '../api/users'
import './Account.css'

export default function Account() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [sysConfig, setSysConfig] = useState(null)
  const [statusError, setStatusError] = useState('')
  const [clearing, setClearing] = useState(false)

  useEffect(() => {
    usersApi
      .getSystemConfig()
      .then(setSysConfig)
      .catch(() => setStatusError('后端服务不可用，无法读取实时运行状态'))
  }, [])

  const clearLocalSession = async () => {
    if (clearing) return
    setClearing(true)
    await logout()
    navigate('/login')
  }

  return (
    <div className="app-container">
      <Sidebar />

      <main className="main-content">
        <div className="page-header">
          <h1 className="page-title">账号管理</h1>
          <p className="page-subtitle">查看当前账号和私人运行边界</p>
        </div>

        <div className="account-layout">
          <section className="card account-section">
            <div className="section-header">
              <User size={18} />
              <h2>账号信息</h2>
            </div>
            <div className="info-list">
              <div className="info-item">
                <span className="info-label">昵称</span>
                <span className="info-value">{user?.nickname || '未设置'}</span>
              </div>
              <div className="info-item">
                <span className="info-label">账号类型</span>
                <span className="tag tag-info">个人用户</span>
              </div>
              <div className="info-item">
                <span className="info-label">账号状态</span>
                <span className="info-value">{user?.status === 'active' ? '正常' : (user?.status || '未知')}</span>
              </div>
              <div className="info-item">
                <span className="info-label">手机号</span>
                <span className="info-value">当前接口不返回手机号明文</span>
              </div>
            </div>
          </section>

          <section className="card account-section">
            <div className="section-header">
              <Server size={18} />
              <h2>系统运行状态</h2>
            </div>
            {sysConfig ? (
              <div className="sys-status-list">
                <div className="sys-status-item">
                  <span className="sys-status-label">运行模式</span>
                  <span className="tag tag-info">
                    {sysConfig.mode === 'private' ? '私人使用' : '服务模式'}
                  </span>
                </div>
                <div className="sys-status-item">
                  <span className="sys-status-label">AI 模型配置</span>
                  <span className={`tag ${sysConfig.llm_ready ? 'tag-success' : 'tag-warning'}`}>
                    {sysConfig.llm_ready ? '已配置' : '未配置，将使用模拟回复'}
                  </span>
                </div>
              </div>
            ) : (
              <p className="empty-text" role={statusError ? 'alert' : undefined}>
                {statusError || '正在读取状态…'}
              </p>
            )}
          </section>

          <section className="card account-section">
            <div className="section-header">
              <Shield size={18} />
              <h2>隐私与安全事实</h2>
            </div>
            <div className="privacy-list">
              <div className="privacy-item">
                <LockKeyhole size={18} />
                <div className="privacy-content">
                  <div className="privacy-title">账号字段保护</div>
                  <div className="privacy-desc">手机号加密存储，并使用不可逆盲索引完成登录查找。</div>
                </div>
              </div>
              <div className="privacy-item">
                <KeyRound size={18} />
                <div className="privacy-content">
                  <div className="privacy-title">会话保护</div>
                  <div className="privacy-desc">访问令牌短期有效，刷新令牌每次使用后轮换。</div>
                </div>
              </div>
              <div className="privacy-item">
                <AlertTriangle size={18} />
                <div className="privacy-content">
                  <div className="privacy-title">私人使用边界</div>
                  <div className="privacy-desc">
                    当前 App 不公开发布；这不代表已经取得备案、合规认证或第三方内容审核。
                  </div>
                </div>
              </div>
            </div>
          </section>

          <section className="card account-section danger-section">
            <div className="section-header">
              <LogOut size={18} />
              <h2>本地会话</h2>
            </div>
            <div className="danger-actions">
              <button
                className="btn btn-danger delete-btn"
                type="button"
                onClick={clearLocalSession}
                disabled={clearing}
              >
                <LogOut size={16} />
                {clearing ? '正在退出…' : '退出并清除本地登录信息'}
              </button>
              <p className="delete-note">
                此操作只清除当前设备的令牌和用户缓存，不会声称删除服务端学习数据。
              </p>
            </div>
          </section>
        </div>
      </main>
    </div>
  )
}
