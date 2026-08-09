# EXEC-028 — Zhipu Development Model Integration

> Status：DONE
>
> Priority：P1 Development Enablement
>
> Decision authority：user-authorized model configuration

## Objective

将智谱 BigModel 的 OpenAI-compatible API 作为 Askora 可选模型供应商接入，并在本机开发配置中使用
`glm-4.7-flash` 作为默认及数学学科模型；密钥仅保存在被 Git 忽略的后端 `.env`。

## Governance Decision

- `SYS08-041/042/061/072` 已允许授权模型路由、语义保持回退和最小数据外发；无需新增 ADR 或改变 Spec。
- 使用现有 `httpx`，不新增生产依赖、状态 owner、公共领域 Schema 或第二 truth。
- GLM-4.7 系列默认开启 Thinking；教学短回复显式关闭 Thinking，避免推理 token 挤占正文预算。
- 不设置独立的真实模型 token 门禁；调用方未显式传值时，智谱请求不发送 `max_tokens`，不继承其他 provider 的 `LLM_MAX_TOKENS=2048` 默认值。
- 备选方案：复用 `DeepSeekProvider` 并替换 URL。未采用，因为会错误记录 provider provenance，且会混淆健康检查、回退与审计。
- 回滚：将本机 `LLM_DEFAULT_PROVIDER`/`LLM_MATH_PROVIDER` 改回原 provider；删除智谱本机密钥即可停用。

## Required Specs

- `docs/specs/systems/08-ai-orchestration.md`
- `docs/specs/interfaces/error-contract.md`
- `docs/specs/quality/security-standard.md`
- `docs/specs/quality/testing-standard.md`
- `docs/specs/quality/observability-standard.md`
- `docs/specs/quality/definition-of-done.md`

## Allowed Files

```text
docs/exec-plans/active/EXEC-028-zhipu-development-model.md
docs/exec-plans/completed/EXEC-028-zhipu-development-model.md
docs/exec-plans/README.md
docs/exec-plans/completed/README.md
apps/backend/.env
apps/backend/.env.example
.env.example
apps/backend/app/core/config.py
apps/backend/app/main.py
apps/backend/app/orchestration/model_rendering.py
apps/backend/app/services/llm/model_router.py
apps/backend/tests/conftest.py
apps/backend/tests/unit/test_model_router.py
apps/backend/tests/evals/test_real_model_e2e.py
```

## Forbidden Changes

- 不提交、打印或写日志泄露 API key；
- 不改变 TeachingAction、Assessment、Mastery、Plan、Review 或知识事实所有权；
- 不让 provider fallback 改变 TeachingAction 语义；
- 不覆盖或整理 UI-02B2 及其他现有用户改动；
- 不把真实模型连通性声明为真人学习效果。

## Acceptance Criteria

- `EXEC028-AC-001`：`zhipu` 是显式 provider，provenance 记录 `zhipu/glm-4.7-flash`。
- `EXEC028-AC-002`：非流式与流式请求均使用配置的 BigModel base URL，错误保持可见。
- `EXEC028-AC-003`：本机默认及数学路由均选择智谱；其他 provider 仍可配置和回退。
- `EXEC028-AC-004`：测试环境显式清空智谱密钥，unit tests 不访问网络或真实凭据。
- `EXEC028-AC-005`：至少一次真实 `glm-4.7-flash` 调用通过 canonical v0.3 real-model gate。
- `EXEC028-AC-006`：密钥不进入 tracked diff、测试结果或日志。

## Required Tests

```bash
cd apps/backend
uv run pytest tests/unit/test_model_router.py
ASKORA_RUN_REAL_MODEL=1 uv run pytest tests/evals/test_real_model_e2e.py -s
uv run ruff check app tests
uv run mypy app --no-error-summary

cd ../..
python3 .github/workflows/check_docs.py
git diff --check
```

## Completion Report Format

- Status；修改文件；路由/回滚；unit/real-model/quality gate evidence；
- 密钥与 worktree preservation；SPEC GAP / residual risks；
- Engineering / Policy-Ownership / Learning Evidence 分层结论。

## Completion Evidence

- Unit：`tests/unit/test_model_router.py`，4 passed；覆盖 non-stream、SSE、default/math route、missing-key provenance。
- Real model：取消本地 token 门禁后 canonical v0.3 gate 1 passed；`provider=zhipu`、`model=glm-4.7-flash`、约 0.7 秒。
- Backend regression：356 passed, 2 skipped；real-model gate 独立运行，未混入普通测试。
- Ruff：`uv run ruff check app tests` PASS。
- Mypy：`uv run mypy app --no-error-summary` PASS（仅保留未检查 untyped function 的提示）。
- Secret：tracked diff 扫描 PASS；真实 key 仅位于 Git-ignored `apps/backend/.env`。
- Docs：本 EXEC 已归档；全仓 docs gate 仍被并发 `CODE_WIKI`/inventory 工作阻塞。
- SPEC GAP：none。Engineering PASS；Policy/Ownership PASS；Learning Evidence 保持 `LEARNING_EVIDENCE_INSUFFICIENT`。
