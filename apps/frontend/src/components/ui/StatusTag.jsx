export default function StatusTag({ tone = 'neutral', children }) {
  const variant = tone === 'neutral' ? 'ds-tag' : `ds-tag ds-tag--${tone}`
  return <span className={variant}>{children}</span>
}
