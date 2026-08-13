export default function Button({
  variant = 'secondary',
  type = 'button',
  className = '',
  children,
  ...props
}) {
  const tone = variant === 'primary' ? 'brand' : variant
  return (
    <button
      type={type}
      className={`ds-btn ds-btn--${tone} ${className}`.trim()}
      {...props}
    >
      {children}
    </button>
  )
}
