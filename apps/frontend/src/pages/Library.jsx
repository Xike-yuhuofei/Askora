import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  BookOpen,
  ChevronLeft,
  ChevronRight,
  FileText,
  FolderOpen,
  Network,
  RefreshCw,
  Trash2,
  Upload,
} from 'lucide-react'
import * as documentApi from '../api/documents'
import * as workspaceApi from '../api/workspace'
import SourceStatus from '../components/SourceStatus'
import './Library.css'

const processingLabels = {
  pending: '等待处理',
  processing: '正在处理',
  completed: '处理完成',
  failed: '处理失败',
  rejected: '已拒绝',
  quarantined: '已隔离',
}

const knowledgeLabels = {
  NOT_MODELED: '尚未建模',
  CANDIDATES: '待审核候选',
  PUBLISHED: '已发布',
  LEGACY_COMPATIBILITY: '正在升级',
}

const nodeStatusLabels = {
  candidate: '候选',
  verified: '已验证',
  published: '已发布',
  rejected: '已拒绝',
  superseded: '已替代',
}

const knowledgeKindLabels = {
  concept: '概念',
  fact: '事实',
  principle: '原理',
  procedure: '步骤',
  method: '方法',
  representation: '表征',
  skill: '技能',
}

const relationStrengthLabels = {
  hard: '必要',
  soft: '建议',
  contextual: '情境相关',
}

const provenanceLabels = {
  source_explicit: '原文明确表述',
  system_inferred: '系统推断',
  human_curated: '人工整理',
}

const processingOptions = [
  ['', '全部状态'],
  ['pending', '等待处理'],
  ['processing', '正在处理'],
  ['completed', '处理完成'],
  ['failed', '处理失败'],
  ['rejected', '已拒绝'],
  ['quarantined', '已隔离'],
]

function formatBytes(value) {
  if (!Number.isFinite(value)) return '大小未知'
  if (value < 1024) return `${value} B`
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`
  return `${(value / 1024 / 1024).toFixed(1)} MB`
}

function formatDate(value) {
  if (!value) return '时间未知'
  return new Intl.DateTimeFormat('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

function responseMessage(error, fallback) {
  if (error?.response?.status === 401) return '登录状态已失效，请重新登录。'
  if (error?.response?.status === 413) return '文件超过 50 MB 上限。'
  const detail = error?.response?.data?.detail
  return typeof detail === 'string' && detail.length <= 120 ? detail : fallback
}

function documentStateHint(document) {
  if (!document) return ''
  if (document.processing_status === 'pending') return '文件已安全保存，等待后台处理。'
  if (document.processing_status === 'processing') return '正在解析资料并生成可审计的知识候选。'
  if (document.processing_status === 'failed') return '处理没有完成。请删除后重新上传，原失败信息不会展示到页面。'
  if (document.processing_status === 'quarantined') return '资料触发安全隔离，不会进入检索或知识地图。'
  if (document.processing_status === 'rejected') return '资料未通过内容审核，不会进入知识地图。'
  if (document.knowledge_status === 'LEGACY_COMPATIBILITY') return '旧版资料正在通过持久任务升级，暂不展示过期知识结果。'
  if (document.knowledge_status === 'NOT_MODELED') return '资料已处理，但尚未形成可引用的知识候选。'
  return ''
}

export default function Library() {
  const fileInputRef = useRef(null)
  const pendingSelectionRef = useRef(null)
  const deleteConfirmRef = useRef(null)
  const deleteReturnFocusRef = useRef(null)
  const [library, setLibrary] = useState({ status: 'loading', payload: null, error: '' })
  const [map, setMap] = useState({ status: 'idle', payload: null, error: '' })
  const [selectedDocumentId, setSelectedDocumentId] = useState(null)
  const [selectedNodeRef, setSelectedNodeRef] = useState(null)
  const [selectedSpanRef, setSelectedSpanRef] = useState(null)
  const [statusFilter, setStatusFilter] = useState('')
  const [subjectDraft, setSubjectDraft] = useState('')
  const [subjectFilter, setSubjectFilter] = useState('')
  const [page, setPage] = useState(1)
  const [uploadSubject, setUploadSubject] = useState('')
  const [uploading, setUploading] = useState(false)
  const [actionMessage, setActionMessage] = useState('')
  const [actionError, setActionError] = useState('')
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [deleting, setDeleting] = useState(false)
  const [mapReloadKey, setMapReloadKey] = useState(0)

  const loadLibrary = useCallback(async ({
    quiet = false,
    status = statusFilter,
    subject = subjectFilter,
    requestedPage = page,
  } = {}) => {
    if (!quiet) setLibrary((current) => ({ ...current, status: 'loading', error: '' }))
    try {
      const payload = await workspaceApi.getLibraryWorkspace({
        status,
        subject,
        page: requestedPage,
        pageSize: 20,
      })
      setLibrary({ status: 'ready', payload, error: '' })
      const documents = payload.data.documents || []
      const pendingSelection = pendingSelectionRef.current
      const pendingExists = documents.some((document) => document.document_id === pendingSelection)
      if (pendingExists) pendingSelectionRef.current = null
      setSelectedDocumentId((current) => {
        const retained = documents.some((document) => document.document_id === current)
        return pendingExists ? pendingSelection : retained ? current : documents[0]?.document_id || null
      })
    } catch (error) {
      const unauthorized = error?.response?.status === 401
      if (quiet && !unauthorized) {
        setActionError(responseMessage(error, '资料状态自动刷新暂时失败，请手动重试。'))
        return
      }
      setLibrary({
        status: unauthorized ? 'unauthorized' : 'error',
        payload: null,
        error: responseMessage(error, '资料库暂时无法读取。'),
      })
    }
  }, [page, statusFilter, subjectFilter])

  useEffect(() => {
    loadLibrary()
  }, [loadLibrary])

  const documents = library.payload?.data?.documents || []
  const selectedDocument = useMemo(
    () => documents.find((document) => document.document_id === selectedDocumentId) || null,
    [documents, selectedDocumentId],
  )
  const hasActiveProcessing = documents.some((document) =>
    ['pending', 'processing'].includes(document.processing_status)
    || document.knowledge_status === 'LEGACY_COMPATIBILITY')

  useEffect(() => {
    if (library.status !== 'ready' || !hasActiveProcessing) return undefined
    const timer = window.setTimeout(() => loadLibrary({ quiet: true }), 1500)
    return () => window.clearTimeout(timer)
  }, [hasActiveProcessing, library.status, loadLibrary])

  useEffect(() => {
    if (!selectedDocumentId) {
      setMap({ status: 'idle', payload: null, error: '' })
      return undefined
    }
    let active = true
    setMap({ status: 'loading', payload: null, error: '' })
    workspaceApi.getKnowledgeMap(selectedDocumentId)
      .then((payload) => {
        if (!active) return
        setMap({ status: 'ready', payload, error: '' })
        setSelectedNodeRef(payload.data.nodes?.[0]?.knowledge_unit_ref || null)
      })
      .catch((error) => {
        if (!active) return
        setMap({
          status: 'error',
          payload: null,
          error: responseMessage(error, '这份资料的知识地图暂时无法读取。'),
        })
      })
    return () => { active = false }
  }, [
    mapReloadKey,
    selectedDocument?.current_revision_ref,
    selectedDocument?.knowledge_status,
    selectedDocument?.processing_status,
    selectedDocumentId,
  ])
  const nodes = map.payload?.data?.nodes || []
  const edges = map.payload?.data?.edges || []
  const sourceSpans = map.payload?.data?.source_spans || []
  const selectedNode = nodes.find((node) => node.knowledge_unit_ref === selectedNodeRef) || null
  const relatedSpanRefs = selectedNode?.evidence_span_refs || []
  const relatedSpans = sourceSpans.filter((span) => relatedSpanRefs.includes(span.source_span_ref))
  const selectedSpan = relatedSpans.find((span) => span.source_span_ref === selectedSpanRef)
    || relatedSpans[0]
    || null

  useEffect(() => {
    setSelectedSpanRef(selectedNode?.evidence_span_refs?.[0] || null)
  }, [selectedNodeRef, selectedNode])

  useEffect(() => {
    if (deleteTarget) {
      deleteConfirmRef.current?.focus()
    } else if (deleteReturnFocusRef.current) {
      deleteReturnFocusRef.current.focus()
      deleteReturnFocusRef.current = null
    }
  }, [deleteTarget])

  const closeDeleteConfirmation = () => {
    setDeleteTarget(null)
  }

  const submitSubjectFilter = (event) => {
    event.preventDefault()
    setPage(1)
    setSubjectFilter(subjectDraft.trim())
  }

  const uploadFile = async (event) => {
    const file = event.target.files?.[0]
    if (!file || uploading) return
    setUploading(true)
    setActionError('')
    setActionMessage('')
    try {
      const result = await documentApi.uploadDocument(file, uploadSubject)
      pendingSelectionRef.current = result.document_id
      setActionMessage('资料已安全保存，后台处理会在页面中自动更新。')
      setUploadSubject('')
      setStatusFilter('')
      setSubjectDraft('')
      setSubjectFilter('')
      setPage(1)
      await loadLibrary({ quiet: true, status: '', subject: '', requestedPage: 1 })
    } catch (error) {
      setActionError(responseMessage(error, '上传失败，请检查文件格式后重试。'))
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const confirmDelete = async () => {
    if (!deleteTarget || deleting) return
    setDeleting(true)
    setActionError('')
    try {
      await documentApi.deleteDocument(deleteTarget.document_id)
      setActionMessage(`已删除“${deleteTarget.title}”。`)
      setDeleteTarget(null)
      if (selectedDocumentId === deleteTarget.document_id) setSelectedDocumentId(null)
      await loadLibrary({ quiet: true })
    } catch (error) {
      setActionError(responseMessage(error, '删除失败，请稍后重试。'))
    } finally {
      setDeleting(false)
    }
  }

  if (library.status === 'loading' && !library.payload) {
    return (
      <div className="page-state" role="status" aria-live="polite">
        <div className="spinner" />
        <p>正在读取你的资料库…</p>
      </div>
    )
  }

  if (library.status === 'error' || library.status === 'unauthorized') {
    return (
      <div className="page-state page-state--error" role="alert">
        <FolderOpen size={28} />
        <h1>资料库</h1>
        <p>{library.error}</p>
        <button type="button" className="button button--secondary" onClick={() => loadLibrary()}>
          <RefreshCw size={16} />
          重试
        </button>
      </div>
    )
  }

  const total = library.payload?.data?.total || 0
  const totalPages = Math.max(1, Math.ceil(total / 20))

  return (
    <div className="library-page page-stack">
      <header className="page-header page-header--split library-header">
        <div>
          <p className="eyebrow">Canonical 资料投影</p>
          <h1>资料库</h1>
          <p>导入私人学习资料，查看可追溯的知识候选与原文依据。</p>
        </div>
        <div className="library-upload">
          <label>
            <span>学科（可选）</span>
            <input
              value={uploadSubject}
              onChange={(event) => setUploadSubject(event.target.value)}
              maxLength={50}
              placeholder="例如：数学"
              disabled={uploading}
            />
          </label>
          <input
            ref={fileInputRef}
            className="visually-hidden"
            type="file"
            accept=".md,.txt,.pdf,.docx,.epub"
            onChange={uploadFile}
            aria-label="选择要上传的资料"
          />
          <button
            type="button"
            className="button button--primary"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
          >
            <Upload size={16} />
            {uploading ? '正在上传…' : '导入资料'}
          </button>
        </div>
      </header>

      <div className="library-announcer" aria-live="polite" aria-atomic="true">
        {actionMessage && <p className="inline-notice">{actionMessage}</p>}
        {actionError && <p className="inline-error" role="alert">{actionError}</p>}
        {hasActiveProcessing && <p className="inline-notice">后台处理进行中，资料状态会自动刷新。</p>}
      </div>

      {deleteTarget && (
        <section
          className="delete-confirmation"
          role="alertdialog"
          aria-labelledby="delete-title"
          onKeyDown={(event) => { if (event.key === 'Escape') closeDeleteConfirmation() }}
        >
          <div>
            <strong id="delete-title">确认删除“{deleteTarget.title}”？</strong>
            <p>资料会从当前资料库移除，知识地图也将不可访问。</p>
          </div>
          <div>
            <button type="button" className="button button--ghost" onClick={closeDeleteConfirmation} disabled={deleting}>
              取消
            </button>
            <button ref={deleteConfirmRef} type="button" className="button button--danger" onClick={confirmDelete} disabled={deleting}>
              {deleting ? '正在删除…' : '确认删除'}
            </button>
          </div>
        </section>
      )}

      <section className="library-filters" aria-label="资料筛选">
        <label>
          <span>处理状态</span>
          <select value={statusFilter} onChange={(event) => { setPage(1); setStatusFilter(event.target.value) }}>
            {processingOptions.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </label>
        <form onSubmit={submitSubjectFilter}>
          <label>
            <span>学科</span>
            <input value={subjectDraft} onChange={(event) => setSubjectDraft(event.target.value)} maxLength={100} placeholder="精确筛选学科" />
          </label>
          <button type="submit" className="button button--secondary">应用筛选</button>
        </form>
        <span className="library-count">共 {total} 份资料</span>
      </section>

      <div className="library-workspace">
        <section className="surface library-documents" aria-labelledby="documents-title">
          <div className="section-heading section-heading--compact">
            <div>
              <p className="eyebrow">资料范围</p>
              <h2 id="documents-title">我的资料</h2>
            </div>
            <FileText size={18} />
          </div>
          {documents.length ? (
            <ul className="document-list">
              {documents.map((document) => (
                <li key={document.document_id} className={document.document_id === selectedDocumentId ? 'is-selected' : ''}>
                  <button
                    type="button"
                    className="document-select"
                    onClick={() => setSelectedDocumentId(document.document_id)}
                    aria-pressed={document.document_id === selectedDocumentId}
                  >
                    <span className="document-title">{document.title}</span>
                    <span>{document.subject || '未标注学科'} · {formatBytes(document.file_size_bytes)}</span>
                    <span className="document-statuses">
                      <span className={`status-pill status-pill--document-${document.processing_status}`}>
                        {processingLabels[document.processing_status] || document.processing_status}
                      </span>
                      <span className="status-pill status-pill--neutral">
                        {knowledgeLabels[document.knowledge_status] || document.knowledge_status}
                      </span>
                    </span>
                    <small>{formatDate(document.updated_at)}</small>
                  </button>
                  <button
                    type="button"
                    className="document-delete"
                    aria-label={`删除资料 ${document.title}`}
                    onClick={(event) => {
                      deleteReturnFocusRef.current = event.currentTarget
                      setDeleteTarget(document)
                    }}
                  >
                    <Trash2 size={15} />
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <div className="library-empty">
              <BookOpen size={24} />
              <strong>还没有符合条件的资料</strong>
              <p>可导入 Markdown、TXT、PDF、DOCX 或 EPUB。系统不会凭空补造资料事实。</p>
            </div>
          )}
          {totalPages > 1 && (
            <nav className="pagination" aria-label="资料分页">
              <button type="button" className="button button--ghost" onClick={() => setPage((value) => value - 1)} disabled={page === 1} aria-label="上一页">
                <ChevronLeft size={16} />
              </button>
              <span>{page} / {totalPages}</span>
              <button type="button" className="button button--ghost" onClick={() => setPage((value) => value + 1)} disabled={page === totalPages} aria-label="下一页">
                <ChevronRight size={16} />
              </button>
            </nav>
          )}
        </section>

        <section className="surface knowledge-map" aria-labelledby="map-title">
          <div className="section-heading section-heading--compact">
            <div>
              <p className="eyebrow">范围化视图</p>
              <h2 id="map-title">知识地图</h2>
            </div>
            <Network size={18} />
          </div>
          {!selectedDocument ? (
            <div className="library-empty"><p>选择一份资料后查看知识候选。</p></div>
          ) : map.status === 'loading' ? (
            <div className="inline-state" role="status"><div className="spinner" />正在读取知识地图…</div>
          ) : map.status === 'error' ? (
            <div className="inline-state inline-state--error" role="alert">
              <p>{map.error}</p>
              <button type="button" className="button button--secondary" onClick={() => setMapReloadKey((value) => value + 1)}>重试</button>
            </div>
          ) : nodes.length ? (
            <>
              <div className="map-scope">
                <strong>{selectedDocument.title}</strong>
                <span>{nodes.length} 个知识候选 · {edges.length} 条有依据的关系</span>
              </div>
              <ul className="knowledge-node-list">
                {nodes.map((node) => (
                  <li key={node.knowledge_unit_ref}>
                    <button
                      type="button"
                      onClick={() => setSelectedNodeRef(node.knowledge_unit_ref)}
                      aria-pressed={node.knowledge_unit_ref === selectedNodeRef}
                      className={node.knowledge_unit_ref === selectedNodeRef ? 'is-selected' : ''}
                    >
                      <span className="knowledge-node__dot" aria-hidden="true" />
                      <span>
                        <strong>{node.canonical_name}</strong>
                        <small>{knowledgeKindLabels[node.kind] || node.kind} · {nodeStatusLabels[node.status] || node.status}</small>
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
              <section className="relation-summary" aria-labelledby="relations-title">
                <h3 id="relations-title">关系</h3>
                {edges.length ? (
                  <ul>
                    {edges.map((edge) => {
                      const from = nodes.find((node) => node.knowledge_unit_ref === edge.prerequisite_ref)
                      const to = nodes.find((node) => node.knowledge_unit_ref === edge.target_ref)
                      return <li key={edge.relation_ref}>{from?.canonical_name || '未知节点'} → {to?.canonical_name || '未知节点'}（{relationStrengthLabels[edge.strength] || edge.strength}）</li>
                    })}
                  </ul>
                ) : (
                  <p>尚无可核验的知识关系。页面不会用装饰性连线冒充先修关系。</p>
                )}
              </section>
            </>
          ) : (
            <div className="library-empty">
              <Network size={24} />
              <strong>暂无可展示的知识候选</strong>
              <p>{documentStateHint(selectedDocument) || '当前资料没有带原文依据的知识节点。'}</p>
            </div>
          )}
        </section>

        <aside className="surface source-inspector" aria-labelledby="inspector-title">
          <div className="section-heading section-heading--compact">
            <div>
              <p className="eyebrow">可追溯证据</p>
              <h2 id="inspector-title">原文检查器</h2>
            </div>
          </div>
          {selectedNode ? (
            <>
              <div className="inspector-node">
                <span className="status-pill status-pill--neutral">{nodeStatusLabels[selectedNode.status] || selectedNode.status}</span>
                <h3>{selectedNode.canonical_name}</h3>
                <p>{selectedNode.description}</p>
                <dl>
                  <div><dt>来源</dt><dd>{provenanceLabels[selectedNode.provenance_type] || selectedNode.provenance_type}</dd></div>
                  <div><dt>置信度</dt><dd>{selectedNode.confidence == null ? '未知，未伪造分数' : `${Math.round(selectedNode.confidence * 100)}%`}</dd></div>
                  <div><dt>学习证据</dt><dd>{selectedNode.learner_evidence_summary ? '已有摘要' : '本切片不适用'}</dd></div>
                </dl>
              </div>
              <div className="span-tabs" aria-label="原文证据位置">
                {relatedSpans.map((span, index) => (
                  <button
                    key={span.source_span_ref}
                    type="button"
                    className={span.source_span_ref === selectedSpan?.source_span_ref ? 'is-selected' : ''}
                    onClick={() => setSelectedSpanRef(span.source_span_ref)}
                  >
                    依据 {index + 1}
                  </button>
                ))}
              </div>
              {selectedSpan ? (
                <figure className="source-span">
                  <figcaption>
                    {selectedSpan.chapter || '未标注章节'}
                    {selectedSpan.page ? ` · 第 ${selectedSpan.page} 页` : ''}
                    {selectedSpan.start_offset != null ? ` · 字符 ${selectedSpan.start_offset}–${selectedSpan.end_offset}` : ''}
                  </figcaption>
                  <blockquote>{selectedSpan.excerpt}</blockquote>
                </figure>
              ) : <p className="empty-copy">该节点没有可向学习者展示的原文片段。</p>}
              <details className="audit-details">
                <summary>审计引用</summary>
                <code>{selectedNode.knowledge_unit_ref}</code>
                {selectedSpan && <code>{selectedSpan.source_span_ref}</code>}
                <code>{map.payload.data.scope.graph_version}</code>
              </details>
            </>
          ) : (
            <p className="empty-copy">选择知识候选后，这里会显示原文片段与稳定引用，不展示隐藏评分材料。</p>
          )}
          {map.payload?.source_status && <SourceStatus items={map.payload.source_status} />}
        </aside>
      </div>
    </div>
  )
}
