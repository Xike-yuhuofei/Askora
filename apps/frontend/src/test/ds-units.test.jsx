import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import Alert from '../components/ui/Alert'
import Button from '../components/ui/Button'
import Composer from '../components/ui/Composer'
import StatusTag from '../components/ui/StatusTag'
import NoticeModal from '../components/NoticeModal'
import RightRail from '../components/RightRail'
import Sidebar from '../components/Sidebar'
import { RouterProvider } from '../router'

vi.mock('../api/workspace', () => ({
  listWorkspaces: vi.fn().mockResolvedValue({ data: { workspaces: [] } }),
  listWorkspaceActivities: vi.fn().mockResolvedValue({ data: { activities: [] } }),
  conversationHref: vi.fn(),
}))

describe('TraeWork Light reusable units', () => {
  it('renders button intents including disabled and focus', () => {
    const { container } = render(
      <>
        <Button variant="brand">新建空间</Button>
        <Button variant="secondary">次要</Button>
        <Button variant="ghost">安静</Button>
        <Button variant="danger" disabled>删除</Button>
      </>,
    )

    const brand = screen.getByRole('button', { name: '新建空间' })
    expect(brand.className).toContain('ds-btn--brand')
    expect(screen.getByRole('button', { name: '次要' }).className).toContain('ds-btn--secondary')
    expect(screen.getByRole('button', { name: '安静' }).className).toContain('ds-btn--ghost')
    expect(screen.getByRole('button', { name: '删除' })).toBeDisabled()

    brand.focus()
    expect(brand).toHaveFocus()
    fireEvent.mouseEnter(brand)
    expect(container.querySelectorAll('.ds-btn').length).toBe(4)
  })

  it('renders composer anatomy and keeps send disabled when empty', () => {
    const { rerender } = render(
      <Composer id="c1" label="写下你的想法" value="" onChange={() => {}} sendDisabled />,
    )
    expect(screen.getByLabelText('写下你的想法')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '发送' })).toBeDisabled()

    rerender(
      <Composer id="c1" label="写下你的想法" value="已有内容" onChange={() => {}} />,
    )
    expect(screen.getByRole('button', { name: '发送' })).not.toBeDisabled()
  })

  it('renders status tags and alerts with text, not color-only meaning', () => {
    render(
      <>
        <StatusTag tone="success">已验证</StatusTag>
        <StatusTag tone="warning">待独立验证</StatusTag>
        <Alert tone="danger" title="保存失败">请重试，数据仍在本地。</Alert>
      </>,
    )
    expect(screen.getByText('已验证').className).toContain('ds-tag--success')
    expect(screen.getByText('待独立验证').className).toContain('ds-tag--warning')
    expect(screen.getByRole('status')).toHaveTextContent('保存失败')
    expect(screen.getByRole('status')).toHaveTextContent('请重试，数据仍在本地。')
  })

  it('closes the shipped dialog on Escape after an API notice', () => {
    render(<NoticeModal />)
    fireEvent(window, new CustomEvent('app:api-error', { detail: { message: '暂时不可用', request_id: 'r1' } }))
    expect(screen.getByRole('dialog')).toBeInTheDocument()
    fireEvent.keyDown(document, { key: 'Escape' })
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('exposes space-centric shell roles instead of Today/Learning L0', () => {
    render(<RouterProvider><Sidebar /></RouterProvider>)
    expect(screen.getByRole('button', { name: '空间管理' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: '资料库' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: '账户设置' })).toBeInTheDocument()
    expect(screen.queryByRole('link', { name: '恢复中心' })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: '欢迎' })).not.toBeInTheDocument()
    expect(screen.queryByText('课程')).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: '今天' })).not.toBeInTheDocument()
    expect(screen.queryByRole('link', { name: '学习' })).not.toBeInTheDocument()
    expect(screen.queryByText('私人本地应用')).not.toBeInTheDocument()
  })

  it('styles the notes rail as the TraeWork right pane', () => {
    render(<RightRail workspaceId="ws-1" />)
    const notes = screen.getByLabelText('参考资料与笔记')
    expect(notes.className).toContain('right-rail')
    expect(notes.className).toContain('ds-shell-three-panel__right')
    expect(notes).toHaveAttribute('data-workspace-id', 'ws-1')
    expect(screen.getByRole('button', { name: '收起右侧栏' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: '收起右侧栏' }))
    expect(screen.getByRole('button', { name: '展开右侧栏' })).toBeInTheDocument()
    expect(screen.getByLabelText('参考资料与笔记（已收起）').className).toContain('right-rail--collapsed')
  })
})
