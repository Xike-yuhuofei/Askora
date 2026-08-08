const sourceLabels = {
  SYS01: '资料与知识',
  SYS03: '学习证据',
  SYS06: '学习计划',
  SYS07: '复习调度',
  LEGACY_COMPATIBILITY: '兼容会话',
}

const availabilityLabels = {
  AVAILABLE: '可用',
  MISSING: '暂不可用',
  STALE: '可能过期',
  LOW_CONFIDENCE: '置信度较低',
  NOT_APPLICABLE: '当前不适用',
}

export default function SourceStatus({ items = [] }) {
  return (
    <section className="source-status" aria-labelledby="source-status-title">
      <div className="section-heading section-heading--compact">
        <div>
          <p className="eyebrow">数据状态</p>
          <h2 id="source-status-title">当前信息来源</h2>
        </div>
      </div>
      <ul className="source-status__list">
        {items.map((item) => (
          <li key={item.source_system} className="source-status__item">
            <span>{sourceLabels[item.source_system] || item.source_system}</span>
            <span className={`status-pill status-pill--${item.availability.toLowerCase()}`}>
              {availabilityLabels[item.availability] || item.availability}
            </span>
          </li>
        ))}
      </ul>
    </section>
  )
}
