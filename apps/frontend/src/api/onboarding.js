import api from './client'

function createIdempotencyKey(prefix) {
  const uuid = globalThis.crypto?.randomUUID?.()
  if (uuid) return `${prefix}-${uuid}`
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2)}`
}

export async function getOnboardingJourney() {
  const response = await api.get('/onboarding/journey')
  return response.data
}

export async function acknowledgeBoundaries({ expectedVersion, noticeVersion }) {
  const response = await api.post('/onboarding/preferences', {
    schema_version: '1.0',
    journey_id: 'first-learning-v1',
    expected_preference_version: expectedVersion,
    action: 'ACKNOWLEDGE_BOUNDARIES',
    notice_version: noticeVersion,
    idempotency_key: createIdempotencyKey('onboarding-ack'),
  })
  return response.data
}

export async function dismissOnboarding({ expectedVersion }) {
  const response = await api.post('/onboarding/preferences', {
    schema_version: '1.0',
    journey_id: 'first-learning-v1',
    expected_preference_version: expectedVersion,
    action: 'DISMISS',
    idempotency_key: createIdempotencyKey('onboarding-dismiss'),
  })
  return response.data
}

export async function reopenOnboarding({ expectedVersion }) {
  const response = await api.post('/onboarding/preferences', {
    schema_version: '1.0',
    journey_id: 'first-learning-v1',
    expected_preference_version: expectedVersion,
    action: 'REOPEN',
    idempotency_key: createIdempotencyKey('onboarding-reopen'),
  })
  return response.data
}

export async function finishAndDismissOnboarding({ expectedVersion }) {
  const response = await api.post('/onboarding/preferences', {
    schema_version: '1.0',
    journey_id: 'first-learning-v1',
    expected_preference_version: expectedVersion,
    action: 'FINISH_AND_DISMISS',
    idempotency_key: createIdempotencyKey('onboarding-finish'),
  })
  return response.data
}
