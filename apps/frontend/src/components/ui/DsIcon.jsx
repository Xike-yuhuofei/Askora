const ICONS = {
  plus: (
    <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true">
      <path fill="currentColor" fillRule="evenodd" d="M8 4C8.3682 4 8.66667 4.29848 8.66667 4.66667V7.33333H11.3333C11.7015 7.33333 12 7.6318 12 8C12 8.3682 11.7015 8.66667 11.3333 8.66667H8.66667V11.3333C8.66667 11.7015 8.3682 12 8 12C7.6318 12 7.33333 11.7015 7.33333 11.3333V8.66667H4.66667C4.29848 8.66667 4 8.3682 4 8C4 7.6318 4.29848 7.33333 4.66667 7.33333H7.33333V4.66667C7.33333 4.29848 7.6318 4 8 4Z" />
    </svg>
  ),
  send: (
    <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true">
      <path fill="currentColor" d="M2.07584 4.1188C1.63254 2.71501 3.0938 1.46785 4.4105 2.12621L13.1766 6.50922C14.405 7.1234 14.405 8.87646 13.1766 9.49066L4.4105 13.8737C3.09379 14.532 1.63254 13.2849 2.07584 11.8811L3.09091 8.66667H6.00059C6.36878 8.66667 6.66728 8.3682 6.66728 8C6.66728 7.6318 6.36878 7.33333 6.00059 7.33333H3.09096L2.07584 4.1188Z" />
    </svg>
  ),
  folder: (
    <svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true">
      <path fill="currentColor" d="M2 3.5A1.5 1.5 0 0 1 3.5 2h3.086a1.5 1.5 0 0 1 1.06.44L8.5 3.293A.5.5 0 0 0 8.854 3.4L9.5 3.5H12.5A1.5 1.5 0 0 1 14 5v7.5A1.5 1.5 0 0 1 12.5 14h-9A1.5 1.5 0 0 1 2 12.5v-9Z" />
    </svg>
  ),
}

export default function DsIcon({ name, className = '' }) {
  const graphic = ICONS[name]
  if (!graphic) return null
  return <span className={`ds-icon-svg ${className}`.trim()}>{graphic}</span>
}
