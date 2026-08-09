import api from './client'

const unsupportedStatus = Object.freeze({
  schema_version: '1.0',
  protection_state: 'UNSUPPORTED',
  supported_mode: 'UNSUPPORTED',
  last_verified: null,
  automatic_backup: { enabled: false, next_due_at: null, last_error_code: null },
  erasure_checkpoint: 0,
  reason_codes: ['DATA_MODE_UNSUPPORTED'],
})

function bridge() {
  return typeof window !== 'undefined' ? window.electronAPI : undefined
}

export async function getDataControlStatus() {
  const api = bridge()
  if (!api?.getDataControlStatus) return unsupportedStatus
  return api.getDataControlStatus()
}

export async function createVerifiedBackup({ saveExternalCopy = false } = {}) {
  const api = bridge()
  if (!api?.createVerifiedBackup) throw new Error('DATA_MODE_UNSUPPORTED')
  return api.createVerifiedBackup({ saveExternalCopy: saveExternalCopy === true })
}

export async function chooseAndVerifyBackup() {
  const api = bridge()
  if (!api?.chooseAndVerifyBackup) throw new Error('DATA_MODE_UNSUPPORTED')
  return api.chooseAndVerifyBackup()
}

export async function chooseAndRestoreBackup() {
  const api = bridge()
  if (!api?.chooseAndRestoreBackup) throw new Error('DATA_MODE_UNSUPPORTED')
  return api.chooseAndRestoreBackup()
}

export async function revealRecoveryKey() {
  const api = bridge()
  if (!api?.revealRecoveryKey) throw new Error('DATA_MODE_UNSUPPORTED')
  return api.revealRecoveryKey()
}

export function onMaintenanceState(callback) {
  const api = bridge()
  if (!api?.onMaintenanceState) return () => {}
  return api.onMaintenanceState(callback)
}

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
