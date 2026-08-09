import { useState } from 'react'
import { AlertTriangle, Clipboard, RefreshCw, ShieldCheck } from 'lucide-react'
import './StartupRecovery.css'

const copy = {
  BOOTSTRAP_BACKEND_BINARY_MISSING: '本地后端组件缺失，无法启动。',
  BOOTSTRAP_BACKEND_SPAWN_FAILED: '本地后端进程未能启动。',
  BOOTSTRAP_BACKEND_EXITED: '本地后端在就绪前退出。',
  BOOTSTRAP_BACKEND_START_TIMEOUT: '本地后端启动超时。',
  BOOTSTRAP_DATABASE_MIGRATION_REQUIRED: '本地数据库版本需要安全迁移。',
  BOOTSTRAP_DATABASE_UNAVAILABLE: '本地数据库暂时不可用。',
  BOOTSTRAP_DATABASE_INTEGRITY_FAILED: '本地数据库完整性检查未通过。',
}

export default function StartupRecovery({ diagnostic, onRetry }) {
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')

  const retry = async () => {
    if (busy || !diagnostic.retryable) return
    setBusy(true)
    setMessage('')
    try {
      await onRetry()
    } catch {
      setMessage('本地服务仍未启动；没有执行数据删除或覆盖。')
    } finally {
      setBusy(false)
    }
  }

  const copyDiagnostic = async () => {
    const safe = JSON.stringify({
      schema_version: diagnostic.schema_version,
      code: diagnostic.code,
      attempt: diagnostic.attempt,
      updated_at: diagnostic.updated_at,
      exit_code: diagnostic.exit_code,
    }, null, 2)
    await navigator.clipboard?.writeText(safe)
    setMessage('已复制脱敏诊断')
  }

  return (
    <main className="startup-recovery">
      <section className="startup-recovery__card" aria-labelledby="startup-title">
        <div className="startup-recovery__icon"><AlertTriangle size={28} /></div>
        <p className="eyebrow">Askora 本地启动</p>
        <h1 id="startup-title">需要处理一个启动问题</h1>
        <p>{copy[diagnostic.code] || '本地服务未能完成启动。'}</p>
        <div className="startup-recovery__safety">
          <ShieldCheck size={18} />
          <span>{diagnostic.data_safety === 'preserved' ? '现有数据已保留。' : '尚无法确认数据状态；Askora 未执行自动删除或覆盖。'}</span>
        </div>
        <div className="startup-recovery__actions">
          {diagnostic.retryable && (
            <button type="button" className="button button--primary" onClick={retry} disabled={busy}>
              <RefreshCw size={16} /> {busy ? '正在重试…' : '重新启动本地服务'}
            </button>
          )}
          <button type="button" className="button button--secondary" onClick={copyDiagnostic}>
            <Clipboard size={16} /> 复制脱敏诊断
          </button>
        </div>
        <p role="status">{message}</p>
        <details><summary>技术详情</summary><p>错误码：{diagnostic.code}</p><p>尝试次数：{diagnostic.attempt}</p></details>
      </section>
    </main>
  )
}
