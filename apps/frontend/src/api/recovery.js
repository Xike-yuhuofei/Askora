import api from './client'

export async function listRecoveryIssues() {
  const response = await api.get('/recovery/issues')
  return response.data
}

export async function executeRecoveryAction(command) {
  const response = await api.post('/recovery/actions', command)
  return response.data
}
