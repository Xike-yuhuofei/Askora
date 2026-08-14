import { describe, expect, it } from 'vitest'

import { resolveRoute } from '../App'

describe('UI-IA-AC-001/003/008 route contract', () => {
  it.each([
    ['/today', '/chat'],
    ['/learning', '/learning/goals'],
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
    expect(resolveRoute('/chat')).toMatchObject({ type: 'page', shell: 'standard' })
    expect(resolveRoute('/learning/goals').type).toBe('page')
    expect(resolveRoute('/learning/plan').type).toBe('page')
    expect(resolveRoute('/learning/progress').type).toBe('page')
    expect(resolveRoute('/learning/history').type).toBe('page')
    expect(resolveRoute('/library').type).toBe('page')
    expect(resolveRoute('/spaces').type).toBe('page')
    expect(resolveRoute('/courses/new').type).toBe('page')
    expect(resolveRoute('/courses/ws-1')).toMatchObject({ type: 'page', shell: 'workspace', workspace_id: 'ws-1' })
    expect(resolveRoute('/courses/ws-1/activities/act-1')).toMatchObject({
      type: 'activity-learning',
      activityId: 'act-1',
      workspace_id: 'ws-1',
    })
    expect(resolveRoute('/settings').type).toBe('page')
    expect(resolveRoute('/settings/recovery').type).toBe('page')
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

  it('treats the new-conversation page as the default home destination (/ and /chat both render it without redirect)', () => {
    expect(resolveRoute('/')).toMatchObject({
      type: 'page',
      Page: expect.anything(),
      shell: 'standard',
    })
    expect(resolveRoute('/chat')).toMatchObject({
      type: 'page',
      Page: expect.anything(),
      shell: 'standard',
    })
    expect(resolveRoute('/welcome').type).toBe('not-found')
  })

  it.each([
    ['/learning/goals', 'page'],
    ['/learning/plan', 'page'],
    ['/learning/progress', 'page'],
    ['/learning/history', 'page'],
    ['/library', 'page'],
    ['/settings', 'page'],
    ['/learn/activity-1', 'activity-learning'],
    ['/book-learning/doc-1', 'book-learning'],
    ['/settings/recovery', 'page'],
  ])('preserves explicit deep link %s as %s instead of forcing a new destination', (path, expectedType) => {
    const result = resolveRoute(path)
    expect(result.type).toBe(expectedType)
  })
})
