import SafeMarkdown from '../SafeMarkdown'

export default function LearningActivityBlock({ payload }) {
  return (
    <section className="learning-block learning-block--activity" aria-label="学习任务">
      <p className="learning-block__eyebrow">学习任务</p>
      <SafeMarkdown source={payload.prompt_markdown} />
    </section>
  )
}
