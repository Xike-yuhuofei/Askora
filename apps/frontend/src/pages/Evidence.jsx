import { useEffect, useState } from 'react'
import { RefreshCw, ShieldCheck } from 'lucide-react'
import * as workspaceApi from '../api/workspace'
import SourceStatus from '../components/SourceStatus'
import './Goals.css'
import './Evidence.css'

function probability(value) { return value == null ? '证据不足' : `${Math.round(value * 100)}%（估计）` }
function count(value) { return value == null ? '暂无可靠记录' : `${value} 次` }
function decimal(value) { return value == null ? '未知' : Number(value).toFixed(2) }

export default function Evidence() {
  const [state, setState] = useState({ status: 'loading', payload: null, error: '' })
  const load = async () => {
    setState((current) => ({ ...current, status: 'loading', error: '' }))
    try { setState({ status: 'ready', payload: await workspaceApi.getEvidenceWorkspace(), error: '' }) }
    catch (error) { const unauthorized = error.response?.status === 401; setState({ status: unauthorized ? 'unauthorized' : 'error', payload: null, error: unauthorized ? '登录状态已失效，请重新登录。' : '学习证据暂时无法读取。' }) }
  }
  useEffect(() => { load() }, [])

  if (state.status === 'loading') return <div className="page-state" role="status"><div className="spinner" /><p>正在读取学习证据…</p></div>
  if (state.status === 'error' || state.status === 'unauthorized') return <div className="page-state page-state--error" role="alert"><h1>学习证据</h1><p>{state.error}</p><button type="button" className="button button--secondary" onClick={load}><RefreshCw size={16} />重试</button></div>

  const { data, source_status: sourceStatus } = state.payload
  return (
    <div className="product-view page-stack">
      <header className="page-header page-header--split"><div><p className="eyebrow">学习者模型</p><h1>学习证据</h1><p>这里只显示学习者模型已经接纳的证据；概率是估计，不是“已掌握”判定。</p></div><span className={`status-pill status-pill--${data.view_state.toLowerCase()}`}>{data.knowledge_units_assessed} 个知识单元</span></header>
      {data.entries.length ? <section className="surface" aria-labelledby="evidence-list-title"><div className="section-heading"><div><p className="eyebrow">已接纳证据</p><h2 id="evidence-list-title">证据概览</h2></div><ShieldCheck size={20} /></div><ul className="evidence-list">{data.entries.map((entry) => <li key={entry.knowledge_unit_ref}><div className="evidence-list__heading"><div><h3>{entry.label || '知识单元名称暂不可用'}</h3><p>{entry.algorithm_id ? `估计方法：${entry.algorithm_id} · ${entry.algorithm_version || '版本未知'}` : '估计方法暂不可用'}</p></div><div className="evidence-estimate"><span>能力估计</span><strong>{probability(entry.competence_probability)}</strong><small>置信度 {decimal(entry.confidence)}</small></div></div><dl className="evidence-counts"><div><dt>独立成功</dt><dd>{count(entry.independent_success_count)}</dd></div><div><dt>延迟回忆</dt><dd>{count(entry.delayed_recall_evidence_count)}</dd></div><div><dt>迁移证据</dt><dd>{count(entry.transfer_evidence_count)}</dd></div><div><dt>全部证据</dt><dd>{count(entry.evidence_count)}</dd></div><div><dt>有效证据权重</dt><dd>{decimal(entry.effective_evidence_weight)}</dd></div><div><dt>当前判断标签</dt><dd>{entry.product_label || '未发布'}</dd></div></dl>{entry.active_misconception_ids?.length > 0 && <p className="data-note">存在 {entry.active_misconception_ids.length} 条活跃误解假设；本页面不暴露内部标识或自行解释。</p>}</li>)}</ul></section> : <section className="surface empty-panel"><ShieldCheck size={24} /><h2>还没有足够的学习证据</h2><p>暂无记录不等于能力为 0，也不表示已经掌握。完成可评估的独立学习活动后，这里才会出现证据。</p></section>}
      <SourceStatus items={sourceStatus} />
    </div>
  )
}
