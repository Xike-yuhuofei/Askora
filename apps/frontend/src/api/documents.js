import api from './client'

export const uploadDocument = (file, subject = '') => {
  const formData = new FormData()
  formData.append('file', file)
  if (subject.trim()) formData.append('subject', subject.trim())
  return api.post('/documents/upload', formData).then((response) => response.data)
}

export const deleteDocument = (documentId) =>
  api.delete(`/documents/${encodeURIComponent(documentId)}`)
    .then((response) => response.data)
