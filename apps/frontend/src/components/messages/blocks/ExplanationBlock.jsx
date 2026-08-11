import SafeMarkdown from '../SafeMarkdown'

export default function ExplanationBlock({ payload }) {
  return (
    <section className="learning-block learning-block--explanation">
      {payload.title && <h3>{payload.title}</h3>}
      <SafeMarkdown source={payload.body_markdown} />
    </section>
  )
}
