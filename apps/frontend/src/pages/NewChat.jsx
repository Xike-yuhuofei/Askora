/*
  新建对话页（/chat 与 / 双入口）—— 第一阶段：像素 + 文案 1:1 复刻
  .design_library/TraeWork/prototypes/shell-replica/components/trae/main-workspace.tsx 中栏。
  仅输入框可编辑；发送、建议 chips、模型/环境/项目选择等按钮暂不接线，
  第二阶段再统一修改文案并接入真实行为。
*/

import { useState } from 'react'
import {
  BracketsIcon,
  ChevronDownIcon,
  ChipAppIcon,
  ChipDocIcon,
  ChipGameIcon,
  ChipScriptIcon,
  CodebaseIcon,
  ComputerIcon,
  GlobeIcon,
  ImageIcon,
  MicIcon,
  PlusIcon,
  VideoIcon,
  WaveIcon,
} from '../components/WelcomeIcons'
import './NewChat.css'

const SUGGESTION_CHIPS = [
  { id: 'app', label: '应用开发', icon: 'app' },
  { id: 'understand', label: '项目理解', icon: 'understand' },
  { id: 'game', label: '游戏创意', icon: 'game' },
  { id: 'script', label: '工具脚本', icon: 'script' },
]

const CHIP_ICONS = {
  app: ChipAppIcon,
  understand: ChipDocIcon,
  game: ChipGameIcon,
  script: ChipScriptIcon,
}

const MODEL_NAME = 'Kimi-K2.7-Code'
const ENVIRONMENT_NAME = '本地'
const PROJECT_NAME = 'Askora'
const COMPOSER_PLACEHOLDER = '帮你编写代码、调试 Bug、优化性能等开发工作，交付生产级代码产物。'

export default function NewChat() {
  const [value, setValue] = useState('')

  return (
    <div className="newchat-page">
      <div className="newchat-page__inner">
        {/* hero */}
        <h1 className="newchat-hero">
          <BracketsIcon className="newchat-hero__icon" />
          <span className="newchat-hero__text">
            <span className="newchat-hero__prefix">Code with{' '}</span>
            <span className="newchat-hero__brand">TRAE</span>
          </span>
        </h1>

        {/* composer */}
        <div className="newchat-composer">
          {/* input zone */}
          <div className="newchat-composer__input-zone">
            <div className="newchat-composer__field">
              <textarea
                value={value}
                onChange={(event) => setValue(event.target.value)}
                rows={1}
                placeholder={COMPOSER_PLACEHOLDER}
                className="newchat-composer__textarea"
                aria-label="新对话输入"
              />
            </div>

            {/* action row */}
            <div className="newchat-composer__actions">
              <button type="button" aria-label="添加" className="newchat-composer__plus">
                <PlusIcon className="newchat-composer__plus-icon" />
              </button>

              {/* media well: video / image / globe */}
              <div className="newchat-composer__media-well">
                <button
                  type="button"
                  aria-label="视频"
                  className="newchat-composer__media-btn newchat-composer__media-btn--video"
                >
                  <VideoIcon className="newchat-composer__media-icon" />
                </button>
                <button
                  type="button"
                  aria-label="图片"
                  className="newchat-composer__media-btn newchat-composer__media-btn--image"
                >
                  <ImageIcon className="newchat-composer__media-icon" />
                </button>
                <button
                  type="button"
                  aria-label="网络"
                  className="newchat-composer__media-btn newchat-composer__media-btn--globe"
                >
                  <GlobeIcon className="newchat-composer__media-icon" />
                </button>
              </div>

              <div className="newchat-composer__trailing">
                <button type="button" className="newchat-composer__model">
                  <span>{MODEL_NAME}</span>
                  <ChevronDownIcon className="newchat-composer__model-chevron" />
                </button>
                <button type="button" aria-label="语音输入" className="newchat-composer__mic">
                  <MicIcon className="newchat-composer__mic-icon" />
                </button>
                <button type="button" aria-label="发送" className="newchat-composer__send">
                  <WaveIcon className="newchat-composer__send-icon" />
                </button>
              </div>
            </div>
          </div>

          {/* context bar */}
          <div className="newchat-composer__context-bar">
            <ContextSelect icon={<ComputerIcon />} label={ENVIRONMENT_NAME} />
            <ContextSelect icon={<CodebaseIcon />} label={PROJECT_NAME} />
          </div>
        </div>

        {/* suggestion chips */}
        <div className="newchat-chips">
          {SUGGESTION_CHIPS.map((chip) => {
            const Icon = CHIP_ICONS[chip.icon]
            return (
              <button key={chip.id} type="button" className="newchat-chip">
                <Icon className="newchat-chip__icon" />
                <span>{chip.label}</span>
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}

function ContextSelect({ icon, label }) {
  return (
    <button type="button" className="newchat-context-select">
      <span className="newchat-context-select__icon">{icon}</span>
      <span>{label}</span>
      <ChevronDownIcon className="newchat-context-select__chevron" />
    </button>
  )
}
