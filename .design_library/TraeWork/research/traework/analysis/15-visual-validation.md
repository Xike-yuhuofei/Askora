# 15 — Visual Validation（Phase 1 基线）

**Phase**: 1 · **Generated**: 2026-08-12
**状态**: Phase 1 未进入 Figma 构建，此文档记录「Token↔Screenshot」基线验证结论，作为 Phase 2 像素级 Overlay 的输入。

---

## 基线验证结果（Token ↔ Screenshot）

| 元素 | Reference | Reconstruction(基线) | Delta | Cause | Action | Confidence |
|---|---|---|---|---|---|---|
| Sidebar 背景 | `#f5f5f5` | Token bg-base-secondary `#f5f5f5` | 0 | — | ✅ | [C] |
| Workspace 背景 | `#ffffff` | Token bg-base-default `#ffffff` | 0 | — | ✅ | [C] |
| Sidebar 右缘 | x=301 `#efefef` | border-neutral-l1 叠加 | ≈1 | 半透明叠加 | ✅ | [I] |
| 发送按钮 | `#4b3fe3` | Token bg-brand `#4b3fe3` | 0 | — | ✅ | [C] |
| Composer 背景 | `#f5f5f5` | bg-base-secondary | 0 | — | ✅ | [C] |
| Composer 边框 | 1px `#e7e7e7` | border-neutral-l1 | ≈1 | 叠加/抗锯齿 | ✅ | [I] |
| 文本色 | `#181818`± | text-default `#171717` | ≤1 | 抗锯齿 | ✅ | [I] |

## 待 Phase 2 验证项

| 项 | 说明 |
|---|---|
| Composer 圆角 | 截图可见圆角，radius 精确值需放大验证 |
| 行高 | 14px 文本 vs 整行高度的换算 |
| Status 色 | 主截图无 status 色块，需其他页面 |
| Typography | 具体字体渲染（SF Pro 是否安装） |

## 优先级

Design System Consistency + High Visual Fidelity，非逐像素机械一致。

## 结论

1. [C] Token 与截图基线一致（≤1 RGB 偏差），Phase 2 可放心以 Token 为构建源。
2. [I] 边框/半透明叠加造成 ±1 偏差，属正常渲染，不重建 Token。
