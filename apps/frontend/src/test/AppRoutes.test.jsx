import { describe, expect, it } from 'vitest'

import { resolveRoute } from '../App'

describe('UI-IA-AC-001/003/008 route contract', () => {
  it.each([
    ['/', '/today'],
    ['/profile', '/learning/progress'],
    ['/knowledge', '/library'],
    ['/goals', '/learning/goals'],
    ['/path', '/learning/plan'],
    ['/evidence', '/learning/progress'],
    ['/history', '/learning/history'],
  ])('maps legacy %s to canonical %s without creating state', (from, to) => {
    expect(resolveRoute(from)).toEqual({ type: 'redirect', to })
  })

  it('keeps compatibility session and canonical activity identities separate', () => {
    expect(resolveRoute('/quick/session-1')).toMatchObject({
      type: 'workspace',
      sessionId: 'session-1',
    })
    expect(resolveRoute('/learn/activity-1')).toMatchObject({
      type: 'activity-learning',
      activityId: 'activity-1',
    })
  })

  it('routes a document-scoped UI-02B1 launch without treating it as a dialog session', () => {
    expect(resolveRoute('/book-learning/document%201')).toMatchObject({
      type: 'book-learning',
      documentId: 'document 1',
      shell: 'standard',
    })
  })

  it('exposes canonical standard and owner-recovery destinations', () => {
    expect(resolveRoute('/today').type).toBe('page')
    expect(resolveRoute('/learning').type).toBe('page')
    expect(resolveRoute('/learning/goals').type).toBe('page')
    expect(resolveRoute('/learning/plan').type).toBe('page')
    expect(resolveRoute('/learning/progress').type).toBe('page')
    expect(resolveRoute('/learning/history').type).toBe('page')
    expect(resolveRoute('/library').type).toBe('page')
    expect(resolveRoute('/settings').type).toBe('page')
    expect(resolveRoute('/settings/recovery').type).toBe('page')
    expect(resolveRoute('/learning')).toMatchObject({ type: 'page', shell: 'workspace' })
  })

  it('routes goal creation, draft, detail and edit under /learning/goals without exposing ids as labels', () => {
    expect(resolveRoute('/goals/new')).toMatchObject({ type: 'redirect', to: '/learning/goals' })
    expect(resolveRoute('/learning/goals/new')).toMatchObject({ type: 'goal-editor', shell: 'learning' })
    expect(resolveRoute('/learning/goals/drafts/draft%201')).toMatchObject({
      type: 'goal-editor', draftId: 'draft 1', shell: 'learning',
    })
    expect(resolveRoute('/learning/goals/goal%201')).toMatchObject({
      type: 'goal-detail', goalId: 'goal 1', shell: 'learning',
    })
    expect(resolveRoute('/learning/goals/goal%201/edit')).toMatchObject({
      type: 'goal-editor', editGoalId: 'goal 1', shell: 'learning',
    })
  })

  it('recognises /welcome as the protected first-use onboarding page without redirect', () => {
    expect(resolveRoute('/welcome')).toMatchObject({
      type: 'page',
      Page: expect.anything(),
      shell: 'standard',
    })
  })

  it.each([
    ['/today', 'page'],
    ['/learning', 'page'],
    ['/learning/goals', 'page'],
    ['/learning/plan', 'page'],
    ['/learning/progress', 'page'],
    ['/learning/history', 'page'],
    ['/library', 'page'],
    ['/settings', 'page'],
    ['/learn/activity-1', 'activity-learning'],
    ['/book-learning/doc-1', 'book-learning'],
    ['/settings/recovery', 'page'],
  ])('preserves explicit deep link %s as %s instead of forcing /welcome', (path, expectedType) => {
    const result = resolveRoute(path)
    expect(result.type).toBe(expectedType)
  })
})
