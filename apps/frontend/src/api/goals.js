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

export const pauseGoal = (goalId, body) =>
  api.post(`/goals/${encode(goalId)}/pause`, body).then((response) => response.data)

export const resumeGoal = (goalId, body) =>
  api.post(`/goals/${encode(goalId)}/resume`, body).then((response) => response.data)

export const archiveGoal = (goalId, body) =>
  api.post(`/goals/${encode(goalId)}/archive`, body).then((response) => response.data)

export const copyArchivedGoal = (goalId, body) =>
  api.post(`/goals/${encode(goalId)}/copy`, body).then((response) => response.data)

export const scheduleGoalAssessments = (goalId, body) =>
  api.post(`/goals/${encode(goalId)}/assessments`, body).then((response) => response.data)

export const getGoalAchievement = (goalId) =>
  api.get(`/goals/${encode(goalId)}/achievement`).then((response) => response.data)

export const submitGoalAssessment = (goalId, activityId, body) =>
  api.post(`/goals/${encode(goalId)}/assessments/${encode(activityId)}/submit`, body)
    .then((response) => response.data)

export const evaluateGoalAchievement = (goalId, body) =>
  api.post(`/goals/${encode(goalId)}/achievement/evaluate`, body).then((response) => response.data)

export const confirmGoalAchievement = (goalId, body) =>
  api.post(`/goals/${encode(goalId)}/achieve`, body).then((response) => response.data)
