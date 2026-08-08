import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as dialogApi from '../api/dialog'
import TutorWorkspace from '../pages/TutorWorkspace'
import { RouterProvider } from '../router'

vi.mock('../api/dialog', () => ({
  getSession: vi.fn(),
  getMessages: vi.fn(),
  getSessions: vi.fn(),
  sendMessage: vi.fn(),
}))

describe('UI-SCREEN-AC-011 compatibility tutor workspace', () => {
  beforeEach(() => {
    window.location.hash = '#/quick/session-1'
    dialogApi.getSession.mockResolvedValue({
      id: 'session-1',
      subject: 'math',
      topic: null,
      status: 'active',
    })
    dialogApi.getMessages.mockResolvedValue({
      items: [
        { id: 'm1', role: 'user', content: '我先尝试求导。', turn_number: 1 },
        { id: 'm2', role: 'assistant', content: '先写出复合函数结构。', render_payload: null, turn_number: 1 },
      ],
    })
    dialogApi.getSessions.mockResolvedValue({
      items: [{ id: 'session-1', subject: 'math', knowledge_point: '函数与导数', status: 'active' }],
    })
  })

  it('renders durable messages while marking unavailable canonical context', async () => {
    render(<RouterProvider><TutorWorkspace sessionId="session-1" /></RouterProvider>)

    expect(await screen.findByRole('heading', { name: '函数与导数' })).toBeInTheDocument()
    expect(screen.getByText('兼容快速学习')).toBeInTheDocument()
    expect(screen.getByText('我先尝试求导。')).toBeInTheDocument()
    expect(screen.getByText('先写出复合函数结构。')).toBeInTheDocument()
    expect(screen.getAllByText('当前记录不可用')).toHaveLength(2)
    expect(screen.getByText(/不会从旧 hint level/)).toBeInTheDocument()
  })
})
