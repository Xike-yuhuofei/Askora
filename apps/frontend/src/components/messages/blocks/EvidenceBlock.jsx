export default function EvidenceBlock({ payload }) {
  return (
    <figure className="learning-block learning-block--evidence">
      <blockquote>{payload.excerpt}</blockquote>
      <figcaption>
        <span>{payload.source_label}</span>
        {payload.locator && <span> · {payload.locator}</span>}
      </figcaption>
    </figure>
  )
}
