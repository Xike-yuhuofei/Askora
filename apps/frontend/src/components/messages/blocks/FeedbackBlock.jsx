import SafeMarkdown from '../SafeMarkdown'

export default function FeedbackBlock({ payload }) {
  return (
    <section className="learning-block learning-block--feedback" aria-label="学习反馈">
      <p className="learning-block__eyebrow">学习反馈</p>
      <h3>{payload.heading}</h3>
      <SafeMarkdown source={payload.body_markdown} />
      {payload.diagnostic_summary && <p>{payload.diagnostic_summary}</p>}
    </section>
  )
}
