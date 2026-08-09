import api from './client'

const encode = (value) => encodeURIComponent(value)

export const suggestSuccessCriteria = (body) =>
  api.post('/goals/criteria/suggest', body).then((response) => response.data)

export const createGoalDraft = (body) =>
  api.post('/goals/drafts', body).then((response) => response.data)

export const getGoalDraft = (draftId) =>
  api.get(`/goals/drafts/${encode(draftId)}`).then((response) => response.data)

export const updateGoalDraft = (draftId, body) =>
  api.patch(`/goals/drafts/${encode(draftId)}`, body).then((response) => response.data)

export const getGoalTargets = (draftId) =>
  api.get(`/goals/drafts/${encode(draftId)}/targets`).then((response) => response.data)

export const previewGoalDraft = (draftId, body) =>
  api.post(`/goals/drafts/${encode(draftId)}/preview`, body).then((response) => response.data)

export const applyGoalDraft = (draftId, body) =>
  api.post(`/goals/drafts/${encode(draftId)}/apply`, body).then((response) => response.data)

export const getGoalDetail = (goalId) =>
  api.get(`/goals/${encode(goalId)}`).then((response) => response.data)

export const createEditGoalDraft = (goalId, body) =>
  api.post(`/goals/${encode(goalId)}/drafts`, body).then((response) => response.data)

export const getFocusedGoal = () =>
  api.get('/goals/focus').then((response) => response.data)
