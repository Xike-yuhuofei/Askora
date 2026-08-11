import SafeMarkdown from '../SafeMarkdown'

export default function KnowledgeBlock({ payload }) {
  return (
    <section className="learning-block learning-block--knowledge" aria-label="知识要点">
      <p className="learning-block__eyebrow">知识要点</p>
      <h3>{payload.title}</h3>
      <SafeMarkdown source={payload.body_markdown} />
      {payload.qualifier && <p className="learning-block__qualifier">{payload.qualifier}</p>}
    </section>
  )
}
