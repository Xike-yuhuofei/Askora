import { fireEvent, render, screen, waitFor } from '@testing-library/react'
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
    vi.stubGlobal('navigator', {
      clipboard: { writeText: vi.fn().mockResolvedValue(undefined) },
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

  it('shows starter suggestions on empty session and sends on click', async () => {
    dialogApi.getMessages.mockResolvedValue({ items: [] })
    render(<RouterProvider><TutorWorkspace sessionId="session-1" /></RouterProvider>)

    expect(await screen.findByText('输入你的问题或想法，开始这一轮兼容学习。')).toBeInTheDocument()
    const chip = screen.getByText('请帮我理解这个知识点')
    expect(chip).toBeInTheDocument()

    dialogApi.sendMessage.mockResolvedValue({ message: { id: 'a1', role: 'assistant', content: '好的。' } })
    fireEvent.click(chip)

    await waitFor(() => {
      expect(dialogApi.sendMessage).toHaveBeenCalledWith('session-1', '请帮我理解这个知识点')
    })
  })

  it('sends message via Enter and renders optimistic echo', async () => {
    dialogApi.getMessages.mockResolvedValue({ items: [] })
    dialogApi.sendMessage.mockResolvedValue({
      message: { id: 'a1', role: 'assistant', content: ' assistant 回复' },
    })
    render(<RouterProvider><TutorWorkspace sessionId="session-1" /></RouterProvider>)

    const textarea = await screen.findByLabelText('学习输入')
    fireEvent.change(textarea, { target: { value: '用户问题' } })
    fireEvent.keyDown(textarea, { key: 'Enter', code: 'Enter' })

    await waitFor(() => {
      expect(screen.getByText('用户问题')).toBeInTheDocument()
    })
    expect(dialogApi.sendMessage).toHaveBeenCalledWith('session-1', '用户问题')
  })

  it('renders inline error and restores input on send failure', async () => {
    dialogApi.getMessages.mockResolvedValue({ items: [] })
    dialogApi.sendMessage.mockRejectedValue({
      response: { data: { error: { message: '发送失败测试' } } },
    })
    render(<RouterProvider><TutorWorkspace sessionId="session-1" /></RouterProvider>)

    const textarea = await screen.findByLabelText('学习输入')
    fireEvent.change(textarea, { target: { value: '会失败的消息' } })
    fireEvent.keyDown(textarea, { key: 'Enter', code: 'Enter' })

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('发送失败测试')
    })
    expect(textarea.value).toBe('会失败的消息')
  })

  it('copies assistant message content', async () => {
    render(<RouterProvider><TutorWorkspace sessionId="session-1" /></RouterProvider>)

    const copyButton = await screen.findByLabelText('复制内容')
    fireEvent.click(copyButton)

    await waitFor(() => {
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith('先写出复合函数结构。')
    })
    expect(await screen.findByLabelText('已复制')).toBeInTheDocument()
  })
})
