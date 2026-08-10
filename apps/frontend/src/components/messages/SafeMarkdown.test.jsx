import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import SafeMarkdown from './SafeMarkdown'

describe('SafeMarkdown RENDER-AC emphasis cleanup', () => {
  it('strips stray emphasis markers that micromark cannot close around CJK quotes', () => {
    render(
      <SafeMarkdown source="根据资料，A 认为**“和优秀的人做有挑战的事”比“管人”和“title”**更重要。" />,
    )
    expect(screen.queryByText(/[*]/)).not.toBeInTheDocument()
    expect(screen.getByText(/比“管人”和“title”/)).toBeInTheDocument()
  })

  it('strips stray triple-asterisk artifacts', () => {
    const { container } = render(<SafeMarkdown source="***重点内容**保持可读。" />)
    expect(screen.queryByText(/[*]/)).not.toBeInTheDocument()
    expect(container).toHaveTextContent('重点内容保持可读')
  })

  it('keeps well-formed bold emphasis rendered as strong', () => {
    const { container } = render(<SafeMarkdown source="这里**很重要**，请记牢。" />)
    expect(container.querySelector('strong')).toBeInTheDocument()
    expect(screen.getByText('很重要')).toBeInTheDocument()
  })

  it('does not touch math or inline code content', () => {
    const { container } = render(
      <SafeMarkdown source="公式 $a^2 + b^2$ 与代码 `2 * 3` 均保留。" />,
    )
    expect(container.querySelector('.katex')).toBeInTheDocument()
    expect(screen.getByText('2 * 3')).toBeInTheDocument()
  })
})