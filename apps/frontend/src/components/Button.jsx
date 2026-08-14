import { createElement } from 'react'

const variantClassMap = {
  primary: 'ds-btn--primary',
  secondary: 'ds-btn--secondary',
  ghost: 'ds-btn--ghost',
  danger: 'ds-btn--danger',
}

const sizeClassMap = {
  sm: 'ds-btn--sm',
  xs: 'ds-btn--xs',
}

export default function Button({
  variant = 'secondary',
  size,
  icon = false,
  block = false,
  className = '',
  children,
  as: Component = 'button',
  type = 'button',
  disabled = false,
  ...rest
}) {
  const classes = [
    'ds-btn',
    variantClassMap[variant] || '',
    sizeClassMap[size] || '',
    icon ? 'ds-btn--icon' : '',
    block ? 'ds-btn--block' : '',
    className,
  ].filter(Boolean).join(' ')

  const elementProps = {
    className: classes,
    ...(Component === 'button' ? { type } : {}),
    ...(disabled ? { disabled } : {}),
    ...rest,
  }

  return createElement(Component, elementProps, children)
}