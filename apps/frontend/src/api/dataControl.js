import api from './client'

export async function createUserExport({ scopes, includeDocumentOriginals = false }) {
  const response = await api.post('/data-control/exports', {
    scopes,
    include_document_originals: includeDocumentOriginals === true,
  })
  return response.data
}

export async function downloadUserExport({ exportId, token }) {
  const response = await api.get(`/data-control/exports/${exportId}`, {
    headers: { 'X-Askora-Export-Token': token },
    responseType: 'blob',
  })
  const disposition = response.headers?.['content-disposition'] || ''
  const encodedName = disposition.match(/filename\*=UTF-8''([^;]+)/i)?.[1]
  const filename = encodedName
    ? decodeURIComponent(encodedName)
    : `Askora-user-data-${exportId}.zip`
  const objectURL = URL.createObjectURL(response.data)
  try {
    const link = document.createElement('a')
    link.href = objectURL
    link.download = filename
    link.click()
  } finally {
    URL.revokeObjectURL(objectURL)
  }
}

export async function createErasurePreview({ scope, targetRef = null }) {
  const response = await api.post('/data-control/erasures/preview', {
    scope,
    target_ref: targetRef,
  })
  return response.data
}

export async function confirmErasure({
  previewId,
  confirmationToken,
  confirmationPhrase,
  idempotencyKey,
}) {
  const response = await api.post('/data-control/erasures/confirm', {
    preview_id: previewId,
    confirmation_token: confirmationToken,
    confirmation_phrase: confirmationPhrase,
    idempotency_key: idempotencyKey,
  })
  return response.data
}