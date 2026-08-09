import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  createVerifiedBackup,
  getDataControlStatus,
  onMaintenanceState,
} from '../api/dataControl'

afterEach(() => {
  delete window.electronAPI
})

describe('data-control desktop bridge', () => {
  it('reports unsupported outside the trusted Electron bridge', async () => {
    const status = await getDataControlStatus()

    expect(status.protection_state).toBe('UNSUPPORTED')
    expect(status.reason_codes).toEqual(['DATA_MODE_UNSUPPORTED'])
  })

  it('normalizes backup options before crossing IPC', async () => {
    const create = vi.fn().mockResolvedValue({ point: { status: 'VERIFIED' } })
    window.electronAPI = { createVerifiedBackup: create }

    const result = await createVerifiedBackup({ saveExternalCopy: 'yes' })

    expect(create).toHaveBeenCalledWith({ saveExternalCopy: false })
    expect(result.point.status).toBe('VERIFIED')
  })

  it('returns the exact unsubscribe function from preload', () => {
    const unsubscribe = vi.fn()
    const subscribe = vi.fn().mockReturnValue(unsubscribe)
    window.electronAPI = { onMaintenanceState: subscribe }
    const callback = vi.fn()

    expect(onMaintenanceState(callback)).toBe(unsubscribe)
    expect(subscribe).toHaveBeenCalledWith(callback)
  })
})
