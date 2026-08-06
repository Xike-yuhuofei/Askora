# Askora 文档服务优化实施计划

## 一、项目现状分析

### 现有基础设施
- **Redis**: 已有 Redis 连接管理（`app/core/redis_client.py`），支持连接池、Key 命名空间
- **PostgreSQL**: 已有完整的数据库模型和异步会话管理
- **工作线程**: `app/workers/` 目录已存在但为空
- **依赖管理**: 使用 `pyproject.toml` + `requirements.txt`

### 当前文档服务实现
- **RAG 检索**: 基于关键词的 TF-IDF 简化检索，无真正的向量语义匹配
- **异步处理**: 使用 `asyncio.create_task` 处理文档解析，无任务队列
- **进度反馈**: 仅通过轮询 API 获取状态，无实时推送
- **分词**: 简单正则提取，无专业中文分词
- **安全扫描**: 无文件病毒扫描能力

### 优化目标
将 MVP 版本升级为生产可用版本，覆盖：分词优化、向量检索、任务队列、实时推送、安全扫描 5 个维度。

---

## 二、实施计划

### Phase 1: 中文分词优化（jieba 接入）

#### 1.1 新增依赖
在 `pyproject.toml` 和 `requirements.txt` 中添加：
```
jieba>=0.42.1
```

#### 1.2 创建分词服务
**新文件**: `app/services/documents/tokenizer.py`

功能：
- 封装 jieba 分词，支持专业术语词典（数学、物理、化学等）
- 提供分词、词性标注、关键词提取接口
- 支持停用词过滤

核心类：
```python
class ChineseTokenizer:
    def tokenize(self, text: str) -> list[str]
    def extract_keywords(self, text: str, top_k: int = 10) -> list[tuple[str, float]]
    def load_custom_dict(self, dict_path: str) -> None
```

#### 1.3 更新 RAG 服务
**修改文件**: `app/services/documents/rag_service.py`

- 将 `_extract_keywords` 方法改为调用 `ChineseTokenizer`
- 支持加权分词（名词 > 动词 > 形容词）
- 支持学科专业词典

#### 1.4 创建专业词典
**新文件**: `app/services/documents/dicts/`

- `math_dict.txt`: 数学术语（方程、导数、积分、矩阵等）
- `physics_dict.txt`: 物理术语（牛顿、重力、电磁、量子等）
- `chemistry_dict.txt`: 化学术语（分子、原子、催化、氧化等）
- `cs_dict.txt`: 计算机术语（算法、递归、编译、数据库等）

---

### Phase 2: 任务队列改造（基于 Redis + asyncio）

#### 2.1 任务队列实现
**新文件**: `app/workers/task_queue.py`

设计原则：
- 基于 Redis List 实现任务队列，无需额外引入 Celery
- 配合 `asyncio` 实现非阻塞任务处理
- 支持任务优先级、重试、超时

核心类：
```python
class TaskQueue:
    async def enqueue(self, task: Task) -> str  # 返回 task_id
    async def process(self, task_id: str) -> TaskResult
    async def retry(self, task_id: str) -> None
    async def cancel(self, task_id: str) -> None

class Task:
    id: str
    type: str  # "document_process", "embedding", ...
    payload: dict
    priority: int  # 0-3
    max_retries: int
    timeout: int

class TaskResult:
    task_id: str
    status: str  # "pending", "running", "completed", "failed"
    result: dict
    error: str
    progress: float
```

#### 2.2 任务处理器注册
**新文件**: `app/workers/handlers.py`

- `DocumentProcessHandler`: 文档解析处理
- `EmbeddingHandler`: 向量生成处理

#### 2.3 Worker 启动入口
**新文件**: `app/workers/__main__.py`

- 启动 Worker 协程，持续消费任务队列
- 支持优雅关闭

#### 2.4 集成到文档服务
**修改文件**: `app/services/documents/document_service.py`
**修改文件**: `app/api/v1/documents.py`

- 上传文档后通过 `TaskQueue.enqueue()` 提交处理任务
- 替代原来的 `asyncio.create_task()`

---

### Phase 3: 实时进度推送（WebSocket）

#### 3.1 WebSocket 服务
**新文件**: `app/services/websocket/ws_manager.py`

功能：
- 管理 WebSocket 连接池
- 支持按用户 ID 分组推送
- 支持心跳检测、断线重连

核心类：
```python
class WebSocketManager:
    async def connect(self, user_id: str, ws: WebSocket) -> None
    async def disconnect(self, user_id: str) -> None
    async def send_to_user(self, user_id: str, message: dict) -> None
    async def broadcast(self, message: dict) -> None
```

#### 3.2 进度推送 API
**新文件**: `app/api/v1/ws.py`

- `WS /api/v1/ws/documents` 建立 WebSocket 连接
- 推送事件类型：
  - `document_processing_started`
  - `document_processing_progress`
  - `document_processing_completed`
  - `document_processing_failed`

#### 3.3 集成到任务队列
**修改文件**: `app/workers/task_queue.py`

- 任务状态变更时自动通过 WebSocket 推送进度
- 进度粒度：读取(20%) → 解析(40%) → 审核(60%) → 分块(80%) → 完成(100%)

---

### Phase 4: 向量检索升级（PGVector）

#### 4.1 数据库扩展
**新增迁移**: `alembic/versions/xxx_add_vector_extension.py`

```sql
CREATE EXTENSION IF NOT EXISTS vector;
ALTER TABLE document_chunks ADD COLUMN embedding vector(1536);
CREATE INDEX idx_chunks_embedding ON document_chunks USING ivfflat (embedding vector_cosine_ops);
```

#### 4.2 向量服务
**新文件**: `app/services/documents/embedding_service.py`

功能：
- 调用 Embedding API 生成向量
- 批量向量化
- 缓存常用文档向量

核心类：
```python
class EmbeddingService:
    async def embed_text(self, text: str) -> list[float]
    async def embed_batch(self, texts: list[str]) -> list[list[float]]
    async def search_similar(self, query_vector: list[float], top_k: int = 5) -> list[SearchResult]
```

#### 4.3 混合检索策略
**修改文件**: `app/services/documents/rag_service.py`

实现双通道检索：
1. **关键词通道**（高速）：使用 jieba 分词 + TF-IDF
2. **向量通道**（精准）：使用 Cosine 相似度
3. **融合策略**：加权融合（0.4 × 关键词 + 0.6 × 向量）

```python
class HybridRetriever:
    async def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedChunk]
    # 1. 关键词检索
    # 2. 向量检索
    # 3. 结果融合去重
```

---

### Phase 5: 文件安全扫描

#### 5.1 轻量级安全检查
**新文件**: `app/services/documents/security_scanner.py`

无需 ClamAV 依赖，实现轻量级检查：
- 文件魔数校验（真实类型 vs 声明类型）
- 危险扩展名检查（.exe, .bat, .js 等）
- 压缩炸弹检测（文件解压后体积过大）
- 内容特征扫描（可执行代码片段、混淆特征）

核心类：
```python
class SecurityScanner:
    DANGEROUS_EXTENSIONS = {".exe", ".bat", ".cmd", ".js", ".vbs", ".scr", ".com"}
    
    def scan(self, file_path: str, declared_ext: str) -> ScanResult
    def check_file_type_mismatch(self, file_content: bytes, declared_ext: str) -> bool
    def check_dangerous_patterns(self, content: str) -> list[str]

class ScanResult:
    safe: bool
    threats: list[str]
    severity: str  # "low", "medium", "high"
```

#### 5.2 集成到上传流程
**修改文件**: `app/services/documents/document_service.py`

- 上传时先进行安全扫描
- 扫描不通过则拒绝上传
- 扫描结果记录在 `user_documents` 表

---

## 三、实施步骤（按依赖顺序）

```
Phase 1: 中文分词 (tokenizer.py + 专业词典)
    ↓
Phase 2: 任务队列 (task_queue.py + handlers.py)
    ↓
Phase 3: 实时推送 (ws_manager.py + ws.py)
    ↓
Phase 4: 向量检索 (embedding_service.py + 混合检索)
    ↓
Phase 5: 安全扫描 (security_scanner.py)
```

---

## 四、需要创建的文件清单

| 序号 | 文件路径 | 功能 |
|------|---------|------|
| 1 | `app/services/documents/tokenizer.py` | 中文分词服务 |
| 2 | `app/services/documents/dicts/math_dict.txt` | 数学专业词典 |
| 3 | `app/services/documents/dicts/physics_dict.txt` | 物理专业词典 |
| 4 | `app/services/documents/dicts/chemistry_dict.txt` | 化学专业词典 |
| 5 | `app/services/documents/dicts/cs_dict.txt` | 计算机专业词典 |
| 6 | `app/workers/task_queue.py` | 任务队列实现 |
| 7 | `app/workers/handlers.py` | 任务处理器 |
| 8 | `app/workers/__main__.py` | Worker 启动入口 |
| 9 | `app/services/websocket/ws_manager.py` | WebSocket 管理 |
| 10 | `app/api/v1/ws.py` | WebSocket API |
| 11 | `app/services/documents/embedding_service.py` | 向量服务 |
| 12 | `app/services/documents/security_scanner.py` | 安全扫描 |

## 五、需要修改的文件清单

| 序号 | 文件路径 | 修改内容 |
|------|---------|---------|
| 1 | `pyproject.toml` | 添加 jieba 依赖 |
| 2 | `requirements.txt` | 添加 jieba 依赖 |
| 3 | `app/services/documents/rag_service.py` | 接入分词 + 混合检索 |
| 4 | `app/services/documents/document_service.py` | 集成任务队列 + 安全扫描 |
| 5 | `app/api/v1/documents.py` | 改为任务队列提交 |
| 6 | `app/main.py` | 启动 Worker + WebSocket |
| 7 | `app/core/config.py` | 添加相关配置项 |
| 8 | `alembic/versions/xxx_add_vector.py` | 向量扩展迁移（可选） |

---

## 六、风险与注意事项

### 1. 性能风险
- jieba 分词：首次加载词典较慢，需预热
- 向量生成：批量调用 Embedding API 需考虑限流
- 任务队列：高频轮询 Redis 需监控性能

### 2. 兼容性风险
- WebSocket 需考虑代理/CDN 配置
- PGVector 扩展需 PostgreSQL 12+
- jieba 与现有停用词表可能冲突

### 3. 降级策略
- 分词失败 → 回退到正则提取
- 向量服务不可用 → 仅使用关键词检索
- Redis 不可用 → 回退到 asyncio.create_task
- WebSocket 断开 → 客户端轮询降级

### 4. 安全考虑
- WebSocket 需鉴权校验
- 任务队列需防任务注入
- 安全扫描规则需定期更新

---

## 七、预期收益

| 优化项 | 预期提升 |
|-------|---------|
| 中文分词 | 检索准确率 +30%~50% |
| 任务队列 | 支持并发处理 10+ 文档 |
| 实时推送 | 用户体验：进度反馈即时可见 |
| 向量检索 | 语义理解能力大幅提升 |
| 安全扫描 | 防止恶意文件上传 |
