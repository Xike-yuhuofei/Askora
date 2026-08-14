import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as documentApi from '../api/documents'
import * as workspaceApi from '../api/workspace'
import Library from '../pages/Library'

vi.mock('../api/documents', () => ({
  uploadDocument: vi.fn(),
  listUnassignedMaterials: vi.fn(),
  assignMaterial: vi.fn(),
  reinspectDocument: vi.fn(),
  createLibraryTag: vi.fn(),
  createLibraryCollection: vi.fn(),
  updateDocumentMetadata: vi.fn(),
  batchOrganizeDocuments: vi.fn(),
  getDuplicateSuggestions: vi.fn(),
  resolveDuplicateSuggestion: vi.fn(),
  requestDocumentOcr: vi.fn(),
  getDocumentOcrRun: vi.fn(),
  reviewDocumentOcrRun: vi.fn(),
  getOcrPageImage: vi.fn(),
}))
vi.mock('../api/workspace', () => ({
  getLibraryWorkspace: vi.fn(),
  getKnowledgeMap: vi.fn(),
  listWorkspaces: vi.fn(),
  createWorkspace: vi.fn(),
  clearTransitionGuard: vi.fn(() => ({
    composer_draft: 'CLEAR',
    stream: 'CLEAR',
    user_note: 'CLEAR',
    material_position: 'PRESERVED',
  })),
}))

const documentView = {
  document_ref: 'source_document:document-1:revision:revision-1',
  document_id: '11111111-1111-4111-8111-111111111111',
  title: '函数基础.md',
  metadata_version: 1,
  media_type: 'text/markdown',
  file_size_bytes: 2048,
  subject: '数学',
  author: null,
  language: null,
  tags: [],
  collections: [],
  match_field: null,
  match_excerpt: null,
  match_source_span_ref: null,
  processing_status: 'completed',
  moderation_status: 'approved',
  current_revision_ref: 'material_revision:revision-1',
  knowledge_status: 'CANDIDATES',
  knowledge_unit_count: 1,
  relation_count: 0,
  reason_codes: [],
  created_at: '2026-08-08T01:00:00Z',
  updated_at: '2026-08-08T01:01:00Z',
}

const libraryPayload = {
  schema_version: '1.0',
  generated_at: '2026-08-08T01:02:00Z',
  correlation_id: 'request-library',
  data: {
    view_state: 'READY',
    total: 1,
    page: 1,
    page_size: 20,
    documents: [documentView],
    available_tags: [],
    available_collections: [],
  },
  source_status: [
    { source_system: 'SYS01', availability: 'AVAILABLE', source_ref: null, reason_codes: ['CURRENT_USER_DOCUMENTS'] },
  ],
}

const mapPayload = {
  schema_version: '1.0',
  generated_at: '2026-08-08T01:02:00Z',
  correlation_id: 'request-map',
  data: {
    scope: {
      document_refs: [documentView.document_ref],
      subject: '数学',
      graph_version: 'material_revision:revision-1',
    },
    nodes: [
      {
        knowledge_unit_ref: 'knowledge_unit:unit-1:v1',
        kind: 'concept',
        canonical_name: '函数的定义',
        description: '来自 Markdown 标题的确定性候选。',
        provenance_type: 'source_explicit',
        confidence: null,
        status: 'candidate',
        evidence_span_refs: ['source_span:span-1:revision:revision-1'],
        learner_evidence_summary: null,
      },
    ],
    edges: [],
    source_spans: [
      {
        source_span_ref: 'source_span:span-1:revision:revision-1',
        source_span_id: '22222222-2222-4222-8222-222222222222',
        document_id: documentView.document_id,
        page: null,
        chapter: '函数的定义',
        start_offset: 0,
        end_offset: 28,
        excerpt: '# 函数的定义\n函数描述输入和输出之间的关系。',
      },
    ],
  },
  source_status: [
    { source_system: 'SYS01', availability: 'AVAILABLE', source_ref: 'material_revision:revision-1', reason_codes: ['NO_VERIFIED_RELATIONS'] },
    { source_system: 'SYS03', availability: 'NOT_APPLICABLE', source_ref: null, reason_codes: ['EVIDENCE_PROFILE_DEFERRED_TO_UI_02B'] },
  ],
}

async function openDetailModal(title) {
  fireEvent.click(await screen.findByRole('button', { name: new RegExp(title) }))
  return screen.findByRole('dialog')
}

describe('UI02A 资料库', () => {
  beforeEach(() => {
    window.location.hash = '#/library'
    workspaceApi.getLibraryWorkspace.mockReset()
    workspaceApi.getKnowledgeMap.mockReset()
    documentApi.uploadDocument.mockReset()
    documentApi.listUnassignedMaterials.mockReset()
    documentApi.assignMaterial.mockReset()
    workspaceApi.listWorkspaces.mockReset()
    documentApi.reinspectDocument.mockReset()
    documentApi.createLibraryTag.mockReset()
    documentApi.createLibraryCollection.mockReset()
    documentApi.updateDocumentMetadata.mockReset()
    documentApi.batchOrganizeDocuments.mockReset()
    documentApi.getDuplicateSuggestions.mockReset()
    documentApi.resolveDuplicateSuggestion.mockReset()
    documentApi.requestDocumentOcr.mockReset()
    documentApi.getDocumentOcrRun.mockReset()
    documentApi.reviewDocumentOcrRun.mockReset()
    documentApi.getOcrPageImage.mockReset()
    workspaceApi.getLibraryWorkspace.mockResolvedValue(libraryPayload)
    workspaceApi.getKnowledgeMap.mockResolvedValue(mapPayload)
    documentApi.getDuplicateSuggestions.mockResolvedValue([])
    documentApi.listUnassignedMaterials.mockResolvedValue({ items: [] })
    workspaceApi.listWorkspaces.mockResolvedValue({ data: { workspaces: [], selection_version: null } })
  })

  it('展示资料卡片，打开详情弹窗后可看到学习入口与可审计知识候选', async () => {
    render(<Library />)

    expect(await screen.findByRole('heading', { name: '资料库' })).toBeInTheDocument()
    // 卡片网格直接呈现资料
    expect(await screen.findByRole('button', { name: /函数基础\.md/ })).toBeInTheDocument()

    // 点击卡片打开详情弹窗
    await openDetailModal('函数基础\\.md')
    // 弹窗底部提供「开始学习」主操作（Product 语义化 CTA）
    expect(screen.getByRole('link', { name: '开始学习' })).toHaveAttribute(
      'href',
      `#/book-learning/${documentView.document_id}`,
    )
    // 弹窗内直接展示知识候选与诚实关系说明
    expect(await screen.findByRole('button', { name: /函数的定义/ })).toBeInTheDocument()
    expect(screen.getByText('尚无可核验的知识关系。页面不会用装饰性连线冒充先修关系。')).toBeInTheDocument()
  })

  it('上传真实文件并刷新 Canonical 资料列表', async () => {
    documentApi.uploadDocument.mockResolvedValue({
      document_id: '33333333-3333-4333-8333-333333333333',
      status: 'pending',
      message: '文档已接收，正在后台处理',
    })
    render(<Library />)
    await screen.findByText('函数基础.md')

    const file = new File(['# 极限'], '极限.md', { type: 'text/markdown' })
    fireEvent.change(screen.getByLabelText('选择要上传的资料'), { target: { files: [file] } })

    await waitFor(() => expect(documentApi.uploadDocument).toHaveBeenCalledWith(file, ''))
    expect(await screen.findByText('资料已保存，尚未加入空间。处理完成后选择去向。')).toBeInTheDocument()
    expect(workspaceApi.getLibraryWorkspace.mock.calls.length).toBeGreaterThan(1)
  })

  it('后台处理完成后自动刷新知识地图而不是保留首次空投影', async () => {
    const pendingDocument = {
      ...documentView,
      processing_status: 'pending',
      current_revision_ref: null,
      knowledge_status: 'NOT_MODELED',
      knowledge_unit_count: 0,
    }
    workspaceApi.getLibraryWorkspace
      .mockResolvedValueOnce({
        ...libraryPayload,
        data: { ...libraryPayload.data, view_state: 'PARTIAL', documents: [pendingDocument] },
      })
      .mockResolvedValue(libraryPayload)
    workspaceApi.getKnowledgeMap
      .mockResolvedValueOnce({
        ...mapPayload,
        data: { ...mapPayload.data, nodes: [], source_spans: [] },
      })
      .mockResolvedValue(mapPayload)

    render(<Library />)
    // 等待阶段，卡片展示「等待处理」状态
    expect((await screen.findAllByText('等待处理')).length).toBeGreaterThanOrEqual(1)

    // 打开详情弹窗，等待自动刷新后的知识候选出现
    await openDetailModal('函数基础\\.md')
    await waitFor(
      () => expect(screen.getByRole('button', { name: /函数的定义/ })).toBeInTheDocument(),
      { timeout: 4000 },
    )
    expect(workspaceApi.getKnowledgeMap.mock.calls.length).toBeGreaterThan(1)
  })

  it('隔离资料只展示主状态并说明建模没有启动', async () => {
    const quarantinedDocument = {
      ...documentView,
      title: 'unsafe.epub',
      processing_status: 'quarantined',
      moderation_status: 'rejected',
      current_revision_ref: null,
      knowledge_status: 'NOT_MODELED',
      knowledge_unit_count: 0,
      reason_codes: [
        'CONTENT_REVISION_MISSING',
        'CONTENT_QUARANTINED',
        'EPUB_ENTRY_PATH_UNSAFE',
        'CONTENT_REINSPECTION_AVAILABLE',
      ],
    }
    workspaceApi.getLibraryWorkspace.mockResolvedValue({
      ...libraryPayload,
      data: { ...libraryPayload.data, view_state: 'PARTIAL', documents: [quarantinedDocument] },
    })
    workspaceApi.getKnowledgeMap.mockResolvedValue({
      ...mapPayload,
      data: { ...mapPayload.data, nodes: [], edges: [], source_spans: [] },
    })

    render(<Library />)

    // 卡片直接展示「已归档」状态（quarantined 在用户可见层面映射为已归档）
    const card = await screen.findByRole('button', { name: /unsafe\.epub/ })
    expect(card).toHaveTextContent('已归档')

    // 打开详情弹窗：明确展示「尚未建模」，不假装成已理解
    await openDetailModal('unsafe\\.epub')
    expect(screen.getAllByText(/尚未建模/).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/电子书包包含不安全的文件路径/).length).toBeGreaterThan(0)
    expect(screen.getByRole('button', { name: '使用新版策略重新检查' })).toBeInTheDocument()
    // 隔离资料不应暴露「开始学习」入口
    expect(screen.queryByRole('link', { name: '开始学习' })).not.toBeInTheDocument()
  })

  it('显式提交新版策略复检并防止重复提交', async () => {
    const quarantinedDocument = {
      ...documentView,
      title: 'legacy.epub',
      processing_status: 'quarantined',
      moderation_status: 'rejected',
      current_revision_ref: null,
      knowledge_status: 'NOT_MODELED',
      knowledge_unit_count: 0,
      reason_codes: ['CONTENT_QUARANTINED', 'CONTENT_REINSPECTION_AVAILABLE'],
    }
    workspaceApi.getLibraryWorkspace.mockResolvedValue({
      ...libraryPayload,
      data: { ...libraryPayload.data, view_state: 'PARTIAL', documents: [quarantinedDocument] },
    })
    workspaceApi.getKnowledgeMap.mockResolvedValue({
      ...mapPayload,
      data: { ...mapPayload.data, nodes: [], edges: [], source_spans: [] },
    })
    documentApi.reinspectDocument.mockResolvedValue({
      document_id: quarantinedDocument.document_id,
      status: 'accepted',
      scanner_version: 'document-safety-v3',
      message: '已提交新版安全策略重新检查',
    })
    render(<Library />)

    await openDetailModal('legacy\\.epub')
    fireEvent.click(await screen.findByRole('button', { name: '使用新版策略重新检查' }))

    await waitFor(() => expect(documentApi.reinspectDocument).toHaveBeenCalledTimes(1))
    expect(documentApi.reinspectDocument).toHaveBeenCalledWith(quarantinedDocument.document_id)
    expect(await screen.findByText('已提交新版安全策略重新检查')).toBeInTheDocument()
  })

  it('复检任务等待期间保持隔离并自动刷新', async () => {
    const pendingReinspection = {
      ...documentView,
      title: 'pending.epub',
      processing_status: 'quarantined',
      moderation_status: 'rejected',
      current_revision_ref: null,
      knowledge_status: 'NOT_MODELED',
      knowledge_unit_count: 0,
      reason_codes: ['CONTENT_QUARANTINED', 'CONTENT_REINSPECTION_PENDING'],
    }
    workspaceApi.getLibraryWorkspace.mockResolvedValue({
      ...libraryPayload,
      data: { ...libraryPayload.data, view_state: 'PARTIAL', documents: [pendingReinspection] },
    })
    workspaceApi.getKnowledgeMap.mockResolvedValue({
      ...mapPayload,
      data: { ...mapPayload.data, nodes: [], edges: [], source_spans: [] },
    })
    render(<Library />)

    // 等待资料库加载完成
    expect(await screen.findByText('pending.epub')).toBeInTheDocument()

    // 打开弹窗，等待期间不应暴露「使用新版策略重新检查」按钮，防止重复提交
    await openDetailModal('pending\\.epub')
    expect(screen.queryByRole('button', { name: '使用新版策略重新检查' })).not.toBeInTheDocument()
    await waitFor(
      () => expect(workspaceApi.getLibraryWorkspace.mock.calls.length).toBeGreaterThan(1),
      { timeout: 4000 },
    )
  })

  it('批量归档资料而不调用物理删除', async () => {
    documentApi.batchOrganizeDocuments.mockResolvedValue({
      schema_version: '1.0',
      operation_id: '44444444-4444-4444-8444-444444444444',
      results: [{ document_id: documentView.document_id, status: 'archived', metadata_version: 2 }],
    })
    workspaceApi.getLibraryWorkspace
      .mockResolvedValueOnce(libraryPayload)
      .mockResolvedValue({ ...libraryPayload, data: { ...libraryPayload.data, total: 0, documents: [] } })
    render(<Library />)
    await screen.findByText('函数基础.md')

    fireEvent.click(screen.getByRole('checkbox', { name: '选择资料 函数基础.md' }))
    fireEvent.click(screen.getByRole('button', { name: '归档' }))

    await waitFor(() => expect(documentApi.batchOrganizeDocuments).toHaveBeenCalledWith(expect.objectContaining({
      document_ids: [documentView.document_id],
      expected_versions: { [documentView.document_id]: 1 },
      archive: true,
    })))
    expect(await screen.findByText('所选资料已归档，可在归档视图恢复。')).toBeInTheDocument()
  })

  it('搜索正文并以版本命令更新资料信息', async () => {
    documentApi.updateDocumentMetadata.mockResolvedValue({
      document_id: documentView.document_id,
      metadata_version: 2,
      display_title: '函数与映射',
      subject: '数学',
      author: null,
      language: null,
    })
    render(<Library />)
    await screen.findByText('函数基础.md')

    fireEvent.change(screen.getByRole('textbox', { name: '搜索资料' }), { target: { value: '映射关系' } })
    fireEvent.submit(screen.getByRole('textbox', { name: '搜索资料' }).closest('form'))
    await waitFor(() => expect(workspaceApi.getLibraryWorkspace).toHaveBeenLastCalledWith(expect.objectContaining({ query: '映射关系' })))

    await openDetailModal('函数基础\\.md')
    fireEvent.click(screen.getByText('编辑资料信息'))
    fireEvent.change(screen.getByRole('textbox', { name: '显示标题' }), { target: { value: '函数与映射' } })
    fireEvent.click(screen.getByRole('button', { name: '保存信息' }))
    await waitFor(() => expect(documentApi.updateDocumentMetadata).toHaveBeenCalledWith(
      documentView.document_id,
      expect.objectContaining({ expected_version: 1, display_title: '函数与映射' }),
    ))
    expect(await screen.findByText('资料信息已保存；原文件与知识 revision 未改变。')).toBeInTheDocument()
  })

  it('扫描 PDF 不提供 OCR 复核，只展示诚实处理状态（UI-LIB-003）', async () => {
    const pdfDocument = {
      ...documentView,
      title: '扫描讲义.pdf',
      media_type: 'application/pdf',
      knowledge_status: 'NOT_MODELED',
      knowledge_unit_count: 0,
    }
    workspaceApi.getLibraryWorkspace.mockResolvedValue({
      ...libraryPayload,
      data: { ...libraryPayload.data, documents: [pdfDocument] },
    })
    render(<Library />)

    expect(await screen.findByText('扫描讲义.pdf')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /识别扫描 PDF/ })).not.toBeInTheDocument()
    expect(screen.queryByText('扫描 PDF 文字复核')).not.toBeInTheDocument()
    // 卡片诚实展示「尚未建模」状态，不伪装成已理解
    expect(screen.getAllByText('尚未建模').length).toBeGreaterThan(0)
    expect(documentApi.requestDocumentOcr).not.toHaveBeenCalled()
  })

  it('从恢复中心深链不再打开 OCR 人工复核（UI-LIB-003）', async () => {
    const runId = '55555555-5555-4555-8555-555555555555'
    window.location.hash = `#/library?document=${documentView.document_id}&ocrRun=${runId}`
    render(<Library />)

    expect(await screen.findByRole('heading', { name: '资料库' })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: '扫描 PDF 文字复核' })).not.toBeInTheDocument()
    expect(documentApi.getDocumentOcrRun).not.toHaveBeenCalled()
  })

  it('扫描 PDF 无可靠文本时显示未建模，不伪装成已理解（EXP-PARSE-001）', async () => {
    const pdfDocument = {
      ...documentView,
      title: '纯扫描件.pdf',
      media_type: 'application/pdf',
      knowledge_status: 'NOT_MODELED',
      knowledge_unit_count: 0,
    }
    workspaceApi.getLibraryWorkspace.mockResolvedValue({
      ...libraryPayload,
      data: { ...libraryPayload.data, documents: [pdfDocument] },
    })
    render(<Library />)

    expect(await screen.findByText('纯扫描件.pdf')).toBeInTheDocument()
    // 卡片直接展示「尚未建模」，与知识空状态一致
    expect(screen.getAllByText('尚未建模').length).toBeGreaterThan(0)
    expect(screen.queryByText('扫描 PDF 文字复核')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /识别扫描 PDF/ })).not.toBeInTheDocument()
    expect(documentApi.reviewDocumentOcrRun).not.toHaveBeenCalled()
  })

  it('不把查询失败渲染为一个空资料库', async () => {
    workspaceApi.getLibraryWorkspace.mockRejectedValueOnce({ response: { status: 503 } })
    render(<Library />)

    expect(await screen.findByRole('alert')).toHaveTextContent('资料库暂时无法读取')
    expect(screen.getByRole('button', { name: '重试' })).toBeInTheDocument()
    expect(screen.queryByText('还没有符合条件的资料')).not.toBeInTheDocument()
  })
})
