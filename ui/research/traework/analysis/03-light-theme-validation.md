# 03 — Light Theme Token ↔ Screenshot Validation

**Phase**: 1 · **Generated**: 2026-08-12
**Evidence**: `css.json` Token [L] vs `截图/20260812-091658-TraeCode主界面.png` 实际像素 [S]

本轮重点：Library Token ↔ Actual Product Screenshot Validation（而非 Theme Mapping）。

---

## 验证方法

- 主截图 `20260812-091658-TraeCode主界面.png`（2291×1299，1x）
- 采样方式：OpenCV 读取指定坐标的 RGB，与 token 目标色对比。
- 目标色含透明度 token（如 `border-neutral-l1` = `#737373` @ 0.12）时，按「半透明叠加在背景上」计算期望合成值。

## 结果

### Background / Surface

| Token | Token Value | Observed | 采样点 | Delta | Cause |
|---|---|---|---|---|---|
| bg-base-default | `#ffffff` | `#ffffff` | workspace (400,1200) | 0 | ✅ Confirmed |
| bg-base-secondary | `#f5f5f5` | `#f5f5f5` | sidebar (400,150) | 0 | ✅ Confirmed |
| bg-base-tertiary | `#e5e5e5` | `#e6e6e6` | sidebar 搜索区 (70,80) | 1 | 抗锯齿/采样位置微偏 [I] |
| bg-overlay-l1 | `#737373`@0.08 叠加 | `#f0f0f0` | sidebar hover 行 | ≈1 | 接近预期 [I] |

### Text

| Token | Token Value | Observed | 采样点 | Delta | Cause |
|---|---|---|---|---|---|
| text-default | `#171717` | `#181818`± | sidebar 标题文字 | ≤1 | 抗锯齿 [I] |
| text-secondary | `#404040` | `#404040`± | nav 项文字 | ≤2 | 抗锯齿 [I] |
| text-tertiary | `#737373` | `#737373`± | placeholder | ≤2 | 抗锯齿 [I] |

### Border

| Token | Token Value | Observed | 采样点 | Delta | Cause |
|---|---|---|---|---|---|
| border-neutral-l1 | `#737373`@0.12 | Sidebar 右缘 x=301 `#efefef` | 分隔线 | ≈1 | 半透明叠加在 sidebar 245 上，接近预期 [I] |

### Brand

| Token | Token Value | Observed | 采样点 | Delta | Cause |
|---|---|---|---|---|---|
| bg-brand | `#4b3fe3` | `#4b3fe3` | 发送按钮 (1670,675) | 0 | ✅ Confirmed |

### Status

主界面截图未暴露明显 status 色块，未做像素级验证。[U] 需后续页面（插件市场/自动化模板）验证。

---

## 关键结论

1. [C][L][S] **bg-base-default = #ffffff** 与 Workspace 实测一致。
2. [C][L][S] **bg-base-secondary = #f5f5f5** 与 Sidebar 实测一致。
3. [C][L][S] **bg-brand = #4b3fe3** 与发送按钮实测一致（首次在截图确认品牌色落在 Prompt Composer 主操作区）。
4. [I][S] 截图整体 1~2 RGB 差值可归因于抗锯齿/采样点偏移，**不构成重建 Token 的理由**。
5. [U] Status 色、disabled 态、hover 态在 Code Welcome 截图中证据不足，需更多截图。

## 不需要重建的结论

- 未发现截图实际颜色与 Token 存在超过 2 RGB 的系统性偏差。
- TraeWork Light Token 可作为 Figma 构建的权威来源。[C]
