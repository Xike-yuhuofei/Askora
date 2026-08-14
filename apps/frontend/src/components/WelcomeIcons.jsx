/*
  新建对话页图标 —— 从 .design_library/TraeWork/prototypes/shell-replica/components/trae/icons.tsx
  逐路径移植（JSX 化，去掉 TS 类型）。描边图标：16×16 viewBox，1.3 描边，圆角端点；
  填充图标使用纯色填充。均通过 currentColor 继承颜色，尺寸由 CSS class 控制。
*/

function Stroke({ className, children, viewBox = '0 0 16 16' }) {
  return (
    <svg
      className={className}
      viewBox={viewBox}
      fill="none"
      stroke="currentColor"
      strokeWidth={1.3}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {children}
    </svg>
  )
}

/* "</>" hero icon — traced from TraeWork asset */
export function BracketsIcon({ className }) {
  return (
    <svg
      className={className}
      viewBox="0 0 16 16"
      fill="currentColor"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <path d="M2.70801 11.3336V9.33362C2.70801 8.9424 2.39121 8.62463 2 8.62463C1.65482 8.62463 1.375 8.34481 1.375 7.99963C1.37518 7.65461 1.65493 7.37463 2 7.37463C2.39121 7.37463 2.70801 7.05784 2.70801 6.66663V4.66663C2.70801 3.21699 3.88341 2.0418 5.33301 2.04163C5.67819 2.04163 5.95801 2.32145 5.95801 2.66663C5.95801 3.0118 5.67819 3.29163 5.33301 3.29163C4.57377 3.2918 3.95801 3.90735 3.95801 4.66663V6.66663C3.95801 7.18254 3.75671 7.64985 3.43066 7.99963C3.7569 8.34945 3.95801 8.81754 3.95801 9.33362V11.3336C3.95818 12.0928 4.57387 12.7084 5.33301 12.7086C5.67819 12.7086 5.95801 12.9884 5.95801 13.3336C5.95783 13.6786 5.67808 13.9586 5.33301 13.9586C3.88353 13.9584 2.70818 12.7831 2.70801 11.3336ZM12.042 11.3336V9.33362C12.042 8.81778 12.2424 8.3494 12.5684 7.99963C12.2426 7.6499 12.042 7.1823 12.042 6.66663V4.66663C12.042 3.90734 11.4263 3.2918 10.667 3.29163C10.3218 3.29163 10.042 3.0118 10.042 2.66663C10.042 2.32145 10.3218 2.04163 10.667 2.04163C12.1166 2.0418 13.292 3.217 13.292 4.66663V6.66663C13.292 7.05785 13.6088 7.37463 14 7.37463C14.3451 7.37463 14.6248 7.65461 14.625 7.99963C14.625 8.34481 14.3452 8.62463 14 8.62463C13.6088 8.62463 13.292 8.9424 13.292 9.33362V11.3336C13.2918 12.7831 12.1165 13.9584 10.667 13.9586C10.3219 13.9586 10.0422 13.6786 10.042 13.3336C10.042 12.9884 10.3218 12.7086 10.667 12.7086C11.4262 12.7084 12.0418 12.0928 12.042 11.3336Z" />
    </svg>
  )
}

/* composer: plain plus */
export function PlusIcon({ className }) {
  return (
    <Stroke className={className}>
      <line x1="8" y1="3.4" x2="8" y2="12.6" />
      <line x1="3.4" y1="8" x2="12.6" y2="8" />
    </Stroke>
  )
}

/* composer well: video (violet fill) */
export function VideoIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
      <rect x="1.8" y="3.8" width="9" height="8.4" rx="2" />
      <path d="M12.4 6.9l2-1.3c.3-.2.6 0 .6.3v4.2c0 .3-.4.5-.6.3l-2-1.3v-2.2Z" />
    </svg>
  )
}

/* composer well: image (orchid fill) */
export function ImageIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
      <path d="M3.6 2.6h8.8c1 0 1.8.8 1.8 1.8v7.2c0 1-.8 1.8-1.8 1.8H3.6c-1 0-1.8-.8-1.8-1.8V4.4c0-1 .8-1.8 1.8-1.8Zm1.6 8.2h5.6L8.4 7.6 6.5 10l-.9-1-2 3.4c.1.1.4.4.6.4Z" />
      <circle cx="10.6" cy="5.6" r="1.1" fill="#252525" />
    </svg>
  )
}

/* composer well: globe */
export function GlobeIcon({ className }) {
  return (
    <Stroke className={className}>
      <circle cx="8" cy="8" r="5.8" />
      <ellipse cx="8" cy="8" rx="2.6" ry="5.8" />
      <line x1="2.4" y1="6.4" x2="13.6" y2="6.4" />
      <line x1="2.4" y1="9.6" x2="13.6" y2="9.6" />
    </Stroke>
  )
}

/* composer: microphone */
export function MicIcon({ className }) {
  return (
    <Stroke className={className}>
      <rect x="6" y="2.2" width="4" height="6.6" rx="2" />
      <path d="M3.8 7.6c0 2.3 1.9 4.2 4.2 4.2s4.2-1.9 4.2-4.2" />
      <line x1="8" y1="11.8" x2="8" y2="13.8" />
    </Stroke>
  )
}

/* composer: send waveform (white on send button) */
export function WaveIcon({ className }) {
  return (
    <svg
      className={className}
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.7}
      strokeLinecap="round"
      aria-hidden="true"
    >
      <line x1="3" y1="6.5" x2="3" y2="9.5" />
      <line x1="6.3" y1="4" x2="6.3" y2="12" />
      <line x1="9.7" y1="5.5" x2="9.7" y2="10.5" />
      <line x1="13" y1="7" x2="13" y2="9" />
    </svg>
  )
}

/* context bar: local computer — traced from TraeWork asset */
export function ComputerIcon({ className }) {
  return (
    <svg
      className={className}
      viewBox="0 0 16 16"
      fill="currentColor"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <path d="M0.666748 12.3333C0.666748 12.1493 0.815988 12 1.00008 12H5.8427C5.9462 12 6.04827 12.0241 6.14085 12.0704L6.52598 12.2629C6.61855 12.3093 6.72061 12.3333 6.82415 12.3333H9.17601C9.27955 12.3333 9.38161 12.3093 9.47415 12.2629L9.85935 12.0704C9.95188 12.0241 10.0539 12 10.1575 12H15.0001C15.1841 12 15.3334 12.1493 15.3334 12.3333V12.6667C15.3334 13.0349 15.0349 13.3333 14.6667 13.3333H1.33341C0.965228 13.3333 0.666748 13.0349 0.666748 12.6667V12.3333Z" />
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M1.33325 4.66675C1.33325 3.56218 2.22869 2.66675 3.33325 2.66675H12.6666C13.7712 2.66675 14.6666 3.56218 14.6666 4.66675V10.3334C14.6666 10.7016 14.3681 11.0001 13.9999 11.0001C13.6317 11.0001 13.3333 10.7016 13.3333 10.3334V4.66675C13.3333 4.29856 13.0348 4.00008 12.6666 4.00008H3.33325C2.96507 4.00008 2.66659 4.29856 2.66659 4.66675V10.3334C2.66659 10.7016 2.36811 11.0001 1.99992 11.0001C1.63173 11.0001 1.33325 10.7016 1.33325 10.3334V4.66675Z"
      />
    </svg>
  )
}

/* context bar: codebase/project — traced from TraeWork asset */
export function CodebaseIcon({ className }) {
  return (
    <svg
      className={className}
      viewBox="0 0 32 32"
      fill="currentColor"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <path d="M28.1555 13.0578C28.0304 12.9311 27.9602 12.7602 27.9602 12.5821V7.91963C27.9588 6.77582 27.5111 5.67926 26.7152 4.87046C25.9194 4.06166 24.8404 3.60667 23.7148 3.60529H8.26203C7.13605 3.60598 6.05637 4.06066 5.25995 4.86953C4.46353 5.67841 4.01547 6.77537 4.01411 7.91963V12.5937C4.01411 12.7711 3.94445 12.9414 3.82014 13.068L1.79855 15.1264C1.54019 15.3895 1.53988 15.8109 1.79787 16.0744L3.82082 18.14C3.94472 18.2666 4.01411 18.4366 4.01411 18.6137V23.2909C4.01547 24.4352 4.46353 25.5322 5.25995 26.341C6.05637 27.15 7.13605 27.6046 8.26203 27.6053H23.7278C24.8532 27.604 25.9323 27.1489 26.7282 26.3401C27.524 25.5313 27.9718 24.4348 27.9731 23.2909V18.6146C27.9731 18.437 28.0429 18.2665 28.1675 18.1398L30.1986 16.0757C30.4582 15.8119 30.4578 15.3886 30.1977 15.1252L28.1555 13.0578ZM13.8339 17.6246C14.0921 17.888 14.0918 18.3097 13.8332 18.5728L12.8048 19.6193C12.5395 19.8894 12.1042 19.8893 11.839 19.6191L8.35952 16.0748C8.10081 15.8113 8.10106 15.389 8.36007 15.1258L11.8418 11.5874C12.1071 11.3179 12.5416 11.3179 12.8068 11.5874L13.8344 12.6317C14.0936 12.8951 14.0937 13.3176 13.8347 13.5811L12.3158 15.1263C12.0572 15.3893 12.0568 15.8111 12.315 16.0746L13.8339 17.6246ZM19.973 19.6196C19.7077 19.8896 19.2727 19.8895 19.0074 19.6196L17.9797 18.5738C17.7207 18.3103 17.7209 17.8879 17.98 17.6246L19.4985 16.0814C19.7572 15.8185 19.7578 15.3968 19.4997 15.1331L17.9804 13.581C17.7223 13.3174 17.7229 12.8957 17.9816 12.6327L19.0102 11.5874C19.2754 11.3179 19.71 11.3179 19.9752 11.5874L23.4567 15.1255C23.7158 15.3889 23.716 15.8113 23.457 16.0748L19.973 19.6196Z" />
    </svg>
  )
}

/* small chevron down (selects) */
export function ChevronDownIcon({ className }) {
  return (
    <Stroke className={className} viewBox="0 0 12 12">
      <polyline points="3,4.5 6,7.5 9,4.5" />
    </Stroke>
  )
}

/* chip: 应用开发 — phone */
export function ChipAppIcon({ className }) {
  return (
    <Stroke className={className}>
      <rect x="4.6" y="2.2" width="6.8" height="11.6" rx="1.6" />
      <line x1="7" y1="11.4" x2="9" y2="11.4" />
    </Stroke>
  )
}

/* chip: 项目理解 — doc with text */
export function ChipDocIcon({ className }) {
  return (
    <Stroke className={className}>
      <path d="M4 2.6h5.4L12 5.2v8.2H4V2.6Z" />
      <polyline points="9.2,2.8 9.2,5.2 11.8,5.2" />
      <line x1="6" y1="8" x2="10" y2="8" />
      <line x1="6" y1="10.4" x2="9" y2="10.4" />
    </Stroke>
  )
}

/* chip: 游戏创意 — gamepad */
export function ChipGameIcon({ className }) {
  return (
    <Stroke className={className}>
      <path d="M5 4.6h6c2 0 3.4 1.7 3.4 3.8 0 1.9-1.2 3-2.6 3-.9 0-1.5-.4-2-1.1H6.2c-.5.7-1.1 1.1-2 1.1-1.4 0-2.6-1.1-2.6-3 0-2.1 1.4-3.8 3.4-3.8Z" />
      <line x1="5.4" y1="6.8" x2="5.4" y2="9.2" />
      <line x1="4.2" y1="8" x2="6.6" y2="8" />
      <circle cx="10.4" cy="7.2" r="0.55" fill="currentColor" stroke="none" />
      <circle cx="11.8" cy="8.8" r="0.55" fill="currentColor" stroke="none" />
    </Stroke>
  )
}

/* chip: 工具脚本 — terminal */
export function ChipScriptIcon({ className }) {
  return (
    <Stroke className={className}>
      <rect x="2.2" y="3" width="11.6" height="10" rx="1.8" />
      <polyline points="5,6.2 6.8,8 5,9.8" />
      <line x1="8.4" y1="10.2" x2="11" y2="10.2" />
    </Stroke>
  )
}
