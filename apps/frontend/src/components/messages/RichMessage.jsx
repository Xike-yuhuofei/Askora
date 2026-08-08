import SafeMarkdown from './SafeMarkdown'
import './RichMessage.css'

const cardVariantLabels = {
  concept: '核心概念',
  hint: '学习提示',
  question: '思考问题',
  feedback: '学习反馈',
  source: '资料说明',
}

function isValidBlock(block) {
  if (
    !block ||
    typeof block !== 'object' ||
    typeof block.id !== 'string' ||
    block.id.length < 1 ||
    block.id.length > 64
  ) return false
  if (block.type === 'markdown') {
    return (
      typeof block.source === 'string' &&
      block.source.length > 0 &&
      block.source.length <= 20_000
    )
  }
  if (block.type === 'card') {
    return (
      Object.hasOwn(cardVariantLabels, block.variant) &&
      typeof block.title === 'string' &&
      block.title.length > 0 &&
      block.title.length <= 200 &&
      typeof block.body_markdown === 'string' &&
      block.body_markdown.length > 0 &&
      block.body_markdown.length <= 10_000
    )
  }
  if (block.type === 'citations') {
    return (
      Array.isArray(block.items) &&
      block.items.length > 0 &&
      block.items.length <= 20 &&
      block.items.every(
        (item) =>
          item &&
          typeof item.label === 'string' &&
          item.label.length > 0 &&
          item.label.length <= 300 &&
          typeof item.source_span_id === 'string',
      )
    )
  }
  return false
}

export function isRenderablePayload(payload) {
  if (
    payload?.schema_version !== '1.0' ||
    !Array.isArray(payload.blocks) ||
    payload.blocks.length < 1 ||
    payload.blocks.length > 32 ||
    !payload.blocks.every(isValidBlock)
  ) return false

  const blockIds = payload.blocks.map((block) => block.id)
  return new Set(blockIds).size === blockIds.length
}

function CardBlock({ block }) {
  return (
    <section className={`rich-card rich-card-${block.variant}`} aria-label={cardVariantLabels[block.variant]}>
      <div className="rich-card-eyebrow">{cardVariantLabels[block.variant]}</div>
      <h3>{block.title}</h3>
      <SafeMarkdown source={block.body_markdown} />
    </section>
  )
}

function CitationBlock({ block }) {
  return (
    <section className="rich-citations" aria-label="引用资料">
      <div className="rich-citations-title">引用资料</div>
      <ol>
        {block.items.map((item) => (
          <li key={`${item.source_span_id}-${item.label}`}>
            <span>{item.label}</span>
            <code>{item.source_span_id}</code>
          </li>
        ))}
      </ol>
    </section>
  )
}

export default function RichMessage({ fallbackText, payload }) {
  if (!isRenderablePayload(payload)) {
    return <p className="rich-message-fallback">{fallbackText}</p>
  }

  return (
    <div className="rich-message">
      {payload.blocks.map((block) => {
        if (block.type === 'markdown') {
          return (
            <div className="rich-markdown" key={block.id}>
              <SafeMarkdown source={block.source} />
            </div>
          )
        }
        if (block.type === 'card') return <CardBlock block={block} key={block.id} />
        return <CitationBlock block={block} key={block.id} />
      })}
    </div>
  )
}
