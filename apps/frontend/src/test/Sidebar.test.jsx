import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import Sidebar from '../components/Sidebar'
import { RouterProvider } from '../router'

vi.mock('../hooks/useAuth', () => ({
  useAuth: () => ({ user: { nickname: '测试用户' } }),
}))

describe('UI01-VSLICE-AC-001 responsive navigation', () => {
  it('exposes exactly the seven canonical destinations without chat-first navigation', () => {
    render(<RouterProvider><Sidebar /></RouterProvider>)

    const links = screen.getAllByRole('link')
    expect(links.map((link) => link.textContent)).toEqual([
      '今天',
      '学习目标',
      '学习路径',
      '资料库',
      '学习证据',
      '历史记录',
      '设置',
    ])
    expect(screen.queryByText('对话学习')).not.toBeInTheDocument()
  })

  it('contains focus in the open drawer and returns it on Escape', async () => {
    render(<RouterProvider><Sidebar /></RouterProvider>)
    const trigger = screen.getByRole('button', { name: '打开导航菜单' })
    fireEvent.click(trigger)

    const drawer = screen.getByRole('dialog', { name: '主导航' })
    const links = screen.getAllByRole('link')
    await waitFor(() => expect(links[0]).toHaveFocus())

    links.at(-1).focus()
    fireEvent.keyDown(document, { key: 'Tab' })
    expect(trigger).toHaveFocus()

    fireEvent.keyDown(document, { key: 'Escape' })
    expect(drawer).not.toHaveClass('open')
    expect(trigger).toHaveFocus()
  })
})
