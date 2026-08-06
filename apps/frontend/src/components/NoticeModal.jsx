import { useEffect, useState } from 'react'
import { ShieldAlert, ServerCrash, X } from 'lucide-react'
import './NoticeModal.css'

// 错误码 → 弹窗标题/图标映射
const codeMeta = {
  'SYS-0001': { title: '系统繁忙', icon: ServerCrash, tone: 'danger' },
}

export default function NoticeModal() {
  const [notice, setNotice] = useState(null)

  useEffect(() => {
    const handler = (e) => setNotice(e.detail)
    window.addEventListener('app:api-error', handler)
    return () => window.removeEventListener('app:api-error', handler)
  }, [])

  if (!notice) return null

  const meta = codeMeta[notice.code] || { title: '服务提示', icon: ShieldAlert, tone: 'info' }
  const Icon = meta.icon

  return (
    <div className="notice-overlay" onClick={() => setNotice(null)}>
      <div
        className={`notice-modal notice-${meta.tone}`}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
      >
        <button className="notice-close" onClick={() => setNotice(null)} aria-label="关闭">
          <X size={18} />
        </button>

        <div className="notice-icon">
          <Icon size={30} />
        </div>

        <h3 className="notice-title">{meta.title}</h3>

        <p className="notice-message">{notice.message}</p>

        {notice.request_id && <p className="notice-detail">请求编号：{notice.request_id}</p>}

        <button className="btn btn-primary notice-btn" onClick={() => setNotice(null)}>
          我知道了
        </button>
      </div>
    </div>
  )
}
