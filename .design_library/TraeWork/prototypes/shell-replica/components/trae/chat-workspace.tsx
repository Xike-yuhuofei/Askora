"use client"

/*
  Chat workspace — measured from TraeWork-chat.png (1326×1299):
  - titlebar h48: [folder icon] task name + timestamp, right "在…中打开" button (border #29292b)
  - message stream left-aligned x≈444 (main card content starts at x≈303)
  - AI/status/tool text #e1e1e1; meta line #5f5f5f; tool call green #59b589 icon
  - user messages: right-aligned #222222 bubble
  - composer x≈420..1199, border #383738, height 138px
*/

import { useState } from "react"
import {
  AppGlyphIcon,
  CheckCircleIcon,
  ChevronRightIcon,
  FileIcon,
  FolderIcon,
  LinkIcon,
  PauseIcon,
  StopIcon,
  PlusIcon,
  VideoIcon,
  ImageIcon,
  GlobeIcon,
  MicIcon,
  WaveIcon,
  ChevronDownIcon,
} from "./icons"
import {
  CHAT_MESSAGES,
  CHAT_TASK_NAME,
  CHAT_TIME,
  CHAT_OPEN_IN,
  CHAT_MODEL,
  CHAT_PLACEHOLDER,
  CHAT_GENERATED_BY,
  CHAT_STOP_BTN,
  type ChatMessage,
} from "@/lib/trae-chat-data"

export function ChatWorkspace() {
  return (
    <div className="flex min-w-0 flex-1 flex-col">
      <ChatHeader />
      <div className="scroll-thin min-h-0 flex-1 overflow-y-auto">
        <div className="flex flex-col pb-4 pt-[20px]">
          {CHAT_MESSAGES.map((msg, i) => (
            <Message key={i} msg={msg} />
          ))}
          {/* footer row: stop button + generated-by note */}
          <div className="mt-[46px] flex items-center px-[141px]">
            <button className="flex items-center gap-[6px] text-[12px] text-text-3 transition-colors hover:text-text-1">
              <StopIcon className="size-3" />
              <span>{CHAT_STOP_BTN}</span>
            </button>
            <span className="ml-auto text-[11px] text-text-4">{CHAT_GENERATED_BY}</span>
          </div>
        </div>
      </div>
      <ChatComposer />
    </div>
  )
}

function ChatHeader() {
  return (
    <header className="flex h-[48px] shrink-0 items-center pl-[22px] pr-[79px]">
      <FolderIcon className="size-[13px] shrink-0 text-[#7c7c7c]" />
      <span className="ml-[17px] truncate text-[13.5px] text-hero">{CHAT_TASK_NAME}</span>
      <span className="ml-[7px] shrink-0 text-[12px] text-text-3">{CHAT_TIME}</span>
      <button
        className="ml-auto flex shrink-0 items-center gap-[9px] rounded-[6px] border border-btn-border px-[11px] py-[5px] text-[12px] leading-none text-[#cbcdd6] transition-colors hover:text-white"
        aria-label={CHAT_OPEN_IN}
      >
        <span>在</span>
        <AppGlyphIcon className="size-[14px]" />
        <span>中打开</span>
        <span className="h-[12px] w-px bg-btn-border" />
        <LinkIcon className="size-[11px] text-[#8b8e9b]" />
      </button>
    </header>
  )
}

function Message({ msg }: { msg: ChatMessage }) {
  const style = { marginTop: msg.mt }
  switch (msg.type) {
    case "meta":
      return (
        <div style={style} className="flex items-center gap-[7px] px-[141px] text-[12px] text-text-2">
          <FileIcon className="size-[12px] shrink-0 text-text-3" />
          <span>{msg.text}</span>
        </div>
      )
    case "ai":
      return (
        <p style={style} className="px-[141px] text-[13.5px] leading-[20px] text-hero">
          {msg.text}
        </p>
      )
    case "tool":
      return (
        <div style={style} className="flex items-start gap-[11px] px-[141px]">
          <CheckCircleIcon className="mt-[3px] size-[13px] shrink-0 text-tool-green" />
          <span className="flex items-center text-[13.5px] leading-[20px] text-hero">
            {msg.text}
            {msg.note ? (
              <span className="ml-[8px] text-[12px] text-text-3">{msg.note}</span>
            ) : null}
            <ChevronRightIcon className="ml-[6px] size-[10px] text-text-3" />
          </span>
        </div>
      )
    case "status":
      return (
        <div style={style} className="flex items-center gap-[9px] px-[141px] text-[13.5px] text-hero">
          <PauseIcon className="size-[11px] shrink-0 text-[#777777]" />
          <span>{msg.text}</span>
        </div>
      )
    case "user":
      return (
        <div style={style} className="flex justify-end pr-[136px]">
          <div className="flex h-[20px] max-w-[560px] items-center rounded-[8px] bg-user-bubble px-[16px] text-[13.5px] leading-[20px] text-hero">
            {msg.text}
          </div>
        </div>
      )
    case "user-gray":
      return (
        <p style={style} className="px-[141px] text-[13.5px] leading-[20px] text-[#a9a9a9]">
          {msg.text}
        </p>
      )
    case "reference":
      return (
        <div style={style} className="flex items-center gap-[7px] px-[141px] text-[13.5px] leading-[20px]">
          <LinkIcon className="size-[12px] shrink-0 text-text-3" />
          <span className={msg.text === "TraeWork" ? "text-hero" : "text-text-3"}>
            {msg.text}
          </span>
        </div>
      )
  }
}

function ChatComposer() {
  const [value, setValue] = useState("")
  return (
    <div className="shrink-0 px-[117px] pb-[16px]">
      <div className="overflow-hidden rounded-[12px] border border-border-composer">
        <div className="flex h-[136px] flex-col bg-main">
          <textarea
            value={value}
            onChange={(e) => setValue(e.target.value)}
            rows={1}
            placeholder={CHAT_PLACEHOLDER}
            className="scroll-thin w-full flex-1 resize-none bg-transparent px-[22px] pt-[20px] text-[13.5px] leading-[20px] text-text-1 placeholder:text-chat-placeholder focus:outline-none"
          />

          {/* action row */}
          <div className="flex h-[44px] items-center pl-[22px] pr-[13px]">
            <button
              aria-label="添加"
              className="text-[#afafaf] transition-colors hover:text-text-1"
            >
              <PlusIcon className="size-[15px]" />
            </button>

            {/* media well: video / image (globe sits outside the well) */}
            <div className="ml-[15px] flex h-[26px] items-center gap-[6px] rounded-[7px] border border-iconwell-border bg-iconwell px-[6px]">
              <button aria-label="视频" className="text-icon-violet">
                <VideoIcon className="size-[14px]" />
              </button>
              <span className="h-[12px] w-px bg-iconwell-border" />
              <button aria-label="图片" className="text-icon-orchid">
                <ImageIcon className="size-[14px]" />
              </button>
            </div>
            <button
              aria-label="网络"
              className="ml-[6px] text-[#d4d4d4] transition-colors hover:text-white"
            >
              <GlobeIcon className="size-[14px]" />
            </button>

            <div className="ml-auto flex items-center">
              <button className="flex items-center gap-[6px] text-[12px] text-model transition-colors hover:text-text-1">
                <span>{CHAT_MODEL}</span>
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
      </div>
    </div>
  )
}
