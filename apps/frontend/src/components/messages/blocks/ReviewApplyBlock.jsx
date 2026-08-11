import SafeMarkdown from '../SafeMarkdown'

export default function ReviewApplyBlock({ payload }) {
  return (
    <section className="learning-block learning-block--review" aria-label={payload.mode === 'REVIEW' ? '复习活动' : '应用活动'}>
      <p className="learning-block__eyebrow">{payload.mode === 'REVIEW' ? '复习' : '应用'}</p>
      <h3>{payload.title}</h3>
      <SafeMarkdown source={payload.description_markdown} />
      {payload.timing_label && <p className="learning-block__qualifier">{payload.timing_label}</p>}
    </section>
  )
}
