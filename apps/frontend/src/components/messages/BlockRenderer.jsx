import InteractiveElement from './InteractiveElement'
import EvidenceBlock from './blocks/EvidenceBlock'
import ExplanationBlock from './blocks/ExplanationBlock'
import FeedbackBlock from './blocks/FeedbackBlock'
import KnowledgeBlock from './blocks/KnowledgeBlock'
import LearningActivityBlock from './blocks/LearningActivityBlock'
import ReviewApplyBlock from './blocks/ReviewApplyBlock'

const components = {
  EXPLANATION: ExplanationBlock,
  KNOWLEDGE: KnowledgeBlock,
  EVIDENCE: EvidenceBlock,
  LEARNING_ACTIVITY: LearningActivityBlock,
  FEEDBACK: FeedbackBlock,
  REVIEW_APPLY: ReviewApplyBlock,
}

function validMetadata(metadata) {
  return Boolean(
    metadata?.schema_version === '1.0' &&
    typeof metadata.semantic_role === 'string' &&
    metadata.provenance && typeof metadata.provenance.mode === 'string' &&
    Array.isArray(metadata.owner_refs) &&
    typeof metadata.availability === 'string',
  )
}

function validPayload(block) {
  const payload = block.payload
  if (!payload || typeof payload !== 'object') return false
  if (block.type === 'EXPLANATION') return typeof payload.body_markdown === 'string'
  if (block.type === 'KNOWLEDGE') return typeof payload.title === 'string' && typeof payload.body_markdown === 'string'
  if (block.type === 'EVIDENCE') return typeof payload.excerpt === 'string' && typeof payload.source_label === 'string'
  if (block.type === 'LEARNING_ACTIVITY') return typeof payload.prompt_markdown === 'string' && typeof payload.response_mode === 'string'
  if (block.type === 'FEEDBACK') return typeof payload.heading === 'string' && typeof payload.body_markdown === 'string'
  if (block.type === 'REVIEW_APPLY') return ['REVIEW', 'APPLY'].includes(payload.mode) && typeof payload.title === 'string' && typeof payload.description_markdown === 'string'
  return false
}

export function isRenderableLearningBlock(block) {
  return Boolean(
    block && typeof block.id === 'string' && block.id.length > 0 && block.id.length <= 100 &&
    Object.hasOwn(components, block.type) && validPayload(block) && validMetadata(block.metadata) &&
    Array.isArray(block.interactions) && block.interactions.length <= 16,
  )
}

export default function BlockRenderer({ block, interactionInput, onInvoke, onRequestInput }) {
  if (!isRenderableLearningBlock(block)) return null
  const Component = components[block.type]
  return (
    <div className={`learning-block-shell learning-block-shell--${block.type.toLowerCase()}`}>
      <Component payload={block.payload} metadata={block.metadata} />
      {block.interactions.length > 0 && (
        <div className="learning-block-actions">
          {block.interactions.map((interaction) => (
            <InteractiveElement
              key={interaction.id}
              interaction={interaction}
              inputPayload={interactionInput}
              onInvoke={onInvoke}
              onRequestInput={onRequestInput}
            />
          ))}
        </div>
      )}
    </div>
  )
}
