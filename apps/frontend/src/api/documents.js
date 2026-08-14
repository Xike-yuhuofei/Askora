import api from './client'

export const uploadDocument = (file, subject = '') => {
  const formData = new FormData()
  formData.append('file', file)
  if (subject.trim()) formData.append('subject', subject.trim())
  return api.post('/documents/upload', formData).then((response) => response.data)
}

export const listUnassignedMaterials = () =>
  api.get('/documents/unassigned').then((response) => response.data)

export const assignMaterial = (documentId, body) =>
  api.post(`/documents/${encodeURIComponent(documentId)}/assign`, body)
    .then((response) => response.data)

export const deleteDocument = (documentId) =>
  api.delete(`/documents/${encodeURIComponent(documentId)}`)
    .then((response) => response.data)

export const reinspectDocument = (documentId) =>
  api.post(`/documents/${encodeURIComponent(documentId)}/reinspect`)
    .then((response) => response.data)

export const createLibraryTag = (name, idempotencyKey) =>
  api.post('/documents/library/tags', { name, idempotency_key: idempotencyKey })
    .then((response) => response.data)

export const createLibraryCollection = (name, idempotencyKey) =>
  api.post('/documents/library/collections', { name, idempotency_key: idempotencyKey })
    .then((response) => response.data)

export const updateDocumentMetadata = (documentId, payload) =>
  api.patch(`/documents/${encodeURIComponent(documentId)}/metadata`, payload)
    .then((response) => response.data)

export const batchOrganizeDocuments = (payload) =>
  api.post('/documents/batch/organize', payload).then((response) => response.data)

export const getDuplicateSuggestions = (status = 'pending') =>
  api.get('/documents/duplicates', { params: { status } }).then((response) => response.data)

export const resolveDuplicateSuggestion = (suggestionId, payload) =>
  api.post(`/documents/duplicates/${encodeURIComponent(suggestionId)}/resolve`, payload)
    .then((response) => response.data)

export const requestDocumentOcr = (documentId, payload) =>
  api.post(`/documents/${encodeURIComponent(documentId)}/ocr-runs`, payload)
    .then((response) => response.data)

export const getDocumentOcrRun = (runId) =>
  api.get(`/documents/ocr-runs/${encodeURIComponent(runId)}`)
    .then((response) => response.data)

export const reviewDocumentOcrRun = (runId, payload) =>
  api.post(`/documents/ocr-runs/${encodeURIComponent(runId)}/review`, payload)
    .then((response) => response.data)

export const getOcrPageImage = (runId, pageNumber) =>
  api.get(
    `/documents/ocr-runs/${encodeURIComponent(runId)}/pages/${encodeURIComponent(pageNumber)}`,
    { responseType: 'blob' },
  ).then((response) => response.data)
