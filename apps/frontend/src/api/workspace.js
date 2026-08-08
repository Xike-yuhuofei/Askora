import api from './client'

export const getTodayWorkspace = (timezone = Intl.DateTimeFormat().resolvedOptions().timeZone) =>
  api.get('/workspace/today', { params: { timezone: timezone || 'Asia/Shanghai' } })
    .then((response) => response.data)

export const getLibraryWorkspace = ({ status, subject, page = 1, pageSize = 20 } = {}) =>
  api.get('/workspace/library', {
    params: {
      ...(status ? { status } : {}),
      ...(subject ? { subject } : {}),
      page,
      page_size: pageSize,
    },
  }).then((response) => response.data)

export const getKnowledgeMap = (documentId) =>
  api.get('/workspace/knowledge-map', { params: { document_id: documentId } })
    .then((response) => response.data)
