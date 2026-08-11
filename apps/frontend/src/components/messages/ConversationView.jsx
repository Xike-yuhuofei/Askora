import MessageRenderer from './MessageRenderer'

export default function ConversationView({ messages, interactionInput, onInvoke, onRequestInput }) {
  return (
    <div className="learning-conversation-view">
      {(messages || []).map((message) => (
        <article
          key={`${message.id}:${message.revision}`}
          className={`learning-conversation-message learning-conversation-message--${message.role.toLowerCase()}`}
          data-message-id={message.id}
        >
          <MessageRenderer
            message={message}
            interactionInput={interactionInput}
            onInvoke={onInvoke}
            onRequestInput={onRequestInput}
          />
        </article>
      ))}
    </div>
  )
}
