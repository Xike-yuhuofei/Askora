import { forwardRef, useState } from 'react'

import DsIcon from './DsIcon'

const Composer = forwardRef(function Composer({
  id,
  label,
  value,
  onChange,
  onSubmit,
  onKeyDown,
  placeholder,
  disabled = false,
  sendDisabled = false,
  sendLabel = '发送',
}, ref) {
  const [focused, setFocused] = useState(false)

  return (
    <div className={`ds-ai-input${focused ? ' ds-ai-input--focused' : ''}${disabled ? ' ds-ai-input--disabled' : ''}`}>
      {label ? <label htmlFor={id} className="visually-hidden">{label}</label> : null}
      <textarea
        id={id}
        ref={ref}
        className="ds-ai-input__textarea"
        rows={3}
        value={value}
        onChange={onChange}
        onKeyDown={onKeyDown}
        onFocus={() => setFocused(true)}
        onBlur={() => setFocused(false)}
        placeholder={placeholder}
        disabled={disabled}
      />
      <div className="ds-ai-input__control-row">
        <button
          type="submit"
          className="ds-ai-input__send"
          disabled={disabled || sendDisabled}
          aria-label={sendLabel}
          onClick={onSubmit}
        >
          <DsIcon name="send" />
        </button>
      </div>
    </div>
  )
})

export default Composer
