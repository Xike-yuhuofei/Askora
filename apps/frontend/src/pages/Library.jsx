import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  Archive,
  BookOpen,
  CheckSquare,
  ChevronLeft,
  ChevronRight,
  Copy,
  FileText,
  FolderOpen,
  FolderPlus,
  GraduationCap,
  Network,
  RefreshCw,
  RotateCcw,
  ScanText,
  Search,
  Tags,
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

const knowledgeBlockedStatuses = new Set(['failed', 'rejected', 'quarantined'])

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

function readRecoveryTarget() {
  const query = window.location.hash.replace(/^#/, '').split('?')[1] || ''
  const params = new URLSearchParams(query)
  return {
    documentId: params.get('document'),
    ocrRunId: params.get('ocrRun'),
  }
}

export default function Library() {
  const fileInputRef = useRef(null)
  const recoveryTargetRef = useRef(readRecoveryTarget())
  const pendingSelectionRef = useRef(recoveryTargetRef.current.documentId)
  const ocrReviewRef = useRef(null)
  const [library, setLibrary] = useState({ status: 'loading', payload: null, error: '' })
  const [map, setMap] = useState({ status: 'idle', payload: null, error: '' })
  const [selectedDocumentId, setSelectedDocumentId] = useState(null)
  const [selectedNodeRef, setSelectedNodeRef] = useState(null)
  const [selectedSpanRef, setSelectedSpanRef] = useState(null)
  const [statusFilter, setStatusFilter] = useState('')
  const [subjectDraft, setSubjectDraft] = useState('')
  const [subjectFilter, setSubjectFilter] = useState('')
  const [queryDraft, setQueryDraft] = useState('')
  const [queryFilter, setQueryFilter] = useState('')
  const [tagFilter, setTagFilter] = useState('')
  const [collectionFilter, setCollectionFilter] = useState('')
  const [archivedFilter, setArchivedFilter] = useState(false)
  const [sort, setSort] = useState('created_desc')
  const [page, setPage] = useState(1)
  const [uploadSubject, setUploadSubject] = useState('')
  const [uploading, setUploading] = useState(false)
  const [actionMessage, setActionMessage] = useState('')
  const [actionError, setActionError] = useState('')
  const [checkedIds, setCheckedIds] = useState([])
  const [batchTagId, setBatchTagId] = useState('')
  const [batchCollectionId, setBatchCollectionId] = useState('')
  const [newTagName, setNewTagName] = useState('')
  const [newCollectionName, setNewCollectionName] = useState('')
  const [managing, setManaging] = useState(false)
  const [metadataDraft, setMetadataDraft] = useState({ title: '', subject: '', author: '', language: '' })
  const [duplicates, setDuplicates] = useState({ status: 'loading', items: [], error: '' })
  const [ocr, setOcr] = useState({ status: 'idle', payload: null, error: '' })
  const [ocrDecisions, setOcrDecisions] = useState({})
  const [ocrPage, setOcrPage] = useState(1)
  const [ocrPageUrl, setOcrPageUrl] = useState('')
  const [reinspectingDocumentId, setReinspectingDocumentId] = useState(null)
  const [mapReloadKey, setMapReloadKey] = useState(0)

  const loadLibrary = useCallback(async ({
    quiet = false,
    status = statusFilter,
    subject = subjectFilter,
    query = queryFilter,
    documentId = recoveryTargetRef.current.documentId,
    tagId = tagFilter,
    collectionId = collectionFilter,
    archived = archivedFilter,
    requestedSort = sort,
    requestedPage = page,
  } = {}) => {
    if (!quiet) setLibrary((current) => ({ ...current, status: 'loading', error: '' }))
    try {
      const payload = await workspaceApi.getLibraryWorkspace({
        status,
        subject,
        query,
        documentId,
        tagId,
        collectionId,
        archived,
        sort: requestedSort,
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
  }, [archivedFilter, collectionFilter, page, queryFilter, sort, statusFilter, subjectFilter, tagFilter])

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
    setMetadataDraft({
      title: selectedDocument?.title || '',
      subject: selectedDocument?.subject || '',
      author: selectedDocument?.author || '',
      language: selectedDocument?.language || '',
    })
    setOcr({ status: 'idle', payload: null, error: '' })
  }, [selectedDocumentId])

  useEffect(() => {
    const target = recoveryTargetRef.current
    if (!target.ocrRunId || !target.documentId || selectedDocumentId !== target.documentId) {
      return undefined
    }
    const runId = target.ocrRunId
    target.ocrRunId = null
    let active = true
    setOcr({ status: 'loading', payload: null, error: '' })
    documentApi.getDocumentOcrRun(runId)
      .then((payload) => {
        if (!active) return
        if (payload.document_id !== target.documentId || payload.status !== 'review_required') {
          setOcr({ status: 'error', payload: null, error: '这项 OCR 复核已不可用或不属于当前资料。' })
          return
        }
        setOcr({ status: 'ready', payload, error: '' })
        setOcrPage(payload.candidates?.[0]?.page_number || 1)
        setOcrDecisions(Object.fromEntries((payload.candidates || []).map((candidate) => [
          candidate.candidate_id,
          { accepted: false, text: candidate.text },
        ])))
      })
      .catch((error) => {
        if (active) {
          setOcr({ status: 'error', payload: null, error: responseMessage(error, 'OCR 复核暂时无法读取。') })
        }
      })
    return () => { active = false }
  }, [selectedDocumentId])

  useEffect(() => {
    if (ocr.payload?.status !== 'review_required') return
    window.requestAnimationFrame(() => ocrReviewRef.current?.focus())
  }, [ocr.payload?.status])

  const loadDuplicates = useCallback(async () => {
    try {
      const items = await documentApi.getDuplicateSuggestions('pending')
      setDuplicates({ status: 'ready', items, error: '' })
    } catch (error) {
      setDuplicates({ status: 'error', items: [], error: responseMessage(error, '重复资料建议暂时无法读取。') })
    }
  }, [])

  useEffect(() => { loadDuplicates() }, [loadDuplicates])

  useEffect(() => {
    if (!['pending', 'processing'].includes(ocr.payload?.status)) return undefined
    const timer = window.setTimeout(async () => {
      try {
        const payload = await documentApi.getDocumentOcrRun(ocr.payload.run_id)
        setOcr({ status: 'ready', payload, error: '' })
        if (payload.status === 'review_required') {
          setOcrPage(payload.candidates?.[0]?.page_number || 1)
          setOcrDecisions(Object.fromEntries((payload.candidates || []).map((candidate) => [
            candidate.candidate_id,
            { accepted: false, text: candidate.text },
          ])))
        }
      } catch (error) {
        setOcr({ status: 'error', payload: null, error: responseMessage(error, '文字识别状态暂时无法读取。') })
      }
    }, 1200)
    return () => window.clearTimeout(timer)
  }, [ocr.payload])

  useEffect(() => {
    let active = true
    let objectUrl = ''
    if (ocr.payload?.status !== 'review_required') {
      setOcrPageUrl('')
      return undefined
    }
    documentApi.getOcrPageImage(ocr.payload.run_id, ocrPage)
      .then((blob) => {
        if (!active) return
        objectUrl = URL.createObjectURL(blob)
        setOcrPageUrl(objectUrl)
      })
      .catch(() => { if (active) setOcrPageUrl('') })
    return () => {
      active = false
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [ocr.payload?.run_id, ocr.payload?.status, ocrPage])

  const submitFilters = (event) => {
    event.preventDefault()
    setPage(1)
    setSubjectFilter(subjectDraft.trim())
    setQueryFilter(queryDraft.trim())
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
      setQueryDraft('')
      setQueryFilter('')
      await loadLibrary({ quiet: true, status: '', subject: '', query: '', requestedPage: 1 })
    } catch (error) {
      setActionError(responseMessage(error, '上传失败，请检查文件格式后重试。'))
    } finally {
      setUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  const createLabel = async (kind) => {
    const name = (kind === 'tag' ? newTagName : newCollectionName).trim()
    if (!name || managing) return
    setManaging(true)
    setActionError('')
    try {
      if (kind === 'tag') {
        await documentApi.createLibraryTag(name, commandKey('create-tag'))
        setNewTagName('')
      } else {
        await documentApi.createLibraryCollection(name, commandKey('create-collection'))
        setNewCollectionName('')
      }
      setActionMessage(kind === 'tag' ? '标签已创建。' : '集合已创建。')
      await loadLibrary({ quiet: true })
    } catch (error) {
      setActionError(responseMessage(error, '分类创建失败，请稍后重试。'))
    } finally {
      setManaging(false)
    }
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

  const resolveDuplicate = async (suggestion, action) => {
    setManaging(true)
    try {
      await documentApi.resolveDuplicateSuggestion(suggestion.suggestion_id, {
        expected_version: suggestion.version,
        idempotency_key: commandKey('resolve-duplicate'),
        action,
      })
      setActionMessage(action === 'ARCHIVE_CANDIDATE' ? '候选资料已归档，原文件仍保留。' : '重复建议已处理。')
      await Promise.all([loadDuplicates(), loadLibrary({ quiet: true })])
    } catch (error) {
      setActionError(responseMessage(error, '重复建议处理失败，请刷新后重试。'))
    } finally {
      setManaging(false)
    }
  }

  const startOcr = async () => {
    if (!selectedDocument || managing) return
    setManaging(true)
    try {
      const payload = await documentApi.requestDocumentOcr(selectedDocument.document_id, {
        idempotency_key: commandKey('ocr-request'),
        languages: ['chi_sim', 'eng'],
      })
      setOcr({ status: 'ready', payload, error: '' })
      setActionMessage('本地 OCR 已进入后台处理；结果必须由你复核后才会发布。')
    } catch (error) {
      setOcr({ status: 'error', payload: null, error: responseMessage(error, '本地 OCR 无法启动。') })
    } finally {
      setManaging(false)
    }
  }

  const publishOcr = async () => {
    if (!ocr.payload || managing) return
    setManaging(true)
    try {
      const payload = await documentApi.reviewDocumentOcrRun(ocr.payload.run_id, {
        idempotency_key: commandKey('ocr-review'),
        decisions: ocr.payload.candidates.map((candidate) => ({
          candidate_id: candidate.candidate_id,
          expected_version: candidate.version,
          action: ocrDecisions[candidate.candidate_id]?.accepted ? 'ACCEPT' : 'REJECT',
          corrected_text: ocrDecisions[candidate.candidate_id]?.accepted
            ? ocrDecisions[candidate.candidate_id]?.text
            : null,
        })),
        publish: true,
      })
      setOcr({ status: 'ready', payload, error: '' })
      setActionMessage('复核文本已发布为新的可追溯 revision。')
      await loadLibrary({ quiet: true })
      setMapReloadKey((value) => value + 1)
    } catch (error) {
      setActionError(responseMessage(error, 'OCR 复核发布失败，请检查至少接受一个候选。'))
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

      <section className="library-filters" aria-label="资料筛选">
        <form onSubmit={submitFilters}>
          <label className="library-search-field">
            <span>搜索标题与正文</span>
            <span className="input-with-icon"><Search size={15} /><input value={queryDraft} onChange={(event) => setQueryDraft(event.target.value)} maxLength={500} placeholder="输入资料中的关键词" /></span>
          </label>
          <label>
            <span>学科</span>
            <input value={subjectDraft} onChange={(event) => setSubjectDraft(event.target.value)} maxLength={100} placeholder="精确筛选学科" />
          </label>
          <button type="submit" className="button button--secondary">搜索</button>
        </form>
        <label>
          <span>处理状态</span>
          <select value={statusFilter} onChange={(event) => { setPage(1); setStatusFilter(event.target.value) }}>
            {processingOptions.map(([value, label]) => <option key={value} value={value}>{label}</option>)}
          </select>
        </label>
        <label>
          <span>标签</span>
          <select value={tagFilter} onChange={(event) => { setPage(1); setTagFilter(event.target.value) }}>
            <option value="">全部标签</option>
            {availableTags.map((tag) => <option key={tag.tag_id} value={tag.tag_id}>{tag.name}</option>)}
          </select>
        </label>
        <label>
          <span>集合</span>
          <select value={collectionFilter} onChange={(event) => { setPage(1); setCollectionFilter(event.target.value) }}>
            <option value="">全部集合</option>
            {availableCollections.map((collection) => <option key={collection.collection_id} value={collection.collection_id}>{collection.name}</option>)}
          </select>
        </label>
        <label>
          <span>视图</span>
          <select value={archivedFilter ? 'archived' : 'active'} onChange={(event) => { setPage(1); setArchivedFilter(event.target.value === 'archived'); setCheckedIds([]) }}>
            <option value="active">使用中</option>
            <option value="archived">已归档</option>
          </select>
        </label>
        <label>
          <span>排序</span>
          <select value={sort} onChange={(event) => { setPage(1); setSort(event.target.value) }}>
            <option value="created_desc">最近导入</option>
            <option value="updated_desc">最近更新</option>
            <option value="title_asc">标题 A–Z</option>
          </select>
        </label>
        <span className="library-count">共 {total} 份资料</span>
      </section>

      {checkedIds.length > 0 ? (
        <section className="surface library-management" aria-labelledby="organize-title">
          <div className="section-heading section-heading--compact">
            <div><p className="eyebrow">已选 {checkedIds.length} 份资料</p><h2 id="organize-title">批量操作</h2></div>
            <CheckSquare size={18} />
          </div>
          <div className="library-management__row">
            <label><span>给所选资料加标签</span><select value={batchTagId} onChange={(event) => setBatchTagId(event.target.value)}><option value="">不更改</option>{availableTags.map((tag) => <option key={tag.tag_id} value={tag.tag_id}>{tag.name}</option>)}</select></label>
            <label><span>加入集合</span><select value={batchCollectionId} onChange={(event) => setBatchCollectionId(event.target.value)}><option value="">不更改</option>{availableCollections.map((collection) => <option key={collection.collection_id} value={collection.collection_id}>{collection.name}</option>)}</select></label>
            <button type="button" className="button button--secondary" onClick={() => applyBatch(null)} disabled={!checkedIds.length || managing}>应用分类</button>
            <button type="button" className="button button--secondary" onClick={() => applyBatch(archivedFilter ? false : true)} disabled={!checkedIds.length || managing}>
              {archivedFilter ? <RotateCcw size={15} /> : <Archive size={15} />}
              {archivedFilter ? '恢复所选' : '归档所选'}
            </button>
            <button type="button" className="button button--ghost" onClick={() => setCheckedIds([])}>取消选择</button>
          </div>
          <div className="library-management__row library-label-create">
            <label><span>新标签</span><input value={newTagName} onChange={(event) => setNewTagName(event.target.value)} maxLength={80} placeholder="例如：核心概念" /></label>
            <button type="button" className="button button--ghost" onClick={() => createLabel('tag')} disabled={!newTagName.trim() || managing}><Tags size={15} />创建标签</button>
            <label><span>新集合</span><input value={newCollectionName} onChange={(event) => setNewCollectionName(event.target.value)} maxLength={120} placeholder="例如：物理教材" /></label>
            <button type="button" className="button button--ghost" onClick={() => createLabel('collection')} disabled={!newCollectionName.trim() || managing}><FolderPlus size={15} />创建集合</button>
          </div>
        </section>
      ) : (
        <section className="surface library-management library-management--collapsed" aria-label="批量操作提示">
          <div className="section-heading section-heading--compact">
            <div><p className="eyebrow">提示</p><h2>选择资料后可批量管理</h2></div>
            <CheckSquare size={18} />
          </div>
          <p className="empty-copy">勾选资料后，可在此处批量加标签、加入集合或归档。</p>
        </section>
      )}

      {duplicates.items.length > 0 && (
        <section className="surface duplicate-review" aria-labelledby="duplicate-title">
          <div className="section-heading section-heading--compact"><div><p className="eyebrow">仅建议，不自动合并</p><h2 id="duplicate-title">重复资料复核</h2></div><Copy size={18} /></div>
          {duplicates.items.map((suggestion) => (
            <div className="duplicate-row" key={suggestion.suggestion_id}>
              <span>{suggestion.kind === 'EXACT_DUPLICATE' ? '文件内容完全一致' : suggestion.kind === 'REVISION_CANDIDATE' ? '可能是同一资料的新版本' : '正文高度相似'} · {Math.round((suggestion.confidence || 0) * 100)}%</span>
              <div><button type="button" className="button button--ghost" onClick={() => resolveDuplicate(suggestion, 'KEEP_SEPARATE')} disabled={managing}>保留两份</button><button type="button" className="button button--secondary" onClick={() => resolveDuplicate(suggestion, 'ARCHIVE_CANDIDATE')} disabled={managing}>归档候选</button></div>
            </div>
          ))}
        </section>
      )}

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
                  <label className="document-check">
                    <input
                      type="checkbox"
                      checked={checkedIds.includes(document.document_id)}
                      onChange={(event) => setCheckedIds((current) => event.target.checked ? [...current, document.document_id] : current.filter((id) => id !== document.document_id))}
                      aria-label={`选择资料 ${document.title}`}
                    />
                  </label>
                  <button
                    type="button"
                    className="document-select"
                    onClick={() => setSelectedDocumentId(document.document_id)}
                    aria-pressed={document.document_id === selectedDocumentId}
                  >
                    <span className="document-title">{document.title}</span>
                    <span>{document.subject || '未标注学科'} · {formatBytes(document.file_size_bytes)}</span>
                    {(document.tags?.length > 0 || document.collections?.length > 0) && <span className="document-labels">{document.collections?.map((item) => item.name).join(' / ')}{document.tags?.length > 0 && ` · ${document.tags.map((item) => `#${item.name}`).join(' ')}`}</span>}
                    {document.match_excerpt && <span className="document-match">命中{document.match_field === 'title' ? '标题' : '正文'}：{document.match_excerpt}</span>}
                    <span className="document-statuses">
                      <span className={`status-pill status-pill--document-${document.processing_status}`}>
                        {processingLabels[document.processing_status] || document.processing_status}
                      </span>
                      {!knowledgeBlockedStatuses.has(document.processing_status) && (
                        <span className="status-pill status-pill--neutral">
                          {knowledgeLabels[document.knowledge_status] || document.knowledge_status}
                        </span>
                      )}
                    </span>
                    <small>{formatDate(document.updated_at)}</small>
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
          {selectedDocument && (
            <form className="metadata-editor" onSubmit={saveMetadata}>
              <h3>资料信息</h3>
              <label><span>显示标题</span><input required value={metadataDraft.title} onChange={(event) => setMetadataDraft((current) => ({ ...current, title: event.target.value }))} maxLength={255} /></label>
              <label><span>学科</span><input value={metadataDraft.subject} onChange={(event) => setMetadataDraft((current) => ({ ...current, subject: event.target.value }))} maxLength={100} /></label>
              <label><span>作者</span><input value={metadataDraft.author} onChange={(event) => setMetadataDraft((current) => ({ ...current, author: event.target.value }))} maxLength={200} /></label>
              <label><span>语言</span><input value={metadataDraft.language} onChange={(event) => setMetadataDraft((current) => ({ ...current, language: event.target.value }))} maxLength={35} placeholder="例如：zh-CN" /></label>
              <button type="submit" className="button button--secondary" disabled={managing}>保存信息</button>
              <small>只更新资料信息，不覆盖原文件，也不创建新的知识 revision。</small>
            </form>
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
          {selectedDocument && !knowledgeBlockedStatuses.has(selectedDocument.processing_status) && (
            <a
              className="button button--primary library-learning-link"
              href={`#/book-learning/${encodeURIComponent(selectedDocument.document_id)}`}
            >
              <GraduationCap size={16} />
              从这份资料开始学习
            </a>
          )}
          {selectedDocument?.media_type === 'application/pdf' && !knowledgeBlockedStatuses.has(selectedDocument.processing_status) && (
            <button type="button" className="button button--secondary library-ocr-button" onClick={startOcr} disabled={managing || ['pending', 'processing'].includes(ocr.payload?.status)}>
              <ScanText size={16} />
              {['pending', 'processing'].includes(ocr.payload?.status) ? '本地 OCR 处理中…' : '识别扫描 PDF'}
            </button>
          )}
          {ocr.error && <p className="inline-error" role="alert">{ocr.error}</p>}
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
              {selectedDocument.reason_codes?.includes('CONTENT_REINSPECTION_AVAILABLE') && (
                <button
                  type="button"
                  className="button button--secondary"
                  onClick={() => requestReinspection(selectedDocument)}
                  disabled={reinspectingDocumentId === selectedDocument.document_id}
                >
                  <RefreshCw size={16} />
                  {reinspectingDocumentId === selectedDocument.document_id
                    ? '正在提交…'
                    : '使用新版策略重新检查'}
                </button>
              )}
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

      {ocr.payload?.status === 'review_required' && (
        <section ref={ocrReviewRef} className="surface ocr-review" aria-labelledby="ocr-review-title" tabIndex="-1">
          <div className="section-heading">
            <div>
              <p className="eyebrow">人工复核门禁</p>
              <h2 id="ocr-review-title">扫描 PDF 文字复核</h2>
              <p>左侧是本地渲染的原页，右侧是 OCR 候选。只有你勾选接受并发布的文字才会进入新的 revision。</p>
            </div>
            <ScanText size={20} />
          </div>
          <div className="ocr-pages" aria-label="OCR 页码">
            {[...new Set(ocr.payload.candidates.map((candidate) => candidate.page_number))].map((pageNumber) => (
              <button type="button" className={pageNumber === ocrPage ? 'is-selected' : ''} key={pageNumber} onClick={() => setOcrPage(pageNumber)}>第 {pageNumber} 页</button>
            ))}
          </div>
          <div className="ocr-review__grid">
            <figure className="ocr-page-preview">
              {ocrPageUrl ? <img src={ocrPageUrl} alt={`PDF 第 ${ocrPage} 页原图`} /> : <div className="inline-state">原页预览载入中…</div>}
              <figcaption>仅在本机临时渲染 · 不上传第三方</figcaption>
            </figure>
            <div className="ocr-candidates">
              {ocr.payload.candidates.filter((candidate) => candidate.page_number === ocrPage).map((candidate) => (
                <article key={candidate.candidate_id}>
                  <header>
                    <label><input type="checkbox" checked={ocrDecisions[candidate.candidate_id]?.accepted || false} onChange={(event) => setOcrDecisions((current) => ({ ...current, [candidate.candidate_id]: { ...current[candidate.candidate_id], accepted: event.target.checked } }))} />接受这段文字</label>
                    <span>置信度 {candidate.confidence == null ? '未知' : `${Math.round(candidate.confidence)}%`}</span>
                  </header>
                  <textarea aria-label={`第 ${candidate.page_number} 页候选 ${candidate.block_index + 1}`} value={ocrDecisions[candidate.candidate_id]?.text ?? candidate.text} onChange={(event) => setOcrDecisions((current) => ({ ...current, [candidate.candidate_id]: { ...current[candidate.candidate_id], text: event.target.value } }))} rows={4} />
                  <small>位置 [{candidate.bbox.join(', ')}] · 图像哈希 {candidate.image_hash.slice(0, 12)}…</small>
                </article>
              ))}
            </div>
          </div>
          <div className="ocr-review__actions">
            <span>未勾选的候选会明确拒绝；发布失败时旧 revision 保持不变。</span>
            <button type="button" className="button button--primary" onClick={publishOcr} disabled={managing || !Object.values(ocrDecisions).some((decision) => decision.accepted)}>发布已复核文字</button>
          </div>
        </section>
      )}
      {ocr.payload?.status === 'accepted' && <p className="inline-notice">OCR 复核已发布；资料搜索与知识地图已切换到新 revision。</p>}
    </div>
  )
}
