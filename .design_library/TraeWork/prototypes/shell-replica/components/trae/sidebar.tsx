"use client"

/*
  Sidebar — geometry measured from the reference PNG (1326×1299):
  - width 301px + 1px right divider (#2c2c2c)
  - titlebar 62px: traffic dots 14px @ centers x 31/55/78, y center 30
  - mode switcher track: x 12→206, h 32, bg #2c2c2c; active pill #171717 + #3f3f3f border
  - primary action rows: pitch 40px, highlight h 34 (#2c2c2c, radius 7)
  - folder rows h 34, task rows h 33, task text indent x=44
  - account bar h 58 anchored to bottom
*/

import { useState } from "react"
import { cn } from "@/lib/utils"
import {
  LayoutIcon,
  SearchIcon,
  CirclePlusIcon,
  ShapesIcon,
  ClockIcon,
  ChatIcon,
  TemplateIcon,
  PinIcon,
  ChevronDownIcon,
  ExpandIcon,
  FilterIcon,
  FolderIcon,
  DeviceIcon,
  BracketsIcon,
} from "./icons"
import {
  WORKSPACE_MODES,
  PRIMARY_ACTIONS,
  PINNED_ITEMS,
  TASK_FOLDERS,
  type WorkspaceMode,
  type PrimaryAction,
} from "@/lib/trae-data"

const ACTION_ICONS: Record<PrimaryAction["icon"], typeof CirclePlusIcon> = {
  "new-task": CirclePlusIcon,
  plugins: ShapesIcon,
  automation: ClockIcon,
  assistant: ChatIcon,
  templates: TemplateIcon,
}

export function Sidebar() {
  const [mode, setMode] = useState<WorkspaceMode>("Code")
  const [openFolders, setOpenFolders] = useState<Record<string, boolean>>(() =>
    Object.fromEntries(TASK_FOLDERS.map((f) => [f.id, Boolean(f.defaultOpen)])),
  )

  const toggleFolder = (id: string) =>
    setOpenFolders((prev) => ({ ...prev, [id]: !prev[id] }))

  return (
    <aside className="flex w-[301px] shrink-0 flex-col border-r border-border-card bg-frame">
      {/* A. title bar: traffic dots + layout + search */}
      <div className="flex h-[62px] shrink-0 items-center pl-6">
        <div className="flex items-center gap-[10px]" aria-label="窗口控制">
          <span className="size-3.5 rounded-full bg-tl" />
          <span className="size-3.5 rounded-full bg-tl" />
          <span className="size-3.5 rounded-full bg-tl" />
        </div>
        <button
          aria-label="布局"
          className="ml-[19px] text-[#b1b1b1] transition-colors hover:text-text-1"
        >
          <LayoutIcon className="size-[13px]" />
        </button>
        <button
          aria-label="搜索"
          className="ml-[26px] text-[#b1b1b1] transition-colors hover:text-text-1"
        >
          <SearchIcon className="size-[13px]" />
        </button>
      </div>

      {/* B. mode switcher — content-width track, active pill = dark fill + border */}
      <div className="ml-3 mt-[1px] inline-flex self-start rounded-[8px] bg-hover p-[2px]">
        {WORKSPACE_MODES.map((m) => (
          <button
            key={m}
            role="tab"
            aria-selected={mode === m}
            onClick={() => setMode(m)}
            className={cn(
              "flex h-7 items-center gap-[3px] rounded-[6px] px-3 text-[13px] transition-colors",
              mode === m
                ? "border border-border-pill bg-pill-active text-hero"
                : "border border-transparent text-text-1 hover:text-hero",
            )}
          >
            {m === "Code" ? <BracketsIcon className="size-[10px]" /> : null}
            <span>{m}</span>
          </button>
        ))}
      </div>

      {/* C. primary actions */}
      <nav className="mt-[16px] px-3" aria-label="主要功能">
        {PRIMARY_ACTIONS.map((action, i) => {
          const Icon = ACTION_ICONS[action.icon]
          const highlighted = i === 0
          return (
            <button
              key={action.id}
              className={cn(
                "flex h-10 w-full items-center text-[13.5px]",
                highlighted ? "text-text-1" : "text-text-1/90",
              )}
            >
              <span
                className={cn(
                  "flex h-[34px] w-full items-center rounded-[7px] pl-[9px] pr-2 transition-colors",
                  highlighted ? "bg-hover" : "hover:bg-hover/60",
                )}
              >
                <Icon className="size-4 shrink-0 text-[#d3d3d3]" />
                <span className="ml-2 flex-1 text-left">{action.label}</span>
                {action.shortcut ? (
                  <kbd className="font-sans text-[11px] tracking-[1px] text-text-4">
                    {action.shortcut}
                  </kbd>
                ) : null}
              </span>
            </button>
          )
        })}
      </nav>

      {/* scroll region: pinned + task tree */}
      <div className="scroll-thin mt-[18px] flex-1 overflow-y-auto px-3">
        {/* D. pinned */}
        <SectionHeader label="置顶" />
        <div className="mt-[4px]">
          {PINNED_ITEMS.map((item) => (
            <button
              key={item.id}
              className="flex h-[34px] w-full items-center rounded-[7px] pl-[9px] pr-2 text-[13.5px] text-text-1 transition-colors hover:bg-hover/60"
            >
              <PinIcon className="size-[13px] shrink-0 text-[#d3d3d3]" />
              <span className="ml-[9px] truncate text-left">{item.title}</span>
            </button>
          ))}
        </div>

        {/* E. task list */}
        <div className="mt-4">
          <SectionHeader
            label="任务列表"
            actions={
              <>
                <button
                  aria-label="展开"
                  className="flex size-5 items-center justify-center text-text-3 transition-colors hover:text-text-1"
                >
                  <ExpandIcon className="size-3" />
                </button>
                <button
                  aria-label="筛选"
                  className="flex size-5 items-center justify-center text-text-3 transition-colors hover:text-text-1"
                >
                  <FilterIcon className="size-3" />
                </button>
              </>
            }
          />
          <div className="mt-[3px]">
            {TASK_FOLDERS.map((folder, fi) => {
              const open = openFolders[folder.id]
              return (
                <div key={folder.id} className={cn(fi > 0 && "mt-[1px]")}>
                  <button
                    onClick={() => toggleFolder(folder.id)}
                    className="flex h-[35px] w-full items-center rounded-[7px] pl-[10px] pr-2 text-[14px] text-text-2 transition-colors hover:bg-hover/60"
                  >
                    <FolderIcon className="size-[15px] shrink-0" />
                    <span className="ml-2 truncate text-left">{folder.name}</span>
                  </button>
                  {open
                    ? folder.tasks.map((task) => (
                        <button
                          key={task.id}
                          className="flex h-[34px] w-full items-center rounded-[7px] pl-8 pr-2 text-[13.5px] text-text-1 transition-colors hover:bg-hover/60"
                        >
                          <span className="truncate text-left">{task.title}</span>
                        </button>
                      ))
                    : null}
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* F. account footer */}
      <div className="flex h-[58px] shrink-0 items-center pl-[22px]">
        <span className="flex size-6 items-center justify-center overflow-hidden rounded-[6px] bg-white">
          {/* avatar illustration placeholder: white tile with gray glyph */}
          <span className="text-[9px] font-semibold leading-none text-[#8a8a8a]">
            稀
          </span>
        </span>
        <span className="ml-[9px] text-[13.5px] text-account">稀客</span>
        <span className="ml-2 rounded-[4px] bg-badge-bg px-[5px] py-[1px] text-[10px] font-medium text-badge-text">
          Pro
        </span>
        <button
          aria-label="设备"
          className="ml-auto mr-4 flex size-6 items-center justify-center rounded-full bg-hover text-[#b4b4b4] transition-colors hover:text-text-1"
        >
          <DeviceIcon className="size-3" />
        </button>
      </div>
    </aside>
  )
}

function SectionHeader({
  label,
  actions,
}: {
  label: string
  actions?: React.ReactNode
}) {
  return (
    <div className="flex h-6 items-center px-2">
      <span className="text-[12px] text-text-3">{label}</span>
      <ChevronDownIcon className="ml-1 size-3 text-text-3" />
      {actions ? <div className="ml-auto flex items-center gap-1.5">{actions}</div> : null}
    </div>
  )
}
