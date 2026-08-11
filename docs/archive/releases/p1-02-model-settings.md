# Askora P1-02 Secure Model Settings Completion Report

> Status：DONE
>
> 日期：2026-08-09
>
> 实现合同：ADR-0012、`MODEL-CONFIG-*`、P1-02 Vertical Slice、EXEC-040/041
>
> Decision authority：user-delegated Codex

## 1. Release 结论

```text
Engineering Gate: PASS
Security / Ownership Gate: PASS
Real Provider Product Gate: PASS
Learning Evidence Gate: LEARNING_EVIDENCE_INSUFFICIENT
Packaged Artifact Signing: AD_HOC / NOT NOTARIZED
```

P1-02 已闭合 packaged macOS App 内的完整路径：

```text
Settings 选择 provider/model 并输入 Key
→ fixed synthetic real probe
→ macOS safeStorage encrypted vault revision
→ isolated backend restart + authenticated private readiness
→ canonical real-model learning response
→ App quit/relaunch exact revision recovery
```

用户不需要编辑或导入 `.env`。候选 Key 不回显，不进入 renderer persistence、普通 HTTP API、
日志、Prompt、audit 或导出；失败不会静默切换 provider，也不会写成 learner failure。

## 2. 交付范围

- `ModelRouteProfileV1` 的 ACTIVE/DISABLED/EXTERNAL_READ_ONLY/UNCONFIGURED/DEGRADED 投影；
- Electron `safeStorage` encrypted vault、原子写入、revision conflict、rollback 与 recovery clear；
- exact top-level sender/origin/path 校验的窄 IPC；renderer 无 decrypt/file/env/control-token 能力；
- qwen/deepseek/doubao/zhipu 既有 adapter 的 provider/model allowlist；
- fixed synthetic probe、bounded timeout、no fallback 与稳定错误映射；
- 每个 App process 独立 loopback port，每次 backend start 新高熵 control token；
- 私有 authenticated readiness 证明当前 child identity，公共 `/ready` 不能满足；
- Settings 的验证、应用、更新、重新验证、停用、错误恢复、费用与数据边界说明；
- sanitized local audit 与 secret-free public summary；
- packaged macOS 真实 provider、canonical learning 与 relaunch recovery 验收。

## 3. Packaged macOS 真实验收

### 3.1 配置与恢复

验收对象：

```text
App: apps/frontend/release/mac-arm64/Askora.app
provider/model: zhipu / glm-4.7-flash
vault state: ACTIVE
vault source: DESKTOP_VAULT
revision/runtime_revision: 1 / 1
probe prompt: model-settings-probe-v1
successful probe latency: 613 ms
verified_at: 2026-08-09T08:25:23Z
```

真实操作从 Settings 输入候选 Key。前两次 provider 返回 429，UI 显示
`MODEL_RATE_LIMITED` 与允许的重试动作，vault 未创建、旧状态未改变，也未 silent failover。
间隔重试后智谱返回 200，audit 记录 `model_config_probe_succeeded`；App 写入 revision 1、
重启 backend，并以当前 start token 的私有 readiness 与 `/health/config` exact revision 完成验证。

退出 App 后，以同一 `ASKORA_USER_DATA_DIR` 重新启动 packaged App：

- backend 只加载 `zhipu`，无其他 generative provider；
- session refresh 成功；
- Settings 恢复 `已验证`、智谱、`glm-4.7-flash`、Askora 安全存储、版本 1；
- audit 新增 `model_config_read`，`prior_revision=1`、`restart_ready=true`；
- Key 输入框为空，stored credential 不回填 renderer。

### 3.2 Canonical real-model learning

为避免多知识单元造成合理的目标映射歧义，验收使用单一已发布 KnowledgeUnit 的最小 EPUB：

```text
document_id: 94a21931-3d61-4084-a5fa-ff53132205de
goal_id: 23e6426a-5013-58e8-ba66-d50d00f18793
plan_id/version: a0954b1f-adbd-5945-9a0b-279682bcb5af / 1
activity_id: 79047774-c703-5ae1-b472-c06724f2a78b
session_id: 84df1a78-b7c4-5ba9-8ab6-d44d4c19628b
turn_kind: system_start
```

packaged App 从资料库点击“从这份资料开始学习”，明确输入并确认目标，完成 mapping、
diagnostic bootstrap、plan 与 activity selection，再点击“开始本次学习”。后端日志记录：

```text
POST https://open.bigmodel.cn/api/paas/v4/chat/completions → 200 OK
POST /api/v1/book-learning/activities/{activity_id}/start → 200 OK
```

durable transcript 当前证据：

| 字段 | 证据 |
|---|---|
| turn | `turn_number=1`、`turn_kind=system_start` |
| execution mode | `real_model` |
| provider/model | `zhipu / glm-4.7-flash` |
| prompt version | `v03-policy-bound-real-render/1.0` |
| latency | 990 ms |
| token usage | 233 input / 36 output / 269 total |
| evidence | exact `EvidenceBundle` ref，1 处 learner-visible source |
| policy action | exact `TeachingAction` ref |

UI 显示非 Mock 的聚焦问题、`依据资料 · 1 处`，折叠技术详情显示
`real_model · zhipu · glm-4.7-flash · v03-policy-bound-real-render/1.0`，并列出 SYS01/02/03/06
owner refs。transcript 的 `next_turn_number=2`，证明首轮已经持久接受。

这份临时 QA 数据库由 `create_all` 建表但没有 migration seed，因此首次 activity start 在模型调用前
fail closed 为 `POLICY_RUNTIME_PROFILE_UNAVAILABLE`。验收只向该临时数据库写入既有 ADR-0003
默认 production `PolicyBundle` 与 activation，再重试；没有新增策略语义或使用测试替身。
后续学习者回合因当前 retrieval 未提供新的 evidence 而 fail closed 为
`AI_MODEL_EVIDENCE_REQUIRED`；已接受首轮保持不变。该既有 Book-to-Learning 后续回合问题不属于
P1-02 配置所有权，但保留为明确的范围外产品债务，不把一次模型连通性声称为完整学习效果。

## 4. Security 与 Ownership 证据

- vault 文件权限 `0600`，wrapper 仅有 `wrapper_version` 与 ciphertext；无 plaintext fallback；
- audit 文件权限 `0600`，字段只来自固定 allowlist；敏感字段扫描为 0；
- audit/error/public summary 不含 Key、Key fragment/fingerprint、ciphertext、control token、
  Authorization、request body 或 provider raw body；
- candidate probe 只发送固定合成文本，不包含用户资料、学习历史、EvidenceBundle 或文档；
- control token 必须为 48 decoded bytes 的 64-char base64url，并满足 unique byte、Shannon entropy
  与 repeated-block 质量阈值；可预测的 16-byte 短周期 token 被拒绝；
- `ModelConfigErrorV1` 的每个 code 只能使用唯一 category/retryable 组合；合法 enum 的非法组合被拒绝；
- vault ACTIVE 会清除全部 inherited provider Key，只注入 exact active route；DISABLED tombstone 防止
  `.env` 复活；
- SYS08 保持 model route 唯一 semantic owner；配置失败不写 learner、assessment、plan、activity、
  review 或 knowledge truth。

## 5. 自动化与构建门禁

| Gate | 当前结果 |
|---|---|
| targeted model configuration backend suite | 25 passed |
| backend full pytest | 378 passed, 2 skipped, 4 warnings |
| Ruff | PASS |
| mypy | 163 source files PASS；仅既有 untyped-body notes |
| PostgreSQL migration upgrade + `alembic check` | PASS；`No new upgrade operations detected` |
| Electron Node tests | 41/41 PASS |
| frontend Vitest | 15 files / 70 tests PASS |
| Vite production build | PASS |
| npm audit high | 0 vulnerabilities |
| docs checker | 145 files / 0 broken local links |
| `git diff --check` | PASS |
| packaged real provider configure/restart | PASS |
| packaged canonical real-model response | PASS |
| packaged quit/relaunch exact recovery | PASS |

迁移校验使用明确命名的临时本地 PostgreSQL 数据库，从 base upgrade 到 head 后执行
`alembic check`，完成后已删除该临时数据库；未修改用户业务数据库。

## 6. P1-02 Acceptance Criteria

| AC | 结论 | 主要证据 |
|---|---|---|
| P102-AC-001 | PASS | `MODEL-CONFIG-AC-001..009` contracts/tests/runtime evidence |
| P102-AC-002 | PASS | packaged Settings apply/reverify/update/clear contracts；无 `.env` 编辑 |
| P102-AC-003 | PASS | 401/403/model/429/timeout/5xx/storage/revision/apply/rollback 稳定分支 |
| P102-AC-004 | PASS | fixed synthetic probe、secret isolation 与 audit scan |
| P102-AC-005 | PASS | rollback 与 DISABLED environment suppression tests |
| P102-AC-006 | PASS | exact route；无 silent failover；Mock 不满足 gate |
| P102-AC-007 | PASS | 1440/1024/768/360、200% zoom、keyboard/live status 自动化与真实页面 |
| P102-AC-008 | PASS | packaged Zhipu configure → canonical real response → relaunch |
| P102-AC-009 | PASS | full backend/frontend/Electron/security/docs gates |
| P102-AC-010 | PASS | EXEC-040/041、release report、gap register 与独立 commits |
| P102-AC-011 | PASS | explicit unreadable-vault recovery 与 Keychain fail-closed tests |
| P102-AC-012 | PASS | sanitized apply/clear/recovery audit；forbidden field count 0 |
| P102-AC-013 | PASS | per-App port、current-token private readiness、impostor `/ready` tests |

Blocking SPEC GAP：none。

## 7. Claim Boundary 与发布限制

P1-02 证明 Engineering、Security/Ownership、真实 provider 产品路径与配置恢复；不证明自适应教学
改善真人学习，因此 Learning Evidence 保持 `LEARNING_EVIDENCE_INSUFFICIENT`。

当前 `.app` 为 ad-hoc/linker signature，`TeamIdentifier` 不存在，未 notarize；`spctl` 不接受该包。
这不影响本机 packaged 功能验收，但在正式分发前仍需有效 Apple Developer 签名与公证门禁。
