export default function Alert({ tone = 'info', title, children, role = 'status' }) {
  return (
    <div className={`ds-alert ds-alert--${tone}`} role={role}>
      <span className="ds-alert__icon" aria-hidden="true">●</span>
      <div>
        {title ? <p className="ds-alert__title">{title}</p> : null}
        <p className="ds-alert__desc">{children}</p>
      </div>
    </div>
  )
}
