import { describe, expect, it } from 'vitest'

import { normalizeApiError } from '../api/client'

describe('ERROR-002 client normalization', () => {
  it('uses structured code/category/retry/correlation without text matching', () => {
    expect(normalizeApiError({
      response: {
        data: {
          error: {
            code: 'AI_PROVIDER_RATE_LIMITED',
            category: 'transient',
            message: '任意本地化文案',
            retryable: true,
            correlation_id: 'corr-429',
            details: null,
            recovery: { retry_after_seconds: 17, actions: [] },
          },
        },
      },
    })).toEqual({
      code: 'AI_PROVIDER_RATE_LIMITED',
      category: 'transient',
      message: '任意本地化文案',
      retryable: true,
      correlation_id: 'corr-429',
      details: null,
      recovery: { retry_after_seconds: 17, actions: [] },
    })
  })
})
