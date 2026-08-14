# 10 — Prompt Composer Anatomy（高优先级 Composite）

**Phase**: 1 · **Generated**: 2026-08-12
**Evidence**: 主截图实测 [S] + ai-input contract [L] + dev-explorer composer [L]

---

## 截图实测（Code Welcome）

| 项 | 值 [S] |
|---|---|
| 容器 | x=892..1691（宽 **800px**），y=654..708（高 **55px**） |
| 背景 | `#f5f5f5` = bg-base-secondary |
| 上边框 | 1px `#e7e7e7`（≈ border-neutral-l1） |
| 圆角 | 截图可见圆角，具体 radius 待定（契约 12px）[I] |
| 发送按钮 | 右端 x≈1663..1678，`#4b3fe3` = bg-brand |
| 居中 | 于 Workspace 几何中心 x≈1296 |

> 截图 Composer 高 55px，与 ai-input contract 的 100px（textarea 72 + control 28）不完全一致。可能原因：截图为 collapsed/single-row 态，或测量含边框。[I][U]

## 契约解剖（ai-input contract）[L]

```
PromptComposer (.ds-ai-input)
├── __textarea        (min-height 72px, 4行)
├── __control-row     (28px)
│   ├── __model-selector
│   ├── __attachment-btn
│   └── __send-btn     (28×28 圆形, radius-full, bg-brand)
└── 状态类: --expanded / --focused / --disabled
```

dev-explorer 补充：[L]
- slashes 命令（`/` 触发）
- attach / plugins（+9）
- Fast pass
- 模型下拉（"SOLO Auto Model"）
- voice
- send

## 拆解结构（综合）

```
PromptComposer
├── Editor (textarea, 支持 slashes/多行)
├── Context Add (+ 按钮)
├── Attachment (附加文件)
├── Tool / Context Controls (plugins)
├── Model Selector (下拉)
├── Voice (语音输入)
├── Submit (发送, brand 圆形)
└── Context Bar (运行时/来源: Local / Solo workspace)
```

## 状态模型（契约）[L]

| 状态 | 说明 |
|---|---|
| idle | 默认 |
| focused | 聚焦（border-brand / focus ring） |
| typing | 输入中 |
| expanded | 展开（多行，max 300px） |
| disabled | 禁用 |
| loading | 提交中/运行中 |

## 尺寸规格（契约 + 实测对照）

| 项 | 契约 [L] | 截图 [S] |
|---|---|---|
| height | 100px default / 300px max | 55px |
| radius | 12px | 待定 [U] |
| border | 1px border-neutral-l1 | 1px #e7e7e7 ✅ |
| send | 28×28 radius-full | 15×14（未含 padding）[I] |
| 字体 | body-base (14px) | — |

## 结论

1. [C][S] Composer 是中心居中的复合输入组件，跨模式（AI Pattern）。
2. [C][L] 解剖：Editor + Context + Attachment + Model + Voice + Submit + Context Bar。
3. [I][L][S] 主控件尺寸以 ai-input contract 为准，截图验证边框与品牌发送按钮。
4. [U] 截图 55px vs 契约 100px 高度差异需 Phase 2 用放大图/多态验证确认。
5. 不要把 Composer 当普通 Textarea。[C][L]
