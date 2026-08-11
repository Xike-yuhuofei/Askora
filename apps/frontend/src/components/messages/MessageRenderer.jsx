import SafeMarkdown from './SafeMarkdown'
import BlockRenderer, { isRenderableLearningBlock } from './BlockRenderer'
import './MessageRenderer.css'

export function isRenderableLearningMessage(message) {
  if (
    message?.schema_version !== '1.0' ||
    typeof message.id !== 'string' ||
    !Number.isInteger(message.revision) || message.revision < 1 ||
    !['LEARNER', 'ASSISTANT', 'SYSTEM_NOTICE'].includes(message.role) ||
    typeof message.content !== 'string' || !message.content ||
    !Array.isArray(message.blocks) || message.blocks.length > 32 ||
    !message.blocks.every(isRenderableLearningBlock)
  ) return false
  const ids = message.blocks.map((block) => block.id)
  return new Set(ids).size === ids.length
}

export default function MessageRenderer({ message, interactionInput, onInvoke, onRequestInput }) {
  if (!isRenderableLearningMessage(message) || message.blocks.length === 0) {
    return <div className="learning-message-fallback"><SafeMarkdown source={message?.content || ''} /></div>
  }
  return (
    <div className="learning-message-renderer">
      {message.blocks.map((block) => (
        <BlockRenderer
          key={block.id}
          block={block}
          interactionInput={interactionInput}
          onInvoke={onInvoke}
          onRequestInput={onRequestInput}
        />
      ))}
    </div>
  )
}
