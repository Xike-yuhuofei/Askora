import { lazy, Suspense, memo, useState } from 'react'
import { Check, Copy } from 'lucide-react'
import './WorkspaceMessage.css'

const RichMessage = lazy(() => import('./RichMessage'))

function formatTime(iso) {
  if (!iso) return ''
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return ''
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

function WorkspaceMessage({ message }) {
  const isUser = message.role === 'user'
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    if (!navigator.clipboard) return
    await navigator.clipboard.writeText(message.content)
    setCopied(true)
    const timer = setTimeout(() => setCopied(false), 2000)
    return () => clearTimeout(timer)
  }

  return (
    <article
      className={`workspace-message workspace-message--${message.role}`}
      aria-label={isUser ? '你的消息' : 'Askora 的回复'}
    >
      <div className="workspace-message__body">
        {!isUser && (
          <div className="workspace-message__avatar" aria-hidden="true">
            A
          </div>
        )}
        <div className="workspace-message__content">
          {isUser ? (
            <p>{message.content}</p>
          ) : (
            <Suspense fallback={<p>{message.content}</p>}>
              <RichMessage fallbackText={message.content} payload={message.render_payload} />
            </Suspense>
          )}
          <footer className="workspace-message__footer">
            {message.created_at && (
              <time dateTime={message.created_at}>{formatTime(message.created_at)}</time>
            )}
            {!isUser && (
              <button
                type="button"
                className="workspace-message__copy"
                onClick={handleCopy}
                aria-label={copied ? '已复制' : '复制内容'}
              >
                {copied ? <Check size={14} aria-hidden="true" /> : <Copy size={14} aria-hidden="true" />}
                <span>{copied ? '已复制' : '复制'}</span>
              </button>
            )}
          </footer>
        </div>
      </div>
    </article>
  )
}

export default memo(WorkspaceMessage)
