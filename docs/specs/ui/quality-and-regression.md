# Askora UI/UX Quality & Regression Contract

> 状态：**Canonical UI/UX Quality Contract — Current Only**  
> 冻结日期：2026-08-11  
> 上游：`docs/product/PRODUCT-DEFINITION.md`、`docs/design/experience/**`  
> Governing quality：`docs/specs/quality/testing-standard.md`、`definition-of-done.md`、`security-standard.md`、`v1-local-web-quality-reconciliation.md`  
> Scope：长期有效 UI/UX verification；一次性 migration 执行细节属于 Vertical Slice / EXEC

---

## 1. Purpose

本文件定义 Askora UI/UX 长期必须满足的质量门禁。

它回答：

> **如何证明界面仍然符合当前 Experience / UI contracts，并且没有破坏学习、来源、数据诚实、可访问性与安全边界。**

本文件不维护当前 backlog、EXEC 队列、临时 migration 顺序或已完成 issue 状态。

---

## 2. Acceptance Ownership

必须区分：

```text
Product Acceptance
UX Acceptance
UI Contract / Engineering Acceptance
Accessibility / Security Acceptance
Learning Evidence
```

UI/UX PASS 不能自动满足 Product Acceptance，更不能证明真实 retention / transfer / mastery 改善。

---

## 3. Traceability Gate

### UI-QR-001

关键 UI test / acceptance evidence 必须可追踪到适用：

- Product `CAP-* / PD-REQ-* / PD-RULE-*`；
- Experience `EXP-* / LEXP-* / INT-*`；
- UI current contract `UI-SN-* / UI-LRN-* / UI-DS-*`；
- technical/security contract（适用时）。

不得只用 screenshot / snapshot 证明业务或学习语义。

### UI-QR-002

如果实现要求改变 Product Scope，报告 `PRODUCT DEFINITION GAP`；如果 Product 已明确但 Experience/Spec 不足，分别报告 `DESIGN GAP` / `SPEC GAP`。

不得通过 frontend-only state 静默解决上游 gap。

---

## 4. Semantic Regression

必须验证：

- L0 仍只有 Today / Learning / Library；
- Settings/Recovery 是 Utility；
- Chat/Tutor 不成为 Product Domain；
- Learning 不恢复 Goal/Plan/Progress/History 常驻管理中心；
- Today canonical activity 存在时仍只有一个 Primary Learning Task；
- route/navigation 不产生隐藏 business write；
- domain object 不因新增 backend projection 自动变成 page/nav/card；
- frontend 不产生第二 canonical truth。

---

## 5. Learning Experience Regression

至少验证：

- current Activity / task 可识别；
- learner 有真实 Attempt 路径；
- Question / Attempt / Feedback / Hint / Remediation / Source 语义可理解；
- learner error 与 model/tool/retrieval/runtime error 分离；
- actual assistance / answer exposure / validation obligation 不由 frontend 推断；
- citation 可回真实 SourceSpan；
- view source 不破坏 current learning context；
- Notes 不静默丢失且 save/conflict 状态真实；
- interrupted learning 可恢复；
- long session/history 不把旧 state 冒充 current state。

---

## 6. Workspace Isolation / Continuity

必须验证：

- Left/Center/Right/Drawer 使用同一 current Workspace；
- Workspace switch 处理 draft / stream / note / active session / material position；
- cross-Workspace Material/Source/Note access fail closed；
- 单一 Workspace 不显示虚假 selector；
- Workspace switch 不通过清空 frontend state 假装成功；
- browser memory 不被描述为 durable recovery。

---

## 7. Screen State Regression

关键 screen/region 至少测试适用：

```text
LOADING
EMPTY
READY
PARTIAL
STALE
ERROR
UNAUTHORIZED
```

特定 projection：

```text
MISSING
LOW_CONFIDENCE
```

Action / Note 等还需适用：

```text
LOADING/PENDING
SAVED
FAILED
CONFLICT
RECOVERABLE
DISABLED
```

禁止：

- catch 后返回空数组伪装 EMPTY；
- MISSING → 0/false/空进度条；
- stale/partial → READY；
- 未持久化 → SAVED；
- system failure → learner incorrect。

---

## 8. Responsive Gate

每次涉及 shell、核心 screen、Design System foundation 的 substantive UI change，至少验证：

```text
1440×900
1024×768
768×1024
360×800
100% zoom
200% zoom
```

必须证明：

- Primary task 可完成；
- 页面无阻断性横向滚动；
- Right Rail / Drawer / auxiliary surfaces 在窄屏有可访问替代；
- citation/error/assistance/validation obligation 不会因窄屏永久消失；
- 无关键三层嵌套滚动；
- 中文长标题、长公式、长引用、长错误可处理。

---

## 9. Keyboard / Accessibility Gate

至少覆盖：

- keyboard-only primary learning path；
- focus order / visible focus；
- route navigation 后语义起点 focus；
- modal/sheet/drawer close 后 focus return；
- Escape close（适用 transient surface）；
- icon-only accessible name；
- contextual action keyboard/touch fallback；
- status/error/save live announcement；
- screen-reader 能理解 Left/Center/Right/Drawer 与主要 learning roles；
- state 不只靠 color；
- reduced motion；
- WCAG AA 对比度（适用文本/关键 UI）。

streaming 不得对每个 token delta 产生 screen-reader spam。

---

## 10. Design System Regression

必须验证：

- semantic token 使用；
- Button/Nav/Row/Input/Disclosure/Tab/Status states；
- Primary/Secondary/Contextual hierarchy；
- repeated object 默认 row/list；
- 无 Card ocean；
- no hover-only core action；
- page-local CSS 不建立第二 token体系；
- `.design_library` / screenshot 不被当作 runtime Authority。

视觉回归只能证明 presentation regression，不证明 interaction/business semantics。

---

## 11. Route / Deep-link Regression

至少验证：

- stable product destinations；
- Workspace-scoped routes（存在时）；
- activity/session deep links；
- compatibility goal/plan/progress/history routes；
- back/reload；
- legacy redirect no side effect；
- no redirect loop；
- route change 不丢未提交/可恢复状态；
- retirement 前历史 deep link 有明确行为。

---

## 12. Library / Provenance Regression

必须验证：

- import/search/filter/material list 基础路径；
- batch/contextual action 只在正确 context 出现；
- normal v1 UI 无 OCR action/status/review；
- scanned PDF unsupported/partial honest fallback；
- deferred candidates 无 placeholder；
- source label/locator/SourceSpan 真实可追踪；
- 无跨 Workspace source leakage。

---

## 13. Settings / Local Data / Security Regression

设置重构不得弱化上游安全与数据合同。

至少验证：

- BYOK credential 不回填、不进入普通 DOM/web storage/log/backup/export；
- data backup / export / restore / erasure 语义不混淆；
- destructive confirmation / revision conflict / retry 保持；
- Account/Login/AuthSession residue 不重新可达；
- Recovery 只使用正式 owner-defined actions；
- raw traceback、secret、绝对路径、敏感 environment 不在普通 UI 暴露。

---

## 14. Rich Content / Streaming Security

继续覆盖：

- unsafe raw HTML；
- unsafe URL；
- unauthorized remote image；
- invalid structured render payload；
- prompt-injection / grader-only leakage；
- unauthorized source/evidence；
- duplicated stream finalization；
- historical message online LLM re-generation。

Durable historical rendering必须使用已持久化 content/render payload，不为旧消息重新调用在线模型补富文本。

---

## 15. Performance Evidence

涉及性能敏感 UI 时先记录 baseline，再定义不回归或明确 budget。

至少关注：

- production bundle；
- first usable shell；
- Workspace switching；
- long learning history；
- Material list；
- RichMessage/Math lazy load；
- memory growth across repeated route/workspace switch。

无 measurement 不得发明硬阈值。

长 History/Conversation SHOULD 评估 pagination/virtualization；不得一次性加载全部私人 message/evidence history。

---

## 16. Required Engineering Gates

前端 UI substantive change 默认至少运行：

```bash
cd apps/frontend
npm test -- --run
npm run build
npm audit --audit-level=high

cd ../..
python3 .github/workflows/check_docs.py
git diff --check
```

如果修改 backend query/API，再运行适用 backend targeted + full gates，以及 current Required CI 所要求的质量命令。

全量 gate 因既有问题失败时必须区分：

```text
introduced failure
vs
pre-existing failure
```

不得删除测试、弱化断言、扩大 ignore 来制造 PASS。

---

## 17. Human UX Acceptance

仅自动化通过仍不足以证明复杂学习体验质量。M5 / release acceptance 应至少人工检查：

- 首次进入是否理解该做什么；
- Today → Learning 是否自然；
- 长解释与 Question boundary 是否清晰；
- Attempt / Feedback 是否容易对应；
- citation / source 查看是否不打断学习；
- assistance / validation 文案是否可理解；
- Workspace switch 风险是否清楚；
- 360/768/1024/1440 下任务层级是否仍成立；
- 错误/partial/stale 是否诚实；
- Settings/Recovery 是否保持次级 utility 角色。

人工 UX Acceptance 仍不能被描述为学习效果证据。

---

## 18. Completion / Claim Boundary

UI / UX 工作完成可以声明：

```text
UX Contract Gate: PASS
UI Engineering Gate: PASS
Accessibility Gate: PASS
Security UI Gate: PASS
```

仅在适用 Product Acceptance 已有独立证据时，才可声明对应 Product Acceptance。

以下永远不能仅由 UI PASS 推导：

```text
Learner mastered
Retention improved
Transfer improved
Adaptive policy superior
Learning Evidence Gate PASS
```

---

## 19. Blocking Conditions

以下任一存在时，不得把相关 UI slice 标 DONE：

- Product / Design / Spec authority conflict 未解决；
- frontend mock 冒充 canonical owner truth；
- Learning 恢复常驻管理 dashboard；
- Today primary hierarchy 回归；
- Workspace scope 不一致；
- Note/source 有静默数据丢失或 leakage；
- Library normal UI 暴露已排除 OCR/deferred candidate；
- 360 / 200% zoom / keyboard / error path 未验证；
- MISSING/PARTIAL/STALE 被伪装 READY；
- UI/spec/API/schema change 未声明；
- 通过删除/弱化测试制造 PASS。

---

## 20. Acceptance Criteria

- `UI-QR-AC-001`：current Experience → UI Contract → test traceability 完整；
- `UI-QR-AC-002`：semantic/nav/learning/workspace regression gates 有自动化证据；
- `UI-QR-AC-003`：1440/1024/768/360 + 200% zoom 验证；
- `UI-QR-AC-004`：keyboard/screen-reader/focus/contextual-action 验证；
- `UI-QR-AC-005`：Library/provenance/Settings/security 边界无回归；
- `UI-QR-AC-006`：long-session / streaming / source / notes failure paths 有验证；
- `UI-QR-AC-007`：一次性 migration status 不进入本长期合同；
- `UI-QR-AC-008`：UI/UX Acceptance、Product Acceptance、Learning Evidence 分开报告。
