import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import RichMessage from './RichMessage'

const markdownPayload = {
  schema_version: '1.0',
  blocks: [
    {
      id: 'content',
      type: 'markdown',
      source: '# 判别式\n\n| 条件 | 结论 |\n| --- | --- |\n| $\\Delta > 0$ | 两个实根 |',
    },
  ],
}

describe('RichMessage RENDER-AC-001..005', () => {
  it('renders historical plain-text fallback without interpreting Markdown', () => {
    render(<RichMessage fallbackText="**旧消息**" payload={null} />)

    expect(screen.getByText('**旧消息**')).toBeInTheDocument()
    expect(screen.queryByText('旧消息')).not.toBeInTheDocument()
  })

  it('renders GFM tables and KaTeX math from an accepted payload', () => {
    const { container } = render(
      <RichMessage fallbackText="fallback" payload={markdownPayload} />,
    )

    expect(screen.getByRole('heading', { name: '判别式' })).toBeInTheDocument()
    expect(container.querySelector('table')).toBeInTheDocument()
    expect(container.querySelector('.katex')).toBeInTheDocument()
  })

  it.each(['concept', 'hint', 'question', 'feedback', 'source'])(
    'renders the %s typed card',
    (variant) => {
      render(
        <RichMessage
          fallbackText="fallback"
          payload={{
            schema_version: '1.0',
            blocks: [
              {
                id: `card-${variant}`,
                type: 'card',
                variant,
                title: `${variant} title`,
                body_markdown: '正文包含 **重点**。',
              },
            ],
          }}
        />,
      )

      expect(screen.getByRole('heading', { name: `${variant} title` })).toBeInTheDocument()
      expect(screen.getByText('重点')).toBeInTheDocument()
    },
  )

  it('renders traceable citation labels and SourceSpan ids', () => {
    render(
      <RichMessage
        fallbackText="fallback"
        payload={{
          schema_version: '1.0',
          blocks: [
            {
              id: 'sources',
              type: 'citations',
              items: [
                {
                  label: '教材第三章',
                  source_span_id: '22222222-2222-4222-8222-222222222222',
                },
              ],
            },
          ],
        }}
      />,
    )

    expect(screen.getByText('教材第三章')).toBeInTheDocument()
    expect(screen.getByText('22222222-2222-4222-8222-222222222222')).toBeInTheDocument()
  })

  it('blocks raw HTML, unsafe links and remote images', () => {
    const { container } = render(
      <RichMessage
        fallbackText="fallback"
        payload={{
          schema_version: '1.0',
          blocks: [
            {
              id: 'unsafe',
              type: 'markdown',
              source:
                '<script>alert(1)</script>\n[危险链接](javascript:alert(1))\n![跟踪图](https://tracker.example/pixel.png)',
            },
          ],
        }}
      />,
    )

    expect(container.querySelector('script')).not.toBeInTheDocument()
    expect(container.querySelector('a')).not.toBeInTheDocument()
    expect(container.querySelector('img')).not.toBeInTheDocument()
    expect(screen.getByText('图片已阻止：跟踪图')).toBeInTheDocument()
  })

  it('keeps invalid math local and readable without crashing the response', () => {
    const { container } = render(
      <RichMessage
        fallbackText="fallback"
        payload={{
          schema_version: '1.0',
          blocks: [
            {
              id: 'invalid-math',
              type: 'markdown',
              source: '公式仍可阅读：$\\notARealCommand{$',
            },
          ],
        }}
      />,
    )

    expect(container.querySelector('.katex-error')).toBeInTheDocument()
    expect(container).toHaveTextContent('公式仍可阅读')
  })

  it('falls back for unknown major versions and invalid blocks', () => {
    const { rerender } = render(
      <RichMessage
        fallbackText="unknown fallback"
        payload={{ schema_version: '2.0', blocks: markdownPayload.blocks }}
      />,
    )
    expect(screen.getByText('unknown fallback')).toBeInTheDocument()

    rerender(
      <RichMessage
        fallbackText="invalid fallback"
        payload={{ schema_version: '1.0', blocks: [{ id: 'x', type: 'video' }] }}
      />,
    )
    expect(screen.getByText('invalid fallback')).toBeInTheDocument()
  })
})
