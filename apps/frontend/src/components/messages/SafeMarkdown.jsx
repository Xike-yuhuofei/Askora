import ReactMarkdown from 'react-markdown'
import rehypeKatex from 'rehype-katex'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import 'katex/dist/katex.min.css'

const allowedProtocols = new Set(['http:', 'https:'])

export function isAllowedExternalUrl(value) {
  if (typeof value !== 'string' || !value) return false
  try {
    return allowedProtocols.has(new URL(value).protocol)
  } catch {
    return false
  }
}

const markdownComponents = {
  a({ href, children }) {
    if (!isAllowedExternalUrl(href)) {
      return <span className="rich-link-blocked">{children}</span>
    }
    return (
      <a href={href} target="_blank" rel="noreferrer noopener">
        {children}
      </a>
    )
  },
  img({ alt }) {
    return (
      <span className="rich-media-blocked" role="note">
        {alt ? `图片已阻止：${alt}` : '图片已阻止'}
      </span>
    )
  },
}

export default function SafeMarkdown({ source }) {
  return (
    <ReactMarkdown
      skipHtml
      remarkPlugins={[remarkGfm, remarkMath]}
      rehypePlugins={[
        [
          rehypeKatex,
          {
            trust: false,
            throwOnError: false,
            strict: 'warn',
            maxSize: 10,
            maxExpand: 1000,
          },
        ],
      ]}
      components={markdownComponents}
    >
      {source}
    </ReactMarkdown>
  )
}
