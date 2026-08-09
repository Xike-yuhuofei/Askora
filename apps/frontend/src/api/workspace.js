import api from './client'

export const getTodayWorkspace = (timezone = Intl.DateTimeFormat().resolvedOptions().timeZone) =>
  api.get('/workspace/today', { params: { timezone: timezone || 'Asia/Shanghai' } })
    .then((response) => response.data)

export const getGoalsWorkspace = () =>
  api.get('/workspace/goals').then((response) => response.data)

export const getLearningPath = (goalId) =>
  api.get('/workspace/path', { params: goalId ? { goal_id: goalId } : {} })
    .then((response) => response.data)

export const getEvidenceWorkspace = () =>
  api.get('/workspace/evidence').then((response) => response.data)

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

export const getActivityLifecycle = (activityId) =>
  api.get(`/workspace/activities/${encodeURIComponent(activityId)}`)
    .then((response) => response.data)

export const startActivity = (activityId, body) =>
  api.post(`/workspace/activities/${encodeURIComponent(activityId)}/start`, body)
    .then((response) => response.data)

export const completeActivity = (activityId, body) =>
  api.post(`/workspace/activities/${encodeURIComponent(activityId)}/complete`, body)
    .then((response) => response.data)
