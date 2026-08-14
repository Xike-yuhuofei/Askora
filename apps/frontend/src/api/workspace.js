import api from './client'

export const getWorkspaceContext = () =>
  api.get('/workspace/context').then((response) => response.data)

export const getTodayWorkspace = (timezone = Intl.DateTimeFormat().resolvedOptions().timeZone) =>
  api.get('/workspace/today', { params: { timezone: timezone || 'Asia/Shanghai' } })
    .then((response) => response.data)

export const getGoalsWorkspace = () =>
  api.get('/workspace/goals').then((response) => response.data)

export const getLearningPath = (goalId) =>
  api.get('/workspace/path', { params: goalId ? { goal_id: goalId } : {} })
    .then((response) => response.data)

export const getLearningContext = (activityId) =>
  api.get('/workspace/learning-context', {
    params: activityId ? { activity_id: activityId } : {},
  }).then((response) => response.data)

export const getEvidenceWorkspace = () =>
  api.get('/workspace/evidence').then((response) => response.data)

export const getLibraryWorkspace = ({
  status,
  subject,
  query,
  documentId,
  tagId,
  collectionId,
  archived = false,
  sort = 'created_desc',
  page = 1,
  pageSize = 20,
} = {}) =>
  api.get('/workspace/library', {
    params: {
      ...(status ? { status } : {}),
      ...(subject ? { subject } : {}),
      ...(query ? { q: query } : {}),
      ...(documentId ? { document_id: documentId } : {}),
      ...(tagId ? { tag_id: tagId } : {}),
      ...(collectionId ? { collection_id: collectionId } : {}),
      archived,
      sort,
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

export const listWorkspaces = () =>
  api.get('/workspaces').then((response) => response.data)

export const createWorkspace = (body) =>
  api.post('/workspaces', body).then((response) => response.data)

export const renameWorkspace = (workspaceId, body) =>
  api.patch(`/workspaces/${encodeURIComponent(workspaceId)}`, body)
    .then((response) => response.data)

export const switchWorkspace = (workspaceId, body) =>
  api.post(`/workspaces/${encodeURIComponent(workspaceId)}/switch`, body)
    .then((response) => response.data)

export const listWorkspaceActivities = (workspaceId) =>
  api.get(`/workspaces/${encodeURIComponent(workspaceId)}/activities`)
    .then((response) => response.data)

const CLEAR_GUARD = {
  composer_draft: 'CLEAR',
  stream: 'CLEAR',
  user_note: 'CLEAR',
  material_position: 'PRESERVED',
}

export const clearTransitionGuard = () => ({ ...CLEAR_GUARD })

export function parseActivityId(activityRef) {
  if (!activityRef) return null
  const match = String(activityRef).match(/(?:learning_activity|LearningActivity):([^:]+)/i)
  return match ? match[1] : String(activityRef)
}

export function conversationHref(workspaceId, activityRef) {
  const activityId = parseActivityId(activityRef)
  if (!activityId) return null
  if (workspaceId) {
    return `/courses/${encodeURIComponent(workspaceId)}/activities/${encodeURIComponent(activityId)}`
  }
  return `/learn/${encodeURIComponent(activityId)}`
}
