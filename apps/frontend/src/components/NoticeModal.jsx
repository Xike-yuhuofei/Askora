import { useEffect, useState } from 'react'
import { ShieldAlert, ServerCrash, X } from 'lucide-react'
import Button from './ui/Button'
import './NoticeModal.css'

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

  useEffect(() => {
    if (!notice) return undefined
    const onKey = (event) => {
      if (event.key === 'Escape') setNotice(null)
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [notice])

  if (!notice) return null

  const meta = codeMeta[notice.code] || { title: '服务提示', icon: ShieldAlert, tone: 'info' }
  const Icon = meta.icon

  return (
    <div className="ds-dialog-backdrop" onClick={() => setNotice(null)}>
      <div
        className={`ds-dialog notice-${meta.tone}`}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="notice-title"
      >
        <div className="ds-dialog__head">
          <h3 id="notice-title" className="ds-dialog__title">{meta.title}</h3>
          <button className="ds-dialog__close" onClick={() => setNotice(null)} aria-label="关闭">
            <X size={16} />
          </button>
        </div>
        <div className="ds-dialog__body">
          <p className="notice-message"><Icon size={16} aria-hidden="true" /> {notice.message}</p>
          {notice.request_id ? <p className="notice-detail">请求编号：{notice.request_id}</p> : null}
        </div>
        <div className="ds-dialog__foot">
          <Button variant="brand" onClick={() => setNotice(null)}>我知道了</Button>
        </div>
      </div>
    </div>
  )
}
