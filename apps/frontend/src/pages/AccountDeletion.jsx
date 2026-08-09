import { useEffect, useState } from 'react'
import { AlertTriangle, ArrowLeft, ShieldAlert } from 'lucide-react'
import * as accountApi from '../api/account'
import * as dataControlApi from '../api/dataControl'
import { useAuth } from '../hooks/useAuth'
import { useNavigate } from '../router'
import './AccountDeletion.css'

const CONFIRMATION = '永久删除我的 Askora 账号'
const CONTROL_KEY = 'account_deletion_control'

const makeKey = (prefix) => `${prefix}-${crypto.randomUUID()}`

export default function AccountDeletion() {
  const navigate = useNavigate()
  const { user, clearForDeletion } = useAuth()
  const [controlToken, setControlToken] = useState(() => sessionStorage.getItem(CONTROL_KEY) || '')
  const [preview, setPreview] = useState(null)
  const [status, setStatus] = useState(null)
  const [phase, setPhase] = useState(controlToken ? 'status' : 'idle')
  const [password, setPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [message, setMessage] = useState('')

  const loadStatus = async (token = controlToken) => {
    if (!token) return
    try {
      const result = await accountApi.getDeletionStatus(token)
      setStatus(result)
      setPhase('status')
      setMessage('')
    } catch {
      setMessage('删除状态读取失败；控制令牌可能已过期。请重新登录核对账号状态。')
    }
  }

  useEffect(() => {
    if (controlToken) loadStatus(controlToken)
    // control token is intentionally the only status credential after request.
  }, [])

  useEffect(() => {
    if (!controlToken || !status || !['deletion_pending', 'purging'].includes(status.lifecycle)) return undefined
    const timer = window.setInterval(() => loadStatus(controlToken), 5000)
    return () => window.clearInterval(timer)
  }, [controlToken, status?.lifecycle])

  const createPreview = async () => {
    setPhase('loading')
    setMessage('')
    try {
      setPreview(await accountApi.previewDeletion())
      setPhase('confirm')
    } catch {
      setPhase('idle')
      setMessage('无法生成删除清单，请确认账号仍处于正常状态后重试。')
    }
  }

  const submitDeletion = async (event) => {
    event.preventDefault()
    setPhase('loading')
    setMessage('')
    try {
      const result = await accountApi.requestDeletion({
        schema_version: '1.0', current_password: password,
        confirmation_phrase: confirmation, preview_id: preview.preview_id,
        preview_digest: preview.preview_digest, policy_version: preview.policy_version,
        idempotency_key: makeKey('delete-account'),
      })
      sessionStorage.setItem(CONTROL_KEY, result.deletion_control_token)
      setControlToken(result.deletion_control_token)
      setStatus(result.status)
      clearForDeletion()
      setPhase('status')
    } catch (error) {
      const code = error.response?.data?.error?.code
      const errors = {
        AUTH_CURRENT_PASSWORD_INVALID: '当前密码不正确，请重新输入。',
        ACCOUNT_DELETION_PREVIEW_STALE: '数据已变化或清单已过期，请重新生成删除清单。',
        PRIVACY_SUBJECT_AMBIGUOUS: '删除范围存在无法安全归属的数据，系统已停止执行。',
      }
      setMessage(errors[code] || '删除请求未被接受，请稍后重试。')
      setPhase(code === 'ACCOUNT_DELETION_PREVIEW_STALE' ? 'idle' : 'confirm')
    }
  }

  const cancel = async () => {
    setPhase('loading')
    try {
      const result = await accountApi.cancelDeletion(controlToken, {
        schema_version: '1.0', request_id: status.request_id,
        idempotency_key: makeKey('cancel-deletion'),
      })
      setStatus(result.status)
      sessionStorage.removeItem(CONTROL_KEY)
      setControlToken('')
      setPhase('cancelled')
    } catch {
      setPhase('status')
      setMessage('取消失败；系统已重新读取状态。进入清除后将不能取消。')
      await loadStatus()
    }
  }

  const retry = async () => {
    setPhase('loading')
    try {
      setStatus(await accountApi.retryDeletion(controlToken, {
        schema_version: '1.0', request_id: status.request_id,
        idempotency_key: makeKey('retry-deletion'),
      }))
      setPhase('status')
    } catch {
      setPhase('status')
      setMessage('重试未能完成；账号继续保持不可用，请保留本页面状态。')
    }
  }

  const finishPostErasureMaintenance = async () => {
    if (!status?.erasure_workflow_id || !status?.erasure_checkpoint) return
    setPhase('loading')
    setMessage('正在使旧恢复点失效并创建删除后恢复基线…')
    try {
      await dataControlApi.finalizeErasure({
        workflowId: status.erasure_workflow_id,
        checkpoint: status.erasure_checkpoint,
        clearLocalSession: true,
      })
      setPhase('status')
      setMessage('删除后恢复基线已验证；正在确认最终账号状态。')
      await loadStatus()
    } catch {
      setPhase('status')
      setMessage('个人数据已进入不可用状态，但删除后恢复基线尚未完成；请重试或重启本地 App。')
    }
  }

  const finish = () => {
    sessionStorage.removeItem(CONTROL_KEY)
    setControlToken('')
    navigate('/login')
  }

  if (!user && !controlToken && phase !== 'cancelled') {
    return <main className="deletion-page"><section className="surface deletion-card"><ShieldAlert /><h1>需要登录或删除控制令牌</h1><p>删除请求会撤销普通会话；刷新后仅使用本次浏览器会话中的删除控制令牌查看进度。</p><button className="button button--primary" onClick={() => navigate('/login')}>前往登录</button></section></main>
  }

  return (
    <main className="deletion-page">
      <section className="surface deletion-card" aria-live="polite">
        <button className="deletion-back" type="button" onClick={() => navigate('/settings')} disabled={!user}><ArrowLeft size={16} />返回设置</button>
        <p className="eyebrow">危险操作</p>
        <h1>永久删除账号</h1>
        {phase === 'idle' && <><p>此操作将删除学习数据、文件、会话和身份信息。全局知识与策略不属于个人数据，不会删除。</p><button className="button button--danger" onClick={createPreview}>生成删除清单</button></>}
        {phase === 'loading' && <p role="status">正在安全处理，请勿重复提交…</p>}
        {phase === 'confirm' && preview && <form className="deletion-form" onSubmit={submitDeletion}><div className="deletion-summary"><strong>删除清单</strong><span>{Object.values(preview.counts_by_owner).reduce((sum, value) => sum + value, 0)} 条记录</span><span>{preview.file_count} 个文件</span><span>{preview.pending_task_count} 个待处理任务</span></div>{preview.blocking_issues.length > 0 && <p className="inline-error" role="alert">范围存在阻断项，不能继续删除。</p>}<label>当前密码<input type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} required /></label><label>输入确认短语：<strong>{CONFIRMATION}</strong><input value={confirmation} onChange={(event) => setConfirmation(event.target.value)} required /></label><p className="deletion-warning"><AlertTriangle size={18} />提交后普通会话会立即撤销。24 小时等待期内可取消；进入清除后不可取消。</p><button className="button button--danger" disabled={confirmation !== CONFIRMATION || preview.blocking_issues.length > 0}>确认进入删除等待期</button></form>}
        {phase === 'status' && status && <div className="deletion-status"><strong>当前状态：{status.lifecycle}</strong><p>计划执行时间：{new Date(status.purge_due_at).toLocaleString('zh-CN')}</p><p>关闭本地 App 会延迟本地清除，重启后会自动继续。</p>{status.lifecycle === 'deletion_pending' && <button className="button button--secondary" onClick={cancel} disabled={!status.cancellable}>取消删除</button>}{status.requires_post_erasure_maintenance && <><p>个人数据已清除，但旧恢复点失效和删除后恢复基线仍待完成；完成前不会显示“已删除”。</p><button className="button button--danger" onClick={finishPostErasureMaintenance}>完成防复活维护</button></>}{status.lifecycle === 'deletion_blocked' && <button className="button button--danger" onClick={retry}>重试安全清除</button>}{status.lifecycle === 'deleted' && <><p>账号及个人数据已清除。完成确认前，刷新仍会保留这份结果。</p><button className="button button--primary" onClick={finish}>完成并清除本地状态</button></>}</div>}
        {phase === 'cancelled' && <div className="deletion-status"><strong>删除已取消</strong><p>旧会话仍保持撤销。请重新登录继续使用。</p><button className="button button--primary" onClick={() => navigate('/login')}>重新登录</button></div>}
        {message && <p className="inline-error" role="alert">{message}</p>}
      </section>
    </main>
  )
}
