import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as documentApi from '../api/documents'
import * as workspaceApi from '../api/workspace'
import Library from '../pages/Library'

vi.mock('../api/documents', () => ({
  uploadDocument: vi.fn(),
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

describe('UI02A 资料库', () => {
  beforeEach(() => {
    workspaceApi.getLibraryWorkspace.mockReset()
    workspaceApi.getKnowledgeMap.mockReset()
    documentApi.uploadDocument.mockReset()
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
  })

  it('展示资料、可审计知识候选，并诚实说明不存在已验证关系', async () => {
    render(<Library />)

    expect(await screen.findByRole('heading', { name: '资料库' })).toBeInTheDocument()
    expect(await screen.findByRole('button', { name: /函数的定义/ })).toBeInTheDocument()
    expect(screen.getByText('尚无可核验的知识关系。页面不会用装饰性连线冒充先修关系。')).toBeInTheDocument()
    expect(screen.getByText(/函数描述输入和输出之间的关系/)).toBeInTheDocument()
    expect(screen.getByText('未知，未伪造分数')).toBeInTheDocument()
    expect(screen.getByText('资料与知识')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: '从这份资料开始学习' })).toHaveAttribute(
      'href',
      `#/book-learning/${documentView.document_id}`,
    )
  })

  it('上传真实文件并刷新 Canonical 资料列表', async () => {
    documentApi.uploadDocument.mockResolvedValue({
      document_id: '33333333-3333-4333-8333-333333333333',
      status: 'pending',
      message: '文档已接收，正在后台处理',
    })
    render(<Library />)
    await screen.findByText('函数基础.md')

    fireEvent.change(screen.getByLabelText('学科（可选）'), { target: { value: '数学' } })
    const file = new File(['# 极限'], '极限.md', { type: 'text/markdown' })
    fireEvent.change(screen.getByLabelText('选择要上传的资料'), { target: { files: [file] } })

    await waitFor(() => expect(documentApi.uploadDocument).toHaveBeenCalledWith(file, '数学'))
    expect(await screen.findByText('资料已安全保存，后台处理会在页面中自动更新。')).toBeInTheDocument()
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
    expect((await screen.findAllByText('等待处理')).length).toBeGreaterThan(1)

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

    expect(await screen.findByText('unsafe.epub')).toBeInTheDocument()
    expect(screen.getByRole('button', { pressed: true })).toHaveTextContent('已隔离')
    expect(screen.queryByText('尚未建模')).not.toBeInTheDocument()
    expect(
      await screen.findByText('电子书包包含不安全的文件路径，资料已隔离；知识建模未启动，也不会进入检索或知识地图。'),
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '使用新版策略重新检查' })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: '从这份资料开始学习' })).not.toBeInTheDocument()
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

    expect(
      await screen.findByText('正在使用新版安全策略重新检查；完成前资料继续保持隔离。'),
    ).toBeInTheDocument()
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
    fireEvent.click(screen.getByRole('button', { name: '归档所选' }))

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

    fireEvent.change(screen.getByRole('textbox', { name: '搜索标题与正文' }), { target: { value: '映射关系' } })
    fireEvent.click(screen.getByRole('button', { name: '搜索' }))
    await waitFor(() => expect(workspaceApi.getLibraryWorkspace).toHaveBeenLastCalledWith(expect.objectContaining({ query: '映射关系' })))

    fireEvent.change(screen.getByRole('textbox', { name: '显示标题' }), { target: { value: '函数与映射' } })
    fireEvent.click(screen.getByRole('button', { name: '保存信息' }))
    await waitFor(() => expect(documentApi.updateDocumentMetadata).toHaveBeenCalledWith(
      documentView.document_id,
      expect.objectContaining({ expected_version: 1, display_title: '函数与映射' }),
    ))
    expect(await screen.findByText('资料信息已保存；原文件与知识 revision 未改变。')).toBeInTheDocument()
  })

  it('扫描 PDF 必须人工接受候选后才发布', async () => {
    const pdfDocument = { ...documentView, title: '扫描讲义.pdf', media_type: 'application/pdf' }
    workspaceApi.getLibraryWorkspace.mockResolvedValue({
      ...libraryPayload,
      data: { ...libraryPayload.data, documents: [pdfDocument] },
    })
    const pending = {
      run_id: '55555555-5555-4555-8555-555555555555',
      document_id: pdfDocument.document_id,
      status: 'pending',
      candidates: [],
    }
    const ready = {
      ...pending,
      status: 'review_required',
      page_count: 1,
      candidate_count: 1,
      candidates: [{
        candidate_id: '66666666-6666-4666-8666-666666666666',
        page_number: 1,
        block_index: 0,
        bbox: [10, 20, 300, 70],
        text: '扫描候选文字',
        confidence: 82,
        image_hash: 'a'.repeat(64),
        status: 'candidate',
        corrected_text: null,
        version: 1,
      }],
    }
    documentApi.requestDocumentOcr.mockResolvedValue(pending)
    documentApi.getDocumentOcrRun.mockResolvedValue(ready)
    documentApi.getOcrPageImage.mockResolvedValue(new Blob(['page'], { type: 'image/png' }))
    documentApi.reviewDocumentOcrRun.mockResolvedValue({ ...ready, status: 'accepted' })
    render(<Library />)

    fireEvent.click(await screen.findByRole('button', { name: '识别扫描 PDF' }))
    expect(await screen.findByText('扫描 PDF 文字复核', {}, { timeout: 4000 })).toBeInTheDocument()
    const publish = screen.getByRole('button', { name: '发布已复核文字' })
    expect(publish).toBeDisabled()
    fireEvent.click(screen.getByRole('checkbox', { name: '接受这段文字' }))
    fireEvent.click(publish)

    await waitFor(() => expect(documentApi.reviewDocumentOcrRun).toHaveBeenCalledWith(
      pending.run_id,
      expect.objectContaining({
        publish: true,
        decisions: [expect.objectContaining({ action: 'ACCEPT', corrected_text: '扫描候选文字' })],
      }),
    ))
    expect(await screen.findByText('复核文本已发布为新的可追溯 revision。')).toBeInTheDocument()
  }, 6000)

  it('不把查询失败渲染为一个空资料库', async () => {
    workspaceApi.getLibraryWorkspace.mockRejectedValueOnce({ response: { status: 503 } })
    render(<Library />)

    expect(await screen.findByRole('alert')).toHaveTextContent('资料库暂时无法读取')
    expect(screen.getByRole('button', { name: '重试' })).toBeInTheDocument()
    expect(screen.queryByText('还没有符合条件的资料')).not.toBeInTheDocument()
  })
})
