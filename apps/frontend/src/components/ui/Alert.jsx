export default function Alert({ tone = 'info', title, children }) {
  return (
    <div className={`ds-alert ds-alert--${tone}`} role="status">
      <span className="ds-alert__icon" aria-hidden="true">●</span>
      <div>
        {title ? <p className="ds-alert__title">{title}</p> : null}
        <p className="ds-alert__desc">{children}</p>
      </div>
    </div>
  )
}
