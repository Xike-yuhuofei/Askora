import { describe, expect, it } from 'vitest'

import { resolveRoute } from '../App'

describe('UI-IA-AC-001/003/008 route contract', () => {
  it.each([
    ['/', '/today'],
    ['/profile', '/evidence'],
    ['/knowledge', '/library'],
    ['/account', '/settings'],
  ])('maps legacy %s to canonical %s without creating state', (from, to) => {
    expect(resolveRoute(from)).toEqual({ type: 'redirect', to })
  })

  it('keeps compatibility session and canonical activity identities separate', () => {
    expect(resolveRoute('/quick/session-1')).toMatchObject({
      type: 'workspace',
      sessionId: 'session-1',
    })
    expect(resolveRoute('/learn/activity-1')).toMatchObject({
      type: 'activity-unavailable',
      activityId: 'activity-1',
    })
  })

  it('exposes the seven canonical standard destinations', () => {
    expect(resolveRoute('/today').type).toBe('page')
    expect(resolveRoute('/goals')).toMatchObject({ type: 'unavailable', kind: 'goals' })
    expect(resolveRoute('/path')).toMatchObject({ type: 'unavailable', kind: 'path' })
    expect(resolveRoute('/library').type).toBe('page')
    expect(resolveRoute('/evidence')).toMatchObject({ type: 'unavailable', kind: 'evidence' })
    expect(resolveRoute('/history').type).toBe('page')
    expect(resolveRoute('/settings').type).toBe('page')
  })
})
