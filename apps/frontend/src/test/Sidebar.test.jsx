import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import Sidebar from '../components/Sidebar'
import { RouterProvider } from '../router'

describe('UI01-VSLICE-AC-001 responsive navigation', () => {
  it('exposes the three product domains and utility destinations', () => {
    render(<RouterProvider><Sidebar /></RouterProvider>)

    expect(screen.getByRole('button', { name: '新课程' })).toBeInTheDocument()
    expect(screen.getByText('课程')).toBeInTheDocument()
    const links = screen.getAllByRole('link')
    expect(links.map((link) => link.textContent)).toEqual([
      '资料库',
      '设置',
    ])
    expect(screen.queryByRole('link', { name: '今天' })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: '学习' })).not.toBeInTheDocument()
    expect(screen.queryByText('对话学习')).not.toBeInTheDocument()
    expect(screen.queryByText('私人本地应用')).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: '恢复中心' })).not.toBeInTheDocument()
    expect(screen.getByRole('navigation', { name: '工具' }).textContent).toMatch(/设置/)
    expect(screen.getByRole('button', { name: '收起左侧栏' })).toBeInTheDocument()
  })

  it('collapses and expands the left sidebar from the always-visible control', () => {
    const { container } = render(<RouterProvider><Sidebar /></RouterProvider>)
    const toggle = screen.getByRole('button', { name: '收起左侧栏' })
    expect(toggle).toHaveAttribute('aria-expanded', 'true')
    fireEvent.click(toggle)
    expect(screen.getByRole('button', { name: '展开左侧栏' })).toHaveAttribute('aria-expanded', 'false')
    expect(container.querySelector('#primary-sidebar')).toHaveClass('sidebar--collapsed')
    fireEvent.click(screen.getByRole('button', { name: '展开左侧栏' }))
    expect(screen.getByRole('button', { name: '收起左侧栏' })).toBeInTheDocument()
    expect(container.querySelector('#primary-sidebar')).not.toHaveClass('sidebar--collapsed')
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
