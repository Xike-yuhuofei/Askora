import { useCallback, useEffect, useRef, useState } from 'react'
import { AlertTriangle, CheckCircle2, ChevronDown, RefreshCw, ShieldCheck } from 'lucide-react'
import { executeRecoveryAction, listRecoveryIssues } from '../api/recovery'
import { normalizeApiError } from '../api/client'
import { useNavigate } from '../router'
import './RecoveryCenter.css'

const safetyCopy = {
  preserved: '数据已保留',
  preserved_but_unavailable: '数据记录已保留，但当前不可用',
  at_risk: '数据完整性需要确认',
  unknown: '暂时无法确认数据状态',
}

const duplicateCopy = {
  none: '此动作不会产生重复副作用',
  prevented_by_idempotency: '重复提交会返回同一结果，不会创建第二份任务',
  requires_confirmation: '无法证明可安全重放，仅提供诊断',
  not_applicable: '此动作没有服务端副作用',
}

export default function RecoveryCenter() {
  const navigate = useNavigate()
  const [state, setState] = useState({ status: 'loading', data: null, error: null })
  const [running, setRunning] = useState(null)
  const [result, setResult] = useState('')
  const resultRef = useRef(null)

  const load = useCallback(async () => {
    setState((current) => ({ ...current, status: 'loading', error: null }))
    try {
      const data = await listRecoveryIssues()
      setState({ status: 'ready', data, error: null })
    } catch (error) {
      setState({ status: 'error', data: null, error: normalizeApiError(error) })
    }
  }, [])

  useEffect(() => { load() }, [load])

  const runAction = async (issue, action) => {
    if (!action.enabled || running) return
    if (action.kind === 'navigate') {
      navigate(action.route)
      return
    }
    if (action.kind === 'wait') return
    if (action.kind === 'client') {
      const diagnostic = JSON.stringify({
        code: issue.code,
        correlation_id: issue.correlation_id,
        resource_ref: issue.resource_ref,
        updated_at: issue.updated_at,
      }, null, 2)
      await navigator.clipboard?.writeText(diagnostic)
      setResult('已复制脱敏诊断')
      resultRef.current?.focus()
      return
    }
    setRunning(`${issue.issue_ref}:${action.action_code}`)
    setResult('')
    try {
      const response = await executeRecoveryAction({
        schema_version: '1.0',
        issue_ref: issue.issue_ref,
        expected_issue_version: issue.issue_version,
        action_code: action.action_code,
        idempotency_key: globalThis.crypto?.randomUUID?.() || `recovery-${Date.now()}`,
      })
      setResult(response.message)
      await load()
      window.dispatchEvent(new CustomEvent('app:recovery-refresh'))
    } catch (error) {
      const normalized = normalizeApiError(error)
      setResult(`${normalized.message}（${normalized.code}）`)
    } finally {
      setRunning(null)
      window.setTimeout(() => resultRef.current?.focus(), 0)
    }
  }

  return (
    <div className="recovery-page page-stack">
      <header className="page-header recovery-header">
        <div>
          <p className="eyebrow">设置 · 本地恢复</p>
          <h1>错误恢复中心</h1>
          <p>这里汇总可安全处理的问题。恢复问题不等于学习失败。</p>
        </div>
        <button type="button" className="button button--secondary" onClick={load} disabled={state.status === 'loading'}>
          <RefreshCw size={16} aria-hidden="true" />
          重新检查
        </button>
      </header>

      <p ref={resultRef} className="recovery-result" role="status" tabIndex="-1">{result}</p>

      {state.status === 'loading' && <div className="surface inline-state" role="status"><div className="spinner" /> 正在检查可恢复问题…</div>}
      {state.status === 'error' && (
        <section className="surface recovery-load-error" role="alert">
          <AlertTriangle size={20} />
          <div><h2>暂时无法读取恢复状态</h2><p>{state.error.message}（{state.error.code}）</p></div>
        </section>
      )}
      {state.status === 'ready' && state.data.issues.length === 0 && (
        <section className="surface recovery-empty">
          <CheckCircle2 size={28} aria-hidden="true" />
          <h2>目前没有待处理问题</h2>
          <p>最近检查：{new Date(state.data.generated_at).toLocaleString('zh-CN')}。这表示当前未检测到已知问题，不代表绝对安全。</p>
        </section>
      )}
      {state.status === 'ready' && state.data.issues.length > 0 && (
        <div className="recovery-list">
          {state.data.issues.map((issue) => (
            <article className={`surface recovery-card recovery-card--${issue.severity}`} key={issue.issue_ref}>
              <div className="recovery-card__title">
                <AlertTriangle size={20} aria-hidden="true" />
                <div><h2>{issue.title}</h2><p>{issue.summary}</p></div>
              </div>
              <div className="recovery-facts">
                <div><span>发生了什么</span><strong>{issue.code}</strong></div>
                <div><span>数据是否安全</span><strong><ShieldCheck size={15} /> {safetyCopy[issue.data_safety]}</strong></div>
                <div><span>重试说明</span><strong>{duplicateCopy[issue.duplicate_risk]}</strong></div>
                <div><span>现在能做什么</span><strong>{issue.actions.length ? '选择下方允许的动作' : '当前只保留诊断'}</strong></div>
              </div>
              {issue.next_eligible_at && <p className="recovery-wait">下次可尝试：{new Date(issue.next_eligible_at).toLocaleString('zh-CN')}</p>}
              {issue.retry_budget !== null && issue.retry_budget !== undefined && (
                <p className="recovery-wait">已尝试 {issue.attempt_count} 次；安全预算上限 {issue.retry_budget} 次。</p>
              )}
              <div className="recovery-actions">
                {issue.actions.map((action) => {
                  const actionKey = `${issue.issue_ref}:${action.action_code}`
                  return <div className="recovery-action" key={action.action_code}>
                    <button
                      type="button"
                      className="button button--secondary"
                      disabled={!action.enabled || running === actionKey || action.kind === 'wait'}
                      onClick={() => runAction(issue, action)}
                    >
                      {running === actionKey ? '正在执行…' : action.label}
                    </button>
                    {!action.enabled && action.disabled_reason_code && (
                      <span>原因：{action.disabled_reason_code}</span>
                    )}
                  </div>
                })}
              </div>
              <details className="recovery-details">
                <summary><ChevronDown size={15} /> 技术详情</summary>
                <dl><div><dt>问题编号</dt><dd>{issue.issue_ref}</dd></div><div><dt>关联编号</dt><dd>{issue.correlation_id || '无'}</dd></div><div><dt>资源引用</dt><dd>{issue.resource_ref || '无'}</dd></div></dl>
              </details>
            </article>
          ))}
        </div>
      )}
    </div>
  )
}
