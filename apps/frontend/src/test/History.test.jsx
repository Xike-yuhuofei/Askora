import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as dialogApi from '../api/dialog'
import History from '../pages/History'
import { RouterProvider } from '../router'

vi.mock('../api/dialog', () => ({ getSessions: vi.fn() }))

describe('UI01-VSLICE-AC-008 history', () => {
  beforeEach(() => {
    window.location.hash = '#/history'
    dialogApi.getSessions.mockReset()
  })

  it('keeps the empty state distinct from learning completion', async () => {
    dialogApi.getSessions.mockResolvedValue({ items: [] })
    render(<RouterProvider><History /></RouterProvider>)

    expect(await screen.findByText(/完成学习活动后，这里会记录过程/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /开始学习/ })).toBeInTheDocument()
    expect(screen.queryByText('已掌握')).not.toBeInTheDocument()
  })

  it('resumes the selected compatibility session without regenerating it', async () => {
    dialogApi.getSessions.mockResolvedValue({
      items: [{
        id: 'session-history',
        subject: 'math',
        knowledge_point: '概率统计',
        status: 'ended',
        updated_at: '2026-08-08T01:00:00Z',
      }],
    })
    render(<RouterProvider><History /></RouterProvider>)

    fireEvent.click(await screen.findByRole('button', { name: /概率统计/ }))
    await waitFor(() => expect(window.location.hash).toBe('#/quick/session-history'))
    expect(dialogApi.getSessions).toHaveBeenCalledTimes(1)
  })
})
