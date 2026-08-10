import ReactMarkdown from 'react-markdown'
import rehypeKatex from 'rehype-katex'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'
import 'katex/dist/katex.min.css'

const allowedProtocols = new Set(['http:', 'https:'])

/**
 * 清理剩余 Markdown 强调符号。
 *
 * micromark 对 `**` 紧邻中文/引号字符时无法闭合强调（例如 `**“……比……**`），
 * 会把 `*`/`_` 当作字面文本泄漏到 UI（用户会看到 `***`、`**`）。
 * 该插件在解析后移除 text 节点中残留的强调符号；代码块、行内代码、数学与
 * 列表标记不受影响（它们不是 text 节点）。
 */
function remarkCleanupStrayMarkers() {
  return (tree) => {
    const walk = (node) => {
      if (node.type === 'text' && typeof node.value === 'string') {
        node.value = node.value.replace(/[*_]+/g, '')
      }
      if (Array.isArray(node.children)) {
        node.children.forEach(walk)
      }
    }
    walk(tree)
  }
}

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
      remarkPlugins={[remarkGfm, remarkMath, remarkCleanupStrayMarkers]}
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
