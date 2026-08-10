"""
应用配置 - 基于 pydantic-settings 的类型安全配置
精简版：移除了合规、防沉迷、审核等非个人用户功能配置

支持从环境变量与 .env 文件加载配置，生产环境强制校验密钥强度。
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnv(str, Enum):
    LOCAL = "local"
    DEVELOPMENT = "development"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class LLMProvider(str, Enum):
    QWEN = "qwen"
    DEEPSEEK = "deepseek"
    DOUBAO = "doubao"
    ZHIPU = "zhipu"


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # 基础配置
    # v1 的正常产品运行形态是 Local Web：单用户、loopback、本地数据。
    app_env: AppEnv = AppEnv.LOCAL
    app_name: str = "socratic-learning-backend"
    app_version: str = "0.1.0"
    debug: bool = False
    host: str = "127.0.0.1"
    port: int = 8000
    private_app: bool = True
    enable_orchestrator_debug_api: bool = False
    cors_allowed_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173"
    )
    websocket_allowed_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:4173,http://127.0.0.1:4173,null,file://"
    )

    # Askora 管理的本地数据目录（PERSIST-003）。
    # 逻辑结构：{askora_data_dir}/askora.db、documents/、indexes/、cache/、jobs/、logs/。
    # 最终用户无需配置；如需迁移数据位置，可设置 ASKORA_DATA_DIR。
    askora_data_dir: str = "./data"

    # 数据库：v1 production-local 默认使用 Askora 管理的本地 SQLite。
    # 若未显式提供 DATABASE_URL，则解析为 {askora_data_dir}/askora.db。
    # PostgreSQL 仅用于 CI / 兼容性验证 / 未来可选服务模式，不是 v1 最终用户运行依赖。
    database_url: str = ""
    database_echo: bool = False
    database_pool_size: int = 20
    database_max_overflow: int = 10

    # Redis：可选，仅用于开发 / 缓存 / 兼容性优化，不是 v1 产品运行 requirement。
    # 默认留空：正常 Local Web 启动不会尝试连接 Redis。
    redis_url: str = ""
    redis_password: Optional[str] = None
    redis_pool_size: int = 50

    # 密钥管理（简化版）
    kek_master_key: str = "change-me-kek-key-at-least-32-bytes-long"

    # LLM
    llm_default_provider: LLMProvider = LLMProvider.QWEN
    llm_qwen_api_key: str = ""
    llm_qwen_model: str = "qwen-turbo"
    llm_deepseek_api_key: str = ""
    llm_deepseek_model: str = "deepseek-chat"
    llm_doubao_api_key: str = ""
    llm_doubao_model: str = "doubao-pro-32k"
    llm_zhipu_api_key: str = ""
    llm_zhipu_model: str = "glm-4.7-flash"
    llm_zhipu_base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    llm_zhipu_thinking_enabled: bool = False
    llm_math_provider: LLMProvider = LLMProvider.DEEPSEEK
    embedding_provider: str = "qwen"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2048
    llm_timeout: int = 30

    # 日志
    log_level: str = "INFO"
    log_format: str = "json"

    # 监控
    prometheus_enabled: bool = True
    prometheus_port: int = 9090

    # 限流
    rate_limit_user_per_minute: int = 20
    rate_limit_ip_per_minute: int = 1000

    # 本地文件存储（文档上传）
    local_storage_enabled: bool = True
    local_storage_base_path: str = "./data/documents"
    local_storage_max_file_size_mb: int = 50
    local_storage_max_total_size_gb: int = 2
    local_storage_chunk_min_tokens: int = 200
    local_storage_chunk_max_tokens: int = 800
    local_storage_archive_max_entries: int = 5000
    local_storage_archive_max_entry_size_mb: int = 50
    local_storage_archive_max_uncompressed_size_mb: int = 250
    local_storage_archive_max_compression_ratio: float = 100.0

    # Embedding 向量服务
    embedding_api_key: str = ""
    embedding_api_base: str = "https://dashscope.aliyuncs.com"
    embedding_model: str = "text-embedding-v2"
    embedding_dimension: int = 1536

    # Worker 任务队列
    worker_enabled: bool = True
    worker_max_concurrent: int = 5
    worker_poll_interval: float = 1.0

    @model_validator(mode="after")
    def validate_production_keys(self) -> "Settings":
        """生产环境强制校验密钥强度，防止使用默认/示例密钥。"""
        # 未显式提供 DATABASE_URL 时，解析到 Askora 管理的本地 SQLite。
        if not self.database_url:
            self.database_url = self.default_database_url
        if self.app_env == AppEnv.PRODUCTION:
            if not self.kek_master_key or len(self.kek_master_key) < 32:
                raise ValueError("KEK_MASTER_KEY must be at least 32 characters in production")
            if self.kek_master_key == "change-me-kek-key-at-least-32-bytes-long":
                raise ValueError("KEK_MASTER_KEY must not use the default value in production")
        if self.local_storage_chunk_min_tokens >= self.local_storage_chunk_max_tokens:
            raise ValueError(
                "LOCAL_STORAGE_CHUNK_MIN_TOKENS must be smaller than LOCAL_STORAGE_CHUNK_MAX_TOKENS"
            )
        if self.local_storage_archive_max_entries < 1:
            raise ValueError("LOCAL_STORAGE_ARCHIVE_MAX_ENTRIES must be positive")
        if self.local_storage_archive_max_entry_size_mb < 1:
            raise ValueError("LOCAL_STORAGE_ARCHIVE_MAX_ENTRY_SIZE_MB must be positive")
        if self.local_storage_archive_max_uncompressed_size_mb < 1:
            raise ValueError("LOCAL_STORAGE_ARCHIVE_MAX_UNCOMPRESSED_SIZE_MB must be positive")
        if self.local_storage_archive_max_compression_ratio <= 1:
            raise ValueError("LOCAL_STORAGE_ARCHIVE_MAX_COMPRESSION_RATIO must be greater than 1")
        return self

    @property
    def is_production(self) -> bool:
        return self.app_env == AppEnv.PRODUCTION

    @property
    def is_development(self) -> bool:
        return self.app_env == AppEnv.DEVELOPMENT

    @property
    def is_local(self) -> bool:
        return self.app_env == AppEnv.LOCAL

    @property
    def is_test(self) -> bool:
        return self.app_env == AppEnv.TEST

    @property
    def auto_create_tables(self) -> bool:
        return self.app_env in {AppEnv.LOCAL, AppEnv.DEVELOPMENT, AppEnv.TEST}

    @property
    def data_directory(self) -> Path:
        """Askora 管理的本地数据根目录（PERSIST-003）。"""
        return Path(self.askora_data_dir).resolve()

    @property
    def default_database_url(self) -> str:
        """未显式配置 DATABASE_URL 时使用的默认 SQLite 路径。"""
        return f"sqlite+aiosqlite:///{self.data_directory / 'askora.db'}"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]

    @property
    def websocket_origins(self) -> set[str]:
        return {
            origin.strip() for origin in self.websocket_allowed_origins.split(",") if origin.strip()
        }


settings = Settings()
