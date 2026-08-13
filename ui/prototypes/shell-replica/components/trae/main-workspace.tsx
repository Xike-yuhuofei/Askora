"use client"

/*
  Main workspace — geometry measured from the reference PNG:
  - no title bar / status bar; pure empty canvas
  - hero "</> Code with TRAE" centered at (810, 468), ~38px type
  - composer card: 800×172, border #383738, radius 12, top y=537
    - input zone 127px on main bg
    - action row: content 32px @ y 620–651
    - context bar 44px, bg #222222, divider #383738
  - suggestion chips: h 38, border #3f3f3f, gap 12, top y=741
  - whole content block sits ~32px above vertical center
*/

import { useRef, useState } from "react"
import { cn } from "@/lib/utils"
import {
  BracketsIcon,
  PlusIcon,
  VideoIcon,
  ImageIcon,
  GlobeIcon,
  MicIcon,
  WaveIcon,
  ComputerIcon,
  CodebaseIcon,
  ChevronDownIcon,
  ChipAppIcon,
  ChipDocIcon,
  ChipGameIcon,
  ChipScriptIcon,
} from "./icons"
import {
  SUGGESTION_CHIPS,
  MODEL_NAME,
  ENVIRONMENT_NAME,
  PROJECT_NAME,
  COMPOSER_PLACEHOLDER,
  type SuggestionChip,
} from "@/lib/trae-data"

const CHIP_ICONS: Record<SuggestionChip["icon"], typeof ChipAppIcon> = {
  app: ChipAppIcon,
  understand: ChipDocIcon,
  game: ChipGameIcon,
  script: ChipScriptIcon,
}

export function MainWorkspace() {
  const [value, setValue] = useState("")
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  return (
    <div className="flex min-w-0 flex-1 flex-col items-center justify-center">
      <div className="flex w-full max-w-[800px] translate-x-[0.5px] -translate-y-[35.5px] flex-col items-center">
        {/* hero */}
        <h1 className="flex items-center gap-[19px] text-hero">
          <BracketsIcon className="size-[36px]" />
          <span className="text-[33px] leading-none">
            <span className="font-semibold">Code with </span>
            <span className="font-normal">TRAE</span>
          </span>
        </h1>

        {/* composer */}
        <div className="mt-[51px] w-full overflow-hidden rounded-[12px] border border-border-composer">
          {/* input zone */}
          <div className="flex h-[126px] flex-col bg-main">
            <div className="px-6 pt-[6px]">
              <textarea
                ref={textareaRef}
                value={value}
                onChange={(e) => setValue(e.target.value)}
                rows={1}
                placeholder={COMPOSER_PLACEHOLDER}
                className="scroll-thin w-full resize-none bg-transparent text-[13.5px] leading-[20px] text-text-1 placeholder:text-placeholder focus:outline-none"
              />
            </div>

            {/* action row */}
            <div className="mt-auto flex h-[57px] items-center pl-[22px] pr-[13px]">
              <button
                aria-label="添加"
                className="text-[#afafaf] transition-colors hover:text-text-1"
              >
                <PlusIcon className="size-[15px]" />
              </button>

              {/* media well: video / image / globe */}
              <div className="ml-[15px] flex h-[26px] items-center gap-[5px] rounded-[7px] border border-iconwell-border bg-iconwell px-[6px]">
                <button aria-label="视频" className="text-icon-violet">
                  <VideoIcon className="size-[14px]" />
                </button>
                <button aria-label="图片" className="text-icon-orchid">
                  <ImageIcon className="size-[14px]" />
                </button>
                <button
                  aria-label="网络"
                  className="text-[#d4d4d4] transition-colors hover:text-white"
                >
                  <GlobeIcon className="size-[14px]" />
                </button>
              </div>

              <div className="ml-auto flex items-center">
                <button className="flex items-center gap-[6px] text-[12px] text-model transition-colors hover:text-text-1">
                  <span>{MODEL_NAME}</span>
                  <ChevronDownIcon className="size-[10px] text-text-2" />
                </button>
                <button
                  aria-label="语音输入"
                  className="ml-[14px] text-[#b4b4b4] transition-colors hover:text-text-1"
                >
                  <MicIcon className="size-4" />
                </button>
                <button
                  aria-label="发送"
                  className="ml-[13px] flex size-8 items-center justify-center rounded-[8px] bg-send text-white transition-opacity hover:opacity-90"
                >
                  <WaveIcon className="size-4" />
                </button>
              </div>
            </div>
          </div>

          {/* context bar */}
          <div className="flex h-[44px] items-center border-t border-border-composer bg-ctxbar pl-[22px]">
            <ContextSelect
              icon={<ComputerIcon className="size-[14px]" />}
              label={ENVIRONMENT_NAME}
            />
            <ContextSelect
              icon={<CodebaseIcon className="size-[14px]" />}
              label={PROJECT_NAME}
              className="ml-[22px]"
            />
          </div>
        </div>

        {/* suggestion chips */}
        <div className="mt-[31px] flex items-center gap-3">
          {SUGGESTION_CHIPS.map((chip) => {
            const Icon = CHIP_ICONS[chip.icon]
            return (
              <button
                key={chip.id}
                className="flex h-[38px] items-center gap-[7px] rounded-[10px] border border-border-pill px-[14px] text-[13px] text-chip-text transition-colors hover:border-[#4a4a4a] hover:text-hero"
              >
                <Icon className="size-[14px] text-[#b4b4b4]" />
                <span>{chip.label}</span>
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}

function ContextSelect({
  icon,
  label,
  className,
}: {
  icon: React.ReactNode
  label: string
  className?: string
}) {
  return (
    <button
      className={cn(
        "flex items-center gap-[9px] text-[13.5px] text-hero transition-colors hover:text-white",
        className,
      )}
    >
      <span className="text-[#b4b4b4]">{icon}</span>
      <span>{label}</span>
      <ChevronDownIcon className="ml-[2px] size-[11px] text-text-2" />
    </button>
  )
}
