import api from './client'

const controlHeaders = (token) => ({ 'X-Deletion-Control': token })

export const previewDeletion = () =>
  api.post('/account/deletion/preview').then((response) => response.data)

export const requestDeletion = (command) =>
  api.post('/account/deletion/request', command, { _skipRefresh: true }).then((response) => response.data)

export const getDeletionStatus = (token) =>
  api.get('/account/deletion/status', {
    headers: controlHeaders(token), skipAuth: true, _skipRefresh: true,
  }).then((response) => response.data)

export const cancelDeletion = (token, command) =>
  api.post('/account/deletion/cancel', command, {
    headers: controlHeaders(token), skipAuth: true, _skipRefresh: true,
  }).then((response) => response.data)

export const retryDeletion = (token, command) =>
  api.post('/account/deletion/retry', command, {
    headers: controlHeaders(token), skipAuth: true, _skipRefresh: true,
  }).then((response) => response.data)
