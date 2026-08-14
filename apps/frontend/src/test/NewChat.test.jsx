import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import NewChat from '../pages/NewChat'

describe('NewChat — 新建对话（TraeWork 中栏 1:1 复刻）', () => {
  it('renders the hero, composer and suggestion chips from the reference design', () => {
    render(<NewChat />)
    const heading = screen.getByRole('heading', { name: /Code with ?TRAE/ })
    expect(heading).toHaveTextContent('Code with TRAE')
    expect(
      screen.getByPlaceholderText('帮你编写代码、调试 Bug、优化性能等开发工作，交付生产级代码产物。'),
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Kimi-K2.7-Code' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '本地' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Askora' })).toBeInTheDocument()
    for (const label of ['应用开发', '项目理解', '游戏创意', '工具脚本']) {
      expect(screen.getByRole('button', { name: label })).toBeInTheDocument()
    }
  })

  it('renders the composer action buttons (unwired in phase one)', () => {
    render(<NewChat />)
    for (const name of ['添加', '视频', '图片', '网络', '语音输入', '发送']) {
      expect(screen.getByRole('button', { name })).toBeInTheDocument()
    }
  })

  it('keeps the input editable while clicking send does nothing in phase one', () => {
    render(<NewChat />)
    const textarea = screen.getByPlaceholderText(/帮你编写代码/)
    fireEvent.change(textarea, { target: { value: '帮我复习线性代数' } })
    expect(textarea).toHaveValue('帮我复习线性代数')
    fireEvent.click(screen.getByRole('button', { name: '发送' }))
    expect(textarea).toHaveValue('帮我复习线性代数')
    expect(screen.getByRole('heading', { name: /Code with ?TRAE/ })).toBeInTheDocument()
  })

  it('does not leak internal system names into copy', () => {
    render(<NewChat />)
    const body = document.body.textContent || ''
    expect(body).not.toMatch(/SYS0[1-8]/)
    expect(body).not.toMatch(/planner/i)
  })
})
