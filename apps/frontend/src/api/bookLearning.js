import api from './client'

export const getReadiness = (documentId) =>
  api.get(`/book-learning/${encodeURIComponent(documentId)}/readiness`)
    .then((response) => response.data)

export const getGoal = (goalId) =>
  api.get(`/book-learning/goals/${encodeURIComponent(goalId)}`)
    .then((response) => response.data)

export const getMapping = (goalId) =>
  api.get(`/book-learning/goals/${encodeURIComponent(goalId)}/mapping`)
    .then((response) => response.data)

export const getDiagnostic = (goalId) =>
  api.get(`/book-learning/goals/${encodeURIComponent(goalId)}/diagnostic`)
    .then((response) => response.data)

export const getPlan = (goalId) =>
  api.get(`/book-learning/goals/${encodeURIComponent(goalId)}/plan`)
    .then((response) => response.data)

export const createGoal = (documentId, body) =>
  api.post(`/book-learning/${encodeURIComponent(documentId)}/goals`, body)
    .then((response) => response.data)

export const confirmGoal = (goalId, body) =>
  api.post(`/book-learning/goals/${encodeURIComponent(goalId)}/confirm`, body)
    .then((response) => response.data)

export const mapGoal = (goalId, body) =>
  api.post(`/book-learning/goals/${encodeURIComponent(goalId)}/mapping`, body)
    .then((response) => response.data)

export const startDiagnostic = (body) =>
  api.post('/book-learning/diagnostics', body).then((response) => response.data)

export const submitDiagnosticResponse = (needId, body) =>
  api.post(`/book-learning/diagnostics/${encodeURIComponent(needId)}/responses`, body)
    .then((response) => response.data)

export const generatePlan = (body) =>
  api.post('/book-learning/plans', body).then((response) => response.data)

export const selectNextActivity = (body) =>
  api.post('/book-learning/activities/select', body).then((response) => response.data)

export const startTeachingRound = (activityId, body) =>
  api.post(`/book-learning/activities/${encodeURIComponent(activityId)}/start`, body)
    .then((response) => response.data)
