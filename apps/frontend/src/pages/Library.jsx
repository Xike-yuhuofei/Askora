import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  Archive,
  ArrowRight,
  BookOpen,
  ChevronLeft,
  ChevronRight,
  FolderOpen,
  GraduationCap,
  Network,
  RefreshCw,
  RotateCcw,
  Search,
  Upload,
  X,
} from 'lucide-react'
import * as documentApi from '../api/documents'
import * as workspaceApi from '../api/workspace'
import Button from '../components/Button'
import MaterialDestination from '../components/MaterialDestination'
import './Library.css'

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

const processingOptions = [
  ['', '全部'],
  ['pending', '等待处理'],
  ['processing', '正在处理'],
  ['completed', '处理完成'],
  ['failed', '处理失败'],
  ['rejected', '已拒绝'],
  ['quarantined', '已隔离'],
]

const sortOptions = [
  ['created_desc', '最近导入'],
  ['updated_desc', '最近更新'],
  ['title_asc', '名称 A-Z'],
  ['title_desc', '名称 Z-A'],
]

const knowledgeBlockedStatuses = new Set(['failed', 'rejected', 'quarantined'])

const processingUserFacing = {
  pending: { label: '等待处理', tone: 'neutral' },
  processing: { label: '处理中…', tone: 'neutral' },
  completed: { label: '可学习', tone: 'success' },
  failed: { label: '处理失败', tone: 'danger' },
  rejected: { label: '处理失败', tone: 'danger' },
  quarantined: { label: '已归档', tone: 'neutral' },
}

const mediaTypeLabels = {
  'text/markdown': 'Markdown',
  'text/plain': 'TXT',
  'application/pdf': 'PDF',
  'application/epub+zip': 'EPUB',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'DOCX',
}

const mediaShortLabels = {
  'text/markdown': 'MD',
  'text/plain': 'TXT',
  'application/pdf': 'PDF',
  'application/epub+zip': 'EPUB',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'DOCX',
}

const safetyReasonLabels = {
  CONTENT_FILE_SIZE_EXCEEDED: '文件超过安全大小限制',
  CONTENT_TYPE_MISMATCH: '文件内容与扩展名不一致',
  CONTENT_UNSUPPORTED_EXTENSION: '文件格式不受支持',
  EPUB_ARCHIVE_INVALID: '电子书压缩结构损坏',
  EPUB_MIMETYPE_INVALID: '电子书格式标识无效',
  EPUB_CONTAINER_INVALID: '电子书目录结构无效',
  EPUB_ENTRY_PATH_UNSAFE: '电子书包包含不安全的文件路径',
  EPUB_ENTRY_SYMLINK: '电子书包包含不安全的符号链接',
  EPUB_ENTRY_ENCRYPTED: '电子书包含无法安全检查的加密内容',
  EPUB_ENTRY_COUNT_EXCEEDED: '电子书包含过多文件',
  EPUB_ENTRY_SIZE_EXCEEDED: '电子书中的单个文件过大',
  EPUB_TOTAL_UNCOMPRESSED_SIZE_EXCEEDED: '电子书解压后的总体积过大',
  EPUB_COMPRESSION_RATIO_EXCEEDED: '电子书压缩比超过安全限制',
  EPUB_NESTED_ARCHIVE_BLOCKED: '电子书包含不允许的嵌套压缩包',
  EPUB_EXTERNAL_ENTITY_BLOCKED: '电子书包含不安全的外部实体',
  EPUB_ENTITY_DECLARATION_BLOCKED: '电子书包含不安全的实体声明',
}

function formatBytes(value) {
  if (!Number.isFinite(value)) return ''
  if (value < 1024) return `${value} B`
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`
  return `${(value / 1024 / 1024).toFixed(1)} MB`
}

function formatDate(value) {
  if (!value) return ''
  return new Intl.DateTimeFormat('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

function responseMessage(error, fallback) {
  if (error?.response?.status === 413) return '文件超过 50 MB 上限。'
  const detail = error?.response?.data?.detail
  const structuredMessage = error?.response?.data?.error?.message
  if (typeof structuredMessage === 'string' && structuredMessage.length <= 120) return structuredMessage
  return typeof detail === 'string' && detail.length <= 120 ? detail : fallback
}

function commandKey(prefix) {
  const random = globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random()}`
  return `${prefix}-${random}`
}

function safetyReason(document) {
  return document?.reason_codes
    ?.map((code) => safetyReasonLabels[code])
    .find(Boolean) || ''
}

function documentStateHint(document) {
  if (!document) return ''
  if (document.processing_status === 'pending') return '文件已安全保存，等待后台处理。'
  if (document.processing_status === 'processing') return '正在解析资料并生成可审计的知识候选。'
  if (document.processing_status === 'failed') return '处理没有完成。请删除后重新上传，原失败信息不会展示到页面。'
  if (document.processing_status === 'quarantined') {
    if (document.reason_codes?.includes('CONTENT_REINSPECTION_PENDING')) {
      return '正在使用新版安全策略重新检查；完成前资料继续保持隔离。'
    }
    if (document.reason_codes?.includes('CONTENT_REINSPECTION_FAILED')) {
      return '重新检查任务没有完成，资料继续保持隔离；请重新上传原文件。'
    }
    const reason = safetyReason(document)
    return `${reason ? `${reason}，` : ''}资料已隔离；知识建模未启动，也不会进入检索或知识地图。`
  }
  if (document.processing_status === 'rejected') {
    const reason = safetyReason(document)
    return `${reason ? `${reason}，` : ''}资料未通过文件校验；知识建模未启动。`
  }
  if (document.knowledge_status === 'LEGACY_COMPATIBILITY') return '旧版资料正在通过持久任务升级，暂不展示过期知识结果。'
  if (document.knowledge_status === 'NOT_MODELED') return '资料已处理，但尚未形成可引用的知识候选。'
  return ''
}

function learningStateFromDocument(document) {
  if (!document) return { label: '尚未学习', tone: 'neutral' }
  if (document.processing_status !== 'completed' || knowledgeBlockedStatuses.has(document.processing_status)) {
    return { label: '尚未学习', tone: 'neutral' }
  }
  if (document.knowledge_status === 'NOT_MODELED') return { label: '尚未学习', tone: 'neutral' }
  return { label: '可学习', tone: 'success' }
}

function unifiedCardStatus(document) {
  const proc = document.processing_status
  if (proc === 'pending') return { label: '等待处理', tone: 'warning' }
  if (proc === 'processing') return { label: '正在处理', tone: 'warning' }
  if (proc === 'failed' || proc === 'rejected') return { label: '处理失败', tone: 'danger' }
  if (proc === 'quarantined') return { label: '已归档', tone: 'neutral' }
  if (document.knowledge_status === 'NOT_MODELED') return { label: '尚未建模', tone: 'neutral' }
  if (document.knowledge_status === 'LEGACY_COMPATIBILITY') return { label: '正在升级', tone: 'warning' }
  return { label: '可学习', tone: 'success' }
}

function canReinspectDocument(document) {
  return document.processing_status === 'quarantined'
    && document.reason_codes?.includes('CONTENT_REINSPECTION_AVAILABLE')
}

function readRecoveryTarget() {
  const query = window.location.hash.replace(/^#/, '').split('?')[1] || ''
  const params = new URLSearchParams(query)
  return {
    documentId: params.get('document'),
  }
}

export default function Library() {
  const fileInputRef = useRef(null)
  const recoveryTargetRef = useRef(readRecoveryTarget())
  const pendingSelectionRef = useRef(recoveryTargetRef.current.documentId)
  const lastOpenerRef = useRef(null)
  const modalCloseRef = useRef(null)
  const dragDepthRef = useRef(0)
  const [library, setLibrary] = useState({ status: 'loading', payload: null, error: '' })
  const [map, setMap] = useState({ status: 'idle', payload: null, error: '' })
  const [selectedDocumentId, setSelectedDocumentId] = useState(null)
  const [selectedNodeRef, setSelectedNodeRef] = useState(null)
  const [statusFilter, setStatusFilter] = useState('')
  const [queryDraft, setQueryDraft] = useState('')
  const [queryFilter, setQueryFilter] = useState('')
  const [sort, setSort] = useState('created_desc')
  const [page, setPage] = useState(1)
  const [uploading, setUploading] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const [actionMessage, setActionMessage] = useState('')
  const [actionError, setActionError] = useState('')
  const [checkedIds, setCheckedIds] = useState([])
  const [batchTagId, setBatchTagId] = useState('')
  const [batchCollectionId, setBatchCollectionId] = useState('')
  const [managing, setManaging] = useState(false)
  const [metadataDraft, setMetadataDraft] = useState({ title: '', subject: '', author: '', language: '' })
  const [reinspectingDocumentId, setReinspectingDocumentId] = useState(null)
  const [mapReloadKey, setMapReloadKey] = useState(0)
  const [unassigned, setUnassigned] = useState([])
  const [destination, setDestination] = useState(null)

  const loadLibrary = useCallback(async ({
    quiet = false,
    status = statusFilter,
    query = queryFilter,
    documentId = recoveryTargetRef.current.documentId,
    archived = false,
    requestedSort = sort,
    requestedPage = page,
  } = {}) => {
    if (!quiet) setLibrary((current) => ({ ...current, status: 'loading', error: '' }))
    try {
      const payload = await workspaceApi.getLibraryWorkspace({
        status,
        query,
        documentId,
        archived,
        sort: requestedSort,
        page: requestedPage,
        pageSize: 20,
      })
      setLibrary({ status: 'ready', payload, error: '' })
      try {
        const unassignedPayload = await documentApi.listUnassignedMaterials()
        const items = unassignedPayload?.items || []
        setUnassigned(items)
        setDestination((current) => {
          if (!current) return current
          return items.find((item) => item.document_id === current.document_id) || current
        })
      } catch {
        setUnassigned([])
      }
      const documents = payload.data.documents || []
      const pendingSelection = pendingSelectionRef.current
      const pendingExists = documents.some((document) => document.document_id === pendingSelection)
      if (pendingExists) pendingSelectionRef.current = null
      setSelectedDocumentId((current) => {
        if (pendingExists) return pendingSelection
        const retained = documents.some((document) => document.document_id === current)
        return retained ? current : null
      })
    } catch (error) {
      if (quiet) {
        setActionError(responseMessage(error, '资料状态自动刷新暂时失败，请手动重试。'))
        return
      }
      setLibrary({
        status: 'error',
        payload: null,
        error: responseMessage(error, '资料库暂时无法读取。'),
      })
    }
  }, [page, queryFilter, sort, statusFilter])

  useEffect(() => {
    loadLibrary()
  }, [loadLibrary])

  const documents = library.payload?.data?.documents || []
  const selectedDocument = useMemo(
    () => documents.find((document) => document.document_id === selectedDocumentId) || null,
    [documents, selectedDocumentId],
  )
  const availableTags = library.payload?.data?.available_tags || []
  const availableCollections = library.payload?.data?.available_collections || []
  const hasActiveProcessing = documents.some((document) =>
    ['pending', 'processing'].includes(document.processing_status)
    || document.knowledge_status === 'LEGACY_COMPATIBILITY'
    || document.reason_codes?.includes('CONTENT_REINSPECTION_PENDING'))
    || unassigned.some((item) => ['pending', 'processing'].includes(item.processing_status))

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

  useEffect(() => {
    setMetadataDraft({
      title: selectedDocument?.title || '',
      subject: selectedDocument?.subject || '',
      author: selectedDocument?.author || '',
      language: selectedDocument?.language || '',
    })
  }, [selectedDocumentId])

  const closeModal = useCallback(() => {
    setSelectedDocumentId(null)
    const opener = lastOpenerRef.current
    lastOpenerRef.current = null
    if (opener && document.contains(opener)) opener.focus()
  }, [])

  const openDocument = useCallback((document, opener) => {
    lastOpenerRef.current = opener || null
    setSelectedDocumentId(document.document_id)
  }, [])

  // 弹窗打开时：Esc 关闭、锁定背景滚动、初始焦点落到关闭按钮
  useEffect(() => {
    if (!selectedDocumentId) return undefined
    const onKeyDown = (event) => {
      if (event.key === 'Escape') closeModal()
    }
    document.addEventListener('keydown', onKeyDown)
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    modalCloseRef.current?.focus()
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      document.body.style.overflow = previousOverflow
    }
  }, [selectedDocumentId, closeModal])

  const submitFilters = (event) => {
    event.preventDefault()
    setPage(1)
    setQueryFilter(queryDraft.trim())
  }

  const upload = async (file) => {
    if (!file || uploading) return
    setUploading(true)
    setActionError('')
    setActionMessage('')
    try {
      const result = await documentApi.uploadDocument(file, '')
      pendingSelectionRef.current = result.document_id
      setDestination({
        document_id: result.document_id,
        title: file.name,
        processing_status: result.status || 'pending',
        lifecycle_version: result.lifecycle_version || 1,
      })
      setActionMessage('资料已保存，尚未加入空间。处理完成后选择去向。')
      setStatusFilter('')
      setPage(1)
      setQueryDraft('')
      setQueryFilter('')
      await loadLibrary({ quiet: true, status: '', query: '', requestedPage: 1 })
    } catch (error) {
      setActionError(responseMessage(error, '上传失败，请检查文件格式后重试。'))
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const uploadFile = (event) => {
    upload(event.target.files?.[0])
  }

  const onDragEnter = (event) => {
    if (!event.dataTransfer?.types?.includes('Files')) return
    event.preventDefault()
    dragDepthRef.current += 1
    setDragActive(true)
  }

  const onDragOver = (event) => {
    if (event.dataTransfer?.types?.includes('Files')) event.preventDefault()
  }

  const onDragLeave = () => {
    dragDepthRef.current = Math.max(0, dragDepthRef.current - 1)
    if (dragDepthRef.current === 0) setDragActive(false)
  }

  const onDrop = (event) => {
    if (!event.dataTransfer?.files?.length) return
    event.preventDefault()
    dragDepthRef.current = 0
    setDragActive(false)
    upload(event.dataTransfer.files[0])
  }

  const applyBatch = async (archive) => {
    const selected = documents.filter((document) => checkedIds.includes(document.document_id))
    if (!selected.length || managing) return
    setManaging(true)
    setActionError('')
    try {
      await documentApi.batchOrganizeDocuments({
        document_ids: selected.map((document) => document.document_id),
        expected_versions: Object.fromEntries(selected.map((document) => [document.document_id, document.metadata_version])),
        idempotency_key: commandKey('batch-organize'),
        add_tag_ids: batchTagId ? [batchTagId] : [],
        add_collection_ids: batchCollectionId ? [batchCollectionId] : [],
        archive,
      })
      setCheckedIds([])
      setBatchTagId('')
      setBatchCollectionId('')
      setActionMessage(archive === true ? '所选资料已归档，可在归档视图恢复。' : archive === false ? '所选资料已恢复。' : '所选资料已完成分类。')
      await loadLibrary({ quiet: true })
    } catch (error) {
      setActionError(responseMessage(error, '批量操作失败，请刷新后重试。'))
    } finally {
      setManaging(false)
    }
  }

  const archiveSingle = async (document) => {
    if (!document || managing) return
    setManaging(true)
    setActionError('')
    try {
      await documentApi.batchOrganizeDocuments({
        document_ids: [document.document_id],
        expected_versions: { [document.document_id]: document.metadata_version },
        idempotency_key: commandKey('archive'),
        archive: true,
      })
      setActionMessage('资料已归档，可在归档视图恢复。')
      closeModal()
      await loadLibrary({ quiet: true })
    } catch (error) {
      setActionError(responseMessage(error, '归档失败，请刷新后重试。'))
    } finally {
      setManaging(false)
    }
  }

  const saveMetadata = async (event) => {
    event.preventDefault()
    if (!selectedDocument || managing) return
    setManaging(true)
    setActionError('')
    try {
      await documentApi.updateDocumentMetadata(selectedDocument.document_id, {
        expected_version: selectedDocument.metadata_version,
        idempotency_key: commandKey('update-metadata'),
        display_title: metadataDraft.title.trim(),
        subject: metadataDraft.subject.trim() || null,
        author: metadataDraft.author.trim() || null,
        language: metadataDraft.language.trim() || null,
      })
      setActionMessage('资料信息已保存；原文件与知识 revision 未改变。')
      await loadLibrary({ quiet: true })
    } catch (error) {
      setActionError(responseMessage(error, '资料信息保存失败，请刷新后重试。'))
    } finally {
      setManaging(false)
    }
  }

  const requestReinspection = async (document) => {
    if (!document || reinspectingDocumentId) return
    setReinspectingDocumentId(document.document_id)
    setActionError('')
    setActionMessage('')
    try {
      const result = await documentApi.reinspectDocument(document.document_id)
      setActionMessage(result.message || '已提交新版安全策略重新检查。')
      await loadLibrary({ quiet: true })
    } catch (error) {
      setActionError(responseMessage(error, '重新检查无法提交，请重新上传资料。'))
    } finally {
      setReinspectingDocumentId(null)
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

  if (library.status === 'error') {
    return (
      <div className="page-state page-state--error" role="alert">
        <FolderOpen size={28} />
        <h1>资料库</h1>
        <p>{library.error}</p>
        <Button variant="secondary" onClick={() => loadLibrary()}>
          <RefreshCw size={16} />
          重试
        </Button>
      </div>
    )
  }

  const total = library.payload?.data?.total || 0
  const totalPages = Math.max(1, Math.ceil(total / 20))
  const hasFilters = Boolean(statusFilter || queryFilter)
  const isEmpty = documents.length === 0

  const renderKnowledgeSection = () => {
    if (!selectedDocument) return null
    const isBlocked = knowledgeBlockedStatuses.has(selectedDocument.processing_status)

    if (map.status === 'loading') {
      return <div className="inline-state" role="status"><div className="spinner" />正在读取知识…</div>
    }

    if (map.status === 'error') {
      return (
        <div className="inline-state inline-state--error" role="alert">
          <p>{map.error}</p>
          <Button variant="secondary" onClick={() => setMapReloadKey((value) => value + 1)}>重试</Button>
        </div>
      )
    }

    if (isBlocked || nodes.length === 0) {
      return (
        <div className="ws-empty-state">
          <Network size={24} />
          <strong>{isBlocked ? '资料尚未建模' : '暂无可展示的知识'}</strong>
          <p>{documentStateHint(selectedDocument) || '当前资料没有带原文依据的知识节点。'}</p>
        </div>
      )
    }

    return (
      <>
        <div className="ws-knowledge-header">
          <span className="ws-kpi">{nodes.length} 个知识点</span>
          <span className="ws-kpi">{edges.length} 条有依据的关系</span>
        </div>

        <ul className="ws-knowledge-list">
          {nodes.map((node) => (
            <li key={node.knowledge_unit_ref} className={node.knowledge_unit_ref === selectedNodeRef ? 'is-selected' : ''}>
              <button
                type="button"
                onClick={() => setSelectedNodeRef(node.knowledge_unit_ref)}
                aria-pressed={node.knowledge_unit_ref === selectedNodeRef}
              >
                <span className="ws-knowledge-dot" aria-hidden="true" />
                <span className="ws-knowledge-info">
                  <strong>{node.canonical_name}</strong>
                  <small>
                    {knowledgeKindLabels[node.kind] || node.kind}
                    {node.status && ` · ${nodeStatusLabels[node.status] || node.status}`}
                  </small>
                </span>
              </button>
            </li>
          ))}
        </ul>

        <section className="ws-relation-section" aria-labelledby="relations-title">
          <h3 id="relations-title">关系</h3>
          {edges.length ? (
            <ul className="ws-relation-list">
              {edges.map((edge) => {
                const from = nodes.find((node) => node.knowledge_unit_ref === edge.prerequisite_ref)
                const to = nodes.find((node) => node.knowledge_unit_ref === edge.target_ref)
                return (
                  <li key={edge.relation_ref}>
                    <span className="ws-relation-list__names">
                      {from?.canonical_name || '未知节点'}
                      <ArrowRight size={13} aria-hidden="true" />
                      {to?.canonical_name || '未知节点'}
                    </span>
                    <span className="ws-relation-list__strength">{relationStrengthLabels[edge.strength] || edge.strength}</span>
                  </li>
                )
              })}
            </ul>
          ) : (
            <p className="ws-empty-copy">尚无可核验的知识关系。页面不会用装饰性连线冒充先修关系。</p>
          )}
        </section>
      </>
    )
  }

  const renderDetailModal = () => {
    if (!selectedDocument) return null
    const proc = processingUserFacing[selectedDocument.processing_status] || processingUserFacing.completed
    const learning = learningStateFromDocument(selectedDocument)
    const hint = documentStateHint(selectedDocument)
    const isBlocked = knowledgeBlockedStatuses.has(selectedDocument.processing_status)
    const hasKnowledge = !isBlocked && selectedDocument.knowledge_status !== 'NOT_MODELED'
    const canViewContent = selectedDocument.processing_status === 'completed' && !isBlocked
    const canReinspect = canReinspectDocument(selectedDocument)
    const reinspectionPending =
      selectedDocument.processing_status === 'quarantined'
      && selectedDocument.reason_codes?.includes('CONTENT_REINSPECTION_PENDING')

    return (
      <div
        className="library-modal"
        onPointerDown={(event) => {
          if (event.target === event.currentTarget) closeModal()
        }}
      >
        <div className="library-modal__dialog" role="dialog" aria-modal="true" aria-labelledby="library-modal-title">
          <header className="library-modal__header">
            <span className="library-card__badge library-modal__badge" aria-hidden="true">
              {mediaShortLabels[selectedDocument.media_type] || '文件'}
            </span>
            <div className="library-modal__heading">
              <h2 id="library-modal-title">{selectedDocument.title}</h2>
              <span className="library-modal__meta">
                {mediaTypeLabels[selectedDocument.media_type] || selectedDocument.media_type}
                {selectedDocument.subject ? ` · ${selectedDocument.subject}` : ''}
                {selectedDocument.author ? ` · ${selectedDocument.author}` : ''}
                {' · '}
                {formatDate(selectedDocument.updated_at) || '时间未知'}
              </span>
            </div>
            <button
              type="button"
              ref={modalCloseRef}
              className="library-modal__close"
              aria-label="关闭详情"
              onClick={closeModal}
            >
              <X size={17} />
            </button>
          </header>

          <div className="library-modal__scroll">
            <div className="library-modal__banner">
              <span className={`ds-pill ds-pill--document-${selectedDocument.processing_status}`}>
                {proc.label}
              </span>
              <span className={`ds-pill ds-pill--${learning.tone}`}>{learning.label}</span>
              <p>{hint || (hasKnowledge ? '知识已就绪，系统会根据这份资料为你安排学习路径。' : '资料处理完成后可开始学习。')}</p>
            </div>

            {hasKnowledge && (
              <div className="ws-kpi-strip" aria-label="知识概览">
                <div className="ws-kpi-block">
                  <span className="ws-kpi-block__num">{selectedDocument.knowledge_unit_count || 0}</span>
                  <span className="ws-kpi-block__label">个知识点</span>
                </div>
                <div className="ws-kpi-block">
                  <span className="ws-kpi-block__num">{selectedDocument.relation_count || 0}</span>
                  <span className="ws-kpi-block__label">条关系</span>
                </div>
              </div>
            )}

            <section className="ws-card" aria-label="资料信息">
              <h3 className="ws-card__title">资料信息</h3>
              <dl className="ws-meta-list ws-meta-list--cols">
                <div className="ws-meta-row"><dt>类型</dt><dd>{mediaTypeLabels[selectedDocument.media_type] || selectedDocument.media_type || '未知'}</dd></div>
                <div className="ws-meta-row">
                  <dt>状态</dt>
                  <dd>
                    <span className={`ds-pill ds-pill--document-${selectedDocument.processing_status}`}>
                      {proc.label}
                    </span>
                  </dd>
                </div>
                <div className="ws-meta-row"><dt>导入时间</dt><dd>{formatDate(selectedDocument.created_at) || '—'}</dd></div>
                {formatBytes(selectedDocument.file_size_bytes) && (
                  <div className="ws-meta-row"><dt>大小</dt><dd>{formatBytes(selectedDocument.file_size_bytes)}</dd></div>
                )}
                {selectedDocument.subject && <div className="ws-meta-row"><dt>学科</dt><dd>{selectedDocument.subject}</dd></div>}
                {selectedDocument.author && <div className="ws-meta-row"><dt>作者</dt><dd>{selectedDocument.author}</dd></div>}
              </dl>
            </section>

            <section className="ws-card" aria-label="知识候选">
              <h3 className="ws-card__title">知识候选</h3>
              <div className="ws-section">
                {renderKnowledgeSection()}
              </div>
            </section>

            <details className="library-metadata-editor">
              <summary>编辑资料信息</summary>
              <form onSubmit={saveMetadata}>
                <label><span>显示标题</span><input required value={metadataDraft.title} onChange={(event) => setMetadataDraft((current) => ({ ...current, title: event.target.value }))} maxLength={255} /></label>
                <label><span>学科</span><input value={metadataDraft.subject} onChange={(event) => setMetadataDraft((current) => ({ ...current, subject: event.target.value }))} maxLength={100} /></label>
                <label><span>作者</span><input value={metadataDraft.author} onChange={(event) => setMetadataDraft((current) => ({ ...current, author: event.target.value }))} maxLength={200} /></label>
                <label><span>语言</span><input value={metadataDraft.language} onChange={(event) => setMetadataDraft((current) => ({ ...current, language: event.target.value }))} maxLength={35} placeholder="例如：zh-CN" /></label>
                <Button type="submit" variant="secondary" disabled={managing}>保存信息</Button>
                <small>只更新资料信息，不覆盖原文件，也不创建新的知识 revision。</small>
              </form>
            </details>
          </div>

          <footer className="library-modal__footer">
            <Button
              variant="ghost"
              onClick={() => archiveSingle(selectedDocument)}
              disabled={managing}
            >
              <Archive size={15} />
              归档
            </Button>
            <div className="library-modal__footer-actions">
              {canReinspect && !reinspectionPending && (
                <Button
                  variant="secondary"
                  onClick={() => requestReinspection(selectedDocument)}
                  disabled={reinspectingDocumentId === selectedDocument.document_id}
                >
                  <RefreshCw size={14} />
                  {reinspectingDocumentId === selectedDocument.document_id ? '正在提交…' : '使用新版策略重新检查'}
                </Button>
              )}
              {canViewContent && (
                <Button
                  as="a"
                  variant="secondary"
                  href={`/documents/${encodeURIComponent(selectedDocument.document_id)}/content`}
                  target="_blank"
                  rel="noreferrer"
                >
                  <BookOpen size={15} />
                  打开原文
                </Button>
              )}
              {hasKnowledge && (
                <Button
                  as="a"
                  variant="primary"
                  href={`#/book-learning/${encodeURIComponent(selectedDocument.document_id)}`}
                >
                  <GraduationCap size={16} />
                  开始学习
                </Button>
              )}
            </div>
          </footer>
        </div>
      </div>
    )
  }

  return (
    <div
      className={`library-page page-stack${dragActive ? ' is-drag-active' : ''}`}
      onDragEnter={onDragEnter}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
    >
      <header className="page-header page-header--split library-header">
        <div>
          <h1>资料库</h1>
          <p className="library-header__subtitle">导入私人学习资料，点击卡片查看内容、知识与学习状态。</p>
        </div>
        <div className="library-upload">
          <input
            ref={fileInputRef}
            className="visually-hidden"
            type="file"
            accept=".md,.txt,.pdf,.docx,.epub"
            onChange={uploadFile}
            aria-label="选择要上传的资料"
          />
          <Button
            variant="primary"
            size="md"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
          >
            <Upload size={16} />
            {uploading ? '正在上传…' : '导入资料'}
          </Button>
        </div>
      </header>

      <div className="library-announcer" aria-live="polite" aria-atomic="true">
        {actionMessage && <p className="inline-notice">{actionMessage}</p>}
        {actionError && <p className="inline-error" role="alert">{actionError}</p>}
        {hasActiveProcessing && <p className="inline-notice">后台处理进行中，资料状态会自动刷新。</p>}
      </div>

      {destination && (
        <MaterialDestination
          material={destination}
          onDismiss={() => setDestination(null)}
          onAssigned={(workspaceId, meta) => {
            setDestination(null)
            setActionMessage('资料已加入空间。')
            if (meta?.startNow && meta.documentId) {
              window.location.hash = `#/book-learning/${encodeURIComponent(meta.documentId)}`
              return
            }
            window.location.hash = `#/courses/${encodeURIComponent(workspaceId)}`
          }}
        />
      )}

      <section className="library-toolbar" aria-label="资料筛选与排序">
        <form onSubmit={submitFilters} className="library-toolbar__search">
          <span className="input-with-icon">
            <Search size={15} />
            <input
              value={queryDraft}
              onChange={(event) => setQueryDraft(event.target.value)}
              maxLength={500}
              placeholder="搜索资料…"
              aria-label="搜索资料"
            />
          </span>
        </form>
        <select
          className="library-toolbar__filter"
          value={statusFilter}
          onChange={(event) => { setPage(1); setStatusFilter(event.target.value) }}
          aria-label="状态筛选"
        >
          {processingOptions.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
        </select>
        <select
          className="library-toolbar__sort"
          value={sort}
          onChange={(event) => { setPage(1); setSort(event.target.value) }}
          aria-label="排序"
        >
          {sortOptions.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
        </select>
      </section>

      {isEmpty ? (
        hasFilters ? (
          <div className="library-no-match">
            <Search size={20} />
            <strong>没有找到匹配的资料</strong>
            <Button variant="ghost" onClick={() => { setQueryFilter(''); setQueryDraft(''); setStatusFilter(''); setPage(1) }}>
              清除筛选
            </Button>
          </div>
        ) : (
          <div className="library-empty-state">
            <BookOpen size={32} />
            <h2>还没有学习资料</h2>
            <p>把 Markdown、TXT、PDF、DOCX 或 EPUB 拖到这里，或点击按钮导入，开始建立你的学习库。</p>
            <Button variant="primary" onClick={() => fileInputRef.current?.click()}>
              <Upload size={16} />
              导入资料
            </Button>
          </div>
        )
      ) : (
        <>
          <ul
            className="library-grid"
            data-batch-active={checkedIds.length > 0 || undefined}
          >
            {documents.map((document) => {
              const cardStatus = unifiedCardStatus(document)
              const isChecked = checkedIds.includes(document.document_id)
              const isOpen = document.document_id === selectedDocumentId
              const isBlocked = knowledgeBlockedStatuses.has(document.processing_status)
              const isNotModeled = document.knowledge_status === 'NOT_MODELED'
              const hasKnowledge = !isBlocked && !isNotModeled
              const fallbackDesc = hasKnowledge
                ? `${document.knowledge_unit_count || 0} 个知识点 · ${document.relation_count || 0} 条关系`
                : `${mediaTypeLabels[document.media_type] || '文件'}${formatBytes(document.file_size_bytes) ? ` · ${formatBytes(document.file_size_bytes)}` : ''}`

              return (
                <li
                  key={document.document_id}
                  className={`library-card${isChecked ? ' is-checked' : ''}${isOpen ? ' is-open' : ''}`}
                >
                  <label
                    className="library-card__check"
                    onClick={(event) => event.stopPropagation()}
                  >
                    <input
                      type="checkbox"
                      checked={isChecked}
                      onChange={(event) => setCheckedIds((current) => event.target.checked ? [...current, document.document_id] : current.filter((id) => id !== document.document_id))}
                      aria-label={`选择资料 ${document.title}`}
                    />
                  </label>
                  <button
                    type="button"
                    className="library-card__button"
                    onClick={(event) => openDocument(document, event.currentTarget)}
                    aria-current={isOpen ? 'true' : undefined}
                  >
                    <span className="library-card__head">
                      <span className="library-card__badge" aria-hidden="true">
                        {mediaShortLabels[document.media_type] || '文件'}
                      </span>
                      <span className="library-card__title">{document.title}</span>
                    </span>
                    {document.match_excerpt && (
                      <span className="library-card__match">
                        命中{document.match_field === 'title' ? '标题' : '正文'}：{document.match_excerpt}
                      </span>
                    )}
                    <span className="library-card__desc">{fallbackDesc}</span>
                    <span className="library-card__meta">
                      <span className={`ds-pill ds-pill--${cardStatus.tone}`}>
                        {cardStatus.label}
                      </span>
                      <small className="library-card__date">{formatDate(document.updated_at)}</small>
                    </span>
                  </button>
                </li>
              )
            })}
          </ul>

          {totalPages > 1 && (
            <nav className="pagination" aria-label="资料分页">
              <Button variant="ghost" size="xs" onClick={() => setPage((value) => value - 1)} disabled={page === 1} aria-label="上一页">
                <ChevronLeft size={16} />
              </Button>
              <span>{page} / {totalPages}</span>
              <Button variant="ghost" size="xs" onClick={() => setPage((value) => value + 1)} disabled={page === totalPages} aria-label="下一页">
                <ChevronRight size={16} />
              </Button>
            </nav>
          )}
        </>
      )}

      {renderDetailModal()}

      {checkedIds.length > 0 && (
        <div className="library-batch-bar">
          <span className="library-batch-bar__count">已选 {checkedIds.length} 份</span>
          <div className="library-batch-bar__actions">
            <select value={batchTagId} onChange={(event) => setBatchTagId(event.target.value)} aria-label="加标签">
              <option value="">加标签…</option>
              {availableTags.map((tag) => <option key={tag.tag_id} value={tag.tag_id}>{tag.name}</option>)}
            </select>
            <select value={batchCollectionId} onChange={(event) => setBatchCollectionId(event.target.value)} aria-label="加入集合">
              <option value="">加入集合…</option>
              {availableCollections.map((collection) => <option key={collection.collection_id} value={collection.collection_id}>{collection.name}</option>)}
            </select>
            <Button variant="secondary" size="sm" onClick={() => applyBatch(null)} disabled={managing}>应用</Button>
            <Button variant="secondary" size="sm" onClick={() => applyBatch(statusFilter ? false : true)} disabled={managing}>
              {statusFilter ? <RotateCcw size={15} /> : <Archive size={15} />}
              {statusFilter ? '恢复' : '归档'}
            </Button>
            <Button variant="ghost" size="sm" onClick={() => setCheckedIds([])}>取消</Button>
          </div>
        </div>
      )}

      {dragActive && (
        <div className="library-drop-overlay" aria-hidden="true">
          <Upload size={26} />
          <strong>松开以导入资料</strong>
          <span>支持 Markdown / TXT / PDF / DOCX / EPUB</span>
        </div>
      )}
    </div>
  )
}
