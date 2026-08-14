# Askora UI

> 仓库根 UI 资产。不是 Product / Experience / Spec 合同。

## 复用谁

只复用 [traework/](traework/README.md)。

消费顺序见 [traework/library-consumption.json](traework/library-consumption.json)：README → tokens（`colors_and_type.css` / `css.json`）→ `components/index.json` → 单个 component contract + preview。`ui_kits/` 只看结构，不要当页面模板复制。

Askora 现行 UI 合同仍是 [`docs/specs/ui.md`](../docs/specs/ui.md)；生产消费路径是该文件的 semantic roles + TraeWork Light 映射（`UI-DS-TOK-005`），不是 `prototypes/shell-replica/`。体验合同在 [`docs/design/experience/`](../docs/design/experience/)。

## 目录

| 路径 | 用途 |
|---|---|
| [traework/](traework/) | 唯一可复用设计系统（tokens / components / icons / previews） |
| [research/traework/](research/traework/) | TraeWork 逆向证据 |
| [research/traecode/](research/traecode/README.md) | 已 superseded 的 TraeCode 研究（源包已删） |
| [prototypes/shell-replica/](prototypes/shell-replica/) | TraeWork 壳的 Next.js 复刻，不是生产前端 |
| [prototypes/learning/](prototypes/learning/) | 旧学习概念 HTML，不是 TraeWork |

## 不要

- 不要把 `research/traecode` 或 `prototypes/learning` 当成复用源；
- 不要用本目录覆盖 `docs/specs/ui.md` 或 Experience Design；
- 不要把 UIKit showcase 根容器抄进 `apps/frontend`。
